import argparse
import threading
from socket import AF_INET, socket, SOCK_STREAM
from threading import Thread

import socket
import time

def accept_incoming_connections():
    """Sets up handling for incoming clients."""
    while True:
        SERVER.setblocking(True)
        client, client_address = SERVER.accept()
        client.setblocking(False)
        SERVER.setblocking(False)
        print("%s:%s has connected." % client_address)
        addresses[client] = client_address
        Thread(target=handle_client, args=(client,)).start()

def handle_client(client):  # Takes client socket as argument.
    """Handles a single client connection."""
    name = ""
    prefix = ""

    while True:
        try:
            msg = client.recv(1024).decode()

            if msg == "":
                msg = "{QUIT}"
            print(msg)
            if msg.endswith("~SEND_FILE"):
                time.sleep(0.2)
                try:
                    print(msg)
                    msg_params = msg.split("}")
                    dest_name_sourc_name = msg_params[0][1:] # Remove the {
                    dest_name = dest_name_sourc_name.split("#")[0]
                    sourc_name = dest_name_sourc_name.split("#")[1]
                    
                    print("dest_name: " + dest_name + "sourc_name: " + sourc_name)
                    if dest_name == "ALL":
                        file_total = msg_params[1].split("~")[0]
                        file_name = file_total.split("@")[0]
                        file_size = file_total.split("@")[1]
                        #receive file
                        with open("./SendAll_Storage/" + file_name, "wb") as file:
                            c = 0
                            start_time = time.time()
                            while True:
                                try:
                                    data = client.recv(1024)
                                except:
                                    break
                                if not (data):
                                    break
                                file.write(data)
                                c += len(data)
                            end_time = time.time()
                        print("File transfer Complete.Total time: ", end_time - start_time)

                        send_msg = bytes("{SEND_FILE}"+str(file_name)+"@"+str(file_size), "utf-8")

                        sourc_socket = find_client_socket(sourc_name)

                        for sock in clients:
                            if sock != sourc_socket:
                                time.sleep(0.2)
                                sock.send(send_msg)
                                with open("./SendAll_Storage/" + file_name, "rb") as file:
                                    c = 0
                                    while True:
                                        try:
                                            data = file.read(1024)
                                        except:
                                            break
                                        if not (data):
                                            break
                                        sock.sendall(data)
                                        c += len(data)
                        continue

                    #receiver is a specific client
                    dest_sock = find_client_socket(dest_name)
                    if dest_sock:
                        file_total = msg_params[1].split("~")[0]
                        file_name = file_total.split("@")[0]
                        file_size = file_total.split("@")[1]
                        #receive file
                        with open("./restore_server/" + file_name, "wb") as file:
                            c = 0
                            start_time = time.time()
                            while True:
                                try:
                                    data = client.recv(1024)
                                except:
                                    break
                                if not (data):
                                    break
                                file.write(data)
                                c += len(data)
                            end_time = time.time()
                        print("File transfer Complete.Total time: ", end_time - start_time)
                        
                        send_msg = bytes("{SEND_FILE}"+str(file_name)+"@"+str(file_size), "utf-8")
                        dest_sock.send(send_msg)

                        with open("./restore_server/" + file_name, "rb") as file:
                            c = 0
                            while True:
                                try:
                                    data = file.read(1024)
                                except:
                                    break
                                if not (data):
                                    break
                                dest_sock.sendall(data)
                                c += len(data)

                    else:
                        print("Invalid Destination. %s" % dest_name)
                except:
                    pass
        

                continue

            # Avoid messages before registering
            if msg.startswith("{ALL}") and name:
                new_msg = msg.replace("{ALL}", "{MSG}"+prefix)
                send_message(new_msg, broadcast=True)
                continue

            if msg.startswith("{REGISTER}"):
                name = msg.split("}")[1]
                welcome = '{MSG}Welcome %s!' % name
                send_message(welcome, destination=client)
                msg = "{MSG}%s has joined the chat!" % name
                send_message(msg, broadcast=True)
                clients[client] = name
                prefix = name + ": "
                send_clients()
                continue
            if msg == "{QUIT}":
                client.close()
                try:
                    del clients[client]
                except KeyError:
                    pass
                if name:
                    send_message("{MSG}%s has left the chat." % name, broadcast=True)
                    send_clients()
                break
            # Avoid messages before registering
            if not name:
                continue
            # Until this point, it is either an unknown message or for an
            # specific client...
            try:
                msg_params = msg.split("}")
                dest_name = msg_params[0][1:] # Remove the {
                dest_sock = find_client_socket(dest_name)
                if dest_sock:
                    send_message(msg_params[1], prefix=prefix, destination=dest_sock)
                else:
                    print("Invalid Destination. %s" % dest_name)
            except:
                print("Error parsing the message: %s" % msg)
        except:
            pass



def send_clients():
    send_message("{CLIENTS}" + get_clients_names(), broadcast=True)


def get_clients_names(separator="|"):
    names = []
    for _, name in clients.items():
        names.append(name)
    return separator.join(names)


def find_client_socket(name):
    for cli_sock, cli_name in clients.items():
        if cli_name == name:
            return cli_sock
    return None


def send_message(msg, prefix="", destination=None, broadcast=False):
    send_msg = bytes(prefix + msg, "utf-8")
    if broadcast:
        """Broadcasts a message to all the clients."""
        for sock in clients:
            sock.send(send_msg)
    else:
        if destination is not None:
            destination.send(send_msg)


clients = {}
addresses = {}

parser = argparse.ArgumentParser(description="Chat Server")
parser.add_argument(
    '--host',
    help='Host IP',
    default="127.0.0.1"
)
parser.add_argument(
    '--port',
    help='Port Number',
    default=33002
)

server_args = parser.parse_args()


HOST = server_args.host
PORT = int(server_args.port)
BUFSIZ = 2048
ADDR = (HOST, PORT)

stop_server = False

SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SERVER.bind(ADDR)

if __name__ == "__main__":
    try:
        SERVER.listen(5)
        print("Server Started at {}:{}".format(HOST, PORT))
        print("Waiting for connection...")
        ACCEPT_THREAD = Thread(target=accept_incoming_connections)
        ACCEPT_THREAD.start()
        ACCEPT_THREAD.join()
        SERVER.close()
    except KeyboardInterrupt:
        print("Closing...")
        ACCEPT_THREAD.interrupt()
