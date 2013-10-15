from ctypes import *
import random
import numpy as np
import time


class Camera():
    totalCameras=c_long()
    init_active=False
    camera_active=False
    low_temperature=False
    readmode=int(0)
    acquisitionmode=int(1)
    exposuretime=c_float(0.1)
    simulation=True

    def toggle_simulation(self,caller):
        self.simulation = not self.simulation
        if not self.simulation and not self.camera_active:
            self.init_active=True
            try: 
                self.atm = WinDLL("C:\Program Files\Andor SOLIS\ATMCD32D.DLL")
                print "Init:", self.atm.Initialize(None)
                print "GetAvailableCameras:",self.atm.GetAvailableCameras(byref(self.totalCameras))
                print "SetReadMode:",self.atm.SetReadMode(self.readmode) #FullverticalBinning
                print "SetAcqMode:",self.atm.SetAcquisitionMode(self.acquisitionmode) # single shoot
                print "SetExpTime:",self.atm.SetExposureTime(self.exposuretime) #Belichtungsdauer 
                self.camera_active=True
            except (NameError,) as e:
                print "Camera init failed: ",e
                self.camera_active=False
                self.simulation=True
            finally:
                self.init_active=False
        caller = self.simulation


    def acquisition(self):
        pixel=1024
        if self.simulation:
            line = [ random.randint(10,100) for i in np.arange(pixel) ]
            print "simulating acquisition 2"
            return line
        line  = (c_long * pixel)()
        print "StartAcq:",self.atm.StartAcquisition()
        print "Wait:",self.atm.WaitForAcquisition()
        print "GetMostRecentImage",self.atm.GetMostRecentImage(byref(line),c_ulong(pixel))
        print "idle is 20073"
        print 'cancel acq:', self.atm.AbortAcquisition()
        return(line)

    def close(self):
        if self.camera_active:
            temp = self.gettemperature()
            print "Camera at ", temp, ' C'
            if temp < -20:
                temp = self.settemperature(-20)
                self.cooler_on()
                while temp < -20:
                    print "Warming up self, pleas wait ... T=",temp,' C'
                    sleep(2)
                    temp = self.getemperature()
            print "Camera warm up finished"
            self.cooler_off()
            print "ShutDown:", self.atm.ShutDown()
        else:
            print "Camera: Simulate Shutdown"
        self.camera_active = False

    def gettemperature(self):
        temperature=c_long()
        if not self.simulation:
            print 'GetTemperature', self.atm.GetTemperature(byref(temperature))
        else:
            print 'GetTemperature: simulate'
            return random.randint(-70,20)
        return(temperature.value)

    def cooler_on(self):
        if self.simulation:
            print "Cooler on: simulation"
            return True
        print 'Cooler on:',self.atm.CoolerON()

    def cooler_off(self):
        if self.simulation:
            print "Cooler off: simulation"
            return True
        print 'Cooler off:',self.atm.CoolerOFF()

    def gettemperature_range(self):
        mintemp=c_long()
        maxtemp=c_long()
        mintemp = -70
        maxtemp = 20
        if not self.simulation:
            print 'Gettemperature_range:', self.atm.GetTemperatureRange(byref(mintemp),byref(maxtemp))
        print 'min temp' ,
        print mintemp
        print 'maxtemp' ,
        print maxtemp

    def settemperature(self,temperature):
        if self.simulation:
            print 'settemperature: simulation'
            return True
        print 'settemperature', self.atm.SetTemperature(temperature)

    def gettemperature_status(self):
        sensortemp=c_float()
        targettemp=c_float()
        AmbientTemp=c_float()
        cooler_volt=c_float()
        if self.simulation:
            sensortemp=float(random.randint(-70,20))
            targettemp=-33.
            AmbientTemp=18.5
            cooler_volt=1.1
        else:
            print'temperautre_status:', self.atm.GetTemperatureStatus(byref(sensortemp),byref(targettemp),byref(AmbientTemp),byref(cooler_volt))
        print 'sensortemp:',
        print sensortemp
        print 'targettemp',
        print targettemp

if __name__ == "__main__":
    c = Camera()
    c.toggle_simulation(True)
    c.close()
