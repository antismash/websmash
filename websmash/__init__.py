from flask import Flask
from flask.ext.mail import Mail
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.downloader import Downloader
from werkzeug import SharedDataMiddleware
from os import path

app = Flask(__name__)
import websmash.default_settings
app.config.from_object(websmash.default_settings)
app.config.from_envvar('WEBSMASH_CONFIG', silent=True)
app.wsgi_app = SharedDataMiddleware(app.wsgi_app,
                                    {app.config['RESULTS_URL']: app.config['RESULTS_PATH'],
                                     '/robots.txt': path.join(path.join(app.root_path, 'static'), 'robots.txt'),
                                     '/favicon.ico': path.join(app.root_path, 'static', 'images', 'favicon.ico')})
mail = Mail(app)
db = SQLAlchemy(app)
dl = Downloader(app)

import websmash.models
import websmash.views
