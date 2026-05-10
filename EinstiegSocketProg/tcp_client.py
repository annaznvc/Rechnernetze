import socket
from protokoll import encode_request, decode_response

client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Frage 4: Timeout setzen - connect() und recv() geben nach 3 Sekunden auf
client_sock.settimeout(3.0)
# Mit socket.setdefaulttimeout(3.0) könnte man einen globalen Timeout für
# alle Sockets auf einmal setzen, ohne jeden einzeln zu konfigurieren

# Frage 3: bind() auskommentiert - wenn aktiv, wird Port 54321 erzwungen
# client_sock.bind(('0.0.0.0', 54321))

try:
    client_sock.connect(('192.168.137.1', 9000))

    # Frage 1 & 2: Nach connect() hat das OS automatisch IP und Port vergeben
    print("Nach connect():", client_sock.getsockname())

    anfragen = [
        (1, 'SUM', [1, 2, 3, 4, 5]),
        (2, 'PRO', [2, 3, 4]),
        (3, 'MIN', [-10, 0, 7, 3]),
        (4, 'MAX', [-10, 0, 7, 3]),
    ]

    for task_id, op, nums in anfragen:
        client_sock.send(encode_request(task_id, op, nums))
        data = client_sock.recv(8)  # blockiert bis Antwort ankommt - Timeout greift hier auch
        resp_id, result = decode_response(data)
        print(f"Aufgabe {resp_id}: {op}{nums} = {result}")

except socket.timeout:
    # Wird ausgelöst wenn connect() oder recv() nach 3 Sekunden keine Antwort bekommt
    print("Timeout! Server nicht erreichbar.")

except ConnectionRefusedError:
    # Wird ausgelöst wenn Server aktiv ablehnt (RST+ACK, Fehler 10061)
    print("Verbindung abgelehnt! Server läuft nicht.")

finally:
    # finally läuft immer - egal ob Fehler oder nicht
    client_sock.close()