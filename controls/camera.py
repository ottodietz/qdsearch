from ctypes import *
import random
import numpy as np
import time
from math import *
from scipy.special import jn

CAM_OKAY = 20002

class Camera(object):
    totalCameras=c_long()
    init_active=False
    camera_active=False
    low_temperature=False
    readmode=int(0)
    acquisitionmode=int(1)
    exposuretime=c_float(0.1)
    simulation=True

    def toggle_simulation(self):
        self.simulation = not self.simulation
        if not self.simulation and not self.camera_active:
            self.init_active=True
            try:
                self.atm = WinDLL("C:\Program Files\Andor SOLIS\ATMCD32D.DLL")
                print "Init:", self.atm.Initialize(None)
                print "GetAvailableCameras:",self.atm.GetAvailableCameras(byref(self.totalCameras))
                print "SetReadMode:",self.atm.SetReadMode(self.readmode) #FullverticalBinning
                print "SetAcqMode:",self.atm.SetAcquisitionMode(self.acquisitionmode) # single shoot
                print "SetExpTime:",self.setexposuretime() #Belichtungsdauer
                print "Cooler ON",self.cooler_on()
                print "SetTemo to -70", self.settemperature(c_long(-70))
                self.camera_active=True
            except (NameError,) as e:
                print "Camera init failed: ",e
                self.camera_active=False
                self.simulation=True
            finally:
                self.init_active=False
        return self.simulation

    def setexposuretime(self, exp=None):
        if not self.simulation:
            if not exp:
                exp = self.exposuretime
            return self.atm.SetExposureTime(c_float(exp))
        return CAM_OKAY

    def acquisition(self, sim_pos=(0,0),sim_volt=(0),exptme=(0)):#,sim_posx=None,sim_posy=None):
        pixel=1024

        if self.simulation:
            line = [ 10*exptme*2*sin(2.*pi/12.*sim_volt)*100*((cos(2.*pi/4.*sim_pos[0]))**2)*((cos(2.*pi/4.*sim_pos[1]))**2)*jn(0,i-512+1*sim_pos[0]//1+1*sim_pos[1]//1) for i in np.arange(pixel) ]
            return line

        line  = (c_long * pixel)()
        action = []
        error  = []
        action.append("StartAcq:")
        error.append(self.atm.StartAcquisition())
        action.append("Wait:")
        error.append(self.atm.WaitForAcquisition())
        action.append("GetMostRecentImage")
        error.append(self.atm.GetMostRecentImage(byref(line),c_ulong(pixel)))
        if not np.all(np.array(error) == CAM_OKAY):
            print action
            print error
        #action.append('cancel acq:')
        #error.append(self.atm.AbortAcquisition())
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
        mintemp=c_long(-70)
        maxtemp=c_long(20)
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
    c.toggle_simulation()
    c.close()
