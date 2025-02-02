# connect to [n/2] + 1 seeds out of n seeds; n changes based on network config
# connection amongst peers must follow power law degree distribution
import random
import socket
import threading
import traceback

class PeerNode:
    def __init__(self):
        
        self.dead = False
        self.seed_node_list = []
        self.peer_list = []
        self.config_file = "config.txt"
        self.ip = socket.gethostbyname(socket.getfqdn())
        self.port = None
        self.listening = False
        self.lock_peer_list = False
        self.lock_seed_list = False
    
    def handle_request(self,peer_socket : socket.socket,peer_addr : str):
        msg = ""
        print(f"Received connection from {peer_addr}")
        peer_socket.settimeout(10.0)
        while True:
            try:
                data = peer_socket.recv(1024)
                if not data: 
                    break
                msg += data.decode()

                if msg.startswith("SeedNode="):
                    self.connect_to_peers(msg,peer_socket,peer_addr)
                    break
                elif msg.startswith("Peer_Request_Sent"):
                    self.accept_received_peer_request(msg,peer_socket)
                elif msg.startswith("Peer_Request_Accepted"):
                    self.accept_sent_peer_request(msg,peer_socket)
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
    
    def connect_to_peers(self,seed_reply:str,seed_socket,seed_addr):
        try:
            seed_address,seed_reply=seed_reply.split('||')
            _,seed_address = seed_address.split('=')
            seed_ip,seed_port = seed_address.split(':')
            print(seed_ip,seed_port)
            while self.lock_seed_list:
                waiting = 0

            self.lock_seed_list = True
            self.seed_node_list.append((seed_ip,int(seed_port)))
            self.lock_seed_list = False

            print(f"----------Seed Node:{seed_addr} connected----------")
            peers_available = None
            if seed_reply != "No":
                peers_available = seed_reply.split(',')
                for peer in peers_available:
                    peer_ip,peer_port = peer.split(':')
                    t = threading.Thread(target=self.send_request_to_peer,args=(peer_ip,int(peer_port)))
                    t.daemon = True
                    t.start()

        except Exception as e:
            print(f"Error occured in connecting to peers! {e}")
            self.lock_seed_list = False
            traceback.print_exc()
    
    def accept_sent_peer_request(self,msg,peer_socket : socket.socket):
        try:
            _,peer_ip,peer_port = msg.split(':')
            peer_socket.close()
            
            while self.lock_peer_list:
                waiting = 1
            
            self.lock_peer_list = True
            self.peer_list.append((peer_ip,int(peer_port)))
            self.lock_peer_list = False

        except Exception as e:
            print(f"Error occured in accpeting sent peer request! {e}")
            self.lock_peer_list = False
            traceback.print_exc()
    
    def accept_received_peer_request(self,msg,peer_socket : socket.socket):
        try:

            peer_socket.close()
            _,peer_ip,peer_port = msg.split(':')
            peer_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            peer_socket.connect((peer_ip,int(peer_port)))
            peer_socket.sendall(f"Peer_Request_Accepted:{self.ip}:{self.port}".encode())
            peer_socket.close()

            while self.lock_peer_list:
                waiting = 0

            self.lock_peer_list = True
            self.peer_list.append((peer_ip,int(peer_port)))
            self.lock_peer_list = False

            
        except Exception as e:
            print(f"Error occured in accepting received peer request! {e}")
            self.lock_peer_list = False
            traceback.print_exc()
    
    def send_request_to_peer(self,peer_ip,peer_port):
        try:
            peer_send_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            peer_send_socket.connect((peer_ip,peer_port))
            peer_send_socket.sendall(f"Peer_Request_Sent:{self.ip}:{self.port}".encode())
            peer_send_socket.close()
        except Exception as e:
            print(f"Error occured in sending peer request! {e}")
            traceback.print_exc()

    def send_request_to_seed(self,ip,port):
        try:
            seed_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            seed_socket.connect((ip,port))
            seed_socket.sendall(f"Myself:{self.ip}:{self.port}".encode())
            seed_socket.close()
        except Exception as e:
            print(f"Error occured in sending seed request! {e}")
            traceback.print_exc()
        

    def listen(self):
        try:
            self.socket.listen()
            print(f"Starting Listening as {self.ip}:{self.port}")
            while self.listening:
                peer_socket,peer_addr = self.socket.accept()
                t = threading.Thread(target=self.handle_request,args=(peer_socket,peer_addr))
                t.daemon = True
                t.start()

        except Exception as e:
            if self.listening:
                print(f"Error in setting up socket {e}")


    def connect_to_network(self):
        try:
            self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            self.socket.bind((self.ip,0))
            self.ip,self.port = self.socket.getsockname()
            self.listening = True

            t_listen = threading.Thread(target=self.listen)
            t_listen.daemon = True
            t_listen.start()

            with open(self.config_file,"r") as seed_list:
                seeds = seed_list.readlines()
                no_of_seeds_to_connect = random.randint(len(seeds)//2+1,len(seeds))

                indices_seeds_to_connect = []
                while len(indices_seeds_to_connect) != no_of_seeds_to_connect:
                    seed_index = random.randint(0,len(seeds)-1)
                    if seed_index not in indices_seeds_to_connect:
                        indices_seeds_to_connect.append(seed_index)
                
                for seed_index in indices_seeds_to_connect:
                    seed_ip,seed_port = seeds[seed_index].split(':')
                    seed_port.replace("\n","")
                    t = threading.Thread(target=self.send_request_to_seed,args=(seed_ip,int(seed_port)))
                    t.daemon = True
                    t.start()
                while len(self.seed_node_list) != no_of_seeds_to_connect:
                    waiting = 0
                return True
                
        except Exception as e:
            print(f"Error occured! {e}")
            self.stop()
            # traceback.print_exc()
            return False
    
    def stop(self):
        self.listening = False
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
    
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

    def see_all_peer_nodes(self):
        try:
            peers = ""
            if len(self.peer_list) == 0:
                return "No Peers Connected Yet"
            
            for peer in self.peer_list:
                peers+=f"{peer[0]}:{peer[1]}\n"
            return peers
        except Exception as e:
            print(f"Error occured! {e}")
            return ""
        
    
    def see_all_seed_nodes(self):
        try:
            seeds = ""
            for seed in self.seed_node_list:
                seeds+=f"{seed[0]}:{seed[1]}\n"
            return seeds
        except Exception as e:
            print(f"Error occured! {e}")
            return ""


peer = PeerNode()
is_all_initialized = peer.connect_to_network()

if is_all_initialized:

    print("\n" + "=" * 50)
    print("       Welcome to the Panel of the this Client       ")
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
                    print(f"Error occured! {e}")

            elif action == 4:
                print(menu)

            else:
                print(f"Invalid option! Please select a valid action.\n{menu}")

        except ValueError:
            print("Invalid input! Please enter a number corresponding to an action.")
        except Exception as e:
            print(f"An error occurred: {e}")