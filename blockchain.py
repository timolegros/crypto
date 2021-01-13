import datetime
from hashlib import sha256
import json
import requests
from network import Network, Node
from mempool import MemPool
from typing import List, Union
from mempool import Transaction
from requests import Response


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
    """
    The main component of the cryptocurrency that handles the instantiation of the chain, mining, and various general
    functions.
    :param miningDiff: The difficulty of mining or in other words the number of required leading 0's
    :param Node2: One other node in the general network. Required for the network to go online
    :param port: The port to use for the current node.
    :param url: The url to use for the current node's flask API interface
    """
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

    def proof_of_work(self, block: Block) -> sha256:
        """
        Called when a miner wants to create a block in order to store transactions and add to the chain. The hash
        computed here becomes the blocks hash if the number of leading 0's is correct. Keeps guessing hashes until
        the hash is correct.

        :param block: A Block object that contains certain data
        :returns: The correct hash that also becomes the mined blocks hash
        """
        # TODO: Incorporate Nonce, timestamp, and transaction rotation to account for Nonce max and high hash capacity
        block.nonce = 0
        computed_hash = block.compute_hash()
        while computed_hash[:self.miningDiff] != '0' * self.miningDiff:
            block.nonce += 1
            computed_hash = block.compute_hash()

        return computed_hash

    def add_block(self, block: Block, proof_computed_hash: sha256) -> bool:
        """
        Adds a block to this blockchain instance if the computed hash is correct.
        :param block: A Block object.
        :param proof_computed_hash: The computed hash mined for the specific block.
        :return: False if the computed hash is wrong or if the previous hash of the block is not the last blocks hash
        and True if the block is successfully appended.
        """
        prev_hash = self.last_block.hash
        if prev_hash != block.prev_hash or not self.check_proof(block, proof_computed_hash):
            return False
        block.hash = proof_computed_hash
        self.chain.append(block)

        return True

    def check_proof(self, block: Block, computed_hash: sha256) -> bool:
        """
        Checks if the computed_hash is valid. computed_hash should be equal to block.computed_hash() because block.nonce
        was updated in proof_of_work().
        :param block: the block in question
        :param computed_hash: the hash that results from the work of a miner
        :return: True if the computed hash is valid according to the mining difficulty and current state of the block.
        False otherwise.
        """
        return (computed_hash[:self.miningDiff] == '0' * self.miningDiff) and computed_hash == block.compute_hash()

    def mine(self) -> Block:
        # TODO: Integrate GitHub API for open-source mining
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

    def validate_chain(self, chain: Union[List[Block], List[dict]]) -> bool:
        """
        Iterates through an entire chain and checks to see if the every previous hash is the hash of the previous block
        and if the hash of every bloc is valid.
        :param chain: A list of Block objects or dictionaries representing blocks.
        :return: True if the chain is valid and False if the chain is invalid.
        """
        if not isinstance(chain[0], Block):
            new_chain = []
            for x in chain:
                new_block = Block(x['index'], x['transactions'], x['prev_hash'], x['nonce'], x['timestamp'])
                new_block.hash = x['hash']
                new_chain.append(new_block)
        else:
            new_chain = chain

        for i in range(len(self.chain) - 1):
            if new_chain[i].hash != new_chain[i + 1].prev_hash:
                return False
            elif new_chain[i].hash[:self.miningDiff] != '0' * self.miningDiff and i != 0:
                return False
        return True

    def compare_chains(self) -> bool:
        """
        Since the longest chain is considered the valid chain this method requests the chains of all the other nodes and
        selects the longest one. If none of them are longer than the current chain is still valid.
        :return: True of the current chain is replaced by a longer chain and False otherwise.
        """
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

    def propagate_transaction(self, transaction: Transaction) -> bool:
        """
        Takes a new transaction, makes sure its not a duplicate, and then makes all the other nodes aware of this new
        transaction.
        :param transaction: A Transaction object.
        :return: True if the transaction is added to the mempool and propagated to the other nodes in the network.
        """
        # makes sure the transaction had not already been added
        for x in self.MemPool.unverified_transactions:
            if transaction.ID == x.ID:
                return False

        # adds the transaction to memPool and propagates the transaction to the other node MemPools
        self.MemPool.insert_single_transaction(transaction)
        self.Network.broadcast({'transaction': transaction.__dict__}, 'add_transaction')

        return True

    def update_node(self, node: Node) -> Response:
        """
        Copies all the data from the current node to another node. Used mainly when a brand new node is inserted into
        a network.
        :param node: A Node object.
        :return: The response object from the post request.
        """
        # transactions = [x.__dict__ for x in self.MemPool.unverified_transactions]
        transactions = self.obj_to_dict(self.MemPool.unverified_transactions)
        # chain = [x.__dict__ for x in self.chain]
        chain = self.obj_to_dict(self.chain)
        url = node.full_url + '/update_node'
        return requests.post(url, json={"chain": chain, "transactions": transactions})

    def obj_to_dict(self, objects: Union[Node, Transaction, List[Node], List[Transaction]]) -> Union[dict, List[dict]]:
        """
        Used to convert an object or list of objects to dictionaries.
        :param objects: Any class instance or list of class instances
        :return: A list of dictionaries if objects was a list and a dictionary if objects is just one object.
        """
        if isinstance(objects, list):
            return [x.__dict__ for x in objects]
        else:
            return objects.__dict__

    @property
    def last_block(self) -> int:
        return self.chain[-1]
