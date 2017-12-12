'''
shire.py
  come join in the adventure!
'''

#
# modules
#
import sqlite3
import pygal
from pygal.style import DarkGreenStyle
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, g, render_template, request, redirect, url_for, session

#
# config
#
DATABASE = 'data.db'

RACES = ['Dwarves', 'Humans', 'Elves', 'Hobbits']
CLASSES = ['Wizards', 'Warriors', 'Rangers', 'Enchanters']

NUM_RACES = {
    'dwarves' : 0,
    'humans'  : 0,
    'elves'   : 0,
    'hobbits' : 0
}

NUM_CLASSES = {
    'wizards'    : 0,
    'warriors'   : 0,
    'rangers'    : 0,
    'enchanters' : 0,
}

#
# app
#
app = Flask(__name__) # pylint: disable=C0103
app.secret_key = '9\n\xa8N,\x8b\xb2\xb44u\x12rgu\xfd\x8d&\x03\xecr6J\xd5\xf0'

#
# session
#
@app.before_request
def before_request():
    '''
    This function is run each time a request is made (before).
    '''
    g.user = None
    if 'username' in session:
        g.user = query_db('select * from user where username = ?',
                          [session['username']], one=True)
        if g.user:
            g.user = dict(g.user)

#
# routes
#
@app.errorhandler(404)
def page_not_found():
    '''
    Display a 404 page if the user tries to go to a nonexistent page.
    '''
    return render_template('404.html'), 404

@app.route('/')
def index():
    '''
    Home page route.
    '''
    if g.user:
        return redirect(url_for('quests'))

    return render_template('index.html')

@app.route('/users/')
def users():
    '''
    The users page shows a list of all usernames.
    '''
    all_users = query_db('select * from user')
    return render_template('users.html', all_users=all_users)

@app.route('/profile/')
def profile():
    '''
    The profile page displays information about a specific user.
    '''
    if g.user:
        return render_template('profile.html', user=g.user)

    return redirect(url_for('signup'))

@app.route('/quests/')
def quests():
    '''
    Display all quests, and the number of posts for each quest.
    '''
    all_quests = query_db('''select q.*, count(p.post_id) as post_count from
            quest q left join post p on p.quest_id=q.quest_id group by q.quest_id''')
    return render_template('quests.html', all_quests=all_quests)

@app.route('/quests/<int:quest_id>/', methods=['POST', 'GET'])
def quest(quest_id):
    '''
    This is the specific page for a particular quest, showing all posts for it.
    '''
    posts = query_db('''select * from post join user where
                     post.author_id=user.user_id and post.quest_id = ?''', [quest_id])
    error = None
    if g.user:
        if request.method == 'POST':
            if not request.form['text']:
                error = "Empty message"
            else:
                database = get_db()
                database.execute('insert into post (author_id,quest_id,text) values (?,?,?)',
                                 [g.user['user_id'], quest_id, request.form['text']])
                database.commit()
                return redirect(url_for('quest', quest_id=quest_id))
    return render_template('posts.html', posts=posts, error=error)

@app.route('/add_quest/', methods=['GET', 'POST'])
def add_quest():
    '''
    Add a new quest. We check to make sure the quest name isn't empty.
    '''
    error = ''
    if g.user:
        if request.method == 'POST':
            if not request.form['title']:
                error = "Missing quest title"
            else:
                database = get_db()
                database.execute('insert into quest (title) values (?)',
                                 [request.form['title']])
                database.commit()
                return redirect(url_for('quests'))
        return render_template('add_quest.html', error=error)
    else:
        return redirect(url_for('login'))

@app.route('/login/', methods=['GET', 'POST'])
def login():
    '''
    Log the user in. If they are already logged in, redirect to quests page.
    '''
    if g.user:
        return redirect(url_for('quests'))
    error = None
    if request.method == 'POST':
        user = get_user_info(request.form['username'])
        if user is None:
            error = 'Invalid username or password'
        elif not check_password(request.form['password'], user['pw_hash']):
            error = 'Invalid username or password'
        else:
            session['username'] = user['username']
            return redirect(url_for('quests'))
    return render_template('login.html', error=error)

@app.route('/signup/', methods=['GET', 'POST'])
def signup():
    '''
    Signup page. We validate username/password, and then create db entry if OK.
    '''
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
        elif get_user_info(request.form['username']) is not None:
            error = 'Username taken, please try another one'
        else:
            database = get_db()
            database.execute('''insert into user (username,pw_hash,race,class,gender)
                             values (?,?,?,?,?)''',
                             [request.form['username'],
                              hash_password(request.form['password']),
                              request.form['race'],
                              request.form['class'],
                              request.form['gender']])
            database.commit()
            return redirect(url_for('login'))
    return render_template('signup.html', error=error)

