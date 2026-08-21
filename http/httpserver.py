"""
 Implements a simple HTTP/1.0 Server

"""

import socket


# Define socket host and port
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 8000

# Create socket
# set server_socket variable to AF_INET (IPv4 address family) and SOCK_STREAM (~TCP)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((SERVER_HOST, SERVER_PORT))
server_socket.listen(1)
print('Listening on port %s ...' % SERVER_PORT)

while True:
    # Wait for client connections
    client_connection, client_address = server_socket.accept()

    # Get the client request (read the request string)
    request = client_connection.recv(1024).decode()
    print(request)

    # Parse HTTP headers, e.g. GET /ipsum.html HTTP1.1\n...
    headers = request.split('\n')
    # e.g. GET /ipsum.html HTTP/1.1
    filename =  headers[0].split()[1]

    # Get the content of the file
    if filename in ['/', '/favicon.ico']:
        filename = '/index.html'

    # ASSUMPTION: all html files are inside the htdocs folder    
    fin = open('htdocs' + filename)
    content = fin.read()
    fin.close()

    # Send HTTP response
    response = 'HTTP/1.0 200 OK\n\n' + content
    client_connection.sendall(response.encode())
    # Close client connnection
    client_connection.close()

# Close socket
server_socket.close()

"""whatever string you put in the response body gets sent verbatim to the browser, and the browser interprets it as HTML.
    """
#root of a server request: GET / HTTP/1.0, which should return the index.html page by default
