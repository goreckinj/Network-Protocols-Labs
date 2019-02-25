"""
- CS2911 - 0NN
- Fall 2017
- Lab N
- Names:
  - Jason Gao
  - Nick Gorecki
  - Alex

A simple email sending program.

Thanks to Trip Horbinski from the Fall 2015 class for providing the password-entering functionality.
"""

# GUI library for password entry
import tkinter as tk

# Socket library
import socket

# SSL/TLS library
import ssl

# base-64 encode/decode
import base64

# Python date/time and timezone modules
import datetime
import time
import pytz
import tzlocal

# Module for reading password from console without echoing it
import getpass

# Modules for some file operations
import os
import mimetypes

# Extraneous

# Host name for MSOE (hosted) SMTP server
SMTP_SERVER = 'smtp.office365.com'

# The default port for STARTTLS SMTP servers is 587
SMTP_PORT = 587

# SMTP domain name
SMTP_DOMAINNAME = 'msoe.edu'


def main():
    """Main test method to send an SMTP email message.

    Modify data as needed/desired to test your code,
    but keep the same interface for the smtp_send
    method.
    """
    (username, password) = login_gui()

    message_info = {}
    message_info['To'] = 'rair@msoe.edu'
    message_info['From'] = username
    message_info['Subject'] = 'SMTP Email'
    message_info['Date'] = get_formatted_date()

    print("message_info =", message_info)

    message_text = 'Test message_info number 6\r\n\r\nAnother line.'

    smtp_send(password, message_info, message_text)


def login_gui():
    """
    Creates a graphical user interface for secure user authorization.

    :return: (email_value, password_value)
        email_value -- The email address as a string.
        password_value -- The password as a string.

    :author: Tripp Horbinski
    """
    gui = tk.Tk()
    gui.title("MSOE Email Client")
    center_gui_on_screen(gui, 370, 120)

    tk.Label(gui, text="Please enter your MSOE credentials below:") \
        .grid(row=0, columnspan=2)
    tk.Label(gui, text="Email Address: ").grid(row=1)
    tk.Label(gui, text="Password:         ").grid(row=2)

    email = tk.StringVar()
    email_input = tk.Entry(gui, textvariable=email)
    email_input.grid(row=1, column=1)

    password = tk.StringVar()
    password_input = tk.Entry(gui, textvariable=password, show='*')
    password_input.grid(row=2, column=1)

    auth_button = tk.Button(gui, text="Authenticate", width=25, command=gui.destroy)
    auth_button.grid(row=3, column=1)

    gui.mainloop()

    email_value = email.get()
    password_value = password.get()

    return email_value, password_value


def center_gui_on_screen(gui, gui_width, gui_height):
    """Centers the graphical user interface on the screen.

    :param gui: The graphical user interface to be centered.
    :param gui_width: The width of the graphical user interface.
    :param gui_height: The height of the graphical user interface.
    :return: The graphical user interface coordinates for the center of the screen.
    :author: Tripp Horbinski
    """
    screen_width = gui.winfo_screenwidth()
    screen_height = gui.winfo_screenheight()
    x_coord = (screen_width / 2) - (gui_width / 2)
    y_coord = (screen_height / 2) - (gui_height / 2)

    return gui.geometry('%dx%d+%d+%d' % (gui_width, gui_height, x_coord, y_coord))


# *** Do not modify code above this line ***


def smtp_send(password, message_info, message_text):
    """Send a message via SMTP.

    :author: gaoj, gorecki, alex
    :param password: String containing user password.
    :param message_info: Dictionary with string values for the following keys:
                'To': Recipient address (only one recipient required)
                'From': Sender address
                'Date': Date string for current date/time in SMTP format
                'Subject': Email subject
            Other keys can be added to support other email headers, etc.
    """

    status_354 = b'354'
    status_334 = b'334'
    status_250 = b'250'
    status_235 = b'235'
    status_221 = b'221'
    status_220 = b'220'

    tcp_socket = None
    wrapped_socket = None
    try:
        # connect socket
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.connect((SMTP_SERVER, SMTP_PORT))

        # get reply from server
        read_response(tcp_socket, status_220)

        # send ehlo
        send_reply(tcp_socket, b'EHLO ' + SMTP_DOMAINNAME.encode() + b'\r\n')

        # read status/header responses
        read_response(tcp_socket, status_250)

        # send starttls
        send_reply(tcp_socket, b'STARTTLS\r\n')

        # get server ready response
        read_response(tcp_socket, status_220)

        # create wrapped socket
        context = ssl.create_default_context()
        wrapped_socket = context.wrap_socket(tcp_socket, server_hostname=SMTP_SERVER)

        # send ehlo
        send_reply(wrapped_socket, b'EHLO ' + SMTP_DOMAINNAME.encode() + b'\r\n')

        # read status/header responses
        read_response(wrapped_socket, status_250)

        # send auth login w/ username b64
        send_reply(wrapped_socket, b'AUTH LOGIN ' + base64.b64encode(message_info['From'].encode()) + b'\r\n')

        # read password request
        read_response(wrapped_socket, status_334)

        # send password b64
        send_reply(wrapped_socket, base64.b64encode(password.encode()) + b'\r\n')

        # read authentication reply
        read_response(wrapped_socket, status_235)

        # Send over header lines + data [e.g.: MAIL FROM: ~~~ . . . DATA . . .]
        send_reply(wrapped_socket, b'MAIL FROM: <' + message_info['From'].encode() + b'>\r\n')
        read_response(wrapped_socket, status_250)
        send_reply(wrapped_socket, b'RCPT TO: <' + message_info['To'].encode() + b'>\r\n')
        read_response(wrapped_socket, status_250)
        send_reply(wrapped_socket, b'DATA\r\n')
        read_response(wrapped_socket, status_354)
        send_reply(wrapped_socket, create_data(message_info, message_text))
        read_response(wrapped_socket, status_250)

        # quit
        send_reply(wrapped_socket, b'QUIT\r\n')
        read_response(wrapped_socket, status_221)
    except RuntimeError as e:
        print(e)
        print('NOTICE: Force-Closing Connection')
        if tcp_socket is not None:
            tcp_socket.close()
        if wrapped_socket is not None:
            wrapped_socket.close()
    if tcp_socket is not None:
        tcp_socket.close()
    if wrapped_socket is not None:
        wrapped_socket.close()


