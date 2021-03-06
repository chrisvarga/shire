drop table if exists user;
create table user (
    user_id integer primary key autoincrement,
    username text not null,
    pw_hash text not null,
    race text not null,
    class text not null,
    gender text not null
);

drop table if exists post;
create table post (
    post_id integer primary key autoincrement,
    author_id integer not null,
    quest_id integer not null,
    text text not null,
    pub_date text
);

drop table if exists quest;
create table quest (
    quest_id integer primary key autoincrement,
    title text not null
);
