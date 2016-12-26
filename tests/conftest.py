import pytest
from websmash import app as flask_app


@pytest.fixture(scope='session')
def app(request, tmpdir_factory):
    '''Flask application for test'''
    results_dir = tmpdir_factory.mktemp('results')
    flask_app.config['TESTING'] = True
    flask_app.config['FAKE_DB'] = True
    flask_app.config['RESULTS_PATH'] = str(results_dir)
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