import socket
import threading
import struct
from protocol_helpers import pad_string, unpad_string

# Der Server läuft dauerhaft über TCP. 
# Er wartet auf Verbindungen, verarbeitet die Registrierungen (Type 0), 
# speichert die aktiven Clients in einer Liste und leitet Broadcasts weiter (Type 3).

# Konfiguration
SERVER_IP = "0.0.0.0"  # Hört auf allen Schnittstellen (lokal & MeshNet) (Any Address)
SERVER_PORT = 50000

# Speichert aktive Clients: { client_socket: {"nickname": str, "ip": str, "udp_port": int} }
active_clients = {}
clients_lock = threading.Lock() # mutex, da viele Client-Threads gleichzeitig auf active_clients zugreifen, verhindert Lock Race Condition

def recv_exact(sock, size):
    """Liest exakt size Bytes vom Socket."""
    data = b''
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            return None
        data += chunk
    return data

def broadcast_message(sender_socket, sender_nickname, message_bytes):
    with clients_lock:
        fmt = "!BB32s256s"
        packed_msg = struct.pack(fmt, 3, 0, pad_string(sender_nickname, 32), message_bytes)
        
        for c_socket in list(active_clients.keys()):
            if c_socket is sender_socket:
                continue  # Nicht an Sender selbst
            try:
                c_socket.sendall(packed_msg)
            except Exception:
                remove_client(c_socket)

def remove_client(client_socket): #Entfernt einen Client aus der Liste
    with clients_lock:
        if client_socket in active_clients:
            print(f"Client {active_clients[client_socket]['nickname']} getrennt.")
            del active_clients[client_socket]
    client_socket.close()

def handle_client(client_socket, client_address): # Verarbeitet die eingehenden TCP-Nachrichten eines Clients
    print(f"Neue TCP-Verbindung von {client_address}")
    
    try:
        while True:
            type_byte = recv_exact(client_socket, 1)
            if not type_byte:
                break
            
            msg_type = type_byte[0]
            
            # Registrierung (Type 0)
            if msg_type == 0:
                data = recv_exact(client_socket, 38)
                if not data:
                    break
                fmt = "!4sH32s"
                raw_ip, udp_port, raw_name = struct.unpack(fmt, data)
                
                nickname = unpad_string(raw_name)
                ip_str = socket.inet_ntoa(raw_ip) # Bytes in IP-String (zB "127.0.0.1") umwandeln
                
                print(f"Registrierung: {nickname} (UDP: {udp_port})")
                
                with clients_lock:
                    # Client in der Liste speichern
                    active_clients[client_socket] = {
                        "nickname": nickname,
                        "ip": ip_str,
                        "udp_port": udp_port
                    }
                    
                    # Antwort vorbereiten: Type 0, Error 0, N (Anzahl Nutzer)
                    n_users = len(active_clients)
                    response_header = struct.pack("!BBI", 0, 0, n_users) #Message Type 0, Errorcode 0
                    client_socket.sendall(response_header)
                    
                    # Die User-Liste senden (Je Eintrag 38 Bytes)
                    for c_sock, info in active_clients.items():
                        packed_entry = struct.pack("!4sH32s", 
                                                   socket.inet_aton(info["ip"]), 
                                                   info["udp_port"], 
                                                   pad_string(info["nickname"], 32))
                        client_socket.sendall(packed_entry)
            
            # Logout (Type 1) - 32B Nickname
            elif msg_type == 1:
                data = recv_exact(client_socket, 32)
                if not data:
                    break
                raw_name = struct.unpack("!32s", data)[0]
                nickname = unpad_string(raw_name)
                print(f"Logout: {nickname}")

                with clients_lock:
                    if client_socket in active_clients:
                        del active_clients[client_socket]

                # Logout-Response: Type 1, Error 0
                client_socket.sendall(struct.pack("!BB", 1, 0))

            # Update (Type 2) - 4B IP + 2B Port = 6 Bytes
            elif msg_type == 2:
                data = recv_exact(client_socket, 6)
                if not data:
                    break
                
                print(f"Update-Anfrage erhalten von {client_address}")
                
                # Antwort: aktuelle Userliste als Update-Response
                # Format: Type 2, Error 0, N_login (4B), N*38B login-entries, N_logout (4B), 0 logout-entries
                with clients_lock:
                    entries = []
                    for info in active_clients.values():
                        entries.append(struct.pack("!4sH32s",
                                                   socket.inet_aton(info["ip"]),
                                                   info["udp_port"],
                                                   pad_string(info["nickname"], 32)))
                    n_login = len(entries)

                response = struct.pack("!BBI", 2, 0, n_login)
                response += b''.join(entries)
                response += struct.pack("!I", 0)  # 0 logouts
                client_socket.sendall(response)

            # Broadcast (Type 3) - 32B Name + 256B Nachricht = 288 Bytes
            elif msg_type == 3:
                data = recv_exact(client_socket, 288)
                if not data:
                    break
                raw_name, raw_msg = struct.unpack("!32s256s", data)
                
                nickname = unpad_string(raw_name)
                print(f"Broadcast von {nickname}")
                
                broadcast_message(client_socket, nickname, raw_msg)
                
                # Error-Ack an Sender 
                client_socket.sendall(struct.pack("!BB", 255, 0))

            else:
                print(f"Unbekannter Message-Type {msg_type} von {client_address}")
                break

    except Exception as e:
        print(f"[Error] Fehler beim Verarbeiten von {client_address}: {e}")
    finally:
        remove_client(client_socket)

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM) #Haupt-Socket des Servers: AF_INET für IPv4 und SOCK_STREAM für TCP.
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) #Aktiviert, dass der Port 50000 beim Server-Neustart wiederverwendet werden darf, ohne dass das BS ihn blockiert.
    server.bind((SERVER_IP, SERVER_PORT)) #socket wird an IP 0.0.0.0 und Port 50000 gekettet
    server.listen()
    print(f"Server läuft auf Port {SERVER_PORT}...")
    
    while True:
        client_socket, client_address = server.accept()
        # Jeder Client bekommt einen eigenen Thread
        t = threading.Thread(target=handle_client, args=(client_socket, client_address))
        t.daemon = True
        t.start()

if __name__ == "__main__":
    start_server()