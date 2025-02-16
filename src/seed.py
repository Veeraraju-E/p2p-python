# >1 seed node
import socket
import threading
import time
import random
from datetime import datetime

"""
1. Power law
"""

class SeedNode:
    def __init__(self, port):
        try:
            self.peer_list = [] # list of tuples of (addr, port) of all peers in the network
            self.peer_degrees = {}  # dictionary to track the degree of each peer

            self.ip = socket.gethostbyname(socket.getfqdn())
            self.port = port
            self.is_peer_list_locked = False
            self.listening = False
            print(f'Config of SeedNode: {self.ip}:{self.port}, Peer List: {self.peer_list}')
            # time.sleep(2)
        except Exception as e:
            print(f"Error initializing SeedNode {port}: {e}")

    def start(self):
        self.listening = True
        self.listen()
    
    def give_description(self):
        try:
            peerList = ""
            for peers_ip,peers_port in self.peer_list:
                    peerList+=f"{peers_ip}:{peers_port}\n"
            if peerList == "":
                peerList = "No peers"
            else:
                peerList="\n"+peerList

            des = f"Myself Seed: {self.ip}:{self.port}\nI am currently connected to {peerList}"
            return des
        except Exception as e:
            print(f"Couldn't return description: {e}")
            return None
        
    def get_peer_degrees(self):
        # print(f"Peer degrees: {self.peer_degrees}")
        return [self.peer_degrees.get(peer, 1) for peer in self.peer_list]
    
    def select_peers_based_on_power_law(self, num_peers):
        """
        Select peers based on power-law distribution
        """
        if not self.peer_list:
            return []

        gamma = 2 # power law exponent
        num_total_peers = len(self.peer_list)
        degrees = [self.peer_degrees.get(peer, 0) + 1 for peer in self.peer_list]
        # print(f"Degrees: {degrees}")
        weights = [(max(degrees) + 1 - d)**gamma for d in degrees]
        total_weight = sum(weights)
        probabilities = [w/total_weight for w in weights]
    
        selected_peers = []
        remaining_peers = self.peer_list.copy()
        remaining_probs = probabilities.copy()

        while len(selected_peers) < min(num_peers, len(remaining_peers)):
            if remaining_peers:
                idx = random.choices(range(len(remaining_peers)),weights=remaining_probs,k=1)[0]
                peer = remaining_peers.pop(idx)
                selected_peers.append(peer)
                remaining_probs.pop(idx)
                
                if remaining_probs:
                    total = sum(remaining_probs)
                    remaining_probs = [p/total for p in remaining_probs]
    
        return selected_peers     
      
    def accept_new_node(self,msg:str,peer_socket:socket.socket,peer_addr):
        '''
        Peer Message Format: Sends a message with string "Myself"
        Add to peer list
        Sending peers format:
        comma separated peers: "<Peer1.IP>:<Peer1.PORT>,<Peer2.IP>:<Peer2.PORT>...,"
        '''
        peer_socket.settimeout(15.0)
        try:

            _,peer_ip,peer_port = msg.split(':')
            print(f"Received connection request from {peer_ip}:{peer_port}")
            with open("logfile.txt", "a") as log_file:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_file.write(f"{timestamp}:Seed received connection request from {peer_ip}:{peer_port}\n")
            
            peer_list_temp = self.peer_list
            # print(f"Peer List at {self.ip}:{self.port} = {self.peer_list}")
            if (peer_ip,peer_port) in self.peer_list:
                peer_socket.sendall("You are already connected to the me".encode())
                return
            
          
            msg = f"SeedNode={self.ip}:{self.port}||"

            if len(peer_list_temp) != 0:
                num_peers_to_send = min(len(peer_list_temp), 5)  # Limit the number of peers sent to new node
                selected_peers = self.select_peers_based_on_power_law(num_peers_to_send)
                for peer in selected_peers:
                    msg += f"{peer[0]}:{peer[1]},"
                msg = msg.rstrip(',')
                # print(msg)
            else:
                msg+="No"
            peer_socket.close()
            
            peer_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            peer_socket.connect((peer_ip,int(peer_port)))
            peer_socket.sendall(msg.encode())
            # self.peer_connections[(peer_ip, peer_port)] = []  # Initialize the connections of the new peer
            peer_socket.close()

            while self.is_peer_list_locked:
                waiting=1

            self.is_peer_list_locked = True
            self.peer_list.append((peer_ip,int(peer_port)))
            self.peer_degrees[(peer_ip, peer_port)] = 0  # Initialize the degree of the new peer
            self.is_peer_list_locked = False            

        except socket.timeout:
            peer_socket.sendall("Timeout!".encode())
        except Exception as e:
            print(f"Error occured: {e}")
        

    def report_dead_node(self,reporter_socket : socket.socket,msg:str):
        '''
        Remove from my peer list
        '''
        # print(msg)
        _,dead_ip,dead_port,ts,reporting_ip = msg.split(':')
        while self.is_peer_list_locked:
            waiting = 0
        self.is_peer_list_locked = True
        if (dead_ip,dead_port) in self.peer_list:
            self.peer_list.remove((dead_ip,dead_port))
            self.peer_degrees.pop((dead_ip, dead_port), None)  # Remove the degree entry
        with open("logfile.txt", "a") as log_file:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_file.write(f"{timestamp}:Node {dead_ip}:{dead_port} is dead.\n")
    
        self.is_peer_list_locked = False
        reporter_socket.close()
    
    def send(self,message: str,ip,port):
        '''
        Send the message (corresponds to one request)
        '''
        pass

    def handle_request(self,peer_socket : socket.socket,peer_addr : str):
        msg = ""
        
        peer_socket.settimeout(10.0)
        while True:
            try:
                data = peer_socket.recv(1024)
                if not data: 
                    break
                msg += data.decode()

                if msg.startswith("Myself"):
                    self.accept_new_node(msg,peer_socket,peer_addr)
                    break
                elif msg.startswith("Dead Node"):
                    self.report_dead_node(peer_socket,msg)
                    break
                else:
                    peer_socket.sendall("Invalid Message Format".encode())
                    break

            except socket.timeout:
                print(f"Timeout no data received from {peer_addr}.")
                break
            except Exception as e:
                print(f"Error receiving data from {peer_addr}: {e}")
                break

        peer_socket.close()

       
    
    def listen(self):
        '''
        Listen for a new connection
        For creation of new node: Peer message format: Myself:<Myself.IP>:<Myself.PORT>
        For reporting a dead node: Peer message format: Dead Node:<DeadNode.IP>:<DeadNode.Port>:<self.timestamp>:<self.IP>
        '''
        try:
            self.server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self.server.bind((self.ip,self.port))
            self.server.listen()
            print(f"SeedNode listening on {self.ip}:{self.port}")
               
            while self.listening:
                peer_socket, peer_addr = self.server.accept()
                print(f"Accepted connection from {peer_addr}")
                with open("logfile.txt", "a") as log_file:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    log_file.write(f"{timestamp}:Seed accepted connection from {peer_addr}\n")
                            
                t = threading.Thread(target=self.handle_request, args=(peer_socket,peer_addr), daemon=True)
                # t.daemon = True
                t.start()
        except Exception as e:
            if self.listening:
                print(f"Self.ip, Self.port : {self.ip}:{self.port} Error in setting up socket {e}")
    
    def stop(self):
        self.listening = False
        if self.server:
            try:
                self.server.shutdown(socket.SHUT_RDWR)
            except Exception as e:
                print(f"Error shutting down socket: {e}")
            finally:
                self.server.close()
