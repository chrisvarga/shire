# shire
## online role-playing forum

![alt tag](static/shire.png)

## Initial Setup
```
git clone https://github.com/chrisvarga/shire.git
cd shire
./setup
```

## Running Server
```
source env/bin/activate
gunicorn --bind 0.0.0.0:8000 shire:app
```
