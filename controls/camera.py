from ctypes import *
import random
import numpy as np
from time import sleep
from math import *
from scipy.special import jn

CAM_OKAY = 20002

#initializing empty c-types is okay for getfunctions, for setfunctions NOT init
#c-types at beginning, ONLY use them DIRECTLY in the setfunction e.g.
#setreadmode()
#IMPORTANT DONT TRUST ANDOR SDK MANUAL
#it lies, check with pdb.set_trace() what args are needed in the setfunctions,
#way it is in the SetVSSpeeds is the right way, trial and error and a lot of
#pain

class Camera(object):
    totalCameras=c_long()
    init_active=False
    camera_active=False
    low_temperature=False

    #section for readmodes
    readmode_dict = {'Full Vertical Binning':0 , 'Image': 4}
    readmode_keys = readmode_dict.viewkeys()
    readmode_values = readmode_dict.viewvalues()
    readmode_default = readmode_dict[readmode_keys[0]]  #hier der default fuer den start

    #section for acquisitionmode
    acquisitionmode_dict = {'One Shot' : 1}
    acquisitionmode_keys = acquisitionmode_dict.viewkeys()
    acquisitionmode_values = acquisitionmode_dict.viewvalues()
    acquisitionmode_default = acquisitionmode_dict[acquisitionmode_keys[0]]
    
    #section for containers for testbutton in speedinit
    NumOfHSpeeds = c_int()
    NumOfVSpeeds = c_int()
    ValueOfHSpeed = c_float()
    ValueOfVSpeed = c_float()
    
    #section for shiftspeeds
    Hshiftspeed_dict = {'16 MHz': 0, '8 MHz' : 1, '4 MHz' : 2}
    Vshiftspeed_dict = {'16 us': 0, '8 us' : 1, '4 us' : 2, '2 us' : 3}
    Hshiftspeed_keys = Hshiftspeed_dict.viewkeys()
    Hshiftspeed_values = Hshiftspeed_dict.viewvalues()
    Vshiftspeed_keys = Vshiftspeed_dict.viewkeys()
    Vshiftspeed_values = Vshiftspeed_dict.viewvalues()
    Vshiftspeed_default = Vshiftspeed_dict[Vshiftspeed_keys[0]] 
    Hshiftspeed_default = Hshiftspeed_dict[Hshiftspeed_keys[0]]
    
    exposuretime_default = 0.1 #hier darf kein c_float stehen, siehe comment am anfang
    temperature_default = -70
    simulation=True

    def toggle_simulation(self):
        self.simulation = not self.simulation
        if not self.simulation and not self.camera_active:
            self.init_active=True
            try:
                self.atm = WinDLL("C:\Program Files\Andor SOLIS\ATMCD32D.DLL")
                print "Init:", self.atm.Initialize(None)
                print "GetAvailableCameras:",self.atm.GetAvailableCameras(byref(self.totalCameras))
                print "SetReadMode:",self.setreadmode(self.readmode_default])
                print "SetHShiftspeed:",self.setHshiftspeed(self.Hshiftspeed_default) #highest speed as default
                print "SetVShiftspeed:",self.setVshiftspeed(self.Vshiftspeed_default) #highest speed as default
                print "SetAcqMode:",self.setacquisitionmode(self.acquisitionmode_default)
                print "SetExpTime:",self.setexposuretime(self.exposuretime_default) #Belichtungsdauer
                print "Cooler ON",self.cooler_on()
                print "SetTemo to -70", self.settemperature(self.temperature_default)
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
                print "set exposure time to ",float(exp)
            return self.atm.SetExposureTime(c_float(exp))
        else:
            print "simulate exposure time at ",float(exp)
        return CAM_OKAY

    def acquisition(self, sim_pos=(0,0),sim_volt=(0),exptme=(0)):#,sim_posx=None,sim_posy=None):
        hpixel=1024
        vpixel=128

        if self.simulation and self.readmode_name == "Full Vertical Binning":
            line = [ 10*exptme*2*sin(2.*pi/12.*sim_volt)*100*((cos(2.*pi/4.*sim_pos[0]))**2)*((cos(2.*pi/4.*sim_pos[1]))**2)*jn(0,i-512+1*sim_pos[0]//1+1*sim_pos[1]//1) for i in np.arange(hpixel) ]
            return line

        if self.simulation and self.readmode_name == "Image":
            image = [[random.randint(1,100) for e in range(128)] for e in range(1024)]
            return image

        action = []
        error  = []
        action.append("StartAcq:")
        error.append(self.atm.StartAcquisition())
        action.append("Wait:")
        error.append(self.atm.WaitForAcquisition())
        action.append("GetMostRecentImage")
        if self.readmode_name == "Full Vertical Binning":
            line  = (c_long * hpixel)()
            error.append(self.atm.GetMostRecentImage(byref(line),c_ulong(hpixel)))
        if self.readmode_name == "Image":
            image = (c_long * hpixel * vpixel)()
            error.append(self.atm.GetMostRecentImage(byref(image),c_ulong(vpixel*hpixel)))
        if not np.all(np.array(error) == CAM_OKAY):
            print action
            print error
        #action.append('cancel acq:')
        #error.append(self.atm.AbortAcquisition())
        if self.readmode_name == "Full Vertical Binning":
            return(line)
        if self.readmode_name == "Image":
            return(image)

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
        print 'settemperature', self.atm.SetTemperature(c_int(temperature))

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

    def speedinit(self):
        print "GetNumerHSSSpeeds"
        print self.atm.GetNumberHSSpeeds(c_int(0), c_int(0), byref(self.NumOfHSpeeds))
        print self.NumOfHSpeeds
        print "MHZ of HSSSpeed"
        for i in range(3):
            print "speed in MHZ of setting",i
            self.atm.GetHSSpeed(c_int(0), c_int(0),c_int(i), byref(self.ValueOfHSpeed))
            print self.ValueOfHSpeed
        self.atm.SetHSSpeed(c_int(0),c_int(0)) #Fastest speed
        print "GetNumerVSSpeeds"
        print self.atm.GetNumberVSSpeeds(byref(self.NumOfVSpeeds))
        print self.NumOfVSpeeds
        print "MHZ of VSSpeed"
        for i in range(4):
            print "speed in MHZ of setting",i
            self.atm.GetVSSpeed(c_int(i), byref(self.ValueOfVSpeed))
            print self.ValueOfVSpeed
        self.atm.SetVSSpeed(c_int(0)) #Fastest speed

    def setVshiftspeed(self,name=None):
        if self.simulation:
            print "simulation Vshiftspeed set to", name
        else:
            self.atm.SetVSSpeed(c_int(self.Vshiftspeed_dict[name]))
            print "Vshiftspeed set to ",name
            
    def setHshiftspeed(self,name=None):
        if self.simulation:
            print "simulation Hshiftspeed set to", name
        else:
            self.atm.SetHSSpeed(c_int(0),c_int(self.Hshiftspeed_dict[name]))
            print "Hshiftspeed set to", name

    def setreadmode(self,name=None):
        if self.simulation:
            print "simulation readmode set to", name
        else:
            self.atm.SetReadMode(c_int(self.readmode_dict[name])) #check ifproblem with ad channel check sdk
            if name == "Image":
                self.atm.SetImage(c_int(1),c_int(1),c_int(1),c_int(1024),c_int(1),c_int(128))
            print "readmode set to", name

    def setacquisitionmode(self,name=None):
        if self.simulation:
            print "simulation Acquisitionmode to", name
        else:
            print "Acquisitionmode to", name
            self.atm.SetAcquisitionMode(c_int(self.acquisitionmode_dict[name]))

if __name__ == "__main__":
    c = Camera()
    c.toggle_simulation()
    c.close()
