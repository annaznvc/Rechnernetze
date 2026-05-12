import socket
import threading

TCP_TARGET = '141.37.122.107'
UDP_TARGET = '141.37.168.26'

PORTS = range(1, 51)
TIMEOUT = 1.0
Continue = True


open_tcp_ports = []
open_udp_ports = []
udp_no_response = []
udp_closed = []

# Lock verhindert dass zwei Threads gleichzeitig in eine Liste schreiben
lock = threading.Lock()


# 4.3 Frage 1 & 2: TCP Port Scanner mit Paketsequenz-Infos


def scan_tcp(port):
    """
    Scannt einen einzelnen TCP-Port.
    Offener Port      -> SYN, SYN-ACK, ACK (3-Wege-Handshake), dann Daten
    Geschlossener Port -> SYN, RST+ACK (Fehlercode 10061)
    Gefilterter Port   -> SYN, keine Antwort -> Timeout (Fehlercode 10060)
    """
    if not Continue:
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(TIMEOUT)

    result = sock.connect_ex((TCP_TARGET, port))  # 0 = offen, sonst Fehlercode

    if result == 0:
        with lock:
            open_tcp_ports.append(port)
        print(f"  [TCP] Port {port}: OFFEN")

        # Echo-Test: Nachricht schicken und schauen ob sie zurueckkommt
        try:
            sock.send(b'Hallo Echo!')
            antwort = sock.recv(1024)
            print(f"    Echo-Antwort auf Port {port}: {antwort}")
        except:
            pass

    elif result == 10061:
        # Server hat aktiv mit RST+ACK abgelehnt -> Port ist geschlossen
        pass  # Zeile unten auskommentieren um alle geschlossenen Ports zu sehen:
        # print(f"  [TCP] Port {port}: geschlossen (RST+ACK, Code 10061)")

    else:
        # Timeout oder anderer Fehler -> Port gefiltert oder kein Server
        pass  
        # print(f"  [TCP] Port {port}: Timeout/gefiltert (Code {result})")

    sock.close()


# 4.3 Frage 1 & 2: UDP Port Scanner mit Unterscheidung der drei Faelle

def scan_udp(port):
    """
    Scannt einen einzelnen UDP-Port.
    Drei moegliche Faelle (Frage 2):
      1. Antwort erhalten       -> Port offen (z.B. Port 7 Echo)
      2. Timeout                -> keine Antwort, unklar ob offen oder gefiltert
      3. OSError 10054 (ICMP)   -> ICMP Port Unreachable -> Port definitiv geschlossen
    """
    if not Continue:
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(TIMEOUT)

    try:
        sock.sendto(b'Hallo Echo!', (UDP_TARGET, port))
        antwort, _ = sock.recvfrom(1024)
        # Antwort bekommen -> Port ist offen
        with lock:
            open_udp_ports.append(port)
        print(f"  [UDP] Port {port}: OFFEN – Antwort: {antwort}")

    except socket.timeout:
        # Keine Antwort -> Firewall verwirft das Paket stillschweigend
        with lock:
            udp_no_response.append(port)

    except OSError as e:
        if e.winerror == 10054:
            # ICMP Port Unreachable -> Port ist definitiv geschlossen
            with lock:
                udp_closed.append(port)
            print(f"  [UDP] Port {port}: geschlossen (ICMP Port Unreachable, Code 10054)")
        else:
            print(f"  [UDP] Port {port}: Fehler {e}")

    finally:
        sock.close()


# 4.3 Frage 3: Echo-Test auf Port 7 fuer TCP und UDP

def echo_test():
    """
    Testet den RFC-862-konformen Echo-Dienst auf Port 7.
    Ein echter Echo-Dienst schickt jedes empfangene Byte unveraendert zurueck.
    """
    NACHRICHT = b'Hallo Echo!'
    print(f"\n{'='*50}")
    print("4.3 Frage 3: Echo-Test auf Port 7")
    print(f"{'='*50}")

    # TCP Echo Test
    print("\n[TCP Echo Test]")
    try:
        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp.settimeout(3.0)
        tcp.connect((TCP_TARGET, 7))
        tcp.send(NACHRICHT)
        antwort = tcp.recv(1024)
        print(f"  Gesendet : {NACHRICHT}")
        print(f"  Empfangen: {antwort}")
        print(f"  Identisch: {NACHRICHT == antwort}")
        tcp.close()
    except Exception as e:
        print(f"  TCP Echo fehlgeschlagen: {e}")

    # UDP Echo Test auf demselben Server (TCP_TARGET hat Port 7 offen)
    print("\n[UDP Echo Test]")
    try:
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp.settimeout(3.0)
        udp.sendto(NACHRICHT, (TCP_TARGET, 7))  # gleicher Server, Port 7
        antwort, addr = udp.recvfrom(1024)
        print(f"  Gesendet : {NACHRICHT}")
        print(f"  Empfangen: {antwort} von {addr}")
        print(f"  Identisch: {NACHRICHT == antwort}")
        udp.close()
    except socket.timeout:
        print("  UDP Echo: Timeout – Port 7 UDP scheint gefiltert zu sein")
    except Exception as e:
        print(f"  UDP Echo fehlgeschlagen: {e}")


# Hauptprogramm

# --- TCP-Scan (Frage 1 & 2) ---
print(f"Starte TCP-Scan auf {TCP_TARGET}, Ports 1-50 ...")
tcp_threads = [threading.Thread(target=scan_tcp, args=(p,)) for p in PORTS]
for t in tcp_threads:
    t.start()
for t in tcp_threads:
    t.join()

# --- UDP-Scan (Frage 1 & 2) ---
print(f"\nStarte UDP-Scan auf {UDP_TARGET}, Ports 1-50 ...")
udp_threads = [threading.Thread(target=scan_udp, args=(p,)) for p in PORTS]
for t in udp_threads:
    t.start()
for t in udp_threads:
    t.join()

# --- Ergebnis Frage 1 ---
print(f"\n{'='*50}")
print("4.3 Frage 1: Ergebnisse")
print(f"{'='*50}")
print(f"Offene TCP-Ports auf {TCP_TARGET}: {sorted(open_tcp_ports)}")
print(f"Offene UDP-Ports auf {UDP_TARGET}: {sorted(open_udp_ports)}")
print(f"UDP keine Antwort (offen/gefiltert): {len(udp_no_response)} Ports")
print(f"UDP geschlossen (ICMP 10054)       : {sorted(udp_closed)}")

# --- Echo-Test Frage 3 ---
echo_test()
