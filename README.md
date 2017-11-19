PonyConf
========
[![Build Status](https://travis-ci.org/toulibre/PonyConf.svg?branch=master)](https://travis-ci.org/toulibre/PonyConf)
[![Coverage Status](https://coveralls.io/repos/github/toulibre/PonyConf/badge.svg?branch=master)](https://coveralls.io/github/toulibre/PonyConf?branch=master)

Organise your conferences

- Jabber : [ponyconf@chat.cannelle.eu.org](https://jappix.cannelle.eu.org/?r=ponyconf@chat.cannelle.eu.org)
- IRC: #ponyconf on freenode


HowTo Test
----------

(you should work on a virtualenv)

```bash
git clone --recursive git@github.com:toulibre/PonyConf.git
cd PonyConf
pip install -U -r requirements.txt
./manage.py migrate
./manage.py runserver
./manage.py createsuperuser
```

HowTo update translations
-------------------------

```bash
./manage.py makemessages
poedit locale/fr/LC_MESSAGES/django.po
./manage.py compilemessages
```
