import socket
from protokoll import decode_request, encode_response, berechne

udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.bind(('', 9001))
print("UDP-Server wartet auf Port 9001 ...")

while True:
    msg, addr = udp_sock.recvfrom(1500)
    task_id, op, numbers = decode_request(msg)
    print(f"  Aufgabe {task_id}: {op}{numbers}")

    result = berechne(op, numbers)
    udp_sock.sendto(encode_response(task_id, result), addr)
    print(f"  Ergebnis: {result}")
