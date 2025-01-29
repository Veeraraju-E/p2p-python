# connect to [n/2] + 1 seeds out of n seeds; n changes based on network config
# connection amongst peers must follow power law degree distribution

class PeerNode:
    def __init__(self, seed_node_list):
        
        self.dead = False
        self.seed_node_list = seed_node_list
        self.peer_list = self.seedNode.peer_list

    def connect_to_network(self):
        """
        first connect to seed node to get info of peers,
        then to other peers
        """
        pass

    def _broadcast_receive(self, message, broadcast=True):
        """
        broadcast message to all peers
        """
        if broadcast:
            # broadcast message to all peers
            pass
        else:
            # receive message from all peers
            pass

    def manage_messages(self):
        """
        manage messages received from peers
        """
        # to broadcast
        msg = ""
        self._broadcast_receive(msg, broadcast=True)

        # to receive
        msg = self._broadcast_receive(msg, broadcast=False)

    def ping_peers(self):
        """
        ping peers at regular intervals
        """
        pass
