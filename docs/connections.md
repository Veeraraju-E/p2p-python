# P2P Network Connection Process Documentation

## Overview

This document explains the connection process in our P2P network, including how peers connect to seed nodes and other peers while maintaining a power-law degree distribution.

## Connection Flow

### 1. Initial Peer Setup

```python
# When a new peer starts:
peer = PeerNode()
peer.connect_to_network()
```

### 2. Seed Node Registration

- Each peer must register with at least ⌊n/2⌋ + 1 randomly chosen seed nodes
- Process:
  1. Read seed nodes from config file
  2. Randomly select seed nodes to connect to
  3. Send registration request to each selected seed node

```python
no_of_seeds_to_connect = random.randint(len(seeds) // 2 + 1, len(seeds))
selected_seeds = random.sample(seed_nodes, no_of_seeds_to_connect)
```

### 3. Peer to Peer Connection

#### A. Getting Peer List

1. Each seed node maintains a list of registered peers
2. When a new peer connects, seed node:
   - Adds the new peer to its peer list
   - Selects a subset of existing peers based on power-law distribution
   - Sends this list to the new peer

#### B. Power-Law Distribution

- Used to ensure network follows power-law degree distribution
- Properties:
  - Most nodes have few connections
  - Few nodes have many connections
  - Probability ∝ 1/k^γ (where k is degree and γ is power-law exponent)

```python
# Example power-law selection in seed node
gamma = 2.5  # power law exponent
weights = [1/(k**gamma) for k in range(1, num_peers + 1)]
```

### 4. Connection Protocol

#### Registration Message Flow

```
Peer → Seed Node: "Myself:{peer_ip}:{peer_port}"
Seed Node → Peer: "SeedNode={seed_ip}:{seed_port}||peer1_ip:peer1_port,peer2_ip:peer2_port,..."
```

#### Peer Connection Message Flow

```
Peer A → Peer B: "Peer_Request_Sent:{peerA_ip}:{peerA_port}"
Peer B → Peer A: "Peer_Request_Accepted:{peerB_ip}:{peerB_port}"
```

### 5. Connection Maintenance

#### A. Peer Degree Tracking

- Each peer maintains:
  - List of connected peers
  - Degree (number of connections) for each peer
  - Connection status

#### B. Dead Node Detection

- Peers periodically ping connected peers
- After 3 failed attempts:
  - Mark peer as dead
  - Remove from peer list
  - Notify seed nodes

## Example Connection Scenario

1. New Peer P joins network with 3 seed nodes (S1, S2, S3)
2. P connects to 2 seed nodes (S1, S2)
3. S1 and S2 provide lists of existing peers
4. P receives: P1, P2, P3, P4
5. P calculates connections based on power-law:
   - If P1 degree=1, P2 degree=2, P3 degree=1, P4 degree=3
   - Higher probability to connect to P1 and P3 (lower degrees)
   - Lower probability to connect to P4 (higher degree)