@app.route('/stats/')
def stats():
    '''
    Display some fun stats about user demographics in pretty charts.
    '''
    num_users = float(query_db('select count(*) as num_users from user', one=True)[0])

    if num_users < 1:
        race_chart = pygal.Pie(height=200, style=DarkGreenStyle)
        race_chart.title = 'races'
        for race in RACES:
            race_chart.add(race, 0)
        race_chart = race_chart.render_data_uri()

        class_chart = pygal.Pie(height=200, style=DarkGreenStyle)
        class_chart.title = 'classes'
        for cls in CLASSES:
            class_chart.add(cls, 0)
        class_chart = class_chart.render_data_uri()

        gender_chart = pygal.Pie(height=200, style=DarkGreenStyle)
        gender_chart.title = 'gender'
        gender_chart.add('Male', 0)
        gender_chart.add('Female', 0)
        gender_chart = gender_chart.render_data_uri()

        return render_template('stats.html', num_users=0, race_chart=race_chart,
                               class_chart=class_chart, gender_chart=gender_chart)

    NUM_RACES['dwarves'] = (query_db('select count(*) from user where race="Dwarf"',
                                     one=True)[0] / num_users) * 100
    NUM_RACES['humans'] = (query_db('select count(*) from user where race="Human"',
                                    one=True)[0] / num_users) * 100
    NUM_RACES['elves'] = (query_db('select count(*) from user where race="Elf"',
                                   one=True)[0] / num_users) * 100
    NUM_RACES['hobbits'] = (query_db('select count(*) from user where race="Hobbit"',
                                     one=True)[0]/num_users) * 100
    NUM_CLASSES['wizards'] = (query_db('select count(*) from user where class="Wizard"',
                                       one=True)[0] / num_users) * 100
    NUM_CLASSES['warriors'] = (query_db('select count(*) from user where class="Warrior"',
                                        one=True)[0] / num_users) * 100
    NUM_CLASSES['rangers'] = (query_db('select count(*) from user where class="Ranger"',
                                       one=True)[0] / num_users) * 100
    NUM_CLASSES['enchanters'] = (query_db('select count(*) from user where class="Enchanter"',
                                          one=True)[0] / num_users) * 100

    race_chart = pygal.Pie(height=200, style=DarkGreenStyle)
    race_chart.title = 'races'
    race_chart.add('Dwarves', round(NUM_RACES['dwarves'], 2))
    race_chart.add('Humans', round(NUM_RACES['humans'], 2))
    race_chart.add('Elves', round(NUM_RACES['elves'], 2))
    race_chart.add('Hobbits', round(NUM_RACES['hobbits'], 2))
    race_chart.value_formatter = lambda x: "%.2f" % x
    race_chart.value_formatter = lambda x: '%s%%' % x
    race_chart = race_chart.render_data_uri()

    class_chart = pygal.Pie(height=200, style=DarkGreenStyle)
    class_chart.title = 'classes'
    class_chart.add('Wizards', round(NUM_CLASSES['wizards'], 2))
    class_chart.add('Warriors', round(NUM_CLASSES['warriors'], 2))
    class_chart.add('Rangers', round(NUM_CLASSES['rangers'], 2))
    class_chart.add('Enchanters', round(NUM_CLASSES['enchanters'], 2))
    class_chart.value_formatter = lambda x: "%.2f" % x
    class_chart.value_formatter = lambda x: '%s%%' % x
    class_chart = class_chart.render_data_uri()

    gender_chart = pygal.Pie(height=200, style=DarkGreenStyle)
    gender_chart.title = 'gender'
    gender_chart.add('Male', round((query_db('select count(*) from user where gender="Male"',
                                             one=True)[0] / num_users) * 100, 1))
    gender_chart.add('Female', round((query_db('select count(*) from user where gender="Female"',
                                               one=True)[0] / num_users) * 100, 1))
    gender_chart.value_formatter = lambda x: "%.2f" % x
    gender_chart.value_formatter = lambda x: '%s%%' % x
    gender_chart = gender_chart.render_data_uri()

    return render_template('stats.html', num_users=int(num_users), race_chart=race_chart,
                           class_chart=class_chart, gender_chart=gender_chart)

@app.route('/logout')
def logout():
    '''
    Remove the username from the session if it's there.
    '''
    session.pop('username', None)
    return redirect(url_for('index'))

#
# database
#
@app.teardown_appcontext
def close_connection(exception):
    '''
    Close our database connection.
    '''
    #pylint: disable=unused-argument
    database = getattr(g, '_database', None)
    if database is not None:
        database.close()

def get_db():
    '''
    Returns a pointer to our database object, that can be used for queries.
    '''
    database = getattr(g, '_database', None)
    if database is None:
        database = g._database = sqlite3.connect(DATABASE)
    database.row_factory = sqlite3.Row
    return database

def query_db(query, args=(), one=False):
    '''
    Issue a query to the database, and return the data if there, or None.
    '''
    database = get_db()
    cursor = database.execute(query, args)
    data = cursor.fetchall()
    return (data[0] if data else None) if one else data

@app.cli.command('initdb')
def initdb_command():
    '''
    Called with 'flask initdb' to create the sqlite file before first use.
    '''
    init_db()
    print('Initialized database.')

def init_db():
    '''
    Read in our schema file and create the sqilite database file.
    '''
    with app.app_context():
        database = get_db()
        with app.open_resource('schema.sql', mode='r') as fileptr:
            database.cursor().executescript(fileptr.read())
        database.commit()

def get_user_info(username):
    '''
    Returns all database info for a user, or None if no data.
    '''
    data = query_db('select * from user where username = ?', [username])
    return data[0] if data else None

#
# authentication
#
def hash_password(plaintext_password):
    '''
    Wrapper function to generate a hash for a given string, i.e. password.
    '''
    return generate_password_hash(plaintext_password, method='pbkdf2:sha256', salt_length=30)

def check_password(plaintext_password, hashed_password):
    '''
    Wrapper function to check a password against a generated hash.
    '''
    return check_password_hash(hashed_password, plaintext_password)

#
# let shire be run with gunicorn
#
if __name__ == "__main__":
    app.run()
