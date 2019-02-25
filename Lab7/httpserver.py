"""
- CS2911 - 011
- Fall 2017
- Lab 7
- Names:
  - goreckinj
  - gaoj

A simple HTTP server
"""

import socket
import re
import threading
import os
import mimetypes
import datetime


def main():
    """ Start the server """
    http_server_setup(8080)


def http_server_setup(port):
    """
    Start the HTTP server
    - Open the listening socket
    - Accept connections and spawn processes to handle requests

    :param port: listening port number
    """

    num_connections = 10
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_address = ('', port)
    server_socket.bind(listen_address)
    server_socket.listen(num_connections)
    try:
        while True:
            request_socket, request_address = server_socket.accept()
            print('connection from {0} {1}'.format(request_address[0], request_address[1]))
            # Create a new thread, and set up the handle_request method and its argument (in a tuple)
            request_handler = threading.Thread(target=handle_request, args=(request_socket,))
            # Start the request handler thread.
            request_handler.start()
            # Just for information, display the running threads (including this main one)
            print('threads: ', threading.enumerate())
    # Set up so a Ctrl-C should terminate the server; this may have some problems on Windows
    except KeyboardInterrupt:
        print("HTTP server exiting . . .")
        print('threads: ', threading.enumerate())
        server_socket.close()


def handle_request(request_socket):
    """
    Handle a single HTTP request, running on a newly started thread.

    Closes request socket after sending response.

    Should include a response header indicating NO persistent connection

    :author: goreckinj, gaoj
    :param request_socket: socket representing TCP connection from the HTTP client_socket
    :return: None
    """

    # gets the contents necessary for making an http response
    # date, connection, content_length, content_type,
    request_lines, version, status_code, status_phrase, response_lines, resource = read_http_request(request_socket)
    for key, value in request_lines.items():
        print(key + b': ' + value)
    # gets creates the response in bytes
    http_response = make_http_response_lines(version, status_code, status_phrase, response_lines)
    if status_code == b'200':
        http_response += get_resource(resource.decode())
        # sends the response to the client
    request_socket.sendall(http_response)
    # closes the socket
    request_socket.close()


def make_http_response_lines(version, status_code, status_phrase, response_lines):
    """
    Makes the http response lines to send to the client

    :author: goreckinj, gaoj
    :param version: The version of the server's HTML
    :param status_code: The status code
    :param status_phrase: The status phrase
    :param response_lines: The header lines of the response
    :return: dict - The dictionary with the header lines
    """

    http_response = (version + b' ' + status_code + b' ' + status_phrase + b'\r\n')
    if status_code == b'200':
        for key, value in response_lines.items():
            http_response += key + b': ' + value + b'\r\n'
        http_response += b'\r\n'
    else:
        for key, value in response_lines.items():
            if key != b'Content-Length' or key != b'Content-Type':
                http_response += key + b': ' + value + b'\r\n'
        http_response += b'\r\n'

    return http_response


def get_resource(resource):
    """
    Gets the bytes from the resource

    :author: goreckinj
    :param resource: The resource to pull bytes from
    :return: bytes - The resource in bytes
    """

    message = b''
    try:
        with open(resource, 'rb') as file:
            for line in file.readlines():
                message += line
    except IOError as e:
        print('Error opening/reading file: ' + resource)

    return message


def read_http_request(data_socket):
    """
    Reads the request from the data socket

    :author: goreckinj, gaoj
    :author: Andersonlp, Goreckinj
    :param data_socket: The data socket to pull bytes from
    :return: str, int - The status line and the status code
    """

    response_lines = {}
    # gets method call, resource and version of client
    method, resource, version = read_status_line(data_socket)
    # if no resource requested, set to default
    if resource == b'/':
        resource = b'./index.html'
    else:
        resource = b'.' + resource
    # gets any possible header lines sent as an array
    request_lines = read_header_lines(data_socket)

    # assigns header line data to a dictionary
    response_lines[b'Date'] = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT').encode()
    response_lines[b'Connection'] = b'close'
    response_lines[b'Content-Length'] = str(get_file_size('.' + resource.decode())).encode()
    type = get_mime_type('.' + resource.decode()).encode()
    print(type)
    response_lines[b'Content-Type'] = type

    # the status code to send to the client
    status_code = b'200'
    # the status phrase to send to the client
    status_phrase = b'OK'
    # updates status code depending on if resource is invalid
    if response_lines[b'Content-Length'] is None or response_lines[b'Content-Type'] is None or method != b'GET':
        status_code = b'500'
        status_phrase = b'Internal Server Error'
    # the connection to send to the client
    # the date the request was satisfied to send to the client
    # returns information needed for making a response

    return request_lines, version, status_code, status_phrase, response_lines, resource


def read_status_line(data_socket):
    """
    Reads the status line of the request from the data socket

    :author: goreckinj, gaoj
    :param data_socket: The data socket to pull bytes from
    :return: str[] - The method call, the resource requested and the version type
    """

    message = next_byte(data_socket, 2)
    while message[-2:] != b'\r\n':
        message += next_byte(data_socket, 1)
    return message[:-2].split(b' ')


def read_header_lines(data_socket):
    """
    Reads the header lines of the request (if there are any)

    :author: goreckinj, gaoj
    :param data_socket: The data socket to pull bytes from
    :return: str[] - The header lines of the request
    """

    header_lines = {}
    message = next_byte(data_socket, 2)
    while message != b'QUIT':
        if len(message) == 0:
            message = next_byte(data_socket, 2)
        else:
            message += next_byte(data_socket, 1)
        if message[-2:] != b'\r\n' or len(message) != 2:
            if message[-2:] == b'\r\n':
                temp_array = message[:-2].split(b' ')
                key = temp_array[0][:-1]
                value = temp_array[1]
                header_lines[key] = value
                message = b''
        else:
            message = b'QUIT'

    return header_lines


def next_byte(data_socket, buffer_size):
    """
    Gets the next byte from the data socket

    :author: goreckinj
    :param data_socket: The data socket to pull bytes from
    :param buffer_size: The amount of bytes to pull
    :return: bytes - The bytes received
    """

    bytez = data_socket.recv(buffer_size)
    while len(bytez) != buffer_size:
        bytez += data_socket.recv(buffer_size - len(bytez))

    return bytez


def get_mime_type(file_path):
    """
    Try to guess the MIME type of a file (resource), given its path (primarily its file extension)

    :param file_path: string containing path to (resource) file, such as './abc.html'
    :return: If successful in guessing the MIME type, a string representing the content type, such as 'text/html'
             Otherwise, None
    :rtype: int or None
    """

    mime_type_and_encoding = mimetypes.guess_type(file_path)
    mime_type = mime_type_and_encoding[0]

    return mime_type


def get_file_size(file_path):
    """
    Try to get the size of a file (resource) as number of bytes, given its path

    :param file_path: string containing path to (resource) file, such as './abc.html'
    :return: If file_path designates a normal file, an integer value representing the the file size in bytes
             Otherwise (no such file, or path is not a file), None
    :rtype: int or None
    """

    # Initially, assume file does not exist
    file_size = None
    if os.path.isfile(file_path):
        file_size = os.stat(file_path).st_size

    return file_size


main()

# The use of a dictionary is very easy and versatile. Building and stripping requests is handy and fun!
