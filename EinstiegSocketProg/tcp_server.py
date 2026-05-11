import socket
import struct
import threading
from protokoll import decode_request, encode_response, berechne

# Globales Flag – wenn False, beenden sich alle Threads sauber
Continue = True

def receive(conn, addr):
    """Läuft in einem eigenen Thread für jeden verbundenen Client."""
    print(f"[Thread] Verbindung von {addr} wird bearbeitet")
    conn.settimeout(2.0)  # damit recv() nicht ewig blockiert und das StopFlag geprüft werden kann
    
    while Continue:
        try:
            # Header lesen: ID(4) + OP(3) + N(1) = 8 Bytes
            header = b''
            while len(header) < 8:
                chunk = conn.recv(8 - len(header))
                if not chunk: # leerer chunk = client weg
                    print(f"[Thread] Client {addr} hat getrennt")
                    conn.close()
                    return
                header += chunk #anhängen

            n = struct.unpack_from('!B', header, 7)[0]

            # Zahlendaten lesen
            zahlen_data = b''
            while len(zahlen_data) < n * 4:
                zahlen_data += conn.recv(n * 4 - len(zahlen_data))

            task_id, op, numbers = decode_request(header + zahlen_data)
            print(f"[Thread {addr}] Aufgabe {task_id}: {op}{numbers}")
            result = berechne(op, numbers)
            conn.send(encode_response(task_id, result))
            print(f"[Thread {addr}] Ergebnis: {result}")

        except socket.timeout:
            # Kein Fehler – einfach prüfen ob wir aufhören sollen
            continue
        except OSError:
            break

    conn.close()
    print(f"[Thread] Thread für {addr} beendet")


def listen(sock):
    """Hauptschleife – nimmt neue Verbindungen entgegen und startet je einen Thread."""
    sock.settimeout(2.0)  # damit accept() nicht ewig blockiert
    
    while Continue:
        try:
            conn, addr = sock.accept() # neuees socket objekt mit adr + port
            print(f"[Server] Neue Verbindung von {addr} – starte Thread")
            # Für jeden Client einen eigenen Thread starten
            threading.Thread(target=receive, args=(conn, addr), daemon=True).start() # welche fkt soll thread ausführen, mit welchen argumenten, stirbt thread automatisch wenn hauptprogramm endet?
        except socket.timeout:
            continue  # kein neuer Client, einfach weiter warten
        except OSError:
            break


# Hauptprogramm
serv_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serv_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # Port sofort wiederverwendbar nach Neustart
serv_sock.bind(('', 9000))
serv_sock.listen(5)  # bis zu 5 Verbindungen in der Warteschlange
print("Threaded TCP-Server wartet auf Port 9000 ...")
print("Strg+C zum Beenden")

try:
    listen(serv_sock)
except KeyboardInterrupt:
    print("\n[Server] Wird beendet ...")
    Continue = False  # alle Threads bekommen das Signal zum Aufhören

serv_sock.close()
print("[Server] Fertig.")
