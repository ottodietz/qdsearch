
from enthought.traits.api import*
from enthought.traits.ui.api import*
import pylab

import control_camera
reload (control_camera)

from control_camera import Camera

class CameraGUI(HasTraits):
    camera=Camera()

    textfield=Str()
    x1=CFloat()
    x2=CFloat()
    y1=CFloat()
    y2=CFloat()

    checkbox_camera=Bool(True)

    scan_sample=Button()
    plot=Button()
    acqusition=Button()

    traits_view=View(VGroup(
                        HGroup(Item('textfield',label='Ausdehnung der Probe',style='readonly')),
                        HGroup(Item('x1'),Item('x2')),
                        HGroup(Item('y1'),Item('y2')),
                        HGroup(Item('scan_sample',show_label=False))),
                        HGroup(Item('acqusition'), Item('plot',show_label=False)),
                        Item('checkbox_camera',label='Simulation'),
                        resizable = True )

    def _acqusition_fired(self):
        print'pass auf self.line auf, line ist nirgends vorher deffiniert!!!'
        self.line=self.camera.acqisition()

    def _checkbox_camera_changed(self):
        self.camera.toggle_simulation(self.checkbox_camera)

    def _plot_fired(self):
        print self.line[:]
        pylab.plot(self.line[:])
        pylab.show()








if __name__=="__main__":
    main=CameraGUI()
    main.configure_traits()