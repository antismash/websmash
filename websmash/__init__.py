from flask import Flask
from flaskext.mail import Mail
from flaskext.sqlalchemy import SQLAlchemy
from flaskext.downloader import Downloader
from werkzeug import SharedDataMiddleware
from os import path

############# Configuration #############
DEBUG = True
SECRET_KEY = "development_key"
RESULTS_PATH = path.join(path.dirname(path.dirname(__file__)), 'results')
NCBI_URL = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
NCBI_URL += '?db=protein&email="%s"&tool="antiSMASH"&val="%s"&dopt=gbwithparts'

# Flask-Mail settings
MAIL_SERVER = "smtpserv.uni-tuebingen.de"
DEFAULT_MAIL_SENDER = "kai.blin@biotech.uni-tuebingen.de"
DEFAULT_RECIPIENTS = ["kai.blin@biotech.uni-tuebingen.de"]

# Flask-SQLAlchemy settings
SQLALCHEMY_DATABASE_URI = 'sqlite:///../jobs.db'

# Flask-Downloader settings
DEFAULT_DOWNLOAD_DIR = RESULTS_PATH
#########################################

app = Flask(__name__)
app.config.from_object(__name__)
app.wsgi_app = SharedDataMiddleware(app.wsgi_app,
                                    {'/results': RESULTS_PATH,
                                     '/robots.txt': path.join(path.join(app.root_path, 'static'), 'robots.txt'),
                                     '/favicon.ico': path.join(path.join(app.root_path, 'static'), 'favicon.ico')})
mail = Mail(app)
db = SQLAlchemy(app)
dl = Downloader(app)

import websmash.models
import websmash.views
