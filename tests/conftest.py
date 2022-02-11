import subprocess
import pytest
from flask_mail import Mail

import websmash
from websmash import app as flask_app

from _pytest.monkeypatch import MonkeyPatch


@pytest.fixture(scope="session")
def monkeysession(request):
    mp = MonkeyPatch()
    request.addfinalizer(mp.undo)
    return mp


@pytest.fixture(scope='session')
def app(request, tmpdir_factory, monkeysession):
    '''Flask application for test'''
    results_dir = tmpdir_factory.mktemp('results')
    flask_app.config['TESTING'] = True
    flask_app.config['FAKE_DB'] = True
    flask_app.config['RESULTS_PATH'] = str(results_dir)
    flask_app.config['MAIL_SUPPRESS_SEND'] = True
    flask_app.config['MAIL_DEFAULT_SENDER'] = "test@antismash.secondarymetabolites.org"
    flask_app.config['MAIL_HOST'] = 'localhost'
    flask_app.config['DARK_LAUNCH_PERCENTAGE'] = 0
    flask_app.config['LEGACY_JOBTYPE'] = "antismash5"
    mail = Mail()
    mail.init_app(flask_app)
    flask_app.mail = mail
    monkeysession.setattr(websmash, 'mail', mail)
    ctx = flask_app.app_context()
    ctx.push()

    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)
    return flask_app


@pytest.fixture(scope="session")
def fake_sequence(tmpdir_factory):
    """Fake sequence file to use for uploads"""
    seq_file = tmpdir_factory.mktemp('to_upload').join('test.fa')
    seq_file.write('>test\nATGACCGAGAGTACATAG\n')
    return seq_file


@pytest.fixture(scope="session")
def git_version():
    """Get the git version"""
    args = ['git', 'rev-parse', '--short', 'HEAD']
    prog = subprocess.Popen(args, stdout=subprocess.PIPE)
    output = prog.stdout.readline()
    git_ver = output.decode('utf-8').strip()
    return git_ver
