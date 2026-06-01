import socket
import threading
import struct
import sys
import time
from protocol_helpers import pad_string, unpad_string

#Der Client muss drei Dinge gleichzeitig tun -> Threads nutzen:
# Vom Server (TCP) Nachrichten empfangen (Broadcasts).  
# Auf dem UDP-Port lauschen, falls ein anderer Client eine P2P-Session aufbauen will (Type 4).  
# Benutzereingaben über die Konsole entgegennehmen.

# Globale Variablen für den eigenen Zustand
MY_NICKNAME = ""
MY_UDP_PORT = 0
MY_IP = "127.0.0.1"
SERVER_IP = "127.0.0.1"
SERVER_PORT = 50000

# Speichert offene P2P-TCP-Verbindungen zu anderen Clients: { nickname: socket } ("Telefonbuch")
p2p_sessions = {}

# Thread1: Empfang vom Server (TCP)
def receive_from_server(tcp_socket):
    try:
        while True:
            type_byte = tcp_socket.recv(1)
            if not type_byte:
                break
            msg_type = type_byte[0]

            # Broadcast erhalten wenn type 3
            if msg_type == 3:
                # 1B Error, 32B Sender, 256B Nachricht = 289 Bytes
                data = recv_exact_raw(tcp_socket, 289)
                if not data:
                    break
                error, raw_sender, raw_msg = struct.unpack("!B32s256s", data)
                
                sender = unpad_string(raw_sender)
                msg = unpad_string(raw_msg)
                print(f"\n[BROADCAST] {sender}: {msg}\n> ", end="")

            # Error-Ack vom Server (z.B. nach eigenem Broadcast) - 1 Byte Errorcode konsumieren
            elif msg_type == 255 or msg_type == 0:
                # Typ 255: Error-Response (1B errcode)
                # Typ 0: Register-Response (1B errcode + 4B N + N*38B) - ignorieren
                if msg_type == 255:
                    tcp_socket.recv(1)  # errcode konsumieren
                else:
                    # Falls unerwartet eine Register-Response kommt, Header lesen und verwerfen
                    rest = recv_exact_raw(tcp_socket, 5)  # 1B err + 4B count
                    if rest:
                        _, count = struct.unpack("!BI", rest)
                        recv_exact_raw(tcp_socket, count * 38)

            elif msg_type == 2:
                # Update-Response: 1B err + 4B login_count + login_count*38 + 4B logout_count + logout_count*38
                rest = recv_exact_raw(tcp_socket, 5)
                if rest:
                    _, login_count = struct.unpack("!BI", rest)
                    recv_exact_raw(tcp_socket, login_count * 38)
                    lc_raw = recv_exact_raw(tcp_socket, 4)
                    if lc_raw:
                        logout_count = struct.unpack("!I", lc_raw)[0]
                        recv_exact_raw(tcp_socket, logout_count * 38)

            elif msg_type == 1:
                # Logout-Response: 1B errcode
                tcp_socket.recv(1)

            else:
                # Unbekannter Typ - 1 Byte konsumieren um nicht zu desyncen
                pass

    except Exception as e:
        print(f"\n Verbindung zum Server verloren: {e}")
    finally:
        tcp_socket.close()


def recv_exact_raw(sock, size):
    """Liest exakt size Bytes vom Socket."""
    data = b''
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            return None
        data += chunk
    return data


# Thread2: Empfang von P2P-Nachrichten (TCP)
def receive_p2p_messages(peer_socket, peer_name):
    try:
        while True:
            type_byte = peer_socket.recv(1)
            if not type_byte:
                break
            msg_type = type_byte[0]
            
            if msg_type == 5:  # Chat Message wenn type 5
                raw_msg = peer_socket.recv(256)
                msg = unpad_string(raw_msg)
                print(f"\n[P2P] {peer_name}: {msg}\n> ", end="")
    except Exception:
        pass
    finally:
        print(f"\nP2P-Session mit {peer_name} beendet.")
        if peer_name in p2p_sessions:
            del p2p_sessions[peer_name]
        peer_socket.close()

