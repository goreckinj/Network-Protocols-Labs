"""
- CS2911 - 011
- Fall 2017
- Lab 5
- Names:
  - Luke Anderson
  - Nicholas Gorecki

A simple HTTP client
"""

# import the "socket" module -- not using "from socket import *" in order to selectively use items with "socket." prefix
import socket

# import the "regular expressions" module
import re


def main():
    """
    Tests the client on a variety of resources
    """
    # Clear out old response file
    record_response('', 'responses.txt', 'w+')

    # this resource request should result in "chunked" data transfer
    get_http_resource('http://seprof.sebern.com/', 'index.html')
    # this resource request should result in "Content-Length" data transfer
    # get_http_resource('http://seprof.sebern.com/sebern1.jpg', 'sebern1.jpg')
    # get_http_resource('http://seprof.sebern.com:8080/sebern1.jpg', 'sebern2.jpg')
    # another resource to try for a little larger and more complex entity
    # get_http_resource('http://seprof.sebern.com/courses/cs2910-2014-2015/sched.md','sched-file.md')


def get_http_resource(url, file_name):
    """
    Get an HTTP resource from a server
           Parse the URL and call function to actually make the request.

    :param url: full URL of the resource to get
    :param file_name: name of file in which to store the retrieved resource

    (do not modify this function)
    """

    # Parse the URL into its component parts using a regular expression.
    url_match = re.search('http://([^/:]*)(:\d*)?(/.*)', url)
    url_match_groups = url_match.groups() if url_match else []
    # print 'url_match_groups=',url_match_groups
    if len(url_match_groups) == 3:
        host_name = url_match_groups[0]
        host_port = int(url_match_groups[1][1:]) if url_match_groups[1] else 80
        host_resource = url_match_groups[2]
        print('host name = {0}, port = {1}, resource = {2}'.format(host_name, host_port, host_resource))
        status_string = make_http_request(host_name.encode(), host_port, host_resource.encode(), file_name)
        print('get_http_resource: URL="{0}", status="{1}"'.format(url, status_string))
    else:
        print('get_http_resource: URL parse failed, request not sent')


def make_http_request(host, port, resource, file_name):
    """
    Get an HTTP resource from a server

    :param bytes host: the ASCII domain name or IP address of the server machine (i.e., host) to connect to
    :param int port: port number to connect to on server host
    :param bytes resource: the ASCII path/name of resource to get. This is everything in the URL after the domain name,
           including the first /.
    :param file_name: string (str) containing name of file in which to store the retrieved resource
    :return: the status code
    :rtype: int
    :author: Goreckinj, Andersonlp
    """
    # connect to host
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.connect(('localhost', 8080))

    # Make request lines and get chunks
    host_name = 'seprof.sebern.com'
    chunks = make_request(b'/index.html', host_name)

    # Send request to server
    for i in range(0, len(chunks)):
        tcp_socket.sendall(chunks[i])

    status_code = 500
    try:
        # Reads the http response and stores to file by chunking. Gets status code, content length and content type
        status_code, content_length, content_type, transfer_encoding = read_http_response(tcp_socket)

        if status_code == 200:
            # Reads the resource requested and stores to a file by chunking
            read_http_resource(tcp_socket, content_length, content_type, transfer_encoding, file_name)
    except RuntimeError as e:
        print(e)

    # Close socket
    tcp_socket.close()

    # Returns the status code of the response
    return status_code


def make_request(resource, host_name):
    """
    Makes a request to send to a server based off the resource and host name passed

    :param bytes resource: the ASCII path/name of resource to get. This is everything in the URL after the domain name,
           including the first /.
    :param str host_name: The domain name of the host to connect to
    :return: List of the chunks of bytes
    :rtype: bytes[]
    :author: Goreckinj, Andersonlp
    """
    # Create the request
    request = b'GET ' + resource + b' HTTP/1.1\r\n' + b'Host: ' + host_name.encode() + b'\r\n\r\n'

    # Chunk the request
    return chunk(request, 17)