def create_data(message_info, message_text):
    """
    Created the data message to send

    :author: gaoj, gorecki, alex
    :param message_info: Dictionary containing the message info
    :param message_text: The message to send
    :return: bytes
    """
    data = b'Content-Transfer-Encoding: 7bit\r\n' \
           + b'Content-Type: text/plain; charset="us-ascii"\r\n' \
           + b'Subject: ' + message_info['Subject'].encode() + b'\r\n' \
           + b'To: <' + message_info['To'].encode() + b'>\r\n' \
           + b'MIME-Version: 1.0\r\n' \
           + b'From: <' + message_info['From'].encode() + b'>\r\n' \
           + b'Date: ' + message_info['Date'].encode() + b'\r\n\r\n' \
           + message_text.encode() + b'\r\n.\r\n'
    return data


def read_response(data_socket, comparator):
    """
    Reads the response from the data_socket

    :author: gaoj, goreckinj, alex
    :param data_socket: The socket to pull bytes from
    :param comparator: the comparator to compare the status_code with
    :return: bytes[]
    """
    response = []

    # get response lines
    line = b''
    while line[3:4] != b' ' or line[-2:] != b'\r\n':
        line += next_byte(data_socket, 1)

        if line[-2:] == b'\r\n':
            response.append(line)
            if line[3:4] != b' ':
                line = b''

    # print response lines
    for lin in response:
        print(b'response: ' + lin)

    # get status code
    status_code = response[-1][:3]

    # check status code
    if status_code != comparator:
        raise RuntimeError('ERROR:\n\tExpected Status: ' + comparator.decode()
                           + '\n\tActual Status: ' + status_code.decode()
                           + '\n\tMessage: ' + response[-1][4:].decode())


def send_reply(data_socket, message):
    """
    Sends a reply to the server

    :author:
    :param data_socket: The socket to pull bytes from
    :param message: The message to send
    :return: None
    """
    print(b'reply: ' + message)
    data_socket.sendall(message)


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


def get_formatted_date():
    """Get the current date and time, in a format suitable for an email date header.

    The constant TIMEZONE_NAME should be one of the standard pytz timezone names.
    If you really want to see them all, call the print_all_timezones function.

    tzlocal suggested by http://stackoverflow.com/a/3168394/1048186

    See RFC 5322 for details about what the timezone should be
    https://tools.ietf.org/html/rfc5322

    :return: Formatted current date/time value, as a string.
    """
    zone = tzlocal.get_localzone()
    print("zone =", zone)
    timestamp = datetime.datetime.now(zone)
    timestring = timestamp.strftime('%a, %d %b %Y %H:%M:%S %z')  # Sun, 06 Nov 1994 08:49:37 +0000
    return timestring


def print_all_timezones():
    """ Print all pytz timezone strings. """
    for tz in pytz.all_timezones:
        print(tz)


# You probably won't need the following methods, unless you decide to
# try to handle email attachments or send multi-part messages.
# These advanced capabilities are not required for the lab assignment.


def get_mime_type(file_path):
    """Try to guess the MIME type of a file (resource), given its path (primarily its file extension)

    :param file_path: String containing path to (resource) file, such as './abc.jpg'
    :return: If successful in guessing the MIME type, a string representing the content
             type, such as 'image/jpeg'
             Otherwise, None
    :rtype: int or None
    """

    mime_type_and_encoding = mimetypes.guess_type(file_path)
    mime_type = mime_type_and_encoding[0]
    return mime_type


def get_file_size(file_path):
    """Try to get the size of a file (resource) in bytes, given its path

    :param file_path: String containing path to (resource) file, such as './abc.html'

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
