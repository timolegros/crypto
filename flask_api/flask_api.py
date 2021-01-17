from flask import Flask, request, jsonify
from Cryptocurrency.blockchain import BlockChain, Block
from Cryptocurrency.network import Node
from Cryptocurrency.mempool import Transaction


app = Flask(__name__)

first = Node(port='50001')
blockchain = BlockChain(1, first, '50000', '127.0.0.1')


@app.route('/get_chain', methods=['GET'])
def get_chain():
    payload = [x.__dict__ for x in blockchain.chain]
    # payload = json.dumps(blockchain.chain, default=lambda x: x.__dict__)
    response = {'chain': payload, 'length': len(blockchain.chain)}
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
    temp = [x.__dict__ for x in blockchain.chain]
    if blockchain.validate_chain(temp):
        response = {'message': 'The blockchain is valid!'}
    else:
        response = {'message': 'The blockchain is invalid!'}

    return jsonify(response), 200


@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    data = request.json['transaction']
    new_transaction = Transaction(data['sender'], data['receiver'], data['amount'], data['fee'], data['ID'])

    if blockchain.propagate_transaction(new_transaction):
        return jsonify({'message': 'Transaction successfully added'}), 201
    else:
        return jsonify({'message': 'Transaction already propagated'}), 201


@app.route('/update_node', methods=['POST'])
def update_node():
    new_chain = []
    chain = request.json['chain']
    for x in chain:
        new_block = Block(x['index'], x['transactions'], x['prev_hash'], x['nonce'], x['timestamp'])
        new_block.hash = x['hash']
        new_chain.append(new_block)

    transactions = request.json['transactions']
    transactions = [Transaction(x['sender'], x['receiver'], x['amount'], x['fee'], x['ID']) for x in transactions]

    blockchain.chain = new_chain
    blockchain.MemPool.unverified_transactions = transactions

    return jsonify({'message': 'Successful'}), 201


@app.route('/get_unverified_transactions', methods=['GET'])
def get_unverified_transactions():
    payload = [x.__dict__ for x in blockchain.MemPool.unverified_transactions]
    return jsonify({'message': payload}), 200


@app.route('/add_node', methods=['POST'])
def add_node():
    data = request.json['node']
    new_node = Node(data['path'], data['port'], data['address'])
    blockchain.Network.add_node(new_node)
    response = {'message': 'Node successfully connected!'}
    return jsonify(response), 201


@app.route('/transactions_verified', methods=['POST'])
def transactions_verified():
    print(request.json)
    data = request.json['transactions']

    # remove transactions from this MemPool
    transactions = [Transaction(x['sender'], x['receiver'], x['amount'], x['fee'], x['ID']) for x in data]
    validity = blockchain.MemPool.remove_transactions(transactions)

    # if transactions have already been removed then this node has already propagated this action to the other nodes
    if validity:
        # propagate remove call to the other nodes
        blockchain.Network.broadcast({'transactions': data}, '/transactions_verified')

    response = {'message': 'Transactions successfully verified and removed from MemPool'}
    return jsonify(response), 201


@app.route('/chain_consensus', methods=['GET'])
def chain_consensus():
    blockchain.compare_chains()
    return jsonify({'message': 'The chain was updated!'}), 200


@app.route('/connect_to_network', methods=['GET'])
def connect_to_network():
    blockchain.Network.connect_to_network()
    return jsonify({'message': 'Node info sent to network'})


@app.route('/get_nodes', methods=['GET'])
def get_nodes():
    payload = [x.__dict__ for x in blockchain.Network.nodes]
    return jsonify({'message': payload}), 200


@app.route('/receive_data', methods=['POST'])
def receive_data():
    print(request.json)
    return jsonify({'message': 'It works'}), 200


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=50000)
