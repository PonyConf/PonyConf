Add a new conference
====================

We suppose our conference is hosted at ``cfp.example.org``.
The slides for this conference will be uploaded in ``/media/example/``.

Create a new ``Site`` object::

  $ ./manage.py shell
  $ from django.contrib.sites.models import Site
  $ Site.objects.create(domain='cfp.example.org', name='example')

The ``name`` field is the sub-directory in the media directory where upload slides.
The displayed name of the conference is stored in the ``Conference`` model.

Add the domain in ``ponyconf/local_settings.py``::

  ALLOWED_HOSTS = [ 'cfp.example.org' ]

Reload the configuration::

  $ touch touch_to_reload

Make sure you web server is configured to serve this new domain.

Configure the e-mails.

Go to ``https://cfp.example.org``, log-in and configure your conference.
