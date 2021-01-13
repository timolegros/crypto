from uuid import uuid4


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
            if x in self.unverified_transactions:
                self.unverified_transactions.remove(x)
                removed = True
        return removed

    def get_top_transactions(self):
        return self.unverified_transactions[:self.max_tran_per_block]

    def get_transaction_index(self, transaction):
        for x in range(len(self.unverified_transactions)):
            if transaction.ID == self.unverified_transactions[x].ID:
                return x

        return False


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

