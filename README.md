[![Build Status](https://travis-ci.org/chrisvarga/shire.svg?branch=master)](https://travis-ci.org/chrisvarga/shire)

# shire
## online role-playing forum

![alt tag](static/shire.png)


## Installing Requirements
```
# From the project directory
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```


## Initial Database Setup
```
export FLASK_APP=shire.py
flask initdb
```

## Running Server
```
gunicorn --bind 0.0.0.0:8000 shire:app
```
