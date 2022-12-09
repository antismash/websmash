import subprocess
from typing import Union
from urllib.parse import urlparse

try:
    from fakeredis import FakeRedis
except ImportError:
    pass
from flask import Flask, g
from flask_mail import Mail
from redis import Redis
from redis.sentinel import Sentinel

import websmash.default_settings

app = Flask(__name__)
app.config.from_object(websmash.default_settings)
app.config.from_envvar('WEBSMASH_CONFIG', silent=True)
mail = Mail(app)

DataStore = Union["Redis[str]", "FakeRedis"]


def get_db() -> DataStore:
    redis_store = getattr(g, '_database', None)
    if redis_store is None:
        if 'FAKE_DB' in app.config and app.config['FAKE_DB']:
            redis_store = g._database = FakeRedis(encoding='utf-8', decode_responses=True)
        else:
            if app.config['REDIS_URL'].startswith('redis://'):
                redis_store = g._database = Redis.from_url(app.config['REDIS_URL'], encoding='utf-8',
                                                           decode_responses=True)
            elif app.config['REDIS_URL'].startswith('sentinel://'):
                parsed_url = urlparse(app.config['REDIS_URL'])
                service = parsed_url.path.lstrip('/')
                port = 26379
                if ':' in parsed_url.netloc:
                    host, str_port = parsed_url.netloc.split(':')
                    port = int(str_port)
                else:
                    host = parsed_url.netloc
                sentinel = Sentinel([(host, port)], socket_timeout=0.1)
                redis_store = sentinel.master_for(
                                        service, redis_class=Redis, socket_timeout=0.1,
                                        encoding='utf-8', decode_responses=True)
            else:
                raise ValueError(f"Invalid redis configuration: {app.config['REDIS_URL']}")
    return redis_store


def _get_git_version():
    args = ['git', 'rev-parse', '--short', 'HEAD']

    try:
        output = subprocess.check_output(args)
    except subprocess.CalledProcessError:
        output = b''

    return output.decode('utf-8').strip()


git_version = _get_git_version()

# These imports need to live here to avoid circular dependencies
import websmash.api  # noqa: E402
import websmash.error_handlers  # noqa: E402
