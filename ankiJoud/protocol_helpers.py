import struct

def pad_string(text, length): #Füllt einen String mit Nullbytes auf die exakte Länge auf
    encoded = text.encode('utf-8') #übersetzungsfkt von Text -> Bytes
    if len(encoded) > length:
        return encoded[:length]  # Abschneiden, falls zu lang
    return encoded.ljust(length, b'\x00') #b bed byte obj (bytes 0-255), Null-Terminator (ende von String), bzw Füllmaterial für Puffer

def unpad_string(byte_data): #Entfernt die Nullbytes und decodiert den String
    return byte_data.decode('utf-8').strip('\x00') #übersetzt Bytes -> text & schneidet ab \x00 ab