import json
from flask import url_for

from websmash import get_db


def test_version(client, app):
    response = client.get(url_for('get_version'))
    assert response.status_code == 200
    assert 'api' in response.json
    assert 'antismash_generation' in response.json
    assert 'taxon' in response.json
    assert response.json['api'] == '1.0.0'
    assert response.json['antismash_generation'] == '4'
    assert response.json['taxon'] == app.config['TAXON']


def test_api_submit_upload(client, fake_sequence):
    """Test submitting a job with an uploaded file"""
    fake_fh = open(str(fake_sequence), 'r')
    data = dict(seq=fake_fh)
    response = client.post(url_for('api_submit'), data=data)
    assert 200 == response.status_code
    assert 'id' in response.json

    job_key = 'job:{}'.format(response.json['id'])
    redis = get_db()
    assert redis.exists(job_key)


def test_api_submit_download(client):
    """Test submitting a job with a download from NCBI"""
    data = dict(ncbi='FAKE')
    response = client.post(url_for('api_submit'), data=data)
    assert 200 == response.status_code
    assert 'id' in response.json

    job_key = 'job:{}'.format(response.json['id'])
    redis = get_db()
    assert redis.exists(job_key)


def test_api_status_pending(client):
    """Test reading the status of a job"""
    data = dict(ncbi='FAKE')
    response = client.post(url_for('api_submit'), data=data)
    job_id = response.json['id']

    response = client.get(url_for('status', task_id=job_id))
    assert 200 == response.status_code
    assert response.json['short_status'] == 'pending'

    job_key = 'job:{}'.format(job_id)
    redis = get_db()
    redis.hset(job_key, 'status', 'done')
    response = client.get(url_for('status', task_id=job_id))
    assert 200 == response.status_code
    assert 'result_url' in response.json

    response = client.get(url_for('status', task_id='nonexistent'))
    assert 404 == response.status_code


def test_api_email_send(client, app):
    """Test sending a feedback email"""
    with app.mail.record_messages() as outbox:
        response = client.post(url_for('send_email'),
                               data=json.dumps(dict(email="test@example.com", message="Test message")),
                               content_type='application/json')
        assert 204 == response.status_code
        assert len(outbox) == 2

