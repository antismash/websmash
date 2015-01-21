from flask import Flask, g
from flask.ext.mail import Mail
from flask.ext.downloader import Downloader
from werkzeug import SharedDataMiddleware
from os import path
from redis import Redis

app = Flask(__name__)
import websmash.default_settings
app.config.from_object(websmash.default_settings)
app.config.from_envvar('WEBSMASH_CONFIG', silent=True)
app.wsgi_app = SharedDataMiddleware(app.wsgi_app,
                                    {app.config['RESULTS_URL']: app.config['RESULTS_PATH'],
                                     '/robots.txt': path.join(path.join(app.root_path, 'static'), 'robots.txt'),
                                     '/favicon.ico': path.join(app.root_path, 'static', 'images', 'favicon.ico')})
mail = Mail(app)


def get_db():
    redis_store = getattr(g, '_database', None)
    if redis_store is None:
        if 'FAKE_DB' in app.config and app.config['FAKE_DB']:
            from mockredis import mock_redis_client
            redis_store = g._database = mock_redis_client()
        else:
            redis_store = g._database = Redis.from_url(app.config['REDIS_URL'])
    return redis_store

dl = Downloader(app)

import websmash.models
import websmash.views
