#!/usr/bin/env python
# -*- coding: utf-8 -*-
from traits.util.refresh import refresh

from traits.api import *
from traitsui.api import *

import views.cryo

import views.spectrometer

import views.camera

import views.voltage
refresh (views.voltage)

class MainWindow(HasTraits):

    ispectrometer = Instance(views.spectrometer.SpectrometerGUI,() ) 
    icryo         = Instance(views.cryo.CryoGUI,())
    ivoltage      = Instance(views.voltage.VoltageGUI)

    icamera       = Instance(views.camera.CameraGUI)# No ",()" as below, Instance is created in _default


    def _icamera_default(self):
        print "CAMERA INIT"
        return views.camera.CameraGUI(icryo=self.icryo, ivoltage=self.ivoltage)
#### kann das hier noch raus? oder für später wichtig?

    def _ivoltage_default(self):
        print "VOLTAGE INIT"
        temp = views.voltage.VoltageGUI()
        try:
            temp.ivoltage.blink()
        except:
            import sys
            print sys.exc_info()
        print temp
        return temp

main = MainWindow()
if __name__ == '__main__':
    main.configure_traits(scrollable = True)
    main.icamera.close()


