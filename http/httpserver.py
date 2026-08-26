"""
 Implements a simple HTTP/1.0 Server

"""

from pathlib import Path
import socket
from collections import abc


# Define socket host and port
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 8000

# Get directory where httpserver.py is located
BASE_DIR = Path(__file__).resolve().parent

# Create socket
# set server_socket variable to AF_INET (IPv4 address family) and SOCK_STREAM (~TCP)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((SERVER_HOST, SERVER_PORT))
server_socket.listen(1)
print('Listening on port %s ...' % SERVER_PORT)

class HeaderDict(abc.MutableMapping):
    def __init__(self):
        # internal/private storage hence _
        self._data = {}
    # print(h)
    def __repr__(self):
        return '\n'.join(f"{k} : {v}" for k, v in self._data.items())
    # inside __setitem__/__getitem__/__delitem__, is the key you store/look up under 
    # the original casing or the normalized casing — and if you normalize, where exactly 
    # does the .upper() (or .lower()) call go?
    # h[i]
    def __getitem__(self, key):
        return self._data[key.upper()]
    # h[j] = smth
    def __setitem__(self, key, value):
        self._data[key.upper()] = value
    # del h[l]
    def __delitem__(self, key):
        self._data.pop(key.upper())
    # list[h] or for i in h: print(i)
    def __iter__(self):
        for i in self._data:
            yield i 
    # len(h)
    def __len__(self):
        return len(self._data)
    
while True:
    # Wait for client connections
    client_connection, client_address = server_socket.accept()

    # Get the client request (read the request string)
    request = client_connection.recv(1024).decode()
    print(request)

    """
    TODO: **Proper header parsing** ⭐⭐
    The tutorial only ever reads `headers[0]` — the request line. Everything else (`Host`, `Content-Type`, `Content-Length`, `Connection`, etc.) is ignored.
    Parse the full header block into a dict/map, not just the first line.
    Signal: string/protocol parsing, edge cases (folded headers, case-insensitivity, duplicate headers).
    """
    def parse_header(header):
        header_dict = HeaderDict()
        lines = header.split('\n')
        for line in lines:
            if not line.split():
                continue
            if ':' not in line: 
                header_dict["FILE"] = line.split()[1]
                continue
            k, v = line.split(': ')
            # per HTTP spec, Host, host, and HOST are the same header. Headers should be case-insensitive to be safe (normalising to upper here)
            header_dict[k] = v
        return header_dict

    # Parse HTTP headers, e.g. GET /ipsum.html HTTP1.1\n...
    headers = parse_header(request)

    # e.g. GET /ipsum.html HTTP/1.1
    filename = headers.get("file", '/')
    # Get the content of the file
    if filename in ['/', '/favicon.ico']:
        filename = '/index.html'

    # Strip leading slash to prevent Path treating it as root
    file_path = BASE_DIR / 'htdocs' / filename.lstrip('/')

    # ASSUMPTION: all html files are inside the htdocs folder    
    try:
        with open(file_path, 'r', encoding='utf-8') as fin:
            content = fin.read()
            fin.close()
            response = 'HTTP/1.0 200 OK\n\n' + content
    except FileNotFoundError:
        response = 'HTTP/1.0 404 NOT FOUND\n\nFile Not Found (oopsie)'

    # Send HTTP response
    client_connection.sendall(response.encode())
    # Close client connnection
    client_connection.close()

# Close socket
server_socket.close()

"""Second question, more important: you're normalizing on the write side (header_dict[k.upper()] = v). What happens the moment you — or future you, weeks from now, adding Content-Length handling for the POST-body TODO — writes headers.get('Content-Length') somewhere else in this file? Will that lookup succeed, given what you're actually storing the key as? If the answer is "no, because I'd need to remember to .upper() every single lookup site too," is that a robust solution, or a landmine you're leaving for yourself? Where would you put the normalization so it's impossible to forget — at write time, at read time, or somewhere that makes it moot either way (hint: is there a data structure or wrapper that does case-insensitive lookups natively)?"""

"""whatever string you put in the response body gets sent verbatim to the browser, and the browser interprets it as HTML.
    """
#root of a server request: GET / HTTP/1.0, which should return the index.html page by default
