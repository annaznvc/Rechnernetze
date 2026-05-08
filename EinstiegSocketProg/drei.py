# <ID><Rechenoperation><N><z1><z2>…<zN>

# ID: unsigned integer
# Rechenoperation: SUM, PRO, MIN, MAX (UTF 8)
# N: Wie viele Zahlen folgen (Unsigned Char)
# z1 - zn: (signed Integer) (pack unpack)

import struct

data = struct.pack('iii', 1, 2, 3)

print(data)