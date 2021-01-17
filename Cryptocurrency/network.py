import requests
from uuid import uuid4


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
    """
    An instance of Network represents the system of nodes connected to the node that initialized the Network instance.
    A Network object can be used to connect to all the other nodes and communicate with the other nodes.

    :param current_node: An instance of Node that the current client/user is hosted on. This Node will be the public
    facing side of the client
    :param nodes: A list of Node objects. If nodes are passed then the nodes in the list will automatically be added to
    the network and will therefore be connected to the current_node.
    """

    def __init__(self, current_node, nodes):
        self.current_node = current_node
        self.nodes = nodes
        self.connected = False

    def __repr__(self):
        print(self.current_node)
        print(f'Connected to: {self.num_nodes} nodes.')

    def __str__(self):
        print(self.current_node)
        print(f'Connected to: {self.num_nodes} nodes.')

    def add_node(self, node: Node) -> bool:
        """
        Adds a new node to this network and propagates the node to all the other nodes in this network as well.
        :param node: A Node object to be added to this Network
        :return: True if the node is added to this network and false if the node is already in the network
        """
        if node not in self.nodes:
            self.nodes.append(node)
            # propagates the new node to all of this networks connected nodes
            self.broadcast({'node': node.__dict__}, 'add_node')
            return True
        else:
            # propagation from node to node stops if the node is already in this network (it has already propagated
            # the new node its own network
            return False

    def connect_to_network(self):
        """
        Takes the current node and connects it to all the other nodes not currently in its network. This works if the
        current node is connected to at least 1 other node that will then propagate the current nodes info to all the
        nodes that the other node is connected to.
        :return: N/A
        """
        # TODO: Make the nodes return their networks so the current node gets greater reach
        payload = {'node': self.current_node.__dict__}
        self.broadcast(payload, 'add_node')
        self.connected = True

    def broadcast(self, payload: dict, link: str):
        for node in self.nodes:
            requests.post(f"{node.full_url}/{link}", json=payload)

    @property
    def num_nodes(self) -> int:
        return len(self.nodes)
