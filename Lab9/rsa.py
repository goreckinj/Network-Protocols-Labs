"""
- CS2911 - 0NN
- Fall 2017
- Lab N
- Names:
  - Nick Gorecki
  - Jason Gao

16-bit RSA
"""

import random
import sys

# Use these named constants as you write your code
import math

MAX_PRIME = 0b11111111  # The maximum value a prime number can have
MIN_PRIME = 0b11000001  # The minimum value a prime number can have
PUBLIC_EXPONENT = 17  # The default public exponent


def main():
    """ Provide the user with a variety of encryption-related actions """
    while True:
        # Get chosen operation from the user.
        action = input("Select an option from the menu below:\n"
                    "(1-CK) create_keys\n"
                    "(2-CC) compute_checksum\n"
                    "(3-VC) verify_checksum\n"
                    "(4-EM) encrypt_message\n"
                    "(5-DM) decrypt_message\n"
                    "(6-BK) break_key\n "
                    "Please enter the option you want:\n")
    # Execute the chosen operation.
        if action in ['1', 'CK', 'ck', 'create_keys']:
            create_keys_interactive()
        elif action in ['2', 'CC', 'cc', 'compute_checksum']:
            compute_checksum_interactive()
        elif action in ['3', 'VC', 'vc', 'verify_checksum']:
            verify_checksum_interactive()
        elif action in ['4', 'EM', 'em', 'encrypt_message']:
            encrypt_message_interactive()
        elif action in ['5', 'DM', 'dm', 'decrypt_message']:
            decrypt_message_interactive()
        elif action in ['6', 'BK', 'bk', 'break_key']:
            break_key_interactive()
        else:
            print("Unknown action: '{0}'".format(action))
            print("Program Exiting")
            exit(0)


def create_keys_interactive():
    """
    Create new public keys

    :return: the private key (d, n) for use by other interactive methods
    """

    key_pair = create_keys()
    pub = get_public_key(key_pair)
    priv = get_private_key(key_pair)
    print("Public key: ")
    print(pub)
    print("Private key: ")
    print(priv)
    return priv


def compute_checksum_interactive():
    """
    Compute the checksum for a message, and encrypt it
    """

    priv = create_keys_interactive()

    message = input('Please enter the message to be checksummed: ')

    hash = compute_checksum(message)
    print('Hash:', "{0:04x}".format(hash))
    cypher = apply_key(priv, hash)
    print('Encrypted Hash:', "{0:04x}".format(cypher))


def verify_checksum_interactive():
    """
    Verify a message with its checksum, interactively
    """

    pub = enter_public_key_interactive()
    message = input('Please enter the message to be verified: ')
    recomputed_hash = compute_checksum(message)

    string_hash = input('Please enter the encrypted hash (in hexadecimal): ')
    encrypted_hash = int(string_hash, 16)
    decrypted_hash = apply_key(pub, encrypted_hash)
    print('Recomputed hash:', "{0:04x}".format(recomputed_hash))
    print('Decrypted hash: ', "{0:04x}".format(decrypted_hash))
    if recomputed_hash == decrypted_hash:
        print('Hashes match -- message is verified')
    else:
        print('Hashes do not match -- has tampering occured?')


def encrypt_message_interactive():
    """
    Encrypt a message
    """

    message = input('Please enter the message to be encrypted: ')
    pub = enter_public_key_interactive()
    encrypted = ''
    for c in message:
        encrypted += "{0:04x}".format(apply_key(pub, ord(c)))
    print("Encrypted message:", encrypted)


def decrypt_message_interactive(priv=None):
    """
    Decrypt a message
    """

    encrypted = input('Please enter the message to be decrypted: ')
    if priv is None:
        priv = enter_key_interactive('private')
    message = ''
    for i in range(0, len(encrypted), 4):
        enc_string = encrypted[i:i + 4]
        enc = int(enc_string, 16)
        dec = apply_key(priv, enc)
        if dec >= 0 and dec < 256:
            message += chr(apply_key(priv, enc))
        else:
            print('Warning: Could not decode encrypted entity: ' + enc_string)
            print('         decrypted as: ' + str(dec) + ' which is out of range.')
            print('         inserting _ at position of this character')
            message += '_'
    print("Decrypted message:", message)


def break_key_interactive():
    """
    Break key, interactively
    """

    pub = enter_public_key_interactive()
    priv = break_key(pub)
    print("Private key:")
    print(priv)
    decrypt_message_interactive(priv)


def enter_public_key_interactive():
    """
    Prompt user to enter the public modulus.

    :return: the tuple (e,n)
    """

    print('(Using public exponent = ' + str(PUBLIC_EXPONENT) + ')')
    string_modulus = input('Please enter the modulus (decimal): ')
    modulus = int(string_modulus)
    return (PUBLIC_EXPONENT, modulus)


