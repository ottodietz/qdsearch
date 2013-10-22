from traits.api import*
from traitsui.api import*
from traitsui.menu import OKButton, CancelButton
from pyface.api import confirm,ImageResource
import time
import thread

import controls.cryo as control_cryo
reload (control_cryo)
from controls.cryo import Cryo


class CryoGUI(HasTraits):
    mi_cryo = Action(name='cryo menu', accelerator='Ctrl+c', action='call_cryo_menu')
    menu =    Menu(mi_cryo,name='Cryo')
    cryo=Cryo('COM3', 9600, timeout=1)
    cryo_refresh=True

    output=Str()
    move=Button()

    #Felder und Button f?r die relaitve Bewegung
    #einstellen der schrittweite
#    rmovex=CFloat(0.01)
#    rmovey=CFloat(0.01)
#    rmove=Button()
    setstepsize=Button()

    up=Button(label=u'\u2191')
    down=Button(label=u'\u2193')

    factor1=CInt(10,desc='defines the factor between a normal relativ move and a wide relativ move')
    x_step=Float(0.1)
    y_step=Float(0.1)

    traits_view=View(
      VGroup(
       Item("up", show_label=False, resizable = True), Item("down", show_label=False, resizable = True)),

       HGroup(Spring(height=20)),
       Item("output",style="readonly"),
       buttons = [OKButton, CancelButton,],
       resizable = True, width = 400, height = 400)

    view_menu=View(
        VGroup(
         HGroup(Item("cal", show_label=False,resizable = True), Item("rm", show_label=False,resizable = True),Item("setzero", show_label=False,resizable = True)),
         
         HGroup(Item("identity", show_label=False,resizable = True))
         ),
        buttons = [OKButton, CancelButton,], resizable = True, width = 400, height = 200, kind='livemodal'
       )

    def __init__(self):
        pass
        #thread.start_new_thread(self.refresh_cryo_gui,())

    def _identity_fired(self):
        self.output=self.cryo.identify()


    def _position_fired(self):
        self.output=str(self.cryo.pos())

    def _cal_fired(self):
        self.output=self.cryo.cal()

    def _rm_fired(self):
        self.output=self.cryo.rm()

    def _up_fired(self):
        self.cryo.rmove(0,self.y_step)

    def _down_fired(self):
        self.cryo.rmove(0,-self.y_step)

if __name__=="__main__":
    main=CryoGUI()
    main.configure_traits()
    if not main.cryo.simulation:
        print"close cryo"
        main.cryo.close()
        main.cryo.cryo_refresh=False
