import util
import mock

ip = ""
port = 0
name = ""
aktive_users = []

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
    #TODO
    pass

def send_message():
    #TODO
    pass

def update():
    global ip, port
    message = util.encode_update(ip,port)
    response = mock.mock_update_response()
    print("Aktive users: " + response)
    return response

message_type = 0
while(message_type != -1):
    action_type = int(input("Trigger action (0: register, 1: logout, 2:Aufbau TCP, 3:send Message): "))
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
            print("update")
            update()
        case _:                        # Der Unterstrich '_' ist der Wildcard/Default-Case (wie 'else')
            print("Unbekannter Befehl!")


