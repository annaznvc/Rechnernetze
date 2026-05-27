import util
import socket
import struct
import threading

# (ip, udp_port, nickname, tcp_conn)
login_usr = []
logout_usr = []
state_lock = threading.Lock()


def recv_exact(conn, size):
    data = b''
    while len(data) < size:
        chunk = conn.recv(size - len(data))
        if not chunk:
            return None
        data += chunk
    return data


def read_framed_message(conn):
    # Erst message_type lesen, dann den Rest je Typ nachladen.
    first = recv_exact(conn, 1)
    if first is None:
        return None

    message_type = struct.unpack('!B', first)[0]
    remaining_by_type = {
        0: 38,   # register: 1 + 4 + 2 + 32
        1: 32,   # logout:   1 + 32
        2: 6,    # update:   1 + 4 + 2
        3: 288,  # broadcast 1 + 32 + 256
    }

    remaining = remaining_by_type.get(message_type)
    if remaining is None:
        return None

    rest = recv_exact(conn, remaining)
    if rest is None:
        return None

    return first + rest


def handle_client(conn, addr):
    print(f"Verbindung von {addr}")
    try:
        while True:
            message = read_framed_message(conn)
            if message is None:
                break

            response = handle_package(message, conn)
            if response is not None:
                conn.sendall(response)
    finally:
        with state_lock:
            global login_usr
            login_usr = [u for u in login_usr if u[3] is not conn]
        conn.close()
        print(f"Verbindung geschlossen: {addr}")


def listen_to_client(open_port):
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(('', open_port))
    server_sock.listen(20)
    print("TCP-Server wartet auf Port " + str(open_port) + " und IP " + str(socket.gethostbyname_ex(socket.gethostname())[-1][0]))

    while True:
        conn, addr = server_sock.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        thread.start()


def handle_package(message, conn):
    message_type = util.decode_message_type(message)
    if message_type == 0:
        return handle_register(message, conn)
    elif message_type == 1:
        return handle_logout(message, conn)
    elif message_type == 2:
        return handle_update(message)
    elif message_type == 3:
        return handle_broadcast(message, conn)
    else:
        return util.encode_error_response(1)


def handle_register(message, conn):
    message_type, ip, port, name = util.decode_register(message)
    with state_lock:
        global login_usr
        login_usr = [u for u in login_usr if u[2] != name]
        login_usr.append((ip, port, name, conn))
        response_message = util.encode_register_response(0, [(u[0], u[1], u[2]) for u in login_usr])
    return response_message


def handle_logout(message, conn):
    _, name = util.decode_logout(message)
    with state_lock:
        global login_usr
        login_usr = [u for u in login_usr if not (u[2] == name and u[3] is conn)]
        logout_usr.append(name)
    return util.encode_logout_response(0)


def handle_update(message):
    _, _, _ = util.decode_update(message)
    with state_lock:
        response_message = util.encode_update_response(0, [(u[0], u[1], u[2]) for u in login_usr], [])
    return response_message


def handle_broadcast(message, conn):
    _, sender_name, sender_msg = util.decode_broadcast_request(message)
    broadcast_msg = util.encode_broadcast_response(0, sender_name, sender_msg)

    with state_lock:
        receivers = [u[3] for u in login_usr if u[3] is not conn]

    for receiver_conn in receivers:
        try:
            receiver_conn.sendall(broadcast_msg)
        except OSError:
            pass

    return util.encode_error_response(0)

listen_to_client(9001)
