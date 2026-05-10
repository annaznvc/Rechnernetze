import socket
import ssl
import base64
import time

# --- Konfiguration ---
SMTP_SERVER = 'asmtp.htwg-konstanz.de'
SMTP_PORT = 587
USERNAME = 'rnetin15'
PASSWORD = 'xxxx'  # hier dein echtes Passwort eintragen

ABSENDER_SMTP = 'rnetin15@htwg-konstanz.de'   # MAIL FROM (was der Server prüft)
ABSENDER_HEADER = 'rnetin15@htwg-konstanz.de'  # From: Header (was im Postfach erscheint)
EMPFAENGER = 'rnetin15@htwg-konstanz.de'       # deine eigene Adresse zum Testen


def b64(text):
    """Hilfsfunktion: ASCII-String -> Base64-String (wie die Aufgabe beschreibt)."""
    return base64.b64encode(text.encode('utf-8')).decode('utf-8')


def send(sock, msg):
    """Sendet eine Zeile UTF-8-kodiert mit \\r\\n Zeilenende – so verlangt es SMTP."""
    print(f">>> {msg}")
    sock.send((msg + '\r\n').encode('utf-8'))


def recv(sock):
    """Empfängt die Antwort des Servers und gibt sie aus."""
    antwort = sock.recv(4096).decode('utf-8')
    print(f"<<< {antwort.strip()}")
    return antwort


# =============================================================================
# Schritt 1: Normalen TCP-Socket öffnen (noch KEIN SSL)
# =============================================================================
raw_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
raw_sock.connect((SMTP_SERVER, SMTP_PORT))
recv(raw_sock)  # Server-Begrüßung: "220 asmtp.htwg-konstanz.de ESMTP"

# =============================================================================
# Schritt 2: EHLO senden – stellt uns beim Server vor und listet seine Features
# =============================================================================
send(raw_sock, 'EHLO meinrechner')
recv(raw_sock)

# =============================================================================
# Schritt 3: STARTTLS anfordern – ab jetzt wollen wir verschlüsseln
# =============================================================================
send(raw_sock, 'STARTTLS')
recv(raw_sock)  # Server antwortet: "220 Ready to start TLS"

# Kurz warten damit der Server bereit ist (Hinweis 4 aus der Aufgabe)
time.sleep(1)

# =============================================================================
# Schritt 4: SSL-Socket aufbauen – wrap_socket() legt einen TLS-Tunnel
#            über die bestehende TCP-Verbindung
# =============================================================================
context = ssl.create_default_context()
sock = context.wrap_socket(raw_sock, server_hostname=SMTP_SERVER)
print(">>> [TLS-Verbindung aufgebaut]")

# Nach STARTTLS muss EHLO wiederholt werden – jetzt über den verschlüsselten Kanal
send(sock, 'EHLO meinrechner')
recv(sock)

# =============================================================================
# Schritt 5: Login mit Base64-kodierten Zugangsdaten
# =============================================================================
send(sock, 'AUTH LOGIN')
recv(sock)  # Server fragt nach Username: "334 VXNlcm5hbWU6"

send(sock, b64(USERNAME))
recv(sock)  # Server fragt nach Passwort: "334 UGFzc3dvcmQ6"

send(sock, b64(PASSWORD))
recv(sock)  # Erfolg: "235 2.7.0 Authentication successful"

# =============================================================================
# Schritt 6: Mail versenden über SMTP-Dialog
# =============================================================================
send(sock, f'MAIL FROM:<{ABSENDER_SMTP}>')
recv(sock)  # "250 Ok"

send(sock, f'rcpt to:<{EMPFAENGER}>')  # WICHTIG: Kleinbuchstaben! (siehe Aufgabe)
recv(sock)  # "250 Ok"

send(sock, 'DATA')
recv(sock)  # "354 End data with <CR><LF>.<CR><LF>"

# Mail-Header und Body – eine Leerzeile trennt Header von Body (RFC 2822)
send(sock, f'From: {ABSENDER_HEADER}')
send(sock, f'To: {EMPFAENGER}')
send(sock, 'Subject: Test Rechnernetze Labor')
send(sock, '')  # Leerzeile = Trenner zwischen Header und Body
send(sock, 'Hallo, das ist ein Test aus dem Rechnernetze Labor.')
send(sock, 'Gesendet per Python-Socket ohne smtplib.')
send(sock, '.')  # einzelner Punkt auf einer Zeile = Ende der Mail
recv(sock)  # "250 Ok: queued"

# =============================================================================
# Schritt 7: Verbindung sauber beenden
# =============================================================================
send(sock, 'QUIT')
recv(sock)  # "221 Bye"
sock.close()

print("\nMail erfolgreich gesendet!")