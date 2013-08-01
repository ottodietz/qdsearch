
from enthought.traits.api import*
from enthought.traits.ui.api import*
import pylab
import thread

import control_camera
reload (control_camera)

from control_camera import Camera
from enthought.pyface.api import error,warning,information

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
                        resizable = True )

    def _acqusition_fired(self):
        """das hier in neuen thread auf zu machen funktioniert so nicht, da dann line leer
        Da nicht auf ende der funktion gewartet wird, muss anders gel?st werden"""
        if self.camera.init_active:
            information(parent=None, title="please wait", message="The initialization of the camera is running. Please wait until the initialization is finished.")
        else:
            self.line=self.camera.acqisition()


    def _plot_fired(self):
        print self.line[:]
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
        else:
            if checkbox_camera:
                cooler=False
            thread.start_new_thread(self.camera.toggle_simulation,(self.checkbox_camera,))

    def _cooler_changed(self):
        if self.cooler:
            self.camera.cooler_on()
        else:
            self.camera.cooler_off()





if __name__=="__main__":
    main=CameraGUI()
    main.configure_traits()
    while main.camera.camera_active:
        thread.start_new_thread(main.camera.closing_camera,())


