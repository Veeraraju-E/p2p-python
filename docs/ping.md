# Ping Utility in PeerNode

The `ping` method in the `PeerNode` class is responsible for periodically checking the connectivity status of peer nodes in the network. It uses a combination of socket connections and system ping commands to determine if a peer node is responsive. Here is a detailed explanation of how the `ping` utility works:

## Method Overview

### Initialization:

- A dictionary `peers_not_responding` is initialized to keep track of peers that are not responding.
- An infinite loop runs to continuously monitor the status of peer nodes.
- We make sure to use a semaphore using `self.lock_peer_list` to ensure that the peer list is not modified by other threads while it is being accessed.

### Ping Mechanism

- For each peer in the `self.peer_list`, the method checks if the peer is responsive.
  If the peer IP is the same as the current node's IP (`self.ip`), it uses a socket connection to check if the peer is reachable. Otherwise, it uses the system ping command to check the connectivity.
- If in case a peer does not repsond , it is added to the `peers_not_responding` dictionary which also tracks how many times it has failed to respond. But, if a previsouly not responding peer starts to respond again, then it is removed from this dictionary
