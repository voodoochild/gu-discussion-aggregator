Discussion Aggregator
=====================

Started during the [Guardian](http://gu.com)'s &lsquo;discovery week&rsquo;, this is a small Flask
app which consumes data from the [Guardian Discussion API](http://discussionapi.guardian.co.uk/discussion-api/docs)
and [Guardian Content API](http://content.guardianapis.com/) to produce new JSON
endpoints. It uses a Redis-backed Celery message queue. You will probably want to
use something like [Gunicorn](http://gunicorn.org/) and [RabbitMQ](http://www.rabbitmq.com/) in production.


Installation
------------

- Install Redis

        $ sudo apt-get install redis-server

- Create a virtualenv and install required packages

        $ virtualenv venv --no-site-packages
        $ source venv/bin/activate
        $ pip install -r requirements.txt

- Run the app and a Celery worker (in separate terminal windows)

        $ python app.js
        $ celery -A app worker --loglevel=info


Endpoints
---------

- [/comments/latest/&lt;userid&gt;](http://localhost:5000/comments/latest/1143370) &ndash; breaks the user's last 50 comments down by section


Additional
----------

### Caching

Comment data is cached in Redis for 6 hours by default. To change this, give
`CACHE_DATA_FOR` whichever value you want in seconds.

### Celery

Celery is configured to use locally installed Redis as its backend. If you want
to use something else, or have Redis configured to use non-default settings, you
need to change `BROKER_URL` and `CELERY_RESULT_BACKEND`. See the [Celery documentation](http://docs.celeryproject.org/en/latest/getting-started/brokers/index.html)
for details of alternative brokers.
