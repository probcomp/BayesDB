import zmq
import random
import sys
import time

port = "5556"
context = zmq.Context()
socket = context.socket(zmq.PAIR)
socket.bind("tcp://*:%s" % port)

counter = 1
while True:
    socket.send("Server message to client " + str(counter))
    counter += 1
    msg = socket.recv()
    print msg
    time.sleep(1)
