import datetime
from hashlib import sha256
import json


class Block:

    def __init__(self, index, transactions, prev_hash, nonce=0):
        self.index = index
        self.nonce = nonce
        self.transactions = transactions
        self.timestamp = str(datetime.datetime.now())
        self.prev_hash = prev_hash

    def compute_hash(self):
        """Simple function to calculate the hash given the current state of the block"""
        block = json.dumps(self.__dict__, sort_keys=True).encode()
        return sha256(block).hexdigest()

    def __str__(self):
        print(
            f"Transactions: {self.transactions}\nProof: {self.nonce}\nPrevious Hash: {self.prev_hash}\nCreation date: "
            f"{self.timestamp}")


class BlockChain:

    def __init__(self, miningDiff):
        self.chain = []
        self.unverified_transactions = []
        self.create_genesis()
        self.miningDiff = miningDiff

    def create_genesis(self):
        """
        Creates the genesis (first) block of the blockchain
        """
        genesis_block = Block(0, [], "0")
        genesis_block.hash = genesis_block.compute_hash()
        self.chain.append(genesis_block)  # TODO: Here as well

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
        self.chain.append(block)  # TODO: Adding __dict__ is not a valid solution -- create custom json encoder

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

    def add_transaction(self, transaction):
        self.unverified_transactions.append(transaction)

    def mine(self):
        # if self.unverified_transactions:
        last_block = self.last_block
        new_block = Block(last_block.index + 1, transactions=self.unverified_transactions, prev_hash=last_block.hash)

        proof_work = self.proof_of_work(new_block)
        self.add_block(new_block, proof_work)
        self.unverified_transactions = []

        return new_block
        # else:
        #     return False

    def validate_chain(self):
        for i in range(len(self.chain) - 1):
            if self.chain[i].hash != self.chain[i + 1].prev_hash:
                return False
            elif self.chain[i].hash[:self.miningDiff] != '0' * self.miningDiff and i != 0:
                return False
        return True

    @property
    def last_block(self):
        return self.chain[-1]


class Transaction:

    def __init__(self, sender, receiver, amount):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount

    def __str__(self):
        print(f'{self.sender} sent {self.amount}$ to {self.receiver}')


class MemPool:
    pass


# coin in which power/hardware does not affect performance of mining