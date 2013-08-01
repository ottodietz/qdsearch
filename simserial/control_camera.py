from ctypes import *
import thread


class Camera():
    totalCameras=c_long()
    init_active=False
    camera_active=False
    low_temperature=False

    def toggle_simulation(self,simulation):
        self.init_active=True
        if simulation:
            self.closing_camera()
        if not simulation:
            self.atm=WinDLL("C:\Program Files\Andor SOLIS\ATMCD32D.DLL")
            self.camera_active=True
            print "Init:", self.atm.Initialize(None)
            print "GetAvailableCameras:",self.atm.GetAvailableCameras(byref(self.totalCameras))
            print "SetReadMode:",self.atm.SetReadMode(0) #FullverticalBinning
            print "SetAcqMode:",self.atm.SetAcquisitionMode(1) # single shoot
            print "SetExpTime:",self.atm.SetExposureTime(c_float(0.1)) #Belichtungsdauer
        self.init_active=False


    def acqisition(self):
        pixel=1024
        line  = (c_long * pixel)()
        print "StartAcq:",self.atm.StartAcquisition()
        print "Wait:",self.atm.WaitForAcquisition()
        print "GetMostRecentImage",self.atm.GetMostRecentImage(byref(line),c_ulong(pixel))
        return(line)

    def close(self):
        print "ShutDown:", self.atm.ShutDown()
        self.camera_active=False

    def gettemperature(self):
        temperature=c_long()
        print 'GetTemperature', self.atm.GetTemperature(byref(temperature))
        print temperature.value
        return(temperature.value)

    def cooler_on(self):
        print 'Cooler on:',self.atm.CoolerON()

    def cooler_off(self):
        print 'Cooler off:',self.atm.CoolerOFF()

    def gettemperature_range(self):
        mintemp=c_long()
        maxtemp=c_long()
        print 'Gettemperature_range:', self.atm.GetTemperatureRange(byref(mintemp),byref(maxtemp))
        print 'min temp' ,
        print mintemp
        print 'maxtemp' ,
        print maxtemp

    def settemperature(self,temperature):
        print 'settemperature', self.atm.SetTemperature(temperature)

    def gettemperature_status(self):
        sensortemp=c_float()
        targettemp=c_float()
        AmbientTemp=c_float()
        cooler_volt=c_float()
        print'temperautre_status:', self.atm.GetTemperatureStatus(byref(sensortemp),byref(targettemp),byref(AmbientTemp),byref(cooler_volt))
        print 'sensortemp:',
        print sensortemp
        print 'targettemp',
        print targettemp

    def closing_camera():
        print 'closing camera start'
        temperature=self.gettemperature()
        while temperature<-1:
            self.low_temperature=True
            time.sleep(30)
            temperature=self.gettemperature()
        self.low_temperature=False
        self.close()



