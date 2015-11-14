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

class Reader(threading.Thread):

    def __init__(self, serial):
        super(Reader, self).__init__()
        self.s=serial
        self.stopRequest = threading.Event()

    def run(self):
        logging.debug('Starting')
        message =""
        while not self.stopRequest.is_set():	#while not terminated 
            try:
                byte =self.s.read(1)#read one byte (blocks until data available or timeout reached)
                #logging.debug('Thread alive')
                if byte=='\n':#if termination character reached 
                    print message #print message
                    message = ""#reset message
                else:
                    message =message +byte #concatenate the message
            except serial.SerialException:
                continue #on timeout try to read again

        logging.debug('Exiting')
        return
    
    

class Sender(threading.Thread):

    def __init__(self, serial, msgQueue, destination):
        super(Sender, self).__init__()
        self.s=serial
        self.msgQueue=msgQueue
        self.destination = destination
        self.stopRequest = threading.Event()

    def run(self):
        logging.debug('Starting')
        time.sleep(0.1)
        while not self.stopRequest.is_set():
            try:
                message = self.msgQueue.get_nowait()               
                self.s.write("m["+message+"\0,"+self.destination+"]\n")#send message to destination
                logging.debug(message)
            except Queue.Empty:
                continue
        logging.debug('Exiting')
        return 

class Chat:

    def __init__(self,serial_port,source,destination,baud_rate=115200):
        self.destination=destination
        self.source=source

        self.threads=[]
        self.lock=threading.RLock()

        self.msgQueue=Queue.Queue()

        self.serial_port=serial_port
        self.baud_rate=baud_rate
	self.s = serial.Serial(self.serial_port,self.baud_rate,timeout=1)	#opens a serial port (resets the device!) 
        time.sleep(2)#give the device some time to startup (2 seconds)
        #write to the device’s serial port
        self.s.write("a["+self.source+"]\n")#set the device address to CD
        time.sleep(0.1)#wait for settings to be applied
        self.s.write("c[1,0,5]\n")#set number of retransmissions to 5
        time.sleep(0.1) #wait for settings to be applied
        self.s.write("c[0,1,30]\n")#set FEC threshold to 30 (apply FEC to packets with payload >= 30)

    def start(self):
        t1=Sender(self.s,self.msgQueue,self.destination)
        t1.setName('sender')
        t2=Reader(self.s) 
        t2.setName('receiver')
        self.threads.append(t1)
        self.threads.append(t2)
        for t in self.threads:
            #t.setDaemon(True)
            t.start()
        while threading.enumerate()>0:
            try:
                message = raw_input('')
                self.msgQueue.put(message)
            except KeyboardInterrupt:
                for t in self.threads:
                    t.stopRequest.set()
                logging.debug('Ctrl+C')
                sys.exit()

    

if __name__=="__main__":
    if len(sys.argv)>1:
        serial_port=sys.argv[1]
        source=sys.argv[2]
        destination=sys.argv[3]
    else:
        serial_port='/dev/ttyACM0'
        source = 'AB'
        destination = 'CD'
    
    c=Chat(serial_port,source,destination)
    c.start()
    


