import util

def mock_update_response():
    #TODO: implementieren
    return ("list von aktiven users")

def mock_register_response():
    #TODO: implementieren
    return ("Erfolgreich registriert")

def mock_tcp_response():
    # Erfolgsantwort fuer TCP-Setup: type=4, err=0, open_port=9002
    return util.encode_tcp_rsponse(9002)
