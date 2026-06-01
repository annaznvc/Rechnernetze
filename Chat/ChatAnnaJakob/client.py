import util
import threading
import time
import socket
import struct
import queue

ip = ""
port = 0
name = ""
aktive_users = []
message_type = 0

#Connections
active_tcp_con_server =  socket.socket(socket.AF_INET, socket.SOCK_STREAM)
active_tcp_con_server.settimeout(3.0)

active_tcp_con_client = None
active_udp_con_client = None
local_tcp_listen_port = 0
tcp_listener_socket = None
client_running = True
udp_setup_response_queue = queue.Queue()
chat_receiver_thread = None


def ensure_udp_socket():
    global active_udp_con_client
    if active_udp_con_client is not None:
        return

    active_udp_con_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    active_udp_con_client.bind(('', port))
    active_udp_con_client.settimeout(1.0)


def start_udp_listener():
    listener = threading.Thread(target=udp_listener, daemon=True)
    listener.start()


def ensure_tcp_listener():
    global tcp_listener_socket
    if tcp_listener_socket is not None:
        return

    tcp_listener_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_listener_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_listener_socket.bind(('', local_tcp_listen_port))
    tcp_listener_socket.listen(5)
    tcp_listener_socket.settimeout(1.0)

    listener = threading.Thread(target=tcp_listener, daemon=True)
    listener.start()


def tcp_listener():
    global active_tcp_con_client

    while client_running:
        if tcp_listener_socket is None:
            time.sleep(0.1)
            continue

        try:
            conn, addr = tcp_listener_socket.accept()
        except socket.timeout:
            continue
        except OSError:
            break

        active_tcp_con_client = conn
        print(f"Eingehende TCP-Chatverbindung von {addr[0]}:{addr[1]}")
        start_chat_receiver()


def udp_listener():
    global active_tcp_con_client

    while client_running:
        if active_udp_con_client is None:
            time.sleep(0.1)
            continue

        try:
            data, addr = active_udp_con_client.recvfrom(1024)
        except socket.timeout:
            continue
        except OSError:
            break

        if not data:
            continue

        msg_type = util.decode_message_type(data)
        if msg_type != 4:
            continue

        # Typ 4 wird fuer Request (35 Byte) und Response (4 Byte) verwendet.
        # Response-Pakete muessen an tcp() weitergereicht werden.
        if len(data) == 4:
            udp_setup_response_queue.put((data, addr))
            continue

        if len(data) != 35:
            print(f"Ignoriere ungueltiges TCP-Setup Paket mit Laenge {len(data)} von {addr[0]}:{addr[1]}")
            continue

        _, sender_name, sender_tcp_port = util.decode_tcp(data)
        print(f"TCP-Setup von {sender_name} ({addr[0]}:{addr[1]}), Ziel-TCP-Port {sender_tcp_port}")

        # Antworte auf den UDP-Request mit dem eigenen offenen TCP-Port.
        response = util.encode_tcp_rsponse(local_tcp_listen_port)
        active_udp_con_client.sendto(response, addr)

        # Zielnutzer baut TCP-Verbindung zum Initiator auf.
        try:
            active_tcp_con_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            active_tcp_con_client.connect((addr[0], sender_tcp_port))
            print(f"TCP-Verbindung zu Initiator aufgebaut: {addr[0]}:{sender_tcp_port}")
            start_chat_receiver()
        except OSError as e:
            print("TCP-Verbindungsaufbau zum Initiator fehlgeschlagen:", e)


def start_chat_receiver():
    global chat_receiver_thread
    if active_tcp_con_client is None:
        return
    if chat_receiver_thread is not None and chat_receiver_thread.is_alive():
        return

    chat_receiver_thread = threading.Thread(target=chat_receiver, daemon=True)
    chat_receiver_thread.start()


def chat_receiver():
    while client_running and active_tcp_con_client is not None:
        try:
            packet = recv_exact(active_tcp_con_client, 257)
        except OSError:
            break

        if packet is None:
            break

        msg_type, text = util.decode_message(packet)
        if msg_type == 5:
            print(f"\n[Peer] {text}")


def recv_exact(conn, size):
    data = b''
    while len(data) < size:
        chunk = conn.recv(size - len(data))
        if not chunk:
            return None
        data += chunk
    return data

def connect_to_server(server_ip, server_port):
    try:
        active_tcp_con_server.connect((server_ip, server_port))
        print("Connected to server at " + server_ip + ":" + str(server_port))
    except Exception as e:
        print("Failed to connect to server: " + str(e))

def show_usrs():
    print(" aktive users:")
    for usr in aktive_users:
        ip_u, port_u, name_u = usr
        print("    " + name_u)
        print("    IP: " + ip_u)
        print("    Port: " + str(port_u))
        print("-----------------------------------------------")

def update_usrlist(login_usrs, logout_usrs):
    global aktive_users
    for usr in logout_usrs:
        if usr in aktive_users:
            aktive_users.remove(usr)
    for usr in login_usrs:
        if usr not in aktive_users:
            aktive_users.append(usr)

def finde_usr_by_name(name):
    for usr in aktive_users:
        if usr[2] == name:
            return usr
    return None


def recv_update_response(conn):
    header = recv_exact(conn, 6)
    if header is None:
        return None

    message_type, errcode, login_count = struct.unpack('!BBI', header)
    if message_type != 2:
        return header

    login_bytes = recv_exact(conn, login_count * 38)
    if login_bytes is None:
        return None

    logout_count_raw = recv_exact(conn, 4)
    if logout_count_raw is None:
        return None
    logout_count = struct.unpack('!I', logout_count_raw)[0]

    logout_bytes = recv_exact(conn, logout_count * 38)
    if logout_bytes is None:
        return None

    return header + login_bytes + logout_count_raw + logout_bytes