def chunk(message, chunk_size):
    """
    Takes a bytes object and chunks it into a list at the specified size

    :param Bytes message: The bytes to be chunked
    :param int chunk_size: The byte size of each chunk
    :return: List of the chunks of bytes
    :rtype: bytes[]
    :author: Goreckinj
    """
    # Goes from 0 to length of request, sublisting for the length chunk_size allows. Stores chunks in a list and returns
    return [message[i:i + chunk_size] for i in range(0, len(message), chunk_size)]


def read_http_response(data_socket):
    """
    Reads the http response bytes and returns the message and the status code

    :param data_socket: The data socket to receive bytes from
    :return: Tuple of the decoded message and the status code
    :rtype: int
    :author: Goreckinj, Andersonlp
    """

    # Gets status line chunk, as well as the status code
    message, status_code = read_status_line(data_socket)
    # Writes status line chunk to file
    record_response(message, 'responses.txt', 'ab')

    content_length = -1
    content_type = 'NONE'
    transfer_encoding = 'NONE'
    # Reads through headers chunk by chunk. Writes each chunk separately to file
    while message != '\r\n':
        # Gets the next header line chunk
        message = read_header_line(data_socket).decode()

        # Check for content-length and content-type
        if message.__contains__('Content-Length'):
            # Get content length
            content_length = int((message[15:len(message) - 2]))
        elif message.__contains__('Content-Type'):
            # Get content type
            content_type = message[14:len(message) - 2]
        elif message.__contains__('Transfer-Encoding'):
            transfer_encoding = message[19: len(message) - 2]

        # Writes the header line chunk to file
        record_response(message, 'responses.txt', 'a')
    record_response('-------------------------------------------------- chunk data\n', 'responses.txt', 'a')
    # Returns the status code of the response
    return status_code, content_length, content_type, transfer_encoding


def read_status_line(data_socket):
    """
    Reads the request line from the data socket

    :author: Andersonlp, Goreckinj
    :param data_socket: The data socket to pull bytes from
    :return: str, int - The status line and the status code
    """
    message = b''
    status_code = b''
    crlf = 0
    spaces = 0

    # Read through status line
    while crlf < 2:
        # Get next byte
        b = next_chunk(data_socket, 1)
        # Identify start/end of status code
        if b == b' ':
            spaces += 1
        # Record status code
        if spaces == 1 and b != b' ':
            status_code += b
        # Checking for \r\n
        if b == b'\r':
            crlf += 1
        elif b == b'\n' and crlf == 1:
            crlf += 1
        elif crlf == 1:
            crlf = 0
        # Add byte to message
        message += b

    # Return message and status code
    return message, int(status_code.decode())


def read_header_line(data_socket):
    """
    Reads through the next header line from the data socket

    :author: Goreckinj, Andersonlp
    :param data_socket: The data socket to pull bytes from
    :return: str - The message from the data socket
    """
    message = b''
    crlf = 0

    # Read through status line
    while crlf < 2:
        # Get next byte
        b = next_chunk(data_socket, 1)
        # Checking for \r\n
        if b == b'\r':
            crlf += 1
        elif b == b'\n' and crlf == 1:
            crlf += 1
        elif crlf == 1:
            crlf = 0
        # Add byte to message
        message += b

    # Return message
    return message


def read_http_resource(data_socket, content_length, content_type, transfer_encoding, file_name):
    """
    Reads the resource, chunking the response and writing each chunk to a specified file

    :author: Andersonlp, Goreckinj
    :param data_socket: The data socket to pull bytes from
    :param content_length: The length in bytes of the resource
    :param content_type: The type of the resource
    :param transfer_encoding: The transfer encoding of the resource
    :param file_name: The specified file name to write the chunks to
    :return: None
    """
    with open(file_name, 'w+b') as file:
        if transfer_encoding.__contains__('chunked'):
            read_chunked_response(data_socket, file)
        elif transfer_encoding.__contains__('NONE'):
            read_unchunked_response(data_socket, content_length, file)
        else:
            print('Unsupported Transfer Encoding')


