from ctypes import *
import thread


class Camera():
    totalCameras=c_long()
    init_aktiv=False

    def toggle_simulation(self,simulation):
        self.init_aktiv=True
        if simulation:
            self.close()
        if not simulation:
            self.atm=WinDLL("C:\Program Files\Andor SOLIS\ATMCD32D.DLL")
            print "Init:", self.atm.Initialize(None)
            print "GetAvailableCameras:",self.atm.GetAvailableCameras(byref(self.totalCameras))
            print "SetReadMode:",self.atm.SetReadMode(0) #FullverticalBinning
            print "SetAcqMode:",self.atm.SetAcquisitionMode(1) # single shoot
            print "SetExpTime:",self.atm.SetExposureTime(c_float(0.1)) #Belichtungsdauer
        self.init_aktiv=False


    def acqisition(self):
        pixel=1024
        line  = (c_long * pixel)()
        print "StartAcq:",self.atm.StartAcquisition()
        print "Wait:",self.atm.WaitForAcquisition()
        print "GetMostRecentImage",self.atm.GetMostRecentImage(byref(line),c_ulong(pixel))
        return(line)

    def close(self):
        print "ShutDown:", self.atm.ShutDown()

    def temperature(self):
        temperature=int()
        print 'GetTemperature', self.atm.GetTemperature(byref(temperature))
        print temperature
