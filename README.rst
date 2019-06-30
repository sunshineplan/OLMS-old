OLMS
======

Overtime and Leave Management System `tutorial`_.

.. _tutorial: https://olms.shlib.cf


Install
-------

Install OLMS::

    $ pip install -e .

Or if you are using the master branch, install Flask from source before
installing OLMS::

    $ pip install -e ../..
    $ pip install -e .


Run
---

::

    $ export FLASK_APP=OLMS
    $ export FLASK_ENV=development
    $ flask init-db
    $ flask run

Or on Windows cmd::

    > set FLASK_APP=OLMS
    > set FLASK_ENV=development
    > flask init-db
    > flask run

Open http://127.0.0.1:5000 in a browser.
