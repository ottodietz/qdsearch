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
#TODO thomas meinte andor haette nur 128 px in der hoehe?!

class Camera(object):
    totalCameras=c_long()
    init_active=False
    camera_active=False
    low_temperature=False
    readmode_name=str('Full Vertical Binning') #hier der default fuer den start
    readmode_value=int()
    acquisitionmode=int(1) #single shot as default
    NumOfHSpeeds = c_int()
    NumOfVSpeeds = c_int()
    ValueOfHSpeed = c_float()
    ValueOfVSpeed = c_float()
    Vshiftspeed_index = int(0) # zero is fastest speed
    Vshiftspeed_value = str()
    Hshiftspeed_index = int(0)
    Hshiftspeed_value = str()
    Hshiftspeed_data = [[0,0],[1,1],[2,2]]
    Vshiftspeed_data = [[0,0],[1,1],[2,2],[3,3]]
    exposuretime=0.1 #hier darf kein c_float stehen, siehe comment am anfang
    simulation=True

    def toggle_simulation(self):
        self.simulation = not self.simulation
        if not self.simulation and not self.camera_active:
            self.init_active=True
            try:
                self.atm = WinDLL("C:\Program Files\Andor SOLIS\ATMCD32D.DLL")
                print "Init:", self.atm.Initialize(None)
                print "GetAvailableCameras:",self.atm.GetAvailableCameras(byref(self.totalCameras))
                print "SetReadMode:",self.setreadmode()
                print "SetHShiftspeed:",self.setHshiftspeed() #highest speed as default
                print "SetVShiftspeed:",self.setVshiftspeed() #highest speed as default
                print "SetAcqMode:",self.setacquisitionmode()
                print "SetExpTime:",self.setexposuretime() #Belichtungsdauer
                print "Cooler ON",self.cooler_on()
                print "SetTemo to -70", self.settemperature(-70)
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

    def setVshiftspeed(self,value=None):
        if value:
            value = int(value) #conversion to int as list[][] takes only int 
            self.Vshiftspeed_index = self.Vshiftspeed_data[value][0]
        self.Vshiftspeed_value = self.Vshiftspeed_data[self.Vshiftspeed_index][1]
        if self.simulation:
            print "simulation Vshiftspeed set to %2f" % self.Vshiftspeed_value
        else:
            self.atm.SetVSSpeed(c_int(self.Vshiftspeed_index)) #first parameter is for conventional mode electron multiplication, second parameter is for speed index (0-(getHSSpeed-1)
            print "Vshiftspeed set to %2f" % self.Vshiftspeed_value
            
    def setHshiftspeed(self,value=None):
        if value:
            value = int(value) #conversion to int as list[][] takes only int 
            self.Hshiftspeed_index = self.Hshiftspeed_data[value][0]
        self.Hshiftspeed_value = self.Hshiftspeed_data[self.Hshiftspeed_index][1]
        if self.simulation:
            print "simulation Hshiftspeed set to %2f" % self.Hshiftspeed_value
        else:
            self.atm.SetHSSpeed(c_int(0),c_int(self.Hshiftspeed_index))
            print "Hshiftspeed set to %2f" % self.Hshiftspeed_value

    def setreadmode(self,name=None):
        if name:
            self.readmode_name = name
        if self.readmode_name == "Full Vertical Binning":
            self.readmode_value = 0
        if self.readmode_name == "Image":
            self.readmode_value = 4
        if self.simulation:
            print "simulation readmode set to",self.readmode_name
        else:
            self.atm.SetReadMode(c_int(self.readmode_value)) #check if problem with ad channel check sdk
            if self.readmode_name == "Image":
                self.atm.SetImage(c_int(1),c_int(1),c_int(1),c_int(1024),c_int(1),c_int(256))
            print "readmode set to",self.readmode_name

    def setacquisitionmode(self,value=None):
        if value:
            self.acquistionmode = value
        if self.simulation:
            print "simulation Acquisitionmode"
        else:
            self.atm.SetAcquisitionMode(c_int(self.acquisitionmode))

if __name__ == "__main__":
    c = Camera()
    c.toggle_simulation()
    c.close()
