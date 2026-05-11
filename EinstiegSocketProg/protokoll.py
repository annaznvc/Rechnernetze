import struct

# Anfrage:  [ID: 4B] [OP: UTF-8 3B] [N: 1B] [z1..zN: je 4B]
# Antwort:  [ID: 4B] [Ergebnis: 4B]

def encode_request(task_id, operation, numbers):
    msg  = struct.pack('!I', task_id)
    msg += operation.encode('utf-8')
    msg += struct.pack('!B', len(numbers))
    for z in numbers:
        msg += struct.pack('!i', z)
    return msg

def decode_request(data):
    task_id,  = struct.unpack_from('!I', data, 0)
    operation = data[4:7].decode('utf-8')
    n,        = struct.unpack_from('!B', data, 7)
    numbers   = [struct.unpack_from('!i', data, 8 + i*4)[0] for i in range(n)]
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
