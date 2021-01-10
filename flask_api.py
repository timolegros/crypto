from flask import Flask, request, jsonify
from blockchain import BlockChain
from uuid import uuid4

app = Flask(__name__)


node_one = str(uuid4()).replace('-', '')

blockchain = BlockChain(1)


@app.route('/get_chain', methods=['GET'])
def get_chain():
    # payload = [x.__dict__ for x in blockchain.chain]
    # payload = json.dumps(blockchain.chain, default=lambda x: x.__dict__)
    response = {'chain': blockchain.chain, 'length': len(blockchain.chain)}
    return jsonify(response), 200


@app.route('/mine_block', methods=['GET'])
def mine_block():
    block = blockchain.mine()
    response = {'message': 'Congratulations, you successfully mined a block!',
                'block': block.__dict__}
    # 'index': block.index,
    # 'timestamp': block.timestamp,
    # 'proof': block.hash,
    # 'previous_hash': block.prev_hash
    return jsonify(response), 200


@app.route('/validate_chain', methods=['GET'])
def validate_chain():
    validate = blockchain.validate_chain()
    if validate:
        response = {'message': 'The blockchain is valid!'}
    else:
        response = {'message': 'The blockchain is invalid!'}

    return jsonify(response), 200


@app.route('/add_transaction', method = ['POST'])
def add_transaction():





app.run(host='127.0.0.1', port=50000)
