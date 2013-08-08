
from enthought.traits.api import*
from enthought.traits.ui.api import*
import pylab
import thread
import time

import control_camera
reload (control_camera)

from control_camera import Camera
from enthought.pyface.api import error,warning,information

class CameraGUIHandler(Handler):
    def close(self, info, isok):
        # Return True to indicate that it is OK to close the window.#
        if main.checkbox_camera:
            return True
        else:
            main.cooler=False
            if main.camera.gettemperature() >-1:
                return True
            else:
                print'Please wait until the temperature of the camera is above 0 degrees'

class CameraGUI(HasTraits):
    camera=Camera()

    checkbox_camera=Bool(True)
    cooler=Bool(False)

    plot=Button()
    acqusition=Button()
    temperature=Button()
    status=Button()
    settemperature=Button()
    inputtemperature=Int()

    output=Str()


    traits_view=View(VGroup(
                        HGroup(Item('acqusition'), Item('plot',show_label=False),Item('temperature',show_label=False)),
                        HGroup(Item('checkbox_camera',label='Simulation')),
                        HGroup(Item('status',show_label=False),Item('settemperature',show_label=False),Item('inputtemperature')),
                        HGroup(Item('cooler'),
                        HGroup(Item('output',show_label=False, style='readonly'))
                        )),
                        handler=CameraGUIHandler(),
                        resizable = True )

    def _acqusition_fired(self):
        """das hier in neuen thread auf zu machen funktioniert so nicht, da dann line leer
        Da nicht auf ende der funktion gewartet wird, muss anders gel?st werden"""
        if self.camera.init_active:
            information(parent=None, title="please wait", message="The initialization of the camera is running. Please wait until the initialization is finished.")
        else:
            self.line=self.camera.acqisition()


    def _plot_fired(self):
        pylab.plot(self.line[:])
        pylab.show()

    def _temperature_fired(self):
        if self.camera.init_active:
            information(parent=None, title="please wait", message="The initialization of the camera is running. Please wait until the initialization is finished.")
        else:
            self.camera.gettemperature()

    def _status_fired(self):
        self.camera.gettemperature_status()
        self.camera.gettemperature_range()

    def _settemperature_fired(self):
        self.camera.settemperature(self.inputtemperature)

    def _checkbox_camera_changed(self):
        if self.camera.init_active:
            information(parent=None, title="please wait", message="The initialization of the camera is running. Please wait until the initialization is finished.")
            self.change_checkbox()
        else:

            if self.checkbox_camera:
                self.cooler=False
                if self.camera.gettemperature() >-1:
                    thread.start_new_thread(self.camera.toggle_simulation,(self.checkbox_camera,))
                else:
                    print 'can not start simulation while temperature camera is under 0 degrees'
                    thread.start_new_thread(self.change_checkbox,())
            else:
                thread.start_new_thread(self.camera.toggle_simulation,(self.checkbox_camera,)) # if the simulation was runing it can be deactivate


    def change_checkbox(self):
        time.sleep(.2)
        self.checkbox_camera=False

    def _cooler_changed(self):
        if self.cooler:
            self.camera.cooler_on()
        else:
            self.camera.cooler_off()


if __name__=="__main__":
    main=CameraGUI()
    main.configure_traits()


