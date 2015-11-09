#!/usr/bin/pyhton
# -*- coding: utf-8 -*-

import sys
import serial
import time
import threading
import logging
#import dequeue


logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s] (%(threadName)-10s) %(message)s',
                    )

class Chat:

    def __init__(self,serial_port,baud_rate=115200):
        self.threads=[]
        self.lock=threading.RLock()
        #self.queue = deque([])
        self.keep_interrupt = False
        self.serial_port=serial_port
        self.baud_rate=baud_rate
	self.s = serial.Serial(self.serial_port,self.baud_rate,timeout=1)	#opens a serial port (resets the device!) 
        time.sleep(2)#give the device some time to startup (2 seconds)
        #write to the device’s serial port
        self.s.write("a[CD]\n")#set the device address to CD
        time.sleep(0.1)#wait for settings to be applied
        self.s.write("c[1,0,5]\n")#set number of retransmissions to 5
        time.sleep(0.1) #wait for settings to be applied
        self.s.write("c[0,1,30]\n")#set FEC threshold to 30 (apply FEC to packets with payload >= 30)
        time.sleep(0.1) #wait for settings to be applied
        self.start()

    def start(self):
	address='FF'
        t1=threading.Thread(target=self.transmit, name='transmitter', args=(address,))
        t2=threading.Thread(target=self.receive, name='receiver')
        self.threads.append(t1)
        self.threads.append(t2)
        for t in self.threads:
            t.start()
        for t in self.threads:
            t.join()
        

    def transmit(self,address):
        logging.debug('Starting')
        time.sleep(0.1)
        while True:
            try:
                message = raw_input('')
                print message
                self.s.write("m["+message+"\0,"+address+"]\n")#send message to device with address
            except KeyboardInterrupt:
                logging.debug('Ctrl+C')
                sys.exit()

        logging.debug('Exiting') 
        return

    def receive(self):
        logging.debug('Starting')
        message =""
        while True:	#while not terminated 
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
            except KeyboardInterrupt:
                logging.debug('Ctrl+C')
                sys.exit()

        logging.debug('Exiting')
        return

if __name__=="__main__":
    if len(sys.argv)>1:
        serial_port=sys.argv[1]
    else:
        serial_port='/dev/ttyACM0'
    
    c=Chat(serial_port)


