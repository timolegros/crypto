# USE python -m pytest tests/ TO INITIATE ALL TESTS -- This is due to fixture importing modules


from fixtures import client  # DO NOT REMOVE THIS IMPORT BC IT IS USED EVEN IF PYCHARM SAYS IT IS NOT
from flask import json


def test_get_chain(client):
    response = client.get('/get_chain')

    data = json.loads(response.get_data(as_text=True))
    chain = data['chain']
    length = data['length']

    assert response.status_code == 200
    assert len(chain) == length
    assert chain[0]['index'] == 0
    assert chain[0]['nonce'] == 0
    assert chain[0]['prev_hash'] == '0'
    assert chain[0]['transactions'] == []


def test_mine_block(client):
    client.get('get_chain')
    client.get('mine_block')
    response = client.get('get_chain')

    data = json.loads(response.get_data(as_text=True))
    chain = data['chain']
    length = data['length']

    assert response.status_code == 200
    assert len(chain) == length
    assert chain[1]['index'] == 1
    assert type(chain[1]['nonce']) == int
    assert chain[1]['prev_hash'] == chain[0]['hash']
    assert chain[1]['transactions'] == []


def test_validate_chain(client):
    client.get('get_chain')
    client.get('mine_block')
    response = client.get('get_chain')

    data = json.loads(response.get_data(as_text=True))
    chain = data['chain']
    length = data['length']

    assert response.status_code == 200
    assert len(chain) == length
    assert chain[1]['index'] == 1
    assert type(chain[1]['nonce']) == int
    assert chain[1]['prev_hash'] == chain[0]['hash']
    assert chain[1]['transactions'] == []

    new_response = client.get('validate_chain')
    new_data = json.loads(new_response.get_data(as_text=True))

    assert new_data['message'] == 'The blockchain is valid!'