from os import path
############# Configuration #############
DEBUG = True
SECRET_KEY = "development_key"
RESULTS_PATH = path.join(path.dirname(path.dirname(__file__)), 'results')
RESULTS_URL = '/upload'

# Flask-Mail settings
MAIL_SERVER = "smtpserv.uni-tuebingen.de"
DEFAULT_MAIL_SENDER = "kai.blin@biotech.uni-tuebingen.de"
DEFAULT_RECIPIENTS = ["kai.blin@biotech.uni-tuebingen.de"]

# Flask-SQLAlchemy settings
SQLALCHEMY_DATABASE_URI = 'sqlite:///../jobs.db'

# Flask-Redis settings
REDIS_URL = "redis://localhost:6379/0"
#########################################