# Thread3: Auf eingehende P2P-Anfragen warten (UDP & TCP-Accept)
def listen_for_p2p_udp(udp_port):
    udp_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #neuen Socket für den Verbindungsaufbau
    udp_server.bind(("0.0.0.0", udp_port)) #bindet den UDP-Socket an die IP 0.0.0.0
    
    # erstellen direkt einen TCP-Socket, um Verbindungen anzunehmen, falls Peer Partner
    tcp_p2p_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_p2p_server.bind(("0.0.0.0", 0)) # 0: Beliebigen freien TCP-Port wählen
    tcp_p2p_server.listen(5) #maximal 5 Verbindungsanfragen gleichzeitig
    assigned_tcp_port = tcp_p2p_server.getsockname()[1]

    print(f"Lausche auf UDP-Port {udp_port} für P2P-Anfragen...")
    
    def accept_tcp_connections():
        while True:
            try:
                peer_sock, addr = tcp_p2p_server.accept()
                # Sobald die Verbindung steht, herausfinden, wer es ist.
                t = threading.Thread(target=receive_p2p_messages, args=(peer_sock, f"Peer@{addr[0]}"))
                t.daemon = True
                t.start()
            except Exception:
                break

    threading.Thread(target=accept_tcp_connections, daemon=True).start()

    while True:
        try:
            # Auf UDP-Paket warten (Type 4)
            data, addr = udp_server.recvfrom(35) # 1B Type, 32B Name, 2B Port
            if len(data) < 35: continue #fehlerhaft oder unvollständig? wird paket übersprungen
            
            msg_type = data[0]
            if msg_type == 4: #type 4 Aufbau einer TCP-Verbindung
                raw_name, peer_tcp_port = struct.unpack("!32sH", data[1:])
                peer_name = unpad_string(raw_name) #Nullbytes entfernt und in string umwandeln
                
                print(f"\n[UDP] Verbindungsanfrage von {peer_name}. Baue TCP auf zu Port {peer_tcp_port}...")
                
                # Anvisierte(Zielperson) baut die TCP-Verbindung zum Initiator(Anrufer) auf
                try:
                    p2p_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #IPv4 Adressen
                    p2p_sock.connect((addr[0], peer_tcp_port))
                    
                    p2p_sessions[peer_name] = p2p_sock
                    
                    # Thread zum Empfangen der Chat-Nachrichten starten
                    t = threading.Thread(target=receive_p2p_messages, args=(p2p_sock, peer_name))
                    t.daemon = True
                    t.start()
                    
                    # UDP-Antwort zurücksenden (Success)
                    reply = struct.pack("!BBH", 4, 0, assigned_tcp_port) #Message Type 4, Errorcode 0 (Erfolg)
                    udp_server.sendto(reply, addr)
                except Exception as e:
                    print(f"TCP-Verbindungsaufbau fehlgeschlagen: {e}")
                    reply = struct.pack("!BBH", 4, 1, 0)
                    udp_server.sendto(reply, addr)
                    
        except Exception as e:
            print(f"Fehler im UDP-Listener: {e}")

# P2P Verbindung aktiv initiieren
def initiate_p2p(target_ip, target_udp_port, target_name="Peer"):
    # Erstelle einen temporären TCP-Socket
    temp_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    temp_tcp.bind(("0.0.0.0", 0))
    temp_tcp.listen(1)
    my_open_tcp_port = temp_tcp.getsockname()[1]
    
    # UDP-Anfrage senden (Type 4)
    udp_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    packet = struct.pack("!B32sH", 4, pad_string(MY_NICKNAME, 32), my_open_tcp_port)
    udp_client.sendto(packet, (target_ip, target_udp_port))
    print(f"UDP-Anfrage an {target_ip}:{target_udp_port} gesendet. Warte auf TCP-Verbindung...")
    
    # Partner sollte sich jetzt via TCP melden
    temp_tcp.settimeout(8.0)
    try:
        peer_sock, addr = temp_tcp.accept()
        print(f"P2P TCP-Verbindung erfolgreich hergestellt mit {target_name}!")

        # In Sessions speichern
        p2p_sessions[target_name] = peer_sock
        t = threading.Thread(target=receive_p2p_messages, args=(peer_sock, target_name))
        t.daemon = True
        t.start()
    except socket.timeout:
        print("Timeout: Partner hat keine TCP-Verbindung aufgebaut.")
    finally:
        temp_tcp.close()
        udp_client.close()

