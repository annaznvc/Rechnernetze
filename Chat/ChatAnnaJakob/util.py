import struct
import socket

# Message types (Client<->Server)
MSG_REGISTER = 0
MSG_LOGOUT = 1
MSG_UPDATE = 2
MSG_BROADCAST = 3

# Message types (Client<->Client)
MSG_TCP_SETUP = 4
MSG_CHAT_MESSAGE = 5


def decode_package(message):
    message_type = decode_message_type(message)
    if message_type == MSG_REGISTER:
        return decode_register(message)
    if message_type == MSG_LOGOUT:
        return decode_logout(message)
    if message_type == MSG_UPDATE:
        return decode_update(message)
    if message_type == MSG_TCP_SETUP:
        return decode_tcp(message)
    if message_type == MSG_BROADCAST:
        return decode_broadcast_request(message)
    return None


def decode_package_server_resonse(message):
    message_type = decode_message_type(message)
    if message_type == MSG_REGISTER:
        return decode_register_response(message)
    if message_type == MSG_LOGOUT:
        return decode_logout_response(message)
    if message_type == MSG_UPDATE:
        return decode_update_response(message)
    if message_type == MSG_BROADCAST:
        return decode_broadcast_response(message)
    if message_type == 255:
        _, errcode = struct.unpack('!BB', message[:2])
        return message_type, errcode
    return None

def decode_message_type(message):
    message_type = struct.unpack('!B', message[:1])[0]
    return message_type


def encode_error_response(errcode):
    return struct.pack('!BB', 255, errcode)

#---register---
#encode register
def decode_register(message):
    message_type, ip, port, name = struct.unpack('!B4sH32s', message)
    IP_str = socket.inet_ntoa(ip)
    name_str = name.decode("utf-8").rstrip('\x00')
    return message_type, IP_str, port, name_str

#decode register
def encode_register(IP, port, name):
    ip_bytes = socket.inet_aton(IP)  # "192.168.1.50" -> b'\xc0\xa8\x012'
    name_bytes = name if isinstance(name, bytes) else name.encode("utf-8")
    name_bytes = name_bytes[:32]  # optional: auf 32 Byte begrenzen
    return struct.pack('!B4sH32s', MSG_REGISTER, ip_bytes, port, name_bytes)

#encode register response
def encode_register_response(errcode, usrlist):
    usrlist_lngt = len(usrlist)
    usrlist_bytes = b''
    for usr in usrlist:
        ip, port, name = usr
        usrlist_bytes += struct.pack('!4sH32s', socket.inet_aton(ip), port, name.encode("utf-8")[:32])
    return struct.pack('!BBI', MSG_REGISTER, errcode, usrlist_lngt) + usrlist_bytes

#decode register response
def decode_register_response(message):
    message_type, errcode, usrlist_lngt = struct.unpack('!BBI', message[:6])
    usrlist = []
    offset = 6
    for _ in range(usrlist_lngt):
        ip_bytes, port, name_bytes = struct.unpack_from('!4sH32s', message, offset)
        ip_str = socket.inet_ntoa(ip_bytes)
        name_str = name_bytes.decode("utf-8").rstrip('\x00')
        usrlist.append((ip_str, port, name_str))
        offset += 38  # 4 + 2 + 32
    return message_type, errcode, usrlist

#---logout---
#encode logout
def encode_logout(name):
    name_bytes = name if isinstance(name, bytes) else name.encode("utf-8")
    return struct.pack('!B32s', MSG_LOGOUT, name_bytes[:32])

#decode logout
def decode_logout(message):
    message_type, name = struct.unpack('!B32s', message)
    name_str = name.decode("utf-8").rstrip('\x00')
    return message_type, name_str

#decode logout response
def decode_logout_response(message):
    message_type, errcode = struct.unpack('!BB', message[:2])
    return message_type, errcode


def encode_logout_response(errcode):
    return struct.pack('!BB', MSG_LOGOUT, errcode)

#---update---
#encode update
def encode_update(ip, port):
    ip_bytes = socket.inet_aton(ip)  # "192.168.1.50" -> b'\xc0\xa8\x012'
    return struct.pack('!B4sH', MSG_UPDATE, ip_bytes, port)

#decode update
def decode_update(message):
    message_type, IP, Port = struct.unpack('!B4sH', message)
    IP_str = socket.inet_ntoa(IP)
    return message_type, IP_str, Port

