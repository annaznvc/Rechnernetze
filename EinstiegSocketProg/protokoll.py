import struct 

# Anfrage:  [ID: !I 4B] [OP: UTF-8 3B] [N: !B 1B] [z1..zN: !i je 4B]
# Antwort:  [ID: !I 4B] [Ergebnis: !i 4B]

def encode_request(task_id, operation, numbers):
    msg  = struct.pack('!I', task_id) #unsigned int, msg = [0, 0, 0, 42]
    msg += operation.encode('utf-8') #Jedes zeichen wird zu seinem Ascii Zahlenwert S = 83, U = 85, M = 77 msg = [0,0,0,42,83,85,77]
    msg += struct.pack('!B', len(numbers)) # 1 unsigend Byte msg = [0, 0, 0, 42, 83, 85, 77, 2]
    for z in numbers: # z.b NUMBERS [10,20], jede Zahl bekommt 4 Bytes
        msg += struct.pack('!i', z) # msg = [0, 0, 0, 42, 83, 85, 77, 2, 0, 0, 0, 10, 0, 0, 0, 20]
    return msg

def decode_request(data): # komma bei task id und n damit Python nicht Tupel entpackt sondern sofort Zahl gibt
    task_id,  = struct.unpack_from('!I', data, 0) #liest ab Byte Position 0 genau 4 Bytes (!I) und baut daraus eine Python Zahl
    operation = data[4:7].decode('utf-8') #schneidet bytes 4,5,6 heraus, weil an der Position Ascii werte für operationen sind
    n,        = struct.unpack_from('!B', data, 7) # ab position 7 lieht ein einzelnes Byte vor, dass Anzahl der Zahlen enthält
    numbers   = [struct.unpack_from('!i', data, 8 + i*4)[0] for i in range(n)] # List Comprehension - Kompakte For Schleife die direkt ne Liste aufbaut ;)
    return task_id, operation, numbers

def encode_response(task_id, result):
    return struct.pack('!Ii', task_id, result)

def decode_response(data):
    return struct.unpack('!Ii', data)

def berechne(op, nums):
    if op == 'SUM': return sum(nums)
    if op == 'PRO':
        r = 1
        for z in nums: r *= z
        return r
    if op == 'MIN': return min(nums)
    if op == 'MAX': return max(nums)