# Hauptprogramm
def main():
    global MY_NICKNAME, MY_UDP_PORT, MY_IP, SERVER_IP, SERVER_PORT

    MY_NICKNAME = input("Nickname eingeben: ")
    MY_UDP_PORT = int(input("Eigener UDP-Port: "))
    MY_IP = input("Eigene IP (testen 127.0.0.1): ")
    SERVER_IP = input("Server IP (testen 127.0.0.1): ")
    SERVER_PORT = int(input("Server Port (50000 oder 9001): "))

    # 1. UDP-Listener Thread starten
    udp_thread = threading.Thread(target=listen_for_p2p_udp, args=(MY_UDP_PORT,))
    udp_thread.daemon = True # Hintergrund Thread (hat kein Eigenleben, sobald Hauptprogramm schließt oder Strg + C , killt alle Daemon-Threads sofort und automatisch mit
    udp_thread.start()
    
    # 2. Verbindung zum Server (50000) aufbauen (TCP)
    server_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_tcp.connect((SERVER_IP, SERVER_PORT))
    except Exception as e:
        print(f"Konnte nicht mit Server verbinden: {e}")
        return
    
    # 3. Registrierungs Nachricht an Server senden (Type 0)
    # Format: Type(1B), IP(4B), UDP-Port(2B), Nickname(32B)
    packed_ip = socket.inet_aton(MY_IP) #Macht aus dem String "127.0.0.1" genau 4 Bytes
    reg_packet = struct.pack("!B4sH32s", 0, packed_ip, MY_UDP_PORT, pad_string(MY_NICKNAME, 32)) #!: Datenpakete auf allen BS gleich interpretiert, B einzelens Byte für Message Type, 4s string aus 4B für IP, H usigned Short 2B für Portnr, 32s string 32B für name =39B
    # 0-> Message Type (1B), packedIP -> 4B IP, M<Udpport -> port (2B), padString -> macht namen genau 32B lang s protc_helpers
    server_tcp.sendall(reg_packet)
    
    # Server-Antwort (Userliste) auswerten
    header = server_tcp.recv(6) #6B : 1B Type + 1B Error Code + 4B Integer I für die Anzahl der Nutzer N
    msg_type, error, n_users = struct.unpack("!BBI", header) #zerlegt 6B wieder in Variablen
    print(f"Am Server registriert. Anzahl anderer Nutzer: {n_users}")
    
    # Userliste einlesen
    for _ in range(n_users):
        user_data = server_tcp.recv(38) # 38B : Listeintrag (4B IP + 2B Port + 32B Name)
        raw_ip, u_port, raw_name = struct.unpack("!4sH32s", user_data)
        print(f" -> User: {unpad_string(raw_name)} | IP: {socket.inet_ntoa(raw_ip)} | UDP-Port: {u_port}") #wandelt die 4 Bytes wieder in einen Text um s protc_helpers
        
    # Thread für Server-Updates starten
    server_thread = threading.Thread(target=receive_from_server, args=(server_tcp,))
    #receive_from_server übernimmt im Hintergrund das Abhören des Server-Sockets
    server_thread.daemon = True
    server_thread.start()
    
    # 4. Benutzerschleife für Eingaben
    time.sleep(1)
    print("\nBefehle:\n/b <text>  -> Broadcast senden\n/p2p <ip> <udp_port> -> P2P Session starten\n/msg <text> -> Nachricht an P2P-Partner senden\n")
    
    while True:
        cmd = input("> ")
        if cmd.startswith("/b "):
            msg_text = cmd[3:] #cmd[3:] schneidet das /b
            # Broadcast senden (Type 3)
            packet = struct.pack("!B32s256s", 3, pad_string(MY_NICKNAME, 32), pad_string(msg_text, 256)) #baut ein Paket mit Message Type 3, Namen (32B) und Nachricht (256B)
            server_tcp.sendall(packet)
            
        elif cmd.startswith("/p2p "):
            parts = cmd.split()
            if len(parts) == 3:
                initiate_p2p(parts[1], int(parts[2]))
            elif len(parts) == 4:
                # /p2p <ip> <udp_port> <name>
                initiate_p2p(parts[1], int(parts[2]), parts[3])

        elif cmd.startswith("/msg "):
            msg_text = cmd[5:]
            if p2p_sessions:
                # An die erste (oder einzige) aktive Session senden
                target_name = list(p2p_sessions.keys())[0]
                packet = struct.pack("!B256s", 5, pad_string(msg_text, 256))
                try:
                    p2p_sessions[target_name].sendall(packet)
                except Exception as e:
                    print(f"Senden fehlgeschlagen: {e}")
                    del p2p_sessions[target_name]
            else:
                print(" Keine aktive P2P-Session vorhanden. Nutze erst /p2p")

        elif cmd.startswith("/sessions"):
            if p2p_sessions:
                print("Aktive P2P-Sessions:")
                for name in p2p_sessions:
                    print(f"  - {name}")
            else:
                print("Keine aktiven Sessions.")

if __name__ == "__main__":
    main()