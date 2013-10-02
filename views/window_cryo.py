from traits.api import*
from traitsui.api import*
from traitsui.menu import OKButton, CancelButton
from pyface.api import confirm,ImageResource
import time
import thread

import control_cryo
reload (control_cryo)
from control_cryo import Cryo


class CryoGUI(HasTraits):
    call_menu_cryo = Action(name='cryo menu', accelerator='Ctrl+c', action='call_cryo_menu')
    menu =    Menu(call_menu_cryo,name='Cryo')
    cryo=Cryo('COM3', 9600, timeout=1)
    cryo_refresh=True

    output=Str()
    movex=CFloat(1.0)
    movey=CFloat(1.0)
    move=Button()

    #Felder und Button f?r die relaitve Bewegung
    #einstellen der schrittweite
    rmovex=CFloat(0.01)
    rmovey=CFloat(0.01)
    rmove=Button()
    up=Button(label='^')
    down=Button(label='v')
    right=Button(label='>')
    left=Button(label='<')
    northwest=Button('^<')
    southwest=Button(label='v<')
    northeast=Button(label='^>')
    southeast=Button(label='v>')
    upup=Button(label='^^')
    downdown=Button(label='vv')
    leftleft=Button(label='<<')
    rightright=Button(label='>>')
    factor1=CInt(10,desc='defines the factor between a normal relativ move and a wide relativ move')


    position=Button()
    identity=Button()
    cal=Button()
    rm=Button()
    setzero=Button()
    stop=Button()
    status=Button()





    checkbox=Bool(True, label="Simulation")

    x=0.1
    y=0.1

    traits_view=View(
                         VGroup(HGroup(Item("movex",resizable = True,label="x"),Item("movey",resizable = True,label="y"),Item("move",resizable=True,show_label=False)),
                            HGroup(Item("upup", show_label=False, resizable = True)),
                            HGroup(Item('northwest',show_label=False,resizable = True,),Item("up", show_label=False, resizable = True),Item('northeast',show_label=False,resizable = True,)),
                            HGroup(Item("leftleft",  resizable = True,show_label=False,), Item("left",  resizable = True,show_label=False,), Item("position", show_label=False,resizable = True),Item("right", resizable = True, show_label=False,), Item("rightright", resizable = True, show_label=False)),
                            HGroup(Item('southwest',show_label=False,resizable = True,),Item("down", show_label=False, resizable = True,),Item('southeast',show_label=False,resizable = True,)),
                            HGroup(Item("downdown", show_label=False, resizable = True,)),
                            HGroup(Item("rmovex",label="x"),Item("rmovey",label="y"),Item("rmove",resizable=True,show_label=False)),
                            HGroup(Item('stop',show_label=False,resizable=True),Item('status',show_label=False,resizable=True))),
                            HGroup (Spring(height=20)),
            Item("output",style="readonly"),
            HGroup(Item("checkbox"),Spring(width=350)),
            buttons = [OKButton, CancelButton,],
                        menubar=MenuBar(menu),
            resizable = True, width = 400, height = 400)

    view_menu=View(VGroup(HGroup(Item("cal", show_label=False,resizable = True), Item("rm", show_label=False,resizable = True),Item("setzero", show_label=False,resizable = True)),
                    HGroup(Item("rmovex",label="x"),Item("rmovey",label="y"),Item("rmove",resizable=True,show_label=False)),
                    HGroup(Item('factor1',label='Step range factor')),
                    HGroup(Item("identity", show_label=False,resizable = True))
                                  ),
                    buttons = [OKButton, CancelButton,],
            resizable = True, width = 400, height = 200,
            kind='livemodal'
         )

    def __init__(self):
        pass
        #thread.start_new_thread(self.refresh_cryo_gui,())

    def _identity_fired(self):
        self.output=self.cryo.identify()


    def _position_fired(self):
        self.output=self.cryo.position()

    def _cal_fired(self):
        self.output=self.cryo.cal()

    def _rm_fired(self):
        self.output=self.cryo.rm()

    def _up_fired(self):
        self.cryo.rmove(0,self.y)

    def _down_fired(self):
        self.cryo.rmove(0,-self.y)

    def _left_fired(self):
        self.cryo.rmove(-self.x,0)

    def _right_fired(self):
        self.cryo.rmove(self.x,0)

    def _northwest_fired(self):
        self.cryo.rmove(-self.x,self.y)

    def _northeast_fired(self):
        self.cryo.rmove(self.x,self.y)

    def _southwest_fired(self):
        self.cryo.rmove(-self.x,-self.y)


    def _southeast_fired(self):
        self.cryo.rmove(self.x,-self.y)


    def _downdown_fired(self):
        self.cryo.rmove(0,-self.y*self.factor1)

    def _leftleft_fired(self):
          self.cryo.rmove(-self.x*self.factor1,0)

    def _rightright_fired(self):
        self.cryo.rmove(self.x*self.factor1,0)

    def _upup_fired(self):
        self.cryo.rmove(0,self.y*self.factor1)

    def _rmove_fired(self):
        self.x=self.rmovex
        self.y=self.rmovey

    def _move_fired(self):
        self.cryo.move(self.movex,self.movey)

    def _setzero_fired(self):
        answer=confirm(parent=None, title="confirmation", message="You want to set a new point of origin. All previous coordinates can be become useless. Do you want to continue?  ")
        # confirm gives a 40 for no and 30 for firing yes
        if answer==30:
            self.cryo.setpos(self.movex,self.movey)

    def _stop_fired(self):
        self.cryo.stop()

    def _status_fired(self):
        self.output=str(self.cryo.status())

    def _checkbox_changed(self):
        self.cryo.toggle_simulation()
        if not self.checkbox:
            position=self.cryo.position()
            [self.movex,self.movey]=self.cryo.convert_output(position)

    def refresh_cryo_gui(self):
        while self.cryo_refresh:
            try:
                self.output=self.cryo.position()
            except:
                pass
            time.sleep(2)

    def call_cryo_menu(self):
       self.configure_traits(view='view_menu')


if __name__=="__main__":
    main=CryoGUI()
    main.configure_traits()
    if not main.cryo.simulation:
        print"close cryo"
        main.cryo.close()
        main.cryo.cryo_refresh=False
