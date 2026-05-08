import socket
from protokoll import encode_request, decode_response

udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.settimeout(3)

anfragen = [
    (1, 'SUM', [1, 2, 3, 4, 5]),
    (2, 'PRO', [2, 3, 4]),
    (3, 'MIN', [-10, 0, 7, 3]),
    (4, 'MAX', [-10, 0, 7, 3]),
]

for task_id, op, nums in anfragen:
    udp_sock.sendto(encode_request(task_id, op, nums), ('127.0.0.1', 9001))
    msg, addr = udp_sock.recvfrom(1500)
    resp_id, result = decode_response(msg)
    print(f"Aufgabe {resp_id}: {op}{nums} = {result}")

udp_sock.close()
