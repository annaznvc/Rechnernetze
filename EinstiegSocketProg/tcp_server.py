import socket, struct
from protokoll import decode_request, encode_response, berechne

serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serv_sock.bind(('', 9000))
serv_sock.listen(1)
print("TCP-Server wartet auf Port 9000 ...")

conn, addr = serv_sock.accept()
print(f"Verbindung von {addr}")

while True:
    # Header: ID(4) + OP(3) + N(1) = 8 Bytes
    header = b''
    while len(header) < 8:
        chunk = conn.recv(8 - len(header))
        if not chunk:
            break
        header += chunk
    if len(header) < 8:
        break

    n = struct.unpack_from('!B', header, 7)[0]

    # n Zahlen: je 4 Bytes
    zahlen_data = b''
    while len(zahlen_data) < n * 4:
        zahlen_data += conn.recv(n * 4 - len(zahlen_data))

    task_id, op, numbers = decode_request(header + zahlen_data)
    print(f"  Aufgabe {task_id}: {op}{numbers}")

    result = berechne(op, numbers)
    conn.send(encode_response(task_id, result))
    print(f"  Ergebnis: {result}")

conn.close()
serv_sock.close()
