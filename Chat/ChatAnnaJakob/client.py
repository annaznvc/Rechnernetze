import util
import mock
import threading
import time

ip = ""
port = 0
name = ""
aktive_users = []
message_type = 0

def show_usrs():
    print(" aktive users:")
    for usr in aktive_users:
        print("    " + usr.name)
        print("    IP: " + usr.ip)
        print("    Port: " + usr.port)
        print("-----------------------------------------------")

def update_usrlist(login_usrs, logout_usrs):
    global aktive_users
    for usr in logout_usrs:
        if aktive_users.contains(usr):
            aktive_users.remove(usr)
    for usr in login_usrs:
        if not aktive_users.contains(usr):
            aktive_users.append(usr)

def register():
    global ip, port, name
    ip = input("IP z.B. 192.168.1.50: ")
    port = int(input("Port: "))
    name = input("Name: ")
    message = util.encode_register(ip, port, name)
    print(message)
    print(util.decode_register(message))
    response = mock.mock_register_response()
    return response

def logout():
    #TODO
    print("Loggout not implemented yet.")
    pass

def tcp():
    global name, port
    #TODO anfrage integrieren
    

def send_message():
    #TODO
    pass

def update(delay):
    global ip, port
    while(ip != -1 and port != -1):
        message = util.encode_update(ip, port)
        #TODO: send message to server and receive response
        response = mock.mock_update_response()
        message_type, err_code, login_usrs, logout_usrs,  = util.decode_package_server_resonse(response)
        update_usrlist(login_usrs, logout_usrs)
        time.sleep(delay)

def read_input():
    while(message_type != -1):
        action_type = int(input("Trigger action (0: register, 1: logout, 2:Aufbau TCP, 3:send Message, 4:show aktive users): "))
        match action_type:
            case 0:
                register()
            case 1:
                logout()
            case 2:
                tcp()
            case 3:
                send_message()
            case 4:
                show_usrs()
            case 99:
                print("update")
                update()
            case _:                        # Der Unterstrich '_' ist der Wildcard/Default-Case (wie 'else')
                print("Unbekannter Befehl!")

def start_register():
    print("please register for use")
    register()

start_register()

# 1. Create threads
thread1 = threading.Thread(target=read_input)
thread2 = threading.Thread(target=update, args=(10))


# 2. Start threads (they run concurrently)
thread1.start()
thread2.start()