#encode update response
def encode_update_response(errcode, usrlist_login, usrlist_logout):
    usrlist_login_lngt = len(usrlist_login)
    usrlist_login_bytes = b''
    for usr in usrlist_login:
        ip, port, name = usr
        usrlist_login_bytes += struct.pack('!4sH32s', socket.inet_aton(ip), port, name.encode("utf-8")[:32])
    usrlist_logout_lngt = len(usrlist_logout)
    usrlist_logout_bytes = b''
    for usr in usrlist_logout:
        ip, port, name = usr
        usrlist_logout_bytes += struct.pack('!4sH32s', socket.inet_aton(ip), port, name.encode("utf-8")[:32])
    return struct.pack('!BBI', MSG_UPDATE, errcode, usrlist_login_lngt) + usrlist_login_bytes + struct.pack('!I', usrlist_logout_lngt) + usrlist_logout_bytes

#decode update response
def decode_update_response(message):
    message_type, errcode, usrlist_login_lngt = struct.unpack('!BBI', message[:6])
    usrlist_login = []
    usrlist_logout = []
    offset = 6
    for _ in range(usrlist_login_lngt):
        ip_bytes, port, name_bytes = struct.unpack_from('!4sH32s', message, offset)
        ip_str = socket.inet_ntoa(ip_bytes)
        name_str = name_bytes.decode("utf-8").rstrip('\x00')
        usrlist_login.append((ip_str, port, name_str))
        offset += 38  # 4 + 2 + 32

    usrlist_logout_lngt = struct.unpack_from('!I', message, offset)[0]
    offset += 4

    for _ in range(usrlist_logout_lngt):
        ip_bytes, port, name_bytes = struct.unpack_from('!4sH32s', message, offset)
        ip_str = socket.inet_ntoa(ip_bytes)
        name_str = name_bytes.decode("utf-8").rstrip('\x00')
        usrlist_logout.append((ip_str, port, name_str))
        offset += 38  # 4 + 2 + 32
    return message_type, errcode, usrlist_login, usrlist_logout


def encode_broadcast_request(name, message_256):
    name_bytes = name if isinstance(name, bytes) else name.encode("utf-8")
    msg_bytes = message_256 if isinstance(message_256, bytes) else message_256.encode("utf-8")
    return struct.pack('!B32s256s', MSG_BROADCAST, name_bytes[:32], msg_bytes[:256])


def decode_broadcast_request(message):
    message_type, name, msg = struct.unpack('!B32s256s', message)
    return message_type, name.decode("utf-8").rstrip('\x00'), msg.decode("utf-8").rstrip('\x00')


def encode_broadcast_response(errcode, sender_name, message_256):
    sender_bytes = sender_name if isinstance(sender_name, bytes) else sender_name.encode("utf-8")
    msg_bytes = message_256 if isinstance(message_256, bytes) else message_256.encode("utf-8")
    return struct.pack('!BB32s256s', MSG_BROADCAST, errcode, sender_bytes[:32], msg_bytes[:256])


def decode_broadcast_response(message):
    message_type, errcode, sender_name, msg = struct.unpack('!BB32s256s', message)
    return message_type, errcode, sender_name.decode("utf-8").rstrip('\x00'), msg.decode("utf-8").rstrip('\x00')

#---Aufbau TCP---
#encode TCP
def encode_tcp(name, tcp_port):
    name_bytes = name if isinstance(name, bytes) else name.encode("utf-8")
    name_bytes = name_bytes[:32]  # optional: auf 32 Byte begrenzen
    return struct.pack('!B32sH', MSG_TCP_SETUP, name_bytes, tcp_port)

#decode TCP
def decode_tcp(message):
    message_type, name, port, = struct.unpack('!B32sH', message)
    message_type_int = int(message_type)
    name_str = name.decode("utf-8").rstrip('\x00')
    return message_type_int, name_str, port

#decode tcp response
def decode_tcp_response(message):
    message_type, errcode, open_tcp_port = struct.unpack('!BBH', message[:4])
    return message_type, errcode, open_tcp_port

#encode TCP response
def encode_tcp_rsponse(open_tcp_port):
    return struct.pack('!BBH', MSG_TCP_SETUP, 0, open_tcp_port)

#---Message---
#encode message
def encode_message(message_256):
    return struct.pack('!B256s', MSG_CHAT_MESSAGE, message_256.encode("utf-8")[:256])
#decode message
def decode_message(message):
    message_type, message_256 = struct.unpack('!B256s', message)
    message_type_int = int(message_type)
    message_str = message_256.decode("utf-8").rstrip('\x00')
    return message_type_int, message_str


