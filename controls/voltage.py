
import time
import random
from ctypes import *
from thread import allocate_lock

class Voltage():
    #constants from LabJackUD.h
    LJ_dtU3=3
    LJ_ctUSB=1

    LJ_ioGET_AIN = 10
    LJ_ioGET_AIN_DIFF=15
    LJ_ioPUT_ANALOG_ENABLE_BIT = 2013;
    LJ_ioGET_ANALOG_ENABLE_BIT = 2014;
    LJ_ioPUT_DAC = 20
    lngHandle=c_long(2)

    simulation=True
    busy=False
    lock = allocate_lock()

    def toggle_simulation(self):
        if self.simulation:
            self.simulation=False
            self.u3=WinDLL('C:\Windows\System32\LabjackUD.dll')
            self.u3.OpenLabJack(self.LJ_dtU3,self.LJ_ctUSB,"1",True,byref(self.lngHandle))
        else:
            self.simulation=True
            self.u3.Close()
        return self.simulation

    def read_voltage(self):
        if self.simulation:
            return(random.randint(1,20))
        else:
            voltage=c_double()
            self.u3.eGet(self.lngHandle,self.LJ_ioGET_AIN,2,byref(voltage),0)
            return(voltage.value)

    def setvoltage(self,voltage):
        self.u3.ePut(self.lngHandle,self.LJ_ioPUT_DAC,1,c_double(voltage),0)

    def close(self):
        if self.simulation==False:
            self.u3.Close()

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
        measurement=self.read_voltage()
        self.busy=False
        return(measurement)
