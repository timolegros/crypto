# DO NOT REMOVE THIS IMPORT BC IT IS USED EVEN IF PYCHARM SAYS IT IS NOT
from fixtures import client, transactions

from flask import json


def test_get_unverified(client):
    response = client.get('/get_unverified_transactions')
    assert response.status_code == 200

    data = json.loads(response.get_data(as_text=True))

    assert data['Transactions'] == []


def test_add_transaction(client, transactions):
    response = client.post('add_transaction', json=transactions)
    assert response.status_code == 201

    response = client.get('/get_unverified_transactions')
    assert response.status_code == 200

    data = json.loads(response.get_data(as_text=True))

    assert data['Transactions'][0] == transactions['transaction']



