import math
import socket
import time
import pickle
import collections

t=0.0
bat1 = 5.0
bat2 = 5.25
bat3 = 4.75
bat4 = 5.5

TCP_IP = '127.0.0.1'
TCP_PORT = 8889
BUFFER_SIZE = 1024


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))

for i in range(0, 651000):
    bat1 = bat1-5/4000000
    bat2 = bat2-5/4000000
    bat3 = bat3-5/4000000
    bat4 = bat4-5/4000000
    IMU1 = 9*math.sin(t/1000*3.14159)
    IMU2 = 10*math.sin(t/1000*2*3.14159)
    IMU3 = 11*math.sin(t/1000*0.5*3.14159)
    IMU4 = 8*math.sin(t/1000*(3.14159+3.14158/8))
    IMU5 = 7*math.sin(t/1000*(3.14159+2*3.14158/8))
    IMU6 = 12*math.sin(t/1000*(3.14159+3*3.14158/8))
    IMU7 = 6*math.sin(t/1000*(3.14159+4*3.14158/8))
    IMU8 = 9.5*math.sin(t/1000*(3.14159+5*3.14158/8))

    #Very Important - You must build you dictionary  this way...
    #TOF in milleseconds first, followed by each channel name and floating point value.
    #Also import collections and pickle 
    dict = collections.OrderedDict()
    dict['TOF']=t
    dict['BAT 1']=bat1
    dict['BAT 2']=bat2
    dict['BAT 3']=bat3
    dict['BAT 4']=bat4
    dict['IMU1 CH1']=IMU1
    dict['IMU1 CH2']=IMU2
    dict['IMU1 CH3']=IMU3
    dict['IMU1 CH4']=IMU4
    dict['IMU2 CH1']=IMU5
    dict['IMU2 CH2']=IMU6
    dict['IMU2 CH3']=IMU7
    dict['IMU2 CH4']=IMU8

    
    t=t+100
    s.send(pickle.dumps(dict))
    data = s.recv(BUFFER_SIZE)
    time.sleep(0.095) 
s.close()
