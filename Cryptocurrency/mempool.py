from uuid import uuid4
from typing import Union, List, Tuple


# TODO: wallets

class Transaction:
    """
    The Transaction class represents a transaction between two entities. Comparison is done value-wise. That is, the
    identity of the object does not matter only its contents.

    :param ID: An identifier used to differentiate transactions. Defaults to a random uuid4 with no dashes or spaces
    :param sender: Address of the node/client that is sending a payment.
    :param receiver: Address of the node/client that is receiving the payment.
    :param amount: The amount being sent.
    :param fee: The fee the sender chooses. This fee is given to the miner who successfully creates a block that
                contains this transaction
    """

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
    """
    The MemPool class is an object that represents the pool of transactions waiting to be verified by miners.

    :param max_tran_per_block: The maximum number of transactions each block can contain.
    :param max_tran_per_MemPool: The maximum number of transactions each instance of the MemPool can hold. This is used
                                to limit the amount of transaction each node keeps track of.
    """

    # TODO: Devise method of recording transaction history so that if collision occurs transactions that were verified
    # TODO: but aren't anymore get moved

    def __init__(self, max_tran_per_block, max_tran_per_MemPool):
        # transactions ordered from greatest to least
        self.unverified_transactions = []
        # the maximum number of transactions that can be put into a block
        self.max_tran_per_block = max_tran_per_block
        # the maximum number of transactions that an instance of the MemPool can hold
        self.max_tran_per_MemPool = max_tran_per_MemPool

    def insert_single_transaction(self, transaction: Transaction) -> Tuple[int, int]:
        """
        Inserts a transaction in the unverified transaction list in its correct place in the order of greatest to least
        transaction fee.

        :param transaction: A Transaction object
        :return: False if the MemPool is full and the index where the transaction was inserted if successful
        """
        if 1 + len(self.unverified_transactions) > self.max_tran_per_MemPool:
            return -1, self.num_transactions
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

    def insert_multiple_transactions(self, transactions: List[Transaction]) -> Union[bool, int]:
        """
        Inserts a batch of Transaction objects and orders them by transaction fee.

        :param transactions: a list of Transaction objects
        :return: False if the MemPool is full and the number of unverified transactions if successful
        """
        if len(transactions) + len(self.unverified_transactions) > self.max_tran_per_MemPool:
            return False
        else:
            self.unverified_transactions.extend(transactions)
            self.unverified_transactions.sort(key=lambda x: x.fee, reverse=True)
            return len(self.unverified_transactions)

    def remove_transactions(self, transactions: Union[Transaction, List[Transaction]]) -> bool:
        """
        Removes one or several Transaction objects from the pool of unverified transactions kept in a nodes MemPool.

        :param transactions: Either one Transaction object or a list of Transaction objects
        :return:
        """
        removed = False
        if isinstance(transactions, list):
            for x in transactions:
                if x in self.unverified_transactions:
                    self.unverified_transactions.remove(x)
                    removed = True
        else:
            if transactions in self.unverified_transactions:
                self.unverified_transactions.remove(transactions)
        return removed

    def get_top_transactions(self) -> List[Transaction]:
        return self.unverified_transactions[:self.max_tran_per_block]

    @property
    def num_transactions(self):
        return len(self.unverified_transactions)
