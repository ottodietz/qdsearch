from enthought.traits.api import*
from enthought.traits.ui.api import*
from traitsui.menu import OKButton, CancelButton
from enthought.pyface.api import confirm,ImageResource

import control_cryo
reload (control_cryo)
from control_cryo import Cryo


class CryoGUI(HasTraits):
    cryo=Cryo('COM3', 9600, timeout=1)

    output=Str()
    movex=CFloat(1.0)
    movey=CFloat(1.0)
    move=Button()

    #Felder und Button f?r die relaitve Bewegung
    #einstellen der schrittweite
    rmovex=CFloat(0.1)
    rmovey=CFloat(0.1)
    rmove=Button()
    up=Button(image=ImageResource('image_cryo/up.png'))
    down=Button(image=ImageResource('image_cryo/down.png'))
    right=Button(image=ImageResource('image_cryo/right.png'))
    left=Button(image=ImageResource('image_cryo/left.png'))
    northwest=Button(image=ImageResource('image_cryo/northwest'))
    southwest=Button(image=ImageResource('image_cryo/southwest'))
    northeast=Button(image=ImageResource('image_cryo/northeast'))
    southeast=Button(image=ImageResource('image_cryo/southeast'))
    upup=Button(image=ImageResource('image_cryo/upup'))
    downdown=Button(image=ImageResource('image_cryo/downdown.png'))
    leftleft=Button(image=ImageResource('image_cryo/leftleft.png'))
    rightright=Button(image=ImageResource('image_cryo/rightright.png'))
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
                            HGroup(Item("upup", show_label=False, resizable = True,style='custom')),
                            HGroup(Item('northwest',show_label=False,resizable = True,style='custom'),Item("up", show_label=False, resizable = True,style='custom'),Item('northeast',show_label=False,resizable = True,style='custom')),
                            HGroup(Item("leftleft",  resizable = True,show_label=False,style='custom'), Item("left",  resizable = True,show_label=False,style='custom'), Item("position", show_label=False,resizable = True),Item("right", resizable = True, show_label=False,style='custom'),Item("rightright",style='custom', resizable = True, show_label=False)),
                            HGroup(Item('southwest',show_label=False,resizable = True,style='custom'),Item("down", show_label=False, resizable = True,style='custom'),Item('southeast',show_label=False,resizable = True,style='custom')),
                            HGroup(Item("downdown", show_label=False, resizable = True,style='custom')),
                            HGroup(Item("rmovex",label="x"),Item("rmovey",label="y"),Item("rmove",resizable=True,show_label=False)),
                            HGroup(Item('stop',show_label=False,resizable=True),Item('status',show_label=False,resizable=True))),
                            HGroup (Spring(height=20)),
            Item("output",style="readonly"),
            HGroup(Item("checkbox"),Spring(width=350)),
            buttons = [OKButton, CancelButton,],
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
        self._position_fired()

    def _down_fired(self):
        self.cryo.rmove(0,-self.y)
        self._position_fired()

    def _left_fired(self):
        self.cryo.rmove(-self.x,0)
        self._position_fired()


    def _right_fired(self):
        self.cryo.rmove(self.x,0)
        self._position_fired()

    def _northwest_fired(self):
        self.cryo.rmove(-self.x,self.y)
        self._position_fired()


    def _northeast_fired(self):
        self.cryo.rmove(self.x,self.y)
        self._position_fired()


    def _southwest_fired(self):
        self.cryo.rmove(-self.x,-self.y)
        self._position_fired()


    def _southeast_fired(self):
        self.cryo.rmove(self.x,-self.y)
        self._position_fired()


    def _downdown_fired(self):
        self.cryo.rmove(0,-self.y*self.factor1)
        self._position_fired()

    def _leftleft_fired(self):
          self.cryo.rmove(-self.x*self.factor1,0)
          self._position_fired()

    def _rightright_fired(self):
        self.cryo.rmove(self.x*self.factor1,0)
        self._position_fired()

    def _upup_fired(self):
        self.cryo.rmove(0,self.y*self.factor1)
        self._position_fired()

    def _rmove_fired(self):
        self.x=self.rmovex
        self.y=self.rmovey

    def _move_fired(self):
        self.cryo.move(self.movex,self.movey)
        self.output=self.cryo.position()

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
            self.refresh_cryo_gui()

    def refresh_cryo_gui(self):
        position=self.cryo.position()
        [self.movex,self.movey]=self.cryo.convert_output(position)


if __name__=="__main__":
    main=CryoGUI()
    main.configure_traits()
    if not main.cryo.simulation:
        print"close cryo"
        main.cryo.close()

