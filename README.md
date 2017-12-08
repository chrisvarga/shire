[![Build Status](https://travis-ci.org/chrisvarga/shire.svg?branch=master)](https://travis-ci.org/chrisvarga/shire)

# shire
## online role-playing forum

![alt tag](static/shire.png)


## Initial Database Setup
```
export FLASK_APP=shire.py
flask initdb
```

## Running Server
```
gunicorn --bind 0.0.0.0:8000 shire:app
```
