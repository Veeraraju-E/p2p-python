# >1 seed node
import socket
import threading
import time

"""
1. Power law
2. Dead node handling
"""

class SeedNode:
    def __init__(self, port):
        try:
            self.peer_list = [] # list of tuples of (addr, port) of all peers in the network
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
            peer_list_temp = self.peer_list
            print(f"Peer List at {self.ip}:{self.port} = {self.peer_list}")
            if (peer_ip,peer_port) in self.peer_list:
                peer_socket.sendall("You are already connected to the me".encode())
                return
            
          
            msg = f"SeedNode={self.ip}:{self.port}||"

            if len(peer_list_temp) != 0:
                for peers_ip,peers_port in peer_list_temp:
                    msg+=f"{peers_ip}:{peers_port},"
                    print(msg)
                
                msg = msg.rstrip(',')
                print(msg)
            else:
                msg+="No"
            peer_socket.close()
            
            peer_socket =  socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            peer_socket.connect((peer_ip,int(peer_port)))
            peer_socket.sendall(msg.encode())
            peer_socket.close()

            while self.is_peer_list_locked:
                waiting=1

            self.is_peer_list_locked = True
            self.peer_list.append((peer_ip,int(peer_port)))
            self.is_peer_list_locked = False

        except socket.timeout:
            peer_socket.sendall("Timeout!".encode())
        except Exception as e:
            print(f"Error occured: {e}")
        

    def report_dead_node(self,reporter_socket : socket.socket,reporter_addr : str):
        '''
        Remove from my peer list
        Broadcast Message to other peers in my list
        '''
        pass

    def send(self,message: str):
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
                    self.report_dead_node(peer_socket,peer_addr)
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
