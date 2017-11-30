Installation guide
==================

Typography
----------

Commands starting with ``#`` must be run as ``root`` user.

Commands starting with ``$`` must be run as ``ponyconf`` user.


Requirements
------------

PonyConf have been tested with python 3.5 and 3.6.


Preparation
-----------

Create a user ``ponyconf``::

  # useradd -r -m -d /srv/www/ponyconf ponyconf

The directory ``/srv/www`` must exist before.
An other base directory is fine.

The following commands are run as ``ponyconf`` user::

  # su - ponyconf

Create ``log`` and ``webdir`` directories::

  $ mkdir log webdir

Clone the repository in the ``app`` directory::

  $ git clone https://github.com/PonyConf/PonyConf.git app

Configuration
-------------

Copy the example configuration file::

  $ cp app/ponyconf/local_settings.py.example app/ponyconf/local_settings.py

Set the ``SECRET_KEY`` value.
You can generate a secret key with ``openssl``::

  $ openssl rand -base64 32

Verify emails related settings values.
Set your timezone and language code.

If you want to use another database than the default one (SQLite), set ``DATABASES``.
You can find the syntax in the `django documentation`_.

.. _django documentation: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-DATABASES
