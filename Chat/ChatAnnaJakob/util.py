import struct
import socket

#---encode package---
def encode_package(message):
    message_type = struct.unpack('!b')
    match message_type:
        case 0:
            return encode_register(message)
        case 1:
            return encode_logout(message)
        case 2:
            return encode_update(message)

#---register---
#encode register
def decode_register(message):
    message_type, IP, Port, Name = struct.unpack('!B4sH32s', message)
    message_type_int = int(message_type)
    IP_str = socket.inet_ntoa(IP)
    name_str = Name.decode("utf-8").rstrip('\x00')
    return message_type_int, IP_str, Port, name_str

#decode register
def encode_register(IP, port, name):
    ip_bytes = socket.inet_aton(IP)  # "192.168.1.50" -> b'\xc0\xa8\x012'
    name_bytes = name if isinstance(name, bytes) else name.encode("utf-8")
    name_bytes = name_bytes[:32]  # optional: auf 32 Byte begrenzen
    return struct.pack('!B4sH32s', 0, ip_bytes, port, name_bytes)

#---logout---
#encode logout
def encode_logout(data):
    #TODO
    pass

#decode logout
def decode_logout(message):
    #TODO
    pass

#---update---
#encode update
def encode_update(IP, port):
    ip_bytes = socket.inet_aton(IP)  # "192.168.1.50" -> b'\xc0\xa8\x012'
    return struct.pack('!B4sH', 0, ip_bytes, port)

#decode update
def decode_update(message):
    message_type, IP, Port = struct.unpack('!B4sH', message)
    message_type_int = int(message_type)
    IP_str = socket.inet_ntoa(IP)
    return message_type_int, IP_str, Port

#---Aufbau TCP---
#encode TCP
def encode_tcp(message):
    #TODO
    pass
#decode TCP
def decode_tcp(data):
    #TODO
    pass

#---Message---
#encode message
def encode_message(message):
    #TODO
    pass
#decode message
def decode_message(data):
    #TODO
    pass