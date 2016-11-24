antiSMASH REST-LIKE API
=======================

[![Build Status](http://github.drone.secondarymetabolites.org/api/badges/antismash/websmash/status.svg)](http://github.drone.secondarymetabolites.org/antismash/websmash)

This is the REST-like API powering http://antismash.secondarymetabolites.org/

Installation
------------

```
pip install -r requirements.txt
```

Running the API
---------------

First, create a settings.cfg file:

```
############# Configuration #############
DEBUG = False
SECRET_KEY = "Better put a proper secret here"
# Path to antiSMASH output directory on disk
RESULTS_PATH = '/data/antismash/upload'
# URL path to antiSMASH results in the webapp
RESULTS_URL = '/upload'

# Flask-Mail settings
DEFAULT_RECIPIENTS = ["alice@example.com", "bob@example.com"]

# Redis settings
REDIS_URL = 'redis://your.redis.database:port/number'
# defaults to redis://localhost:6379/0
# You can also point at a Redis Sentinel instance using 'sentinel://sentinel.address:port/number'
#########################################
```

Then export the path to the settings file as `WEBSMASH_CONFIG` environment
variable and use a WSGI runner of your choice to run the app (I'm using uwsgi
in this example).

```
export WEBSMASH_CONFIG=/var/www/settings.cfg
uwsgi --pythonpath /var/www --http :5000 --module websmash:app --uid 33 --gid 33 --touch-reload /tmp/reload_websmash --daemonize /var/log/uwsgi.log
```

Now you can connect to the antiSMASH web api at port 5000. Now set up a reverse proxy to serve the web api from port 80.

License
-------

Just like antiSMASH, the web interface is available under the GNU AGPL version 3.
See the `LICENSE.txt` file for details.