def register():
    global ip, port, name, local_tcp_listen_port
    server_ip = input("Server IP z.B. 127.0.0.1: ")
    server_port = int(input("Server Port z.B. 9001: "))
    ip = input("Eigene IP z.B. 192.168.1.50: ")
    port = int(input("Eigener UDP-Port: "))
    local_tcp_listen_port = int(input("Eigener offener TCP-Port fuer Chats: "))
    name = input("Name: ")

    message = util.encode_register(ip, port, name)
    connect_to_server(server_ip, server_port)
    active_tcp_con_server.sendall(message)

    header = recv_exact(active_tcp_con_server, 6)
    if header is None:
        print("Keine Register-Antwort vom Server erhalten")
        return None

    message_type, errcode, user_count = struct.unpack('!BBI', header)
    user_bytes = recv_exact(active_tcp_con_server, user_count * 38)
    if user_bytes is None:
        print("Unvollstaendige Register-Antwort vom Server")
        return None

    full_response = header + user_bytes
    decoded = util.decode_register_response(full_response)
    print("Register-Antwort:", decoded)

    ensure_udp_socket()
    start_udp_listener()
    ensure_tcp_listener()

    return decoded

def logout():
    global client_running
    client_running = False

    try:
        if name:
            active_tcp_con_server.sendall(util.encode_logout(name))
            _ = recv_exact(active_tcp_con_server, 2)
    except OSError:
        pass

    for sock in [active_tcp_con_client, active_udp_con_client, tcp_listener_socket, active_tcp_con_server]:
        if sock is None:
            continue
        try:
            sock.close()
        except OSError:
            pass

    print("Logout abgeschlossen.")

def tcp():
    global name, port

    nickname_chatpartner = input("enter the nickname of the chatpartner: ")
    usr_chatpartner = finde_usr_by_name(nickname_chatpartner)
    if usr_chatpartner == None:
        return print("User not found")

    partner_ip, partner_udp_port, _ = usr_chatpartner

    ensure_udp_socket()

    # Sende TCP-Setup Anfrage via UDP an den richtigen UDP-Port des Partners.
    request = util.encode_tcp(name, local_tcp_listen_port)
    try:
        # Alte Responses verwerfen, damit kein veraltetes Paket verarbeitet wird.
        while True:
            udp_setup_response_queue.get_nowait()
    except queue.Empty:
        pass

    try:
        active_udp_con_client.sendto(request, (partner_ip, partner_udp_port))
        response, response_addr = udp_setup_response_queue.get(timeout=2.5)
        if response_addr[0] != partner_ip:
            print(f"Warnung: TCP-Setup Antwort kam von {response_addr[0]} statt {partner_ip}")
    except socket.timeout:
        print("Keine TCP-Setup Antwort vom Partner erhalten (UDP Timeout)")
        return
    except queue.Empty:
        print("Keine TCP-Setup Antwort vom Partner erhalten (UDP Timeout)")
        return
    except OSError as e:
        print("UDP Fehler bei TCP-Setup:", e)
        return

    message_type, err_code, open_tcp_port = util.decode_tcp_response(response)
    if message_type != 4:
        print("Unerwarteter Nachrichtentyp bei TCP-Setup Antwort:", message_type)
        return

    if err_code not in [0, 1]:
        print("Fehler bei TCP Anfrage")
    elif err_code == 0:
        print("TCP Anfrage erfolgreich, Partner-TCP-Port: " + str(open_tcp_port))
        print("Warte auf eingehende TCP-Verbindung vom Partner...")
    elif err_code == 1:
        print("Fehler bei TCP Anfrage, Port nicht offen")

def send_message():
    if active_tcp_con_client is None:
        print("Keine aktive Peer-TCP-Verbindung. Erst TCP-Aufbau (2) ausfuehren.")
        return

    text = input("Nachricht an Peer (max 256): ")
    packet = util.encode_message(text)
    try:
        active_tcp_con_client.sendall(packet)
    except OSError as e:
        print("Senden an Peer fehlgeschlagen:", e)

def update(delay):
    global ip, port
    while client_running:
        if not ip:
            time.sleep(delay)
            continue

        try:
            message = util.encode_update(ip, port)
            active_tcp_con_server.sendall(message)
            response = recv_update_response(active_tcp_con_server)
            if response is None:
                print("Keine/Unvollstaendige Update-Antwort vom Server")
                time.sleep(delay)
                continue

            decoded = util.decode_package_server_resonse(response)
            if decoded is None:
                print("Update-Antwort konnte nicht geparst werden")
                time.sleep(delay)
                continue

            message_type, err_code, login_usrs, logout_usrs = decoded
            if err_code == 0:
                update_usrlist(login_usrs, logout_usrs)
        except (socket.timeout, OSError) as e:
            if client_running:
                print("Update fehlgeschlagen:", e)
            break

        time.sleep(delay)

def read_input():
    while client_running:
        action_type = int(input("Trigger action (0: register, 1: logout, 2:Aufbau TCP, 3:send Message, 4:show aktive users): "))
        match action_type:
            case 0:
                register()
            case 1:
                logout()
                break
            case 2:
                tcp()
            case 3:
                send_message()
            case 4:
                show_usrs()
            case 99:
                print("update")
                update(10)
            case _:                        # Der Unterstrich '_' ist der Wildcard/Default-Case (wie 'else')
                print("Unbekannter Befehl!")

def start_register():
    print("please register for use")
    register()

start_register()

# 1. Create threads
thread1 = threading.Thread(target=read_input)
thread2 = threading.Thread(target=update, args=(10,))


# 2. Start threads (they run concurrently)
thread1.start()
thread2.start()

