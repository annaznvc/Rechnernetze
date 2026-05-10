import socket
from protokoll import encode_request, decode_response

client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_sock.connect(('192.168.137.1', 9000))

anfragen = [
    (1, 'SUM', [1, 2, 3, 4, 5]),
    (2, 'PRO', [2, 3, 4]),
    (3, 'MIN', [-10, 0, 7, 3]),
    (4, 'MAX', [-10, 0, 7, 3]),
]

for task_id, op, nums in anfragen:
    client_sock.send(encode_request(task_id, op, nums))
    data = client_sock.recv(8)
    resp_id, result = decode_response(data)
    print(f"Aufgabe {resp_id}: {op}{nums} = {result}")


print(client_sock.getsockname())

client_sock.close()
