import socket
import threading

# --- Ziel-Server ---
TCP_TARGET = '141.37.122.107'
UDP_TARGET = '141.37.168.26'

PORTS = range(1, 51)
TIMEOUT = 1.0
Continue = True

# Ergebnislisten
open_tcp_ports = []
open_udp_ports = []
udp_no_response = []
udp_closed = []

# Lock verhindert dass zwei Threads gleichzeitig in eine Liste schreiben
lock = threading.Lock()


def scan_tcp(port):
    """Scannt einen einzelnen TCP-Port und fuehrt bei Erfolg einen Echo-Test durch."""
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

    sock.close()


def scan_udp(port):
    """
    Scannt einen einzelnen UDP-Port.
    Unterscheidet drei Faelle:
      - Antwort erhalten       -> Port offen
      - Timeout                -> keine Antwort, unklar ob offen oder gefiltert
      - OSError 10054 (ICMP)   -> Port definitiv geschlossen
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
        # Keine Antwort -> koennte offen oder gefiltert sein
        with lock:
            udp_no_response.append(port)

    except OSError as e:
        if e.winerror == 10054:
            # ICMP Port Unreachable -> Port ist definitiv geschlossen
            with lock:
                udp_closed.append(port)
        else:
            print(f"  [UDP] Port {port}: Fehler {e}")

    finally:
        sock.close()


# --- TCP-Scan ---
print(f"Starte TCP-Scan auf {TCP_TARGET}, Ports 1-50 ...")
tcp_threads = [threading.Thread(target=scan_tcp, args=(p,)) for p in PORTS]
for t in tcp_threads:
    t.start()
for t in tcp_threads:
    t.join()

# --- UDP-Scan ---
print(f"\nStarte UDP-Scan auf {UDP_TARGET}, Ports 1-50 ...")
udp_threads = [threading.Thread(target=scan_udp, args=(p,)) for p in PORTS]
for t in udp_threads:
    t.start()
for t in udp_threads:
    t.join()

# --- Ergebnis ---
print(f"\n{'='*50}")
print(f"Offene TCP-Ports auf {TCP_TARGET}: {sorted(open_tcp_ports)}")
print(f"Offene UDP-Ports auf {UDP_TARGET}: {sorted(open_udp_ports)}")
print(f"UDP keine Antwort (offen/gefiltert): {len(udp_no_response)} Ports")
print(f"UDP geschlossen (ICMP 10054): {sorted(udp_closed)}")
