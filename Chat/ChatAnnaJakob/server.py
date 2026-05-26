import util

login_usr = [] #name, ip, port, socket
logout_usr = []

def handle_package(message):
    message_type = util.decode_message_type(message)
    if message_type == 0:
        return handle_register(message)
    elif message_type == 1:
        return handle_logout(message)
    elif message_type == 2:
        return handle_update(message)
    else:
        return util.encode_error_response(1)

def handle_register(message):
    message_type, ip, port, name = util.decode_register(message)
    login_usr.append((ip, port, name))
    response_message = util.encode_register_response( 0, login_usr)
    #TODO implement response
    return response_message

def handle_logout(message):
    #TODO implementieren
    return util.encode_error_response(1)

def handle_update(message):
    IP_str, Port = util.decode_update(message)
    #TODO tcp implement
    response_message = util.encode_update_response(0, login_usr, logout_usr)
    return response_message

