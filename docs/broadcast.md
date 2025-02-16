# Broadcast Utility in PeerNode

The `broadcast` method in the `PeerNode` class is responsible for periodically broadcasting messages to all peer nodes in the network. It uses a combination of message hashing and a locking mechanism using semaphores to ensure that messages are broadcasted efficiently and without <b>duplication</b>. Here is a detailed explanation of how the `broadcast` utility works:

## Method Overview

### Intialization

- To ensure that a maximum of 10 broadacst messages are sent, a loop until `self.message_count` reaches 10.
- We make sure to use a semaphore using `self.lock_peer_list` to ensure that the peer list is not modified by other threads while it is being accessed.

### Message Handling

- Firstly, a Timestamp is generated using `datetime.now().strftime("%Y-%m-%d %H:%M:%S")` method.
- Then, we follow the prescribed message format (`"Gossip:<TS>:<IP>:<Port>:<broadcaest_num>"`) to create the Plain Text for the message. We additionally included the port number as part of the message to differentiate between messages with same timestamp an broadcast number coming from different peers (obviously, each peer has its the same IP addr, but different port num).
- Hashing is performed in the `_hash_msg()` method using SHA-256 algorithm, which is then checked for uniqueness and appended to `self.message_list` if so.

### Broadcasting

- The driver method for broadcasting is `broadcast()` and the actual method that perform the `sendall()` functioanlity is the `_broadcast()` method.
- We ensure to lock all the other peers, then iterate through `self.peer_list` to broadcast the message to peers. Note that the message formulation is done in `broadcast()`, while the forwarding in `_broadcast()`.
- As for the forwarding process, we ensure that we lock all the other peers, and send the hashed message to the immedaite neighbours while ensuring no repetition. Once the neighboring peers receive the broadcasted message, they forward it to their neighbouring peers (whilst ensuring they do not resend it to the sender or any other peers which previusly received the same broadcast message) and so on...
- The above process is done using a bunch of conditionals and tracking mechanisms as can be seen in the `_broadcast()` method.
