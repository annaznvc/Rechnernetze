import struct
import socket

#---decode package---
#anfrage
def decode_package(message):
    message_type = struct.unpack('!b')
    match message_type:
        case 0:
            return encode_register(message)
        case 1:
            return encode_logout(message)
        case 2:
            return encode_update(message)
        case 4:
            return encode_tcp(message)

#server response
def decode_package_server_resonse(message):
    message_type, errcode, usrlist_lngt = struct.unpack('!BBI', message[:6])
    if errcode != 0:
        return message_type, errcode, None
    match message_type:
        case 0:
            return decode_register_response(message)
        case 1:
            return decode_logout_response(message)
        case 2:
            return decode_update_response(message)

def decode_message_type(message):
    message_type = struct.unpack('!b', message[:1])[0]
    return message_type

#---register---
#encode register
def decode_register(message):
    message_type, ip, port, name = struct.unpack('!B4sH32s', message)
    message_type_int = int(message_type)
    IP_str = socket.inet_ntoa(ip)
    name_str = name.decode("utf-8").rstrip('\x00')
    return message_type_int, IP_str, port, name_str

#decode register
def encode_register(IP, port, name):
    ip_bytes = socket.inet_aton(IP)  # "192.168.1.50" -> b'\xc0\xa8\x012'
    name_bytes = name if isinstance(name, bytes) else name.encode("utf-8")
    name_bytes = name_bytes[:32]  # optional: auf 32 Byte begrenzen
    return struct.pack('!B4sH32s', 0, ip_bytes, port, name_bytes)

#encode register response
def encode_register_response(errcode, usrlist):
    usrlist_lngt = usrlist.length
    usrlist_bytes = b''
    for usr in usrlist:
        usrlist_bytes += struct.pack('!4sH32s', socket.inet_aton(usr.ip), usr.port, usr.name.encode("utf-8"))
    return struct.pack('!B',0) + struct.pack('!B', errcode) + struct.pack('!I', usrlist_lngt)  + usrlist_bytes

#decode register response
def decode_register_response(message):
    usrlist = []
    offset = 6
    for _ in range(usrlist_lngt):
        ip_bytes, port, name_bytes = struct.unpack_from('!4sH32s', message, offset)
        ip_str = socket.inet_ntoa(ip_bytes)
        name_str = name_bytes.decode("utf-8").rstrip('\x00')
        usrlist.append((ip_str, port, name_str))
        offset += 38  # 4 + 2 + 32
    return 0, 0, usrlist

#---logout---
#encode logout
def encode_logout(data):
    #TODO
    pass

#decode logout
def decode_logout(message):
    #TODO
    pass

#decode logout response
def decode_logout_response(message):
    #TODO
    pass

#---update---
#encode update
def encode_update(ip, port):
    ip_bytes = socket.inet_aton(ip)  # "192.168.1.50" -> b'\xc0\xa8\x012'
    return struct.pack('!B4sH', 0, ip_bytes, port)

#decode update
def decode_update(message):
    message_type, IP, Port = struct.unpack('!B4sH', message)
    message_type_int = int(message_type)
    IP_str = socket.inet_ntoa(IP)
    return message_type_int, IP_str, Port

#encode update response
def encode_update_response(errcode, usrlist_login, usrlist_logout):
    usrlist_login_lngt = usrlist_login.length
    usrlist_login_bytes = b''
    for usr in usrlist_login:
        usrlist_login_bytes += struct.pack('!4sH32s', socket.inet_aton(usr.ip), usr.port, usr.name.encode("utf-8"))
    usrlist_logout_lngt = usrlist_login.length
    usrlist_logout_bytes = b''
    for usr in usrlist_logout:
        usrlist_logout_bytes += struct.pack('!4sH32s', socket.inet_aton(usr.ip), usr.port, usr.name.encode("utf-8"))
    return struct.pack('!B',0) + struct.pack('!B', errcode) + struct.pack('!I', usrlist_login_lngt)  + usrlist_login_bytes + struct.pack('!I', usrlist_logout_lngt) + usrlist_logout_bytes

#decode update response
def decode_update_response(message):
    usrlist_login = []
    usrlist_logout = []
    offset = 6
    for _ in range(usrlist_login_lngt):
        ip_bytes, port, name_bytes = struct.unpack_from('!4sH32s', message, offset)
        ip_str = socket.inet_ntoa(ip_bytes)
        name_str = name_bytes.decode("utf-8").rstrip('\x00')
        usrlist_login.append((ip_str, port, name_str))
        offset += 38  # 4 + 2 + 32
    for _ in range(usrlist_logout_lngt):
        ip_bytes, port, name_bytes = struct.unpack_from('!4sH32s', message, offset)
        ip_str = socket.inet_ntoa(ip_bytes)
        name_str = name_bytes.decode("utf-8").rstrip('\x00')
        usrlist_logout.append((ip_str, port, name_str))
        offset += 38  # 4 + 2 + 32
    return 2, 0, usrlist_login, usrlist_logout

#---Aufbau TCP---
#encode TCP
def encode_tcp(name, tcp_port):
    name_bytes = name if isinstance(name, bytes) else name.encode("utf-8")
    name_bytes = name_bytes[:32]  # optional: auf 32 Byte begrenzen
    return struct.pack('!B32sH', 4, name_bytes, tcp_port)

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
    return struct.pack('!BBH', 4, 0, open_tcp_port)

#---Message---
#encode message
def encode_message(message_256):
    return struct.pack('!B256s', 5, message_256.encode("utf-8")[:256])
#decode message
def decode_message(message):
    message_type, message_256 = struct.unpack('!B256s', message)
    message_type_int = int(message_type)
    message_str = message_256.decode("utf-8").rstrip('\x00')
    return message_type_int, message_str


