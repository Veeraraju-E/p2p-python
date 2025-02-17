# >1 seed node
import socket
import threading
from datetime import datetime
import requests

"""
1. Power law
2. Update Network topology when there is a dead node
"""

class SeedNode:
    def __init__(self, port):
        try:
            self.topology = {}
            self.peer_list = []
            self.ip = '10.23.16.114'
            self.port = port
            self.gamma = 2.5
            self.config_file = "config.txt"
            self.is_peer_list_locked = False
            self.listening = False
            self.is_network_updating = False
            print(f'Config of SeedNode: {self.ip}:{self.port}, Peer List: {self.peer_list}')

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
    
    def update_network(self,peer_socket:socket.socket,msg:str):

        _,peer_ip,peer_port,degree = msg.split(':')
        
        self.is_network_updating = True
        if self.topology.get((peer_ip,int(peer_port)),None) == None:
            self.topology[(peer_ip,int(peer_port))]=int(degree)
        elif self.topology.get((peer_ip,int(peer_port))) != int(degree):
            self.topology[(peer_ip,int(peer_port))]=int(degree)
        self.is_network_updating = False
        

    def send_update_network_message(self,msg):
        seed_list = open(self.config_file,"r").readlines()
        for seed in seed_list:
            seed_ip, seed_port = seed.split(':')
            seed_port = seed_port.strip() 
            if seed_ip == self.ip and int(seed_port) == self.port:
                continue
            seed_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            seed_socket.connect((seed_ip,int(seed_port)))
            seed_socket.sendall(msg.encode())
            seed_socket.close()

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
            with open("logfile.txt", "a") as log_file:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                log_file.write(f"{timestamp}:Seed received connection request from {peer_ip}:{peer_port}\n")
            
            peer_list_temp = self.peer_list
            # print(f"Peer List at {self.ip}:{self.port} = {self.peer_list}")
            if (peer_ip,peer_port) in self.peer_list:
                peer_socket.sendall("You are already connected to the me".encode())
                return
            
            peer_socket.close()
            peer_list_msg = self.list_to_send(peer_ip,int(peer_port))
            
            peer_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            peer_socket.connect((peer_ip,int(peer_port)))
            peer_socket.sendall(peer_list_msg.encode())
            peer_socket.close()

        except socket.timeout:
            peer_socket.sendall("Timeout!".encode())
        except Exception as e:
            print(f"Error occured: {e}")
    
    def list_to_send(self,peer_ip,peer_port):
        try:

            while self.is_peer_list_locked or self.is_network_updating:
                waiting = 0
            
            self.is_peer_list_locked = True
            
            msg = f"SeedNode={self.ip}:{self.port}||"

            if len(self.peer_list) == 0:
                self.peer_list.append((peer_ip,peer_port))
                self.is_peer_list_locked = False
                return msg+"No"

            self.is_peer_list_locked = False
            msg+="".join([f"{p[0]}:{p[1]}:{self.topology.get(p,0)}," for p in self.peer_list]).rstrip(',')
            self.peer_list.append((peer_ip,peer_port))
            return msg
        
        except Exception as e:
            print(f"Error occured while calculating power law {e}")
            self.is_peer_list_locked = False

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
        with open("output.txt", "a") as log_file:
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
                elif msg.startswith("Degree_Sent"):
                    self.update_network(peer_socket,msg)
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
                with open("output.txt", "a") as log_file:
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
