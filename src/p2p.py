from seed import SeedNode
import threading
import traceback
import os
import time
import json

class P2PNetwork:

    def __init__(self, config_file="config.txt"):
        self.config_file = config_file
        self.seeds = []
        self.seed_list_lock = False
    
    def initialize_seed(self,port):
        try:
            seed = SeedNode(port)
            print(f"----------Seed {seed.ip}:{seed.port} initialized----------")
            while self.seed_list_lock:
                waiting = 0
            self.seed_list_lock = True

            self.seeds.append(seed)
            with open(self.config_file,"a") as file:
                file.write(f"{seed.ip}:{seed.port}\n")

            self.seed_list_lock = False
            seed.start()
        except Exception as e:
            print(f"Error occured: {e}")
            traceback.print_exc()


    def initialize_seeds(self,n:int):
        try:
            for i in range(n):
                t = threading.Thread(target=self.initialize_seed,args=(2000+i*10,), daemon=True)
                # t.daemon = True
                t.start()
            return True
        except:
            return False
    
    def close_seed(self,ip,port):
        try:
            seed_to_close = None
            for seed in self.seeds:
                if seed.ip == ip and seed.port == port:
                    seed.stop()
                    seed_to_close = seed
                    break
            if seed_to_close != None:
                self.seeds.remove(seed_to_close)
                print(f"Seed {ip}:{port} is shut down now...")
            else:
                print(f"Seed {ip}:{port} was not found")
        except:
            print(f"Error!! Couldn't shut down the seed {ip}:{port}")
    
    def see_seed_nodes(self):
        seeds = ""
        for i,seed in enumerate(self.seeds):
            seeds+=f"Seed {i+1}: {seed.ip}:{seed.port}\n"
        return seeds

    def close_all_seeds(self):
        try:
            for seed in self.seeds:
                seed.stop()
                print(f"Seed {seed.ip}:{seed.port} is shut down now...")
            self.seeds = []
            os.remove(self.config_file)
        except FileNotFoundError:
            print("You have deleted the config file...")
        except:
            print("Error!! Couldn't shutdown all seeds...")
    
    def see_seed_node_description(self,ip,port):
        try:
            seed_not_found = True
            for seed in self.seeds:
                if seed.ip == ip and seed.port == port:
                    des = seed.give_description()
                    if des != None:
                        print(des)
                    seed_not_found = False
                    break
            if seed_not_found == True:
                print(f"No Seed Node found at {ip}:{port}")
        except Exception as e:
            print(f"Couldn't Process your request...\nIssue: {e}")

    def save_topology(self, filename="topology.json"):
        topology = {}
        for seed in self.seeds:
            seed_info = f"{seed.ip}:{seed.port}"
            peers = [f"{peer_ip}:{peer_port}" for peer_ip, peer_port in seed.peer_list]
            topology[seed_info] = peers
        with open(filename, "w") as file:
            json.dump(topology, file)


print("=" * 50)
print("           Welcome to the VnS Network!          ")
print("=" * 50)

print("\nYou can find the details of the network at our GitHub Repo.")

try:
    n = int(input("\nEnter the number of Seed Nodes you want in the network: "))
except ValueError:
    print("Invalid input! Please enter a valid number.")
    exit(1)

if __name__ == "__main__":
    # Initialize the P2P network
    try:
        p2p = P2PNetwork()
        is_all_initialized =  p2p.initialize_seeds(n)

        while len(p2p.seeds) != n:
            waiting = 0

        if is_all_initialized:

            print("\n" + "=" * 50)
            print("       Welcome to the Admin Panel of the Network       ")
            print("=" * 50)

            menu = """
            Menu Options:
            1. See all Seed Nodes of the Network
            2. Get A Seed Node Description
            3: Stop a specific seed node
            4: Stop all seed nodes and shut down the network
            5: Show the menu again
            """

            print(menu)

            while True:
                try:
                    action = int(input("\nEnter your action number: "))

                    if action == 1:
                        seeds = p2p.see_seed_nodes()
                        print(seeds)

                    elif action == 2:
                        ip_port = input("Enter the IP and PORT of the seed node (format: IP:PORT): ")
                        try:
                            ip, port = ip_port.split(':')
                            p2p.see_seed_node_description(ip.strip(),int(port.strip()))
                        except ValueError:
                            print("Invalid format! Please enter in IP:PORT format by entering the action number again...")

                    elif action == 3:
                        ip_port = input("Enter the IP and PORT of the seed node (format: IP:PORT): ")
                        try:
                            ip, port = ip_port.strip().split(':')
                            p2p.close_seed(ip.strip(), int(port.strip()))
                        except ValueError:
                            print("Invalid format! Please enter in IP:PORT format by entering the action number again...")

                    elif action == 4:
                        p2p.close_all_seeds()
                        print("We were happy to provide service :-)\nShutting Down Network!!")
                        break

                    elif action == 5:
                        print(menu)

                    else:
                        print(f"Invalid option! Please select a valid action.\n{menu}")

                except ValueError:
                    print("Invalid input! Please enter a number corresponding to an action.")
                except Exception as e:
                    print(f"An error occurred: {e}")

            p2p.save_topology()
            
    except KeyboardInterrupt:
        p2p.close_all_seeds()
        print("We were happy to provide service :-)\nShutting Down Network!!")