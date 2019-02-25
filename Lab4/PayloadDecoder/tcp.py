"""
- CS2911 - 011
- Fall 2017
- Lab 5
- Names:
  - Lukas Anderson
  - Nick Gorecki

A simple TCP server/client pair.

The application protocol is a simple format: For each file uploaded, the client first sends four (big-endian) bytes indicating the number of lines as an unsigned binary number.

The client then sends each of the lines, terminated only by '\\n' (an ASCII LF byte).

The server responds with 'A' if it accepts the file, and 'R' if it rejects it.

Then the client can send the next file.
"""

# import the 'socket' module -- not using 'from socket import *' in order to selectively use items with 'socket.' prefix
import socket
import struct
import time
import sys

# Port number definitions
# (May have to be adjusted if they collide with ports in use by other programs/services.)
TCP_PORT = 12100

# Address to listen on when acting as server.
# The address '' means accept any connection for our 'receive' port from any network interface
# on this system (including 'localhost' loopback connection).
LISTEN_ON_INTERFACE = ''

# Address of the 'other' ('server') host that should be connected to for 'send' operations.
# When connecting on one system, use 'localhost'
# When 'sending' to another system, use its IP address (or DNS name if it has one)
# OTHER_HOST = '155.92.x.x'
OTHER_HOST = '169.254.221.206'
#OTHER_HOST = 'localhost'


def main():
    """
    Allows user to either send or receive bytes
    """
    # Get chosen operation from the user.
    action = input('Select "(1-TS) tcpsend", or "(2-TR) tcpreceive":')
    # Execute the chosen operation.
    if action in ['1', 'TS', 'ts', 'tcpsend']:
        tcp_send(OTHER_HOST, TCP_PORT)
    elif action in ['2', 'TR', 'tr', 'tcpreceive']:
        tcp_receive(LISTEN_ON_INTERFACE, TCP_PORT)
    else:
        print('Unknown action: "{0}"'.format(action))


def tcp_send(server_host, server_port):
    """
    - Send multiple messages over a TCP connection to a designated host/port
    - Receive a one-character response from the 'server'
    - Print the received response
    - Close the socket

    :param str server_host: name of the server host machine
    :param int server_port: port number on server to send to
    """
    print('tcp_send: dst_host="{0}", dst_port={1}'.format(server_host, server_port))
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.connect((server_host, server_port))

    num_lines = int(input('Enter the number of lines you want to send (0 to exit):'))
    while num_lines != 0:
        print('Now enter all the lines of your message')
        # This client code does not completely conform to the specification.
        #
        # In it, I only pack one byte of the range, limiting the number of lines this
        # client can send.
        #
        # While writing tcp_receive, you will need to use a different approach to unpack to meet the specification.
        #
        # Feel free to upgrade this code to handle a higher number of lines, too.
        tcp_socket.sendall(b'\x00\x00')
        time.sleep(1)  # Just to mess with your servers. :-)
        tcp_socket.sendall(b'\x00' + bytes((num_lines,)))

        # Enter the lines of the message. Each line will be sent as it is entered.
        for line_num in range(0, num_lines):
            line = input('')
            tcp_socket.sendall(line.encode() + b'\n')

        print('Done sending. Awaiting reply.')
        response = tcp_socket.recv(1)
        if response == b'A':  # Note: == in Python is like .equals in Java
            print('File accepted.')
        else:
            print('Unexpected response:', response)

        num_lines = int(input('Enter the number of lines you want to send (0 to exit):'))

    tcp_socket.sendall(b'\x00\x00')
    time.sleep(1)  # Just to mess with your servers. :-)  Your code should work with this line here.
    tcp_socket.sendall(b'\x00\x00')
    response = tcp_socket.recv(1)
    if response == b'Q':  # Reminder: == in Python is like .equals in Java
        print('Server closing connection, as expected.')
    else:
        print('Unexpected response:', response)

    tcp_socket.close()