def read_chunked_response(data_socket, file):
    """
    Reads a chunked response of data from the socket and writes it to a file

    :author: Gorecki, Andersonlp
    :param data_socket: The data socket to pull bytes from
    :param file: The file to write to
    :return: None
    """
    packet_size = 0
    content_size = -1
    chunk_num = 1
    while content_size != 0:
        size_line = read_header_line(data_socket)
        content_size = int(size_line[0:len(size_line) - 2], 16)
        message = b''
        crlf = 0
        while crlf < 2:
            # Get next byte
            b = next_chunk(data_socket, 1)
            # Checking for \r\n
            if b == b'\n' and crlf == 1:
                crlf += 1
            elif b == b'\r':
                crlf += 1
            else:
                if crlf == 1:
                    crlf = 0
            # Add byte to message
            message += b
        file.write(message)
        packet_size += len(message)
        record_chunk(chunk_num, len(message), '[expected-length: ' + str(content_size + 2)
                     + ']' + ' [content-length: ' + str(len(message) - 2) + ']')
        chunk_num += 1
    record_response(('-------------------------------------------------- '
                     + str(("%.2f" % (packet_size / 1024)))
                     + ' kB\r\n\r\n'), 'responses.txt', 'a')


def read_unchunked_response(data_socket, content_length, file):
    """
    Reads the unchunked response from the data socket and writes it to a specified file.

    :author: Goreckinj, Andersonlp
    :param data_socket: The data socket to pull bytes from
    :param content_length: The byte-length of the content
    :param file: The file to write to
    :return: None
    """
    if 1024 >= content_length:
        b = next_chunk(data_socket, content_length)
        file.write(b)
        record_chunk(1, content_length, '')
    else:
        prev_i = 0
        chunk_num = 1
        # Loop content, taking *at max* 1kB per chunk
        for i in range(1024, content_length, 1024):
            # Get next chunk based off of Δi. i will jump 1kB each chunk, only go up to content_length. Thus
            # the last chunk possibly won't be exactly 1kB. This is done by the properties of the range()
            buffer_size = i - prev_i
            b = next_chunk(data_socket, buffer_size)
            # Write chunk to file
            file.write(b)
            record_chunk(chunk_num, buffer_size, '')
            # Get i to use as previous for next loop operation
            prev_i = i
            chunk_num += 1
        # Get last chunk that isn't a full 1kB
        b = next_chunk(data_socket, content_length - prev_i)
        # Write that chunk to the file
        file.write(b)
        record_chunk(chunk_num, content_length - prev_i, '')
    # Formatting that splits each response in responses.txt for visual aid. Also gives size of the resource
    record_response(('-------------------------------------------------- '
                     + str(("%.2f" % (content_length / 1024)))
                     + ' kB\r\n\r\n'), 'responses.txt', 'a')


def next_chunk(data_socket, buffer_size):
    """
    Gets the next chunk from the data socket

    :author: Goreckinj, Andersonlp
    :param data_socket: The data socket to pull the bytes from
    :param buffer_size: The amount of bytes to pull each time
    :return: buffer_size amount of bytes
    :rtype: bytes
    """
    # Makes sure that the next_chunk is equal to the buffer_size.
    bytez = data_socket.recv(buffer_size)
    while len(bytez) != buffer_size:
        bytez += data_socket.recv(buffer_size - len(bytez))

    return bytez


def record_chunk(chunk_num, chunk_length, foot_note):
    """
    Records the chunk received into responses.txt

    :author: Goreckinj
    :param chunk_num: The sequence number of the chunk
    :param chunk_length: The length of the chunk
    :param: foot_note: The foot note of the chunk record
    :return: None
    """
    record_response('Chunk ' + str(chunk_num) + ': ' + str(chunk_length) + ' b ' + foot_note
                    + '\n', 'responses.txt', 'a')


def record_response(message, file_name, file_action):
    """
    Write string message to file numbered by specified sequence

    :author: Goreckinj
    :param String message: The message to be stored
    :param String file_name: The file name to write the message to
    :param file_action: The specified file action when opening the file
    :return: None
    """
    try:
        # Open file specified by action
        with open(file_name, file_action) as file:
            # Write message to file
            file.write(message)
    except IOError as e:
        raise RuntimeError('Could not write message to file ' + file_name + ':\n', e)


main()
