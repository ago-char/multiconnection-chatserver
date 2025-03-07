
import selectors
import socket
import threading
import sys
from time import sleep
import signal

stop_flag=False

c_list=[]
MAX_CLIENTS=2

def signal_handler(sig, frame):
	global stop_flag
	# cleanup
	client: socket.socket
	for client in c_list:
		try:
			client.sendall("Conn closed by server. Press Return to return.".encode("utf-8"))
			client.close()
		except:
			removeClient(client)
	print(f"\nCtrl+C caught.. Aborting {len(c_list)} clients.")
	stop_flag = True
	exit()
    # selector.close()  # Close the selector to stop the I/O loop

def catchCtrlC():
    # Register the signal handler for SIGINT (Ctrl+C)
    signal.signal(signal.SIGINT, signal_handler)
    
    while not stop_flag:
        sleep(1.0)

def addClient(new_client: socket.socket):
        c_list.append(new_client)
        print(f"totalConn={len(c_list)}")

def removeClient(client: socket.socket):
        c_list.remove(client)
        print(f"totalConn={len(c_list)}")

def isClientConnected(cli_sock: socket.socket):
	try:
		cli_sock.sendall("test connection")
	except:
		return False
	return True


def main():
	# Create a default selector
	selector = selectors.DefaultSelector()

	# Create a non-blocking server socket
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_socket.bind(('localhost', 12345))
	server_socket.listen(0)
	server_socket.setblocking(False)

	# Register the server socket with the selector for read events
	selector.register(server_socket, selectors.EVENT_READ, data=None)
	selector.register(sys.stdin, selectors.EVENT_READ, data=None)

	print("Server is listening on port 12345...")

	no_of_clients=0
	while not stop_flag:
		# Wait for events on the registered sockets
		events = selector.select()  # Returns a list of (key, events) tuples
		
		for key, event in events:
			# If the event is on the server socket (new connection)
			if key.fileobj == server_socket:
				if no_of_clients < MAX_CLIENTS:
					# server_socket.listen(1)
					client_socket, addr = server_socket.accept()  # Accept the new connection
					print(f"Accepted connection from {addr}")
					client_socket.sendall("You are connected.\n".encode())
					
					addClient(client_socket)
					no_of_clients+=1
					client_socket.setblocking(False)  # Set the client socket to non-blocking
					# Register the client socket for read events
					selector.register(client_socket, selectors.EVENT_READ, data=client_socket)

				else:
					selector.unregister(server_socket)
						
			
			# if event is occured on stdin, server is trying to send message 
			elif key.fileobj == sys.stdin:
				# print("hi")
				if c_list:
					data=sys.stdin.readline()
					client: socket.socket
					for client in c_list:
						if client.fileno() != -1 and c_list and no_of_clients >= 1:
							client.sendall(data.encode("utf-8"))

			# If the event is on a client socket (data is available)
			else:
				client_socket: socket.socket
				client_socket = key.fileobj
				print("Waiting...!")
				data = client_socket.recv(1024)  # Read data from the client
				if data:
					_, port=client_socket.getpeername()
					print(f"\t{port} says: {data.decode()}",end='\0')
					# client_socket.send(data)  # Echo back the data this is not mandetory 
				else:
					print("Closing connection")
					no_of_clients-=1
					removeClient(client_socket)
					selector.unregister(client_socket)
					client_socket.close()
					selector.register(server_socket,selectors.EVENT_READ,data=None)

# a thread for main task
t1=threading.Thread(target=main)
t1.daemon=True
t1.start()

catchCtrlC()