def enter_key_interactive(key_type):
    """
    Prompt user to enter the exponent and modulus of a key

    :param key_type: either the string 'public' or 'private' -- used to prompt the user on how
                     this key is interpretted by the program.
    :return: the tuple (e,n)
    """
    string_exponent = input('Please enter the ' + key_type + ' exponent (decimal): ')
    exponent = int(string_exponent)
    string_modulus = input('Please enter the modulus (decimal): ')
    modulus = int(string_modulus)
    return (exponent, modulus)


def compute_checksum(string):
    """
    Compute simple hash

    Given a string, compute a simple hash as the sum of characters
    in the string.

    (If the sum goes over sixteen bits, the numbers should "wrap around"
    back into a sixteen bit number.  e.g. 0x3E6A7 should "wrap around" to
    0xE6A7)

    This checksum is similar to the internet checksum used in UDP and TCP
    packets, but it is a two's complement sum rather than a one's
    complement sum.

    :param str string: The string to hash
    :return: the checksum as an integer
    """

    total = 0
    for c in string:
        total += ord(c)
    total %= 0x8000  # Guarantees checksum is only 4 hex digits
    # How many bytes is that?
    #
    # Also guarantees that that the checksum will
    # always be less than the modulus.
    return total


# ---------------------------------------
# Do not modify code above this line
# ---------------------------------------

def create_keys():
    """
    Create the public and private keys.

    :author: gaoj, goreckinj
    :return: the keys as a three-tuple: (e,d,n)
    """
    e = PUBLIC_EXPONENT
    p, q = gen_p_q(e)
    n = p*q
    z = (p-1)*(q-1)
    d = get_d(e, z)

    # visual aid
    print('p: ' + str(p)
          + '\nq: ' + str(q)
          + '\nn: ' + str(n)
          + '\nz: ' + str(z)
          + '\nd: ' + str(d)
          + '\n')
    return (e, d, n)


def apply_key(key, m):
    """
    Apply the key, given as a tuple (e,n) or (d,n) to the message.

    This can be used both for encryption and decription.

    :author: gaoj, goreckinj
    :param tuple key: (e,n) or (e,d)
    :param int m: the message as a number 1 < m < n (roughly)
    :return: the message with the key applied. For example,
             if given the public key and a message, encrypts the message
             and returns the ciphertext.
    """

    return (m**key[0]) % key[1]


def break_key(pub):
    """
    Break a key.  Given the public key, find the private key.
    Factorizes the modulus n to find the prime numbers p and q.

    You can follow the steps in the "optional" part of the in-class
    exercise.

    :author: gaoj, goreckinj
    :param pub: a tuple containing the public key (e,n)
    :return: a tuple containing the private key (d,n)
    """

    e = pub[0]
    n = pub[1]
    p = 0
    q = 0

    # get p and q
    for i in range(0, 32):
        p = i << 1 | 0b11000001
        if n % p == 0 and int(n / p) != p:
            q = int(n / p)
            break

    # get d
    if p*q == n:
        z = (p-1)*(q-1)
        d = get_d(e, z)
    else:
        print("ERROR:\n\tKey could not be properly broke.")

    return (d, p*q)


def get_d(e, z):
    """
    Gets d given e and z

    :author: gaoj, goreckinj
    :param e: encryption exponent
    :param z: the totient
    :return: int
    """
    for i in range(2, z):
        if ((i * e) % z) == 1:
            return i
    return -1


def gen_p_q(e):
    """
    Gets p and q given e

    :author: gaoj, goreckinj
    :param e: encryption exponent
    :return: int[]
    """
    p = 4
    q = 4

    # keep generating p and q while equal
    while p == q:
        # generate p
        while not is_prime(p) or ((p - 1) % e) == 0:
            p = random.randint(0, 31) << 1 | 0b11000001
        # generate q
        while not is_prime(q) or ((q - 1) % e) == 0:
            q = random.randint(0, 31) << 1 | 0b11000001
        # if equal to each other, reset p and q
        if p == q:
            print('P AND Q EQUAL')
            p = 4
            q = 4

    return p, q


def is_prime(num):
    """
    Checks if num is prime

    :author: gaoj, goreckinj
    :param num: the number to check
    :return: boolean
    """
    if num < 2:
        return False
    for i in range(2, int(math.sqrt(num)) + 1):
        if num % i == 0:
            return False
    return True

# ---------------------------------------
# Do not modify code below this line
# ---------------------------------------


def get_public_key(key_pair):
    """
    Pulls the public key out of the tuple structure created by
    create_keys()

    :param key_pair: (e,d,n)
    :return: (e,n)
    """

    return (key_pair[0], key_pair[2])


def get_private_key(key_pair):
    """
    Pulls the private key out of the tuple structure created by
    create_keys()

    :param key_pair: (e,d,n)
    :return: (d,n)
    """

    return (key_pair[1], key_pair[2])


main()

"""
# Introduction:
    Use RSA to create and break public/private keys. 
    
# What we learned:
    To use bitwise operators instead of concatenating ASCII characters.
    
# Things we liked:
    Being able to implement successful RSA code in such a simple way.
"""
