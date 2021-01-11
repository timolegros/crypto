import datetime
from hashlib import sha256
import json
from urllib.parse import urlparse
import requests
from uuid import uuid4


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

        # removes all the verified transactions
        if not self.MemPool.remove_transactions(block.transactions):
            self.Network.broadcast([x.__dict__ for x in block.transactions], 'transactions_verified')

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
        new_transactions = self.MemPool.get_top_transactions()
        new_transactions = [x.__dict__ for x in new_transactions]
        new_block = Block(last_block.index + 1, transactions=new_transactions, prev_hash=last_block.hash)
        proof_work = self.proof_of_work(new_block)
        self.add_block(new_block, proof_work)
        self.MemPool.remove_transactions(new_transactions)

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
            self.chain = [Block(x['index'], x['transactions'], x['prev_hash'], x['nonce'], x['timestamp']) for x in
                          longest_chain]
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

    @property
    def last_block(self):
        return self.chain[-1]


class Transaction:

    def __init__(self, sender, receiver, amount, fee, ID=str(uuid4()).replace('-', '')):
        self.ID = ID
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.fee = fee

    def __repr__(self):
        return f"{self.sender} sent {self.amount}$ to {self.receiver} for a fee of: {self.fee} --- ID: {self.ID}"

    def __str__(self):
        return f"{self.sender} sent {self.amount}$ to {self.receiver} for a fee of: {self.fee} --- ID: {self.ID}"

    def __eq__(self, other):
        """
        Ensures that the equality of Transaction objects is defined by their actual values and not identity.
        :param other: another Transaction object
        :return: True if the Transaction objects have the same __dict__ and False otherwise
        """
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)


class MemPool:
    # TODO: Devise method of recording transaction history so that if collision occurs transactions that were verified
    # TODO: but aren't anymore get moved

    def __init__(self, max_tran_per_block, max_tran_per_MemPool):
        # transactions ordered from greatest to least
        self.unverified_transactions = []
        # the maximum number of transactions that can be put into a block
        self.max_tran_per_block = max_tran_per_block
        # the maximum number of transactions that an instance of the MemPool can hold
        self.max_tran_per_MemPool = max_tran_per_MemPool

    def insert_single_transaction(self, transaction):
        """
        Inserts a transaction in the unverified transaction list in its correct place in the order of greatest to least
        transaction fee
        :param transaction: A transaction object
        :return: False if the MemPool is full and the index where the transaction was inserted if successful
        """
        if 1 + len(self.unverified_transactions) > self.max_tran_per_MemPool:
            return False
        elif transaction not in self.unverified_transactions:
            new_fee = transaction.fee
            if self.unverified_transactions:
                for i in range(len(self.unverified_transactions)):
                    if new_fee >= self.unverified_transactions[i].fee:
                        self.unverified_transactions.insert(i, transaction)
                        return i, len(self.unverified_transactions)
            else:
                self.unverified_transactions.append(transaction)
                return 0, len(self.unverified_transactions)

    def insert_multiple_transactions(self, transactions):
        """
        Inserts a batch of transactions and orders them by transaction fee
        :param transactions: a list of transaction objects
        :return: False if the MemPool is full and the number of unverified transactions if successful
        """
        if len(transactions) + len(self.unverified_transactions) > self.max_tran_per_MemPool:
            return False
        else:
            self.unverified_transactions.extend(transactions)
            self.unverified_transactions.sort(key=lambda x: x.fee, reverse=True)
            return len(self.unverified_transactions)

    def remove_transactions(self, transactions):
        removed = False
        for x in transactions:
            try:
                index = self.get_transaction_index(x)
                if index:
                    del self.unverified_transactions[self.get_transaction_index(x)]
                    removed = True
                else:
                    pass
            except Exception as error:
                pass
        return removed

    def get_top_transactions(self):
        return self.unverified_transactions[:self.max_tran_per_block]

    def get_transaction_index(self, transaction):
        for x in range(len(self.unverified_transactions)):
            if transaction.ID == self.unverified_transactions[x].ID:
                return x

        return False


class Node:

    def __init__(self, path='127.0.0.1', port='50000', address=str(uuid4()).replace('-', '')):
        self.path = path
        self.port = port
        self.address = address

    @property
    def full_url(self):
        return 'http://' + self.path + ':' + self.port

    def __repr__(self):
        return f"Node url: {self.full_url}\nNode Address: {self.address}"

    def __str__(self):
        return f"Node url: {self.full_url}\nNode Address: {self.address}"

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)


class Network:

    def __init__(self, current_node, nodes):
        self.current_node = current_node
        self.nodes = nodes
        self.connected = False

    def list_nodes(self):
        for node in self.nodes:
            print(node)

    def add_node(self, node):
        """
        Adds a new node to this network and propagates the node to all the other nodes in this network
        :param node: The node to be added to this Network log
        :return: True if the node is added to this network and false if the node is already in the network
        """
        if node not in self.nodes:
            # appends node to this instance of the network
            self.nodes.append(node)
            # propagates the new node to all of this networks connected nodes
            self.broadcast({'node': node.__dict__}, 'add_node')
            return True
        else:
            # propagation from node to node stops if the node is already in this network (it has already propagated
            # the new node its own network
            return False

    def connect_to_network(self):
        payload = {'node': self.current_node.__dict__}
        self.broadcast(payload, 'add_node')
        self.connected = True

    def broadcast(self, message, link):
        for node in self.nodes:
            requests.post(f"{node.full_url}/{link}", data=message)

# TODO: Figure out why hash is included in original chain but not in the copied chain in another node
# TODO: Test transaction features as well as adding nodes/transactions 3 way

# coin in which power/hardware does not affect performance of mining -- something tied into productivity/good output
# so reward is not computing power based but productivity based (open source contributions based?)
