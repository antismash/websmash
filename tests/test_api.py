from flask import url_for

from websmash import get_db


def test_version(client):
    response = client.get(url_for('get_version'))
    assert response.status_code == 200
    assert 'api' in response.json
    assert 'antismash_generation' in response.json
    assert response.json['api'] == '1.0.0'
    assert response.json['antismash_generation'] == '4'


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
