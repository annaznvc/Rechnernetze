# Codes
## Error codes
- 0 -> ***success***
- 1 -> error (standart)
# Server-Client Protokoll

***message type***
- 0 -> Registrierung
- 1 -> Abmelden
- 2 -> Update
- 3 -> Broadcast
## Registrierung
Protokoll = ==TCP==
### Anfrage (von Client)
- message type -> 1 Byte
- IP -> 4 byte
- UDP-Port ->  2 byte
- Nickname -> 32 byte
### Antwort (von Server User-list)
- message type -> 1 Byte 
- errorcode -> 1 Byte
- N (Anz an Nutzern) -> 4 byte
- Listeneintrag: (Liste = N * 38 byte)
	- IP -> 4 byte
	- UDP-Port ->  2 byte
	- Nickname -> 32 byte
## Updates
### Anfrage (von Client)
- message type -> 1 Byte
- IP -> 4 byte
- UDP-Port ->  2 byte
### Antwort (von Server)
- message type -> 1 Byte
- errorcode -> 1 Byte 
- X Anz Neu
	- Listeneintrag: 
		- Nickname -> 32 byte
		- port ->  2 byte
		- ip -> 4 byte
- Y Anz Abgemeldet
	-  Listeneintrag: 
		- Nickname -> 32 byte
## Broadcast
### Anfrage (von Client)
- message type -> 1 Byte
- Nickname -> 32 byte 
- Nachricht -> 256
### Antwort (Server an Clients)
- message type -> 1 Byte
- errorcode -> 1 Byte
- Nickname Sender -> 32
- Nachricht -> 256
# Client-Client Protokoll
***message type***
- 4 Aufbau TCP
- 5 Message
## Aufbau TCP connection
Protokoll : ==UDP==
### Anfrage (Client Initiator)
- message type -> 1 Byte
- Nickname -> 32 byte
- offener TCP-Port -> 2 byte
### Antwort (Client Anvisierter)
- message type -> 1 Byte
- errorcode -> 1 Byte
- offener TCP-Port -> 2 byte
## Message 
Protokull ==TCP==
- Message -> 256 bytes
