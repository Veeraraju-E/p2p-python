# Assumptions of the network

This file contains all the basic assumptions that we have made upon which the network is built.

## Assumptions about the seed nodes

1. At least one of the [n/2] + 1 seed nodes would respond to the new peer by sending its peer list.
2. The seed nodes will update the degrees of the peers in their list as soon as the peer sends its degree.
3. The seed nodes will never end up into deadlocks.

## Assumptions about the peer nodes

1. The peers will respond if they are alive to every message sent to them.
2. The peers will never end up into deadlocks.
3. The peers will do all their functionality rightly without performing any kind of attacks (DOS by flooding).

## Libraries used

### The following libraries were used:

#### Standard Libraries
- `socket`
- `datetime`
- `random`
- `os`
- `threading`
- `time`
- `hashlib`
- `json`
- `traceback`

#### Installed libraries
- `numpy`
- `matplotlib`
- `networkx`

#### Assumptions on libraries

1. We assume that the libraries used in this system function well and handle the errors rightly.
2. We assume that the random number generator used are close to `true RGs` and are not much biased.
3. The ping utility used in the `peer.py` file functions rightly.

