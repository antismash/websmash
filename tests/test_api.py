import json
from flask import url_for


def test_version(client):
    response = client.get(url_for('get_version'))
    assert response.status_code == 200
    assert 'api' in response.json
    assert 'antismash_generation' in response.json
    assert response.json['api'] == '1.0.0'
    assert response.json['antismash_generation'] == '4'
