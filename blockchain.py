import datetime
from hashlib import sha256
import json
import requests
from network import Network, Node
from mempool import MemPool


class BlockChain:

    def __init__(self, miningDiff, Node2, port='50000', url='127.0.0.1'):
        # chain and unverified_transactions are both lists of dictionary's since blocks and transactions are added with
        # the .__dict__ extension
        self.chain = []
        self.MemPool = MemPool(10, 100)

        # initialize this node and network
        self.node = Node(url, port)
        self.Network = Network(self.node, [Node2])
        # self.Network.connect_to_network()

        self.create_genesis()
        self.miningDiff = miningDiff

    def create_genesis(self):
        """
        Creates the genesis (first) block of the blockchain
        """
        genesis_block = Block(0, [], "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)

    def proof_of_work(self, block):
        """
        Called when a miner wants to create a block in order to store transactions and add to the chain -- the hash
        computed here becomes the blocks hash
        """
        block.nonce = 0
        computed_hash = block.compute_hash()
        while computed_hash[:self.miningDiff] != '0' * self.miningDiff:
            block.nonce += 1
            computed_hash = block.compute_hash()

        return computed_hash

    def add_block(self, block, proof_computed_hash):
        prev_hash = self.last_block.hash
        if prev_hash != block.prev_hash or not self.check_proof(block, proof_computed_hash):
            return False
        block.hash = proof_computed_hash
        self.chain.append(block)

        return True

    def check_proof(self, block, computed_hash):
        """
        Checks if the computed_hash is valid. computed_hash should be equal to block.computed_hash() because block.nonce
        was updated in proof_of_work()
        :param block: the block in question
        :param computed_hash: the hash that results from the work of a miner
        :return:
        """
        return (computed_hash[:self.miningDiff] == '0' * self.miningDiff) and computed_hash == block.compute_hash()

    def mine(self):
        # if self.unverified_transactions:
        last_block = self.last_block
        obj_transactions = self.MemPool.get_top_transactions()
        # new_transactions = [x.__dict__ for x in obj_transactions]
        new_transactions = self.obj_to_dict(obj_transactions)
        new_block = Block(last_block.index + 1, transactions=new_transactions, prev_hash=last_block.hash)
        proof_work = self.proof_of_work(new_block)
        self.add_block(new_block, proof_work)

        # self.MemPool.remove_transactions

        # removes all the verified transactions
        if self.MemPool.remove_transactions(obj_transactions):
            self.Network.broadcast({'transactions': new_transactions}, 'transactions_verified')

        return new_block
        # else:
        #     return False

    def validate_chain(self, chain):
        for i in range(len(self.chain) - 1):
            if chain[i]['hash'] != chain[i + 1]['prev_hash']:
                return False
            elif chain[i]['hash'][:self.miningDiff] != '0' * self.miningDiff and i != 0:
                return False
        return True

    def consensus(self):
        network = self.Network.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'{node.full_url}/get_chain')
            if response.status_code == 200:
                node_chain_length = response.json()['length']
                node_chain = response.json()['chain']
                if node_chain_length > max_length and self.validate_chain(node_chain):
                    max_length = node_chain_length
                    longest_chain = node_chain
        if longest_chain:
            new_chain = []
            for x in longest_chain:
                new_block = Block(x['index'], x['transactions'], x['prev_hash'], x['nonce'], x['timestamp'])
                new_block.hash = x['hash']
                new_chain.append(new_block)
            self.chain = new_chain
            return True
        else:
            return False

    def propagate_transaction(self, transaction):
        # makes sure the transaction had not already been added
        for x in self.MemPool.unverified_transactions:
            if transaction.ID == x.ID:
                return False

        # adds the transaction to memPool and propagates the transaction to the other node MemPools
        self.MemPool.insert_single_transaction(transaction)
        self.Network.broadcast({'transaction': transaction.__dict__}, 'add_transaction')

        return True

    def update_node(self, node):
        # transactions = [x.__dict__ for x in self.MemPool.unverified_transactions]
        transactions = self.obj_to_dict(self.MemPool.unverified_transactions)
        # chain = [x.__dict__ for x in self.chain]
        chain = self.obj_to_dict(self.chain)
        url = node.full_url + '/update_node'
        requests.post(url, json={"chain": chain, "transactions": transactions})

    def obj_to_dict(self, objects):
        if isinstance(objects, list):
            return [x.__dict__ for x in objects]
        else:
            return objects.__dict__

    @property
    def last_block(self):
        return self.chain[-1]


class Block:

    def __init__(self, index, transactions, prev_hash, nonce=0, timestamp=str(datetime.datetime.now())):
        self.index = index
        self.nonce = nonce
        self.transactions = transactions
        self.timestamp = timestamp
        self.prev_hash = prev_hash

    def compute_hash(self):
        """Simple function to calculate the hash given the current state of the block"""
        block = json.dumps(self.__dict__, sort_keys=True).encode()
        return sha256(block).hexdigest()

    def __repr__(self):
        return f"""Transactions: {self.transactions}\n
                        Proof: {self.nonce}\n
                        Previous Hash: {self.prev_hash}\n
                        Creation date: {self.timestamp}"""

    def __str__(self):
        return f"""Transactions: {self.transactions}\n
                Proof: {self.nonce}\n
                Previous Hash: {self.prev_hash}\n
                Creation date: {self.timestamp}"""








# TODO: Test transaction features as well as adding nodes/transactions 3 way
# TODO: Reorganize classes and flask functions for simplicity -- class inheritance simplification?

# coin in which power/hardware does not affect performance of mining -- something tied into productivity/good output
# so reward is not computing power based but productivity based (open source contributions based?)
