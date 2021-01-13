import requests


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

    def broadcast(self, payload, link):
        for node in self.nodes:
            requests.post(f"{node.full_url}/{link}", json=payload)


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
