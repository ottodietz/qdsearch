from simserial import SimSerial
import time
import random
import math
from thread import allocate_lock
import re

class Voltage(SimSerial):
    EOL=''
    CMD='^[A-Z]'
    PARMS='[^a-zA-Z]+'
    simulation=True
    busy=False

    lock = allocate_lock()
    
    def blink(self):
        self.write("B")

    def _B(self):
        print 'blinken'

    def read_voltage(self):
        #start = time.clock()
        temp=''
        self.flushInput()
        while (temp.find("Voltage")==-1):
            self.write("V")
            temp=self.readline()
        voltage=temp[9:14]
        #ende = time.clock()
        #print "the function read runs %1.2f s" % (ende - start)
        return(float(voltage))

    def read_voltage_new(self):
        #start = time.clock()
        temp=''
        self.flushInput()
        self.write('V')
        time.sleep(0.2)
        number=self.inWaiting()
        voltage=self.read(number)
#        a=temp.find('Voltage')
#        if a!=-1:
#            voltage=temp[a+9:a+14]
#        else:
#            voltage=0
#            print 'can not read voltage correctly'
        #ende = time.clock()
        #print "the function read 2 runs %1.2f s" % (ende - start)
        return(float(voltage))


    def _V(self):
        self.buffer='Voltage'+'  '+str(random.randint(1,20))
        
    def measure(self):
        i = 0

        # do not measure if our thread is measuring
        self.lock.acquire()
        while self.busy:
            i+=1
            time.sleep(0.1)
            if i > 100:
                print "Warning Voltage.measure waited 10s for busy==False"
                i = 0
        self.busy=True
        self.lock.release()

#        if  self.simulation:
#            measurement=random.randint(1,20)
#            time.sleep(0.2)
#        else:

        measurement=self.read_voltage()
        self.busy=False
        return(measurement)

    def setvoltage(self,voltage):
        Sxxxd = "S%03dd"% int(voltage*255/5.)
        self.write(Sxxxd,inter_char_delay=0.1);
        return voltage

    def _S(self,string):
        temp = re.search(self.PARMS,string).group(0)
        voltprint = float(int(temp)*5./255.)
        print "die gesetzte Spannung liegt bei %1.2f  Volt" % voltprint
