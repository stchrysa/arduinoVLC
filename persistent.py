#!/usr/bin/pyhton
# -*- coding: utf-8 -*-

import sys
import serial
import time
import threading
import logging
import Queue

logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s] (%(threadName)-10s) %(message)s',
                    )
lock=threading.Lock()

class Reader(threading.Thread):

    def __init__(self, serial,comQueue):
        super(Reader, self).__init__()
        self.s=serial
        self.comQueue=comQueue
        self.stopRequest = threading.Event()

    def run(self):
        logging.debug('Starting')
        message =""
	done="m[D]"
        while not self.stopRequest.is_set(): 
            try:
                #logging.debug("Reading...")
                byte =self.s.read(1)#read one byte (blocks until data available or timeout reached)
                if byte=='\n':#if termination character reached 
                    print self.parse(message) #print message
                    """"
                    if message==done:
                        lock.acquire()
                        try:
                            self.comQueue.put("m[D]")
                        finally:
                            lock.release()
                            logging.debug("Done!")
                    """
                     
                    message = ""#reset message
                else:
                    message =message +byte #concatenate the message
            except serial.SerialException:
                continue #on timeout try to read again

        logging.debug('Exiting')
        return
    
    def parse(self,msg):
        m1=msg.split(']')
        m2=m1[0].split('[')
        m2b=m2[1].split(',')
        return m2[0:1]+m2b
        
    
    

class Sender(threading.Thread):

    def __init__(self, serial, comQueue, destination):
        super(Sender, self).__init__()
        self.s=serial
        self.comQueue=comQueue
        self.destination = destination
        self.stopRequest = threading.Event()

    def run(self):
        logging.debug('Starting')
        time.sleep(0.1)
        self.s.write("m[Testing...\0,"+self.destination+"]\n")#send message to destination
        while not self.stopRequest.is_set():
            """
            lock.acquire()
            #logging.debug(self.comQueue)
            try:
                try:
                    message = self.comQueue.get_nowait()
                except Queue.Empty:
                    continue
                logging.debug(message)
                if message == "m[D]":               
                    self.s.write("m[Testing...\0,"+self.destination+"]\n")
            finally:
                lock.release()
            """
            self.s.write("m[Testing...\0,"+self.destination+"]\n")  
        logging.debug('Exiting')
        return 

class Communicator:

    def __init__(self,serial_port,source,destination,baud_rate=115200):
        self.destination=destination
        self.source=source

        self.threads=[]

        self.comQueue=Queue.Queue()

        self.serial_port=serial_port
        self.baud_rate=baud_rate
	self.initialize_device()

    def initialize_device(self):
        self.s = serial.Serial(self.serial_port,self.baud_rate,timeout=1)	#opens a serial port (resets the device!) 
        time.sleep(2)#give the device some time to startup (2 seconds)
        #write to the device’s serial port
        self.s.write("a["+self.source+"]\n")#set the device address to CD
        time.sleep(0.1)#wait for settings to be applied
        self.s.write("c[1,0,5]\n")#set number of retransmissions to 5
        time.sleep(0.1) #wait for settings to be applied
        self.s.write("c[0,1,30]\n")#set FEC threshold to 30 (apply FEC to packets with payload >= 30)

    def start(self):
        t1=Sender(self.s,self.comQueue,self.destination)
        t1.setName('sender')
        t2=Reader(self.s,self.comQueue) 
        t2.setName('receiver')
        self.threads.append(t1)
        self.threads.append(t2)
        for t in self.threads:
            t.setDaemon(True)
            t.start()
        while True:
            try:
                continue
            except KeyboardInterrupt:
                for t in self.threads:
                    t.stopRequest.set()
                logging.debug('Ctrl+C')
                sys.exit()


class Measurements:

    def __init__(self,communicator):
        self.communicator = communicator

        with open('log.csv', 'w') as csvfile:
    	    fieldnames = ['timestamp', 'RTT','arrival_offset','src_ip','message_type','peer_ip','tx_hash','peers_no','arrival']
    	    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
	    writer.writeheader()       
 


if __name__=="__main__":
    if len(sys.argv)>1:
        serial_port=sys.argv[1]
        source=sys.argv[2]
        destination=sys.argv[3]
    else:
        serial_port='/dev/ttyACM0'
        source = 'AB'
        destination = 'CD'
    
    c=Communicator(serial_port,source,destination)
    c.start()

