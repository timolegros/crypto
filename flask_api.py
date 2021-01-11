from flask import Flask, request, jsonify
from blockchain import BlockChain,Transaction, Node
from uuid import uuid4

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
    data = request.form['transaction']
    new_transaction = Transaction(data['sender'], data['receiver'], data['amount'], data['fee'], data['ID'])

    if blockchain.propagate_transaction(new_transaction):
        return jsonify({'message': 'Transaction successfully added'})
    else:
        return 400


@app.route('/add_node', methods=['POST'])
def add_node():
    data = request.form['node']
    new_node = Node(data['path'], data['port'], data['address'])
    blockchain.Network.add_node(new_node)
    response = {'message': 'Node successfully connected!'}
    return jsonify(response), 201


@app.route('/transactions_verified', methods=['POST'])
def transactions_verified():
    data = request.form['transactions']

    # remove transactions from this MemPool
    transactions = [Transaction(x['sender'], x['receiver'], x['amount'], x['fee'], x['ID']) for x in data]
    validity = blockchain.MemPool.remove_transactions(transactions)

    # if transactions have already been removed then this node has already propagated this action to the other nodes
    if validity:
        # propagate remove call to the other nodes
        blockchain.Network.broadcast(data, '/transactions_verified')

    response = {'message': 'Transactions successfully verified and removed from MemPool'}
    return jsonify(response), 201


@app.route('/chain_consensus', methods=['GET'])
def chain_consensus():
    blockchain.consensus()
    return jsonify({'message': 'The chain was updated!'}), 200


app.run(host='127.0.0.1', port=50000)
