
from traits.api import*
from traitsui.api import*
from traitsui.menu import OKButton, CancelButton
import pylab
import thread
import time
from ctypes import *

import control_camera
reload (control_camera)

from control_camera import Camera
from pyface.api import error,warning,information

class CameraGUIHandler(Handler):
    def close(self, info, isok):
        if info.object.checkbox_camera:
            return True
        else:
            info.object.cooler=False
            if info.object.camera.gettemperature() >-1:
                return True
            else:
                information(parent=None, title="please wait", message="Please wait until the temperature of the camera is above 0 degrees.")


class CameraGUI(HasTraits):
    camera=Camera()
    iCameraGUIHandler = CameraGUIHandler()

    checkbox_camera=Bool(True)
    cooler=Bool(False)
    plot=Button()
    acquisition=Button()
    temperature=Button()
    status=Button()
    temperature=Range(low=-70,high=20,value=20)

    """menu"""
    readmode=Int(0)
    acquisitionmode=Int(1)
    exposuretime=Range(low=0.0001,high=10,value=0.1)
    output=Str()


    def _acquisition_fired(self):
        if self.camera.init_active:
            information(parent=None, title="please wait", message="The initialization of the camera is running. Please wait until the initialization is finished.")
            while self.camera.init_active:
                time.sleep(.5)
        else:
            self.line=self.camera.acquisition()


    def _plot_fired(self):
        pylab.plot(self.line[:])
        pylab.show()

    def _temperature_fired(self):
        if self.camera.init_active:
            information(parent=None, title="please wait", message="The initialization of the camera is running. Please wait until the initialization is finished.")
        else:
            self.temperature=self.camera.gettemperature()

    def _status_fired(self):
        self.camera.gettemperature_status()
        self.camera.gettemperature_range()
        self.temperature = self.camera.gettemperature()


    def _settemperature_fired(self):
        self.camera.settemperature(self.temperature)

    def _checkbox_camera_changed(self):
        if self.camera.init_active:
            information(parent=None, title="please wait", message="The initialization of the camera is running. Please wait until the initialization is finished.")
            self.change_checkbox()
        else:

            if self.checkbox_camera:
                self.cooler=False
                if self.camera.gettemperature() >-1:
                    thread.start_new_thread(self.camera.toggle_simulation,(self.checkbox_camera))
                else:
                    information(parent=None, title="please wait", message="Please wait until the temperature of the camera is above 0 degrees.")
                    thread.start_new_thread(self.change_checkbox,())
            else:
                thread.start_new_thread(self.camera.toggle_simulation,(self.checkbox_camera)) # if the simulation was runing it can be deactivate


    def change_checkbox(self):
        time.sleep(.2)
        self.checkbox_camera=False

    def _cooler_changed(self):
        if self.cooler:
            self.camera.cooler_on()
        else:
            self.camera.cooler_off()

    def _readmode_changed(self):
       self.camera.readmode=c_long(self.readmode)
       print "readmode changed"

    def _acquisitionmode_changed(self):
       self.camera.acquisitionmode=c_long(self.acquisitionmode)
       print "readmode changed"

    def _exposuretime_changed(self):
       self.camera.exposuretime=c_float(self.exposuretime)
       print "readmode changed"

    def call_menu(self):
       self.configure_traits(view='menu_view')

    menu_view=View(VGroup(
                        HGroup(Item('acquisition',show_label=False), Item('plot',show_label=False)),
                        HGroup(Item('temperature'),Item('status',show_label=False)),
                        HGroup(Item('cooler'),Item('checkbox_camera',label='Simulation camera')),
                        HGroup(Item('output',label='Camera output',
                            style='readonly')),
                        VGroup(Item('readmode'),Item('acquisitionmode'),Item('exposuretime'))
                        ),
                        handler=iCameraGUIHandler,
                        resizable = True )

    menu_action = Action(name='camera menu', accelerator='Ctrl+p', action='call_menu')

    menu=Menu(menu_action,name='Camera')


    traits_view=View(VGroup(
                        HGroup(Item('acquisition',label='Single',show_label=False),Item('plot',show_label=False)),
                        Item('exposuretime'),
                        HGroup(Item('checkbox_camera',label='Simulation camera')),
                        HGroup(Item('output',label='Camera output', style='readonly'))
                       ),
                       handler=iCameraGUIHandler,
                       resizable = True, menubar=MenuBar(menu) )


if __name__=="__main__":
    main=CameraGUI()
    main.configure_traits()

