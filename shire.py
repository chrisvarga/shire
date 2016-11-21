#
# modules
#
from flask import Flask, g, render_template, request, redirect, url_for, session
import datetime
import sqlite3
import time
import bcrypt

#
# config
#
DATABASE = 'data.db'

#
# app
#
app = Flask(__name__)
app.secret_key = '9\n\xa8N,\x8b\xb2\xb44u\x12rgu\xfd\x8d&\x03\xecr6J\xd5\xf0'

#
# session
#
@app.before_request
def before_request():
    g.user = None
    if 'username' in session:
        g.user = query_db('select * from user where username = ?',
                [session['username']],one=True)
        if g.user:
            g.user = dict(g.user)

#
# routes
#
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/')
def index():
    if g.user:
        return redirect(url_for('quests'))
    else:
        return render_template('index.html')

@app.route('/profile/')
def profile():
    if g.user:
        return render_template('profile.html',user=g.user)
    else:
        return redirect(url_for('signup'))

@app.route('/quests/')
def quests():
    quests = query_db('''select q.*, count(p.post_id) as post_count from
            quest q left join post p on p.quest_id=q.quest_id group by q.quest_id''')
    return render_template('quests.html', quests=quests)

@app.route('/quests/<int:quest_id>/', methods=['POST','GET'])
def quest(quest_id):
    posts = query_db('''select * from post join user where post.author_id=user.user_id and post.quest_id = ?''',[quest_id])
    error = None
    if g.user:
        if request.method == 'POST':
            if not request.form['text']:
                error = "Empty message"
            else:
                db = get_db()
                db.execute('insert into post (author_id,quest_id,text) values (?,?,?)',
                        [g.user['user_id'],quest_id,request.form['text']])
                db.commit()
                return redirect(url_for('quest',quest_id=quest_id))
    return render_template('posts.html', posts=posts, error=error)

@app.route('/add_quest/', methods=['GET', 'POST'])
def add_quest():
    error = None
    if g.user:
        if request.method == 'POST':
            if not request.form['title']:
                error = "Missing quest title"
            else:
                db = get_db()
                db.execute('insert into quest (title) values (?)',
                        [request.form['title']])
                db.commit()
                return redirect(url_for('quests'))
        return render_template('add_quest.html',error=error)
    else:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('quests'))
    error = None
    if request.method == 'POST':
        user = get_user_info(request.form['username'])
        if user is None:
            error = 'Invalid username or password'
        elif not check_password(request.form['password'],user['pw_hash']):
            error = 'Invalid username or password'
        else:
            session['username'] = user['username']
            return redirect(url_for('quests'))
    return render_template('login.html', error=error)

@app.route('/signup/', methods=['GET', 'POST'])
def signup():
    if g.user:
        return redirect(url_for('profile'))
    error = None
    if request.method == 'POST':
        if not request.form['username']:
            error = 'Missing username'
        elif not request.form['password']:
            error = 'Missing password'
        elif request.form['password'] != request.form['password2']:
            error = 'The two passwords do not match'
        elif len(request.form['password']) < 5:
            error = 'Password must be at least 5 characters'
        elif not request.form['race']:
            error = 'Missing race'
        elif not request.form['class']:
            error = 'Missing class'
        elif not request.form['gender']:
            error = 'Missing gender'
        elif get_user_info(request.form['username']) is not None:
            error = 'Username taken, please try another one'
        else:
            db = get_db()
            db.execute('''insert into user (username,pw_hash,race,class,gender)
                    values (?,?,?,?,?)''',[request.form['username'],
                        hash_password(request.form['password']),
                        request.form['race'],request.form['class'],
                        request.form['gender']])
            db.commit()
            return redirect(url_for('login'))
    return render_template('signup.html', error=error)

@app.route('/stats/')
def stats():
    num_dwarves = query_db('select count(*) from user where race="Dwarf"',one=True)
    num_humans = query_db('select count(*) from user where race="Human"',one=True)
    num_elves = query_db('select count(*) from user where race="Elf"',one=True)
    num_hobbits = query_db('select count(*) from user where race="Hobbit"',one=True)
    num_users = query_db('select count(*) from user',one=True)
    num_wizards = query_db('select count(*) from user where class="Wizard"',one=True)
    num_warriors = query_db('select count(*) from user where class="Warrior"',one=True)
    num_rangers = query_db('select count(*) from user where class="Ranger"',one=True)
    num_enchanters = query_db('select count(*) from user where class="Enchanter"',one=True)
    stats = {
        'num_dwarves'    : num_dwarves[0],
        'num_humans'     : num_humans[0],
        'num_elves'      : num_elves[0],
        'num_hobbits'    : num_hobbits[0],
        'num_users'      : num_users[0],
        'num_wizards'    : num_wizards[0],
        'num_warriors'   : num_warriors[0],
        'num_rangers'    : num_rangers[0],
        'num_enchanters' : num_enchanters[0]
    }
    return render_template('stats.html', stats=stats)

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect(url_for('index'))

#
# database
#
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    return db

def query_db(query, args=(), one=False):
    db = get_db()
    cur = db.execute(query, args)
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv

@app.cli.command('initdb')
def initdb_command():
    init_db()
    print('Initialized database.')

def init_db():
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

def get_user_info(username):
    rv = query_db('select * from user where username = ?', [username])
    return rv[0] if rv else None

#
# authentication
#
def hash_password(plaintext_password):
    return bcrypt.hashpw(plaintext_password, bcrypt.gensalt())

def check_password(plaintext_password, hashed_password):
    return bcrypt.checkpw(plaintext_password, hashed_password)
