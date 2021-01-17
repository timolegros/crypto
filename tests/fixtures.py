import pytest
from flask_api import flask_api

@pytest.fixture
def client():
    return flask_api.app.test_client()
#
#
# @pytest.fixture
# def transaction():
#     return {'transactions': [
#                 {
#                     "sender": "Tim",
#                     "receiver": "Div",
#                     "amount": "100",
#                     "fee": "0.1",
#                     "ID": "123456789"
#                 },
#                 {
#                     "sender": "Raghu",
#                     "receiver": "Tim",
#                     "amount": "100",
#                     "fee": "0.05",
#                     "ID": "987654321"
#                 }]
#             }
#
