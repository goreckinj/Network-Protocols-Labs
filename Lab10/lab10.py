import socket
import ssl
import pprint

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(('expired.badssl.com', 443))
context = ssl.create_default_context()

# SSLv2 considered harmful.


# SSLv3 has problematic security and is only required for really old
# clients such as IE6 on Windows XP


# disable compression to prevent CRIME attacks (OpenSSL 1.0+)


# verify certs and host name in client mode


# Let's try to load default system
# root CA certificates for the given purpose. This may fail silently.
ssl_socket = context.wrap_socket(sock, server_hostname = 'expired.badssl.com')
print(pprint.pformat(ssl_socket.getpeercert()))