def tcp_receive(listen_interface, listen_port):
    """
    - Listen for a TCP connection on a designated "listening" port
    - Accept the connection, creating a connection socket
    - Print the address and port of the sender
    - Repeat until a zero-length message is received:
      - Receive a message, saving it to a text-file (1.txt for first file, 2.txt for second file, etc.)
      - Send a single-character response 'A' to indicate that the upload was accepted.
    - Send a 'Q' to indicate a zero-length message was received.
    - Close data connection.

    :param String listen_interface: The listen interface for the server to listen on
    :param int listen_port: Port number on the server to listen on
    :author: Lukas Anderson
    :author: Nick Gorecki
    """
    print('tcp_receive (server): listen_port={0}'.format(listen_port))
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket.bind((listen_interface, listen_port))
    listen_socket.listen(1)
    print('Listening for data from client.')
    data_socket, sender_address = listen_socket.accept()
    print('Connected.')
    sequence = 1
    header = 1
    while header != 0:
        header = read_message(data_socket, sequence)
        if header != 0:
            data_socket.send(b'A')
            sequence += 1
    data_socket.send(b'Q')

    data_socket.close()
    listen_socket.close()


def read_message(data_socket, sequence):
    """
    Reads in byte after byte to create a human readable message.

    -Read first four bytes to determine lines
    -Each 0a should add 1 to a counter for line: Stop when counter = line count
    -0a must read in a new line: 20 must read in as a space
    -if next_byte() does not return, block

    :param socket data_socket: The data socket to pull bytes from
    :author: Lukas Anderson
    :author: Nick Gorecki
    """

    newLineCount = read_header(data_socket)
    if newLineCount != 0:
        read_message_body(newLineCount, data_socket, sequence)
    return newLineCount


def read_header(data_socket):
    """
    Loop through first four bytes: next_byte()

    :param socket data_socket: The data socket to pull bytes from
    :author: Nick Gorecki
    """
    header = b''

    for i in range(4):
        b = next_byte(data_socket)
        header += b
    # Decode bytes to int and return.
    return int.from_bytes(header, 'big')


def read_message_body(newLineCount, data_socket, sequence):
    """
    Accepts new next_byte() bytes until the currentLineCount equals the newLineCount

    :param int newLineCount: Uses the value read from read_header() to track the number of lines.
    :param socket data_socket: The data socket to pull bytes from
    :author: Lukas Anderson
    """

    read_line_by_byte(newLineCount, data_socket, sequence)


def read_line_by_byte(newLineCount, data_socket, sequence):
    """
    Reads the bytes line by line. Calls the write_to_file() method

    :param newLineCount: The line count of the data sent
    :param data_socket: The data socket to pull bytes from
    :author Lukas Anderson
    """
    currentLineCount = 0
    message = ''
    while currentLineCount < newLineCount:
        newByte = next_byte(data_socket)
        if newByte == b'\n':
            message += '\n'
            currentLineCount += 1
        else:
            message = message + newByte.decode('ASCII')

    try:
        write_to_file(message, sequence)
    except RuntimeError as e:
        print(e)


def next_byte(data_socket):
    """
    Read the next byte from the socket data_socket.
    The data_socket argument should be an open tcp data connection
    socket (either a client socket or a server data socket).
    It should not be a tcp server's listening socket.

    Read the next byte from the server.
    If the byte is not yet available, this method blocks (waits)
    until the byte becomes available.
    If there are no more bytes, this method blocks indefinitely.

    :param socket data_socket: The socket to read from
    :return: the next byte, as a bytes object with a single byte in it
    """
    return data_socket.recv(1)


def write_to_file(message, sequence):
    """
    Write whole string message to file.

    :param str message: The message to write to a file
    :author: Nick Gorecki
    """

    try:
        with open(sequence.__str__() + '.txt', "a+") as file:
            file.write(message)
    except IOError as e:
        raise RuntimeError('Could not write message to file:', e)


# Invoke the main method to run the program.
main()
