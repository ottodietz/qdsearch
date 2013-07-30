from SimSerial import SimSerial
import time
import random
import math

class Voltage(SimSerial):

    commando_position="first"
    number_of_EOL=0
    new_simulation=True

    voltage_simulation=float(2.511)

    def blink(self):
        self.write("B")

    def _B(self):
        print 'blinken'

    def read_voltage(self):
        start = time.clock()
        temp=''
        self.flushInput()
        while (temp.find("Voltage")==-1):
            self.write("V")
            #time.sleep(0.1)
            temp=self.readline()
        voltage=temp[9:14]
        ende = time.clock()
        # print "the function runs %1.2f s" % (ende - start)
        return(float(voltage))

    def read_voltage_new(self):
        start = time.clock()
        temp=''
        self.flushInput()
        self.write('V')
        time.sleep(0.9)
        number=self.inWaiting()
        temp=self.read(number)
        a=temp.find('Voltage')
        voltage=temp[a+9:a+14]
        ende = time.clock()
        print "the function runs %1.2f s" % (ende - start)
        return(float(voltage))


    def _V(self):
        self.buffer='Voltage'+'  '+str(self.voltage_simulation)

    def measure(self):
        if  self.simulation:
            measurement=random.randint(1,20)
            time.sleep(0.2)
        else:
            measurement=self.read_voltage()
        return(measurement)

    def setvoltage(self,voltage):
        self.voltage_simulation=voltage
        dutycycle = "%03d"% int(voltage*255/5.) # problem ist das simserial keine vielen einzelne stringsverarbeitet...
        self.write("S");
        time.sleep(0.1)
        for i in [0,1,2]:
            self.write(dutycycle[i])
            time.sleep(0.1)
        self.write("d")

    def _S(self,string):
        print self.voltage_simulation
