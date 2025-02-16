import random
import socket
import threading
import traceback
import os
from time import sleep
from time import time
import hashlib
from datetime import datetime

"""
1. Broadcast - remove port from the message
"""

class PeerNode:
    def __init__(self, config_file='config.txt'):
        try:
            self.dead = False
            self.seed_node_list = []
            self.peer_list = []
            self.peer_degrees = {}  # dictionary to track the degree of each peer
            self.peer_connections = {}  # dictionary to track connections between peers

            self.config_file = config_file
            self.ip = socket.gethostbyname(socket.getfqdn())
            self.port = None
            self.listening = False
            self.lock_peer_list = False
            self.lock_seed_list = False
            self.received_peer_set = set()
            self.no_seed_nodes = 0
            self.no_peers_connected = 0

            self.message_list = {}  # {hash_msg: set of peers}
            self.message_count = 0

        except Exception as e:
            print(f"Error initializing PeerNode: {e}")

    def connect_to_network(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind((self.ip, 0))
            self.ip, self.port = self.socket.getsockname()
            self.listening = True

            t_listen = threading.Thread(target=self.listen, daemon=True)
            t_listen.start()

            with open(self.config_file, "r") as seed_list:
                seeds = seed_list.readlines()
                seed_nodes = []
                for seed in seeds:
                    seed_ip, seed_port = seed.split(':')
                    seed_port = seed_port.strip()
                    seed_nodes.append((seed_ip, seed_port))

                no_of_seeds_to_connect = random.randint(len(seeds) // 2 + 1, len(seeds))
                self.no_seed_nodes = no_of_seeds_to_connect
                selected_seeds = random.sample(seed_nodes, no_of_seeds_to_connect)
                for selected_seed in selected_seeds:
                    t = threading.Thread(target=self.send_request_to_seed, args=(selected_seed[0], selected_seed[1]), daemon=True)
                    t.start()

                while len(self.seed_node_list) != no_of_seeds_to_connect:
                    waiting = 0

            return True

        except Exception as e:
            print(f"Error occurred in connecting to network: {e}")
            self.stop()
            return False

    def listen(self):
        try:
            self.socket.listen()
            print(f"Starting Listening as {self.ip}:{self.port}")
            while self.listening:
                peer_socket, peer_addr = self.socket.accept()
                t = threading.Thread(target=self.handle_request, args=(peer_socket, peer_addr), daemon=True)
                t.start()
        except Exception as e:
            if self.listening:
                print(f"Error in setting up socket {e}")
    
    def handle_request(self, peer_socket: socket.socket, peer_addr: str):
        msg = ""

        peer_socket.settimeout(10.0)
        try:
            while True:
                try:
                    data = peer_socket.recv(1024)
                    if not data:
                        break
                    msg += data.decode()

                except socket.timeout:
                    print(f"Timeout no data received from {peer_addr}.")
                    break

            if msg.startswith("SeedNode="):

                self.no_seed_nodes-=1
                self.process_seed_request(msg)

                if self.no_seed_nodes == 0:
                    self.no_peers_connected = len(self.received_peer_set)
                    # for peer_ip,peer_port in self.received_peer_set:
                    #     t = threading.Thread(target=self.send_request_to_peer,args=(peer_ip,peer_port),daemon=True)
                    #     t.start()
                    self.connect_to_peers()
                    while self.no_peers_connected != 0:
                        waiting = 0
                    
                    threading.Thread(target=self.broadcast,daemon=True).start()
                    threading.Thread(target=self.ping,daemon=True).start()
                    
            elif msg.startswith("Peer_Request_Sent"):
                self.accept_received_peer_request(msg, peer_socket)
            elif msg.startswith("Peer_Request_Accepted"):
                self.accept_sent_peer_request(msg, peer_socket)
            elif msg.startswith("Gossip:"): # to forward broadcast messages and gossip, msg will start with Gossip:
                message = msg.split("Gossip:")[1]
                # print(f'Gossip Received: {message}')
                message_hashed = self._hash_msg(message)
                if message_hashed not in self.message_list.keys():
                    self.message_list[message_hashed] = set()
                if peer_addr[1] not in self.message_list[message_hashed]:
                    self.message_list[message_hashed].add(peer_addr[1])
                    self._broadcast(message, message_hashed, peer_addr)
                # print(f'For Peer {peer_addr[0]}:{peer_addr[1]}: ML: {self.message_list}')
            else:
                peer_socket.sendall("Invalid Message Format".encode())

        except Exception as e:
            print(f"Error receiving data from {peer_addr}: {e}")
        
        peer_socket.close()
#---------------------------------------------------------------------------------------------------------------------#
    def send_request_to_seed(self, ip, port):
        try:
            seed_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            seed_socket.connect((ip, int(port)))
            seed_socket.sendall(f"Myself:{self.ip}:{self.port}".encode())
            seed_socket.close()
        except Exception as e:
            print(f"Error occurred in sending seed request! {e}")
            traceback.print_exc()
    
    def process_seed_request(self, seed_reply: str):
        try:
            seed_address, seed_reply = seed_reply.split('||')
            _, seed_address = seed_address.split('=')
            seed_ip, seed_port = seed_address.split(':')
            
            while self.lock_seed_list:
                waiting = 0
            
            self.lock_seed_list = True
            self.seed_node_list.append((seed_ip, int(seed_port)))
            self.lock_seed_list = False

            print(f"----------Seed Node:{seed_address} connected----------")
            peers_available = None
            if seed_reply != "No":

                peers_available = seed_reply.split(',')
                for peer in peers_available:
                    peer_ip, peer_port = peer.split(':')
                    self.received_peer_set.add((peer_ip,int(peer_port)))

        except Exception as e:
            print(f"Error occurred in connecting to peers! {e}")
            self.lock_seed_list = False
            traceback.print_exc()
#----------------------------------------------------------------------------------------------------------------------#
    def connect_to_peers(self):
        try:
            if not self.received_peer_set:
                return True

            num_peers = len(self.received_peer_set)
            gamma = 2.5  # power law exponent
            
            degrees = [self.peer_degrees.get(peer, 1) for peer in self.received_peer_set]
            weights = [1/(k**gamma) for k in range(1, num_peers + 1)]
            total_weight = sum(weights)
            probabilities = [w/total_weight for w in weights]

            num_connections = min(int(num_peers/2) + 1, num_peers)
            selected_peers = set()
            
            while len(selected_peers) < num_connections:
                peer = random.choices(list(self.received_peer_set), weights=probabilities, k=1)[0]
                if peer not in selected_peers:
                    selected_peers.add(peer)

            self.no_peers_connected = len(selected_peers)
        
            # Connect to selected peers
            for peer_ip, peer_port in selected_peers:
                t = threading.Thread(target=self.send_request_to_peer, 
                                args=(peer_ip, peer_port), 
                                daemon=True)
                t.start()

            while self.no_peers_connected != 0:
                waiting = 0

            return True

        except Exception as e:
            print(f"Error occurred in connecting to peers: {e}")
            self.stop()
            return False
    
    def send_request_to_peer(self, peer_ip, peer_port):
        try:
            print(f"Entered the send request to peer node function {self.ip}:{self.port}")

            peer_send_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_send_socket.connect((peer_ip, peer_port))
            peer_send_socket.sendall(f"Peer_Request_Sent:{self.ip}:{self.port}".encode())
            peer_send_socket.close()
            print(f"Peer request sent to {peer_ip}:{peer_port}")
        except Exception as e:
            print(f"Error occurred in sending peer request! {e}")
            traceback.print_exc()

    def update_peer_connections(self, peer1, peer2):
        if peer1 in self.peer_connections:
            self.peer_connections[peer1].append(peer2)
        else:
            self.peer_connections[peer1] = [peer2]

        if peer2 in self.peer_connections:
            self.peer_connections[peer2].append(peer1)
        else:
            self.peer_connections[peer2] = [peer1]

    # def get_peer_connections(self, peer):
    #     return self.peer_connections.get(peer, [])


    def accept_received_peer_request(self, msg, peer_socket: socket.socket):
        try:
            peer_socket.close()
            _, peer_ip, peer_port = msg.split(':')
            print(f"Peer request received from {peer_ip}:{peer_port}")
            with open("logfile.txt", "a") as log_file:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_file.write(f"{timestamp}:Peer request received from {peer_ip}:{peer_port}")
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.connect((peer_ip, int(peer_port)))
            peer_socket.sendall(f"Peer_Request_Accepted:{self.ip}:{self.port}".encode())
            peer_socket.close()
            print(f"Peer request accepted message is sent to {peer_ip}:{peer_port}")
            with open("logfile.txt", "a") as log_file:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_file.write(f"{timestamp}:Peer request accepted message is sent to {peer_ip}:{peer_port}\n")
            while self.lock_peer_list:
                waiting = 0

            self.lock_peer_list = True
            self.peer_list.append((peer_ip, int(peer_port)))
            self.peer_degrees[(peer_ip, peer_port)] = self.peer_degrees.get((peer_ip, peer_port), 0) + 1
            self.peer_degrees[(self.ip, self.port)] = self.peer_degrees.get((self.ip, self.port), 0) + 1
            
            self.lock_peer_list = False
            self.update_peer_connections((self.ip, self.port), (peer_ip, peer_port))


        except Exception as e:
            print(f"Error occurred in accepting received peer request! {e}")
            with open("logfile.txt", "a") as log_file:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_file.write(f"{timestamp}:Error occurred in accepting received peer request! {e}\n")
            self.lock_peer_list = False
            traceback.print_exc()

    def accept_sent_peer_request(self, msg, peer_socket: socket.socket):
        try:
            _, peer_ip, peer_port = msg.split(':')
            peer_socket.close()
            print(f"Received acceptance from the peer {peer_ip}:{peer_port}")
            with open("logfile.txt", "a") as log_file:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_file.write(f"{timestamp}:Received acceptance from the peer {peer_ip}:{peer_port}\n")
            
            while self.lock_peer_list:
                waiting = 1

            self.lock_peer_list = True
            self.peer_list.append((peer_ip, int(peer_port)))
            self.peer_degrees[(peer_ip, peer_port)] = self.peer_degrees.get((peer_ip, peer_port), 0) + 1
            self.peer_degrees[(self.ip, self.port)] = self.peer_degrees.get((self.ip, self.port), 0) + 1
            
            self.no_peers_connected-=1
            print(f"Peer List now is {self.peer_list}")
            with open("logfile.txt", "a") as log_file:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_file.write(f"{timestamp}:Peer List now is {self.peer_list}\n")
            
            self.lock_peer_list = False
            self.update_peer_connections((self.ip, self.port), (peer_ip, peer_port))

        except Exception as e:
            print(f"Error occurred in accepting sent peer request! {e}")
            self.lock_peer_list = False
            traceback.print_exc()
#---------------------------------------------------------------------------------------------------------------------#
    def stop(self):
        self.listening = False
        if self.socket:
            try:
                self.socket.close()
            except Exception as e:
                print(f"Error shutting down socket: {e}")
            finally:
                self.socket.close()
                print(f"Socket on {self.ip}:{self.port} closed successfully")

    def see_all_peer_nodes(self):
        try:
            peers = ""
            if len(self.peer_list) == 0:
                return "No Peers Connected Yet"

            for peer in self.peer_list:
                peers += f"{peer[0]}:{peer[1]}\n"
            return peers
        except Exception as e:
            print(f"Error occurred! {e}")
            return ""

    def see_all_seed_nodes(self):
        try:
            seeds = ""
            for seed in self.seed_node_list:
                seeds += f"{seed[0]}:{seed[1]}\n"
            return seeds
        except Exception as e:
            print(f"Error occurred! {e}")
            return ""
#---------------------------------------------------------------------------------------------------------------------#
    def _hash_msg(self, msg):
        return hashlib.sha256(msg.encode()).hexdigest()

    def _broadcast(self, message, message_hash, sender):
        try:
            while self.lock_peer_list:
                pass

            self.lock_peer_list = True
            
            for peer_ip, peer_port in self.peer_list:
                if (peer_ip, peer_port) == sender:  # sender may occur in the future iterations, not the first time
                    continue
                if peer_port in self.message_list.get(message_hash, set()):  # Avoid duplicate forwarding
                    continue
                try:
                    peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    peer_socket.connect((peer_ip, peer_port))
                    peer_socket.sendall(f"Gossip:{message}".encode())
                    peer_socket.close()
                    self.message_list[message_hash].add(peer_port)    # add to set
                except Exception as e:
                    print(f"Error occurred while forwarind msg! {e}")
            self.lock_peer_list = False

        except Exception as e:
            print(f"Error occurred while forwarind msg! {e}")


    def broadcast(self):
        try:
            while self.message_count < 10:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                message = f"{timestamp}:{self.ip}:{self.port}:{self.message_count}" # adding port for debugging only
                message_hash = self._hash_msg(message)
                self.message_list[message_hash] = set()
                print(f"Broadcasting Message #{self.message_count}: {message}")
                if self.message_count == 0:
                    with open("logfile.txt", "a") as log_file:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        log_file.write(f"{timestamp}:Broadcasting First Message : {message}\n")
                self._broadcast(message, message_hash, None)
                self.message_count += 1
                sleep(5)   # generate msg every 5s for 10 times
        except Exception as e:
            print(f"Error occurred while broadcasting! {e}")

    def ping(self):
        try:
            peers_not_responding = {}
            while True:

                while self.lock_peer_list:
                    waiting = 0
                
                self.lock_peer_list = True

                for peer_ip,peer_port in self.peer_list:
                    response = None
                    if peer_ip == self.ip:
                        response = socket.socket(socket.AF_INET,socket.SOCK_STREAM).connect_ex((peer_ip,peer_port))
                    else:
                        response = os.system(f"ping -c 1 {peer_ip}")
                    
                    if response != 0:
                        if peers_not_responding.get((peer_ip,peer_port),None) == None:
                            
                            peers_not_responding[(peer_ip,peer_port)] = 1
                        else:
                            peers_not_responding[(peer_ip,peer_port)]+=1
                            if peers_not_responding[(peer_ip,peer_port)] == 3:
                                print(f"{peer_ip} {peer_port} is dead")
                                self.peer_list.remove((peer_ip,peer_port))
                                peers_not_responding.pop((peer_ip,peer_port))
                                threading.Thread(target=self.report_dead_node,args=((peer_ip,peer_port),),daemon=True).start()
                    else:
                        if peers_not_responding.get((peer_ip,peer_port),None) != None:
                            print(f"{peer_ip} {peer_port} started responding again")
                            peers_not_responding.pop((peer_ip,peer_port))
                            
                self.lock_peer_list = False
                print(peers_not_responding)
                sleep(5)

        except Exception as e:
            print(f"Exception occured while pinging! {e}")
    
    def report_dead_node(self,dead_node_addr):
        try:
            for seed in self.seed_node_list:
                seed_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                seed_socket.connect(seed)
                ts = time()
                seed_socket.sendall(f"Dead Node:{dead_node_addr[0]}:{dead_node_addr[1]}:{ts}:{self.ip}".encode())
                seed_socket.close()
            
        except Exception as e:
            print(f"Error occured while reporting dead node: {e}")

if __name__ == "__main__":
    try:
        peer = PeerNode()
        is_all_initialized = peer.connect_to_network()

        if is_all_initialized:
            print("\n" + "=" * 50)
            print("       Welcome to the Panel of this Client       ")
            print("=" * 50)

            menu = """
            Menu Options:
            1. See all Peers Nodes connections
            2. See all Seed Nodes connections
            3: Stop the client
            4: Show the menu again
            """

            print(menu)

            while True:
                try:
                    action = int(input("\nEnter your action number: "))

                    if action == 1:
                        peers = peer.see_all_peer_nodes()
                        print(peers)

                    elif action == 2:
                        seeds = peer.see_all_seed_nodes()
                        print(seeds)

                    elif action == 3:
                        try:
                            peer.stop()
                            print("Peer Shut Down...")
                            break
                        except Exception as e:
                            print(f"Error occurred! {e}")

                    elif action == 4:
                        print(menu)

                    else:
                        print(f"Invalid option! Please select a valid action.\n{menu}")

                except ValueError:
                    print("Invalid input! Please enter a number corresponding to an action.")
                except Exception as e:
                    print(f"An error occurred: {e}")
    except KeyboardInterrupt:
        try:
            peer.stop()
            print("Peer Shut Down...")
        except Exception as e:
            print(f"Error occurred! {e}")