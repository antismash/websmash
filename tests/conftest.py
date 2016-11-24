import pytest
from websmash import app as flask_app


@pytest.fixture(scope='session')
def app(request):
    '''Flask application for test'''
    flask_app.config['TESTING'] = True
    ctx = flask_app.app_context()
    ctx.push()

    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)
    return flask_app
