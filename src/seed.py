# >1 seed node
import socket
import threading


class SeedNode:
    def __init__(self):
        self.peer_list = [] # list of tuples of (addr, port) of all peers in the network
        self.ip = socket.gethostname()
        self.port = 5000
    
    def accept_new_node(self,peer_socket : socket.socket ,peer_addr : str):
        '''
        Peer Message Format: Myself:<Myself.IP>:<Myself.PORT>
        Add to peer list
        Sending peers format:
        comma separated peers: "<Peer1.IP>:<Peer1.PORT>,<Peer2.IP>:<Peer2.PORT>..."
        '''
        msg = ""
        while True:
            data = peer_socket.recv(1024)
            if not data:
                break
            msg+=data.decode()
        
        _,peer_ip,peer_port = msg.split(':')
        peer_list = self.peer_list
        self.peer_list.append((peer_ip,peer_addr))
        msg = ""
        
        for peers_ip,peers_port in peer_list:
            msg+=f"{peers_ip}:{peer_port}"  
        peer_socket.sendall(msg)
        peer_socket.close()    
        

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
        while True:
           data =  peer_socket.recv(1024)
           if not data:
               break
           msg+=data.decode()
        if msg.startswith("Myself"):
            self.accept_new_node(peer_socket,peer_addr)
        elif msg.startswith("Dead Node"):
            self.report_dead_node(peer_socket,peer_addr)
        else:
            peer_socket.sendall("Invalid Message Format".encode())
            peer_socket.close()
    
    def listen(self):
        '''
        Listen for a new connection
        For creation of new node: Peer message format: Myself:<Myself.IP>:<Myself.PORT>
        For reporting a dead node: Peer message format: Dead Node:<DeadNode.IP>:<DeadNode.Port>:<self.timestamp>:<self.IP>
        '''
        s =  socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.bind(self.ip,self.port)
        s.listen()
        while True:
            peer_socket,peer_addr = s.accept()
            threading.Thread(target=self.handle_request,args=(peer_socket,peer_addr)).start()