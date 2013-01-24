import zmq
import random
import sys
import time

port = "5556"
context = zmq.Context()
socket = context.socket(zmq.PAIR)
socket.connect("tcp://localhost:%s" % port)

counter = 1
while True:
    msg = socket.recv()
    print msg
    socket.send("client message to server " + str(counter))
    socket.send("client message to server " + str(counter+1))
    counter += 2
    time.sleep(1)
