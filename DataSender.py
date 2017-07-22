#Data Sender

import socket
import time
import struct

b = 4 #bytes per channel
n = 13 #number per data set

TCP_IP = '127.0.0.1'
TCP_PORT = 8889
BUFFER_SIZE = 52


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))

count = 0
filename ='DemoBinaryData.bin'
with open(filename, mode='rb') as file:
    while count<6500000:
        file.seek(b*n,1)
        buffer = file.read(b*n)
        if count == 15000* int(count/15000):
            time.sleep(.25)
            file.seek(b*n*1000,1)
            buffer = file.read(b*n)
            s.send(buffer)
            data = s.recv(BUFFER_SIZE)
            
        else:    
            s.send(buffer)
            data = s.recv(BUFFER_SIZE)
        count = count + 1
    s.close()
    
        
        


