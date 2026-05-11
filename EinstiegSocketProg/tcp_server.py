import socket, struct
from protokoll import decode_request, encode_response, berechne

serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serv_sock.bind(('', 9000))
serv_sock.listen(1) #maximal 1 verbindung
print("TCP-Server wartet auf Port 9000 ...")

conn, addr = serv_sock.accept() # accept gibt ein tuppel zurück
print(f"Verbindung von {addr}")

while True: # server läuft dauerhaft in schleife weil er mehrere Anfragen hintereinander vom selben Client verarbeiten kann
    # Header: ID(4) + OP(3) + N(1) = 8 Bytes
    header = b'' # leeres Byte Objekt
    while len(header) < 8: #solange nicht alle 8 bytes da sind
        chunk = conn.recv(8 - len(header)) # übrigen bytes anfordern
        if not chunk: # leerer Chunk = Client hat verbindung getrennt
            break
        header += chunk # chunk an header anhängen
    if len(header) < 8:
        break

    n = struct.unpack_from('!B', header, 7)[0] #Byte 7 enthält die Anzahl der Zahlen, zugriff auf erstes eleemnt im tupel

    # n Zahlen: je 4 Bytes
    zahlen_data = b''
    while len(zahlen_data) < n * 4: 
        zahlen_data += conn.recv(n * 4 - len(zahlen_data)) # übrigen Zahlen sammeln

    task_id, op, numbers = decode_request(header + zahlen_data)
    print(f"  Aufgabe {task_id}: {op}{numbers}")

    result = berechne(op, numbers)
    conn.send(encode_response(task_id, result))
    print(f"  Ergebnis: {result}")

conn.close()
serv_sock.close()
