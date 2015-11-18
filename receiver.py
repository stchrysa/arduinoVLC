#!/usr/bin/pyhton
# -*- coding: utf-8 -*-

import sys
import serial
import time
import threading
import logging
import Queue
import csv

logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s] (%(threadName)-10s) %(message)s',
                    )
lock = threading.Lock()

class Message:

    def __init__(self, message):
        self.message = message
        self.type = ''
        self.msgType = ''
        self.rxType = ''
        self.data = ''
        self.stats = {}
        self.parse(message)


    def parse(self,msg):
        struct = {}
        m1 = msg.split(']')
        m2 = m1[0].split('[')
        if len(m2) > 1:
            m2b = m2[1].split(',')
        if m2[0] == 'm':
            self.type = 'msg'
            self.msgType = m2b[0]
            if self.msgType == 'R':
                self.rxType = m2b[0]
                self.data = m2b[1]
        elif m2[0] == 's':
            self.type = 'stats'
            self.stats['mode'] = m2b[0]
            self.stats['type'] = m2b[1]
            self.stats['src'] = m2b[2].split('->')[0]
            self.stats['dst'] = m2b[2].split('->')[1]
            self.stats['size'] = m2b[3].split('(')[0]
            self.stats['seq'] = m2b[4]
            self.stats['cw'] =  m2b[5]
            self.stats['cwsize'] = m2b[6]
            self.stats['dispatch'] = m2b[7]
            self.stats['time'] = m2b[8]
        else:
            self.type = m2[0]   

class Reader(threading.Thread):

    def __init__(self, serial,comQueue):
        super(Reader, self).__init__()
        self.s = serial
        self.comQueue = comQueue
        self.stopRequest = threading.Event()
        with open('throughput.csv','w') as fd:
            fd.write('time data\n')
        
    def run(self):
        logging.debug('Starting')
        message = ""
        while not self.stopRequest.is_set(): 
            try:
                #logging.debug("Reading...")
                byte = self.s.read(1)#read one byte (blocks until data available or timeout reached)
                if byte == '\n':#if termination character reached 
                    print message
                    msgObj = Message(message)
                    if (msgObj.type == 'msg') & (msgObj.msgType == 'D'):
                        #pass
                        #"""
                        #logging.debug("Done!")
                        lock.acquire()
                        try:
                            self.comQueue.put("m[D]")
                        finally:
                            lock.release()
                            
                        #"""
                    elif msgObj.type == 'stats':
                         if msgObj.stats['type'] == 'D':
                             t = msgObj.stats['time']
                             data = msgObj.stats['size']
                             with open('throughput.csv','a') as fd:
                                 fd.write(str(t)+' '+str(data)+'\n')
                                
                    message = ""#reset message
                else:
                    message = message +byte #concatenate the message
            except serial.SerialException:
                continue #on timeout try to read again

  
        logging.debug('Exiting')
        return
    

        
    

class Communicator:

    def __init__(self,serial_port,payload,source,destination,baud_rate=115200):
        self.source = source
        self.destination = destination
        self.defaultTxPayload = payload

        self.threads = []

        self.comQueue = Queue.Queue()

        self.serial_port = serial_port
        self.baud_rate = baud_rate
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
        t2 = Reader(self.s,self.comQueue) 
        t2.setName('receiver')
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



if __name__ == "__main__":
    if len(sys.argv)>1:
        serial_port = sys.argv[1]
        payloadSize = sys.argv[2]
        source = sys.argv[3]
        destination = sys.argv[4]
        payload = ''
        for i in range(int(payloadSize)):
            payload = payload + 'a'
    else:
        payload = 'Test'
        serial_port = '/dev/ttyACM0'
        source = 'AB'
        destination = 'CD'
    
    c = Communicator(serial_port,payload,source,destination)
    c.start()

