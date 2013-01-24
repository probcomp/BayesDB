import argparse
import zmq
import time
import random
from  multiprocessing import Process

def server_push(port="5556"):
    context = zmq.Context()
    socket = context.socket(zmq.PUSH)
    socket.bind("tcp://*:%s" % port)
    print "Running server on port: ", port
    # serves only 5 request and dies
    for reqnum in range(10):
        if reqnum < 6:
            socket.send("Continue")
        else:
            socket.send("Exit")
            break
        time.sleep(1)
    print "server_push exiting"

def server_pub(port="5558"):
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://*:%s" % port)
    publisher_id = random.randrange(0,9999)
    print "Running server on port: ", port
    # serves only 5 request and dies
    for reqnum in range(10):
        # Wait for next request from client
        topic = random.randrange(8,10)
        messagedata = "server#%s" % publisher_id
        print "%s %s" % (topic, messagedata)
        socket.send("%d %s" % (topic, messagedata))
        time.sleep(1)
    print "server_pub exiting"

def client(port_push, port_sub):
    context = zmq.Context()
    socket_pull = context.socket(zmq.PULL)
    socket_pull.connect ("tcp://localhost:%s" % port_push)
    print "Connected to server with port %s" % port_push
    socket_sub = context.socket(zmq.SUB)
    socket_sub.connect ("tcp://localhost:%s" % port_sub)
    socket_sub.setsockopt(zmq.SUBSCRIBE, "9")
    print "Connected to publisher with port %s" % port_sub
    # Initialize poll set
    poller = zmq.Poller()
    poller.register(socket_pull, zmq.POLLIN)
    poller.register(socket_sub, zmq.POLLIN)
    # Work on requests from both server and publisher
    should_continue = True
    while should_continue:
        socks = dict(poller.poll())
        if socket_pull in socks and socks[socket_pull] == zmq.POLLIN:
            message = socket_pull.recv()
            print "Recieved control command: %s" % message
            if message == "Exit": 
                print "Recieved exit command, client will stop recieving messages"
                should_continue = False

        if socket_sub in socks and socks[socket_sub] == zmq.POLLIN:
            string = socket_sub.recv()
            topic, messagedata = string.split()
            print "Processing ... ", topic, messagedata
    print "client exiting"

if __name__ == "__main__":
    # some settings
    server_push_port = "5556"
    server_pub_port = "5558"
    # parse some args
    parser = argparse.ArgumentParser()
    parser.add_argument('--client', action='store_true')
    parser.add_argument('--server_pub', action='store_true')
    parser.add_argument('--server_push', action='store_true')
    args = parser.parse_args()
    # kick off the appropriate job
    if args.client:
        client(server_push_port, server_pub_port)
    elif args.server_pub:
        server_pub(server_pub_port)
    elif args.server_push:
        server_push(server_push_port)
    else:
        raise Exception("unknown job type")
