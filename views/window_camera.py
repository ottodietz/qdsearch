
from enthought.traits.api import*
from enthought.traits.ui.api import*
import pylab

import control_camera
reload (control_camera)

from control_camera import Camera
from enthought.pyface.api import error,warning,information

class CameraGUI(HasTraits):
    camera=Camera()

    checkbox_camera=Bool(True)

    plot=Button()
    acqusition=Button()
    temperature=Button()


    traits_view=View(VGroup(
                        HGroup(Item('acqusition'), Item('plot',show_label=False),Item('temperature',show_label=False)),
                        Item('checkbox_camera',label='Simulation')),
                        resizable = True )

    def _acqusition_fired(self):
        """das hier in neuen thread auf zu machen funktioniert so nicht, da dann line leer
        Da nicht auf ende der funktion gewartet wird, muss anders gel?st werden"""
        if self.camera.init_aktiv:
            information(parent=None, title="please wait", message="The initialization of the camera is running. Please wait until the initialization is finished.")
        else:
            self.line=self.camera.acqisition()

    def _checkbox_camera_changed(self):
        if self.camera.init_aktiv:
            information(parent=None, title="please wait", message="The initialization of the camera is running. Please wait until the initialization is finished.")
        else:
            thread.start_new_thread(self.camera.toggle_simulation,(self.checkbox_camera,))

    def _plot_fired(self):
        print self.line[:]
        pylab.plot(self.line[:])
        pylab.show()

    def _temperature_fired(self):
        if self.camera.init_aktiv:
            information(parent=None, title="please wait", message="The initialization of the camera is running. Please wait until the initialization is finished.")
        else:
            self.camera.temperature()





if __name__=="__main__":
    main=CameraGUI()
    main.configure_traits()
    if not main.checkbox_camera:
        print'close:',main.camera.close()