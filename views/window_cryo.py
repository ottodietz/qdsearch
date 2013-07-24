from enthought.traits.api import*
from enthought.traits.ui.api import*
from traitsui.menu import OKButton, CancelButton

import control_cryo
reload (control_cryo)
from control_cryo import Cryo


class CryoGUI(HasTraits):
    cryo=Cryo('COM3', 9600, timeout=1)

    ausgabe=Str()
    # Felder und Button zur direkten Bewegung
    movex=CFloat(1.0)
    movey=CFloat(1.0)
    move=Button()

    #Felder und Button f?r die relaitve Bewegung
    #einstellen der schrittweite
    rmovex=CFloat(0.1)
    rmovey=CFloat(0.1)
    rmove=Button()
    # Buttons

    up=Button(label="^")
    down=Button(label="v")
    right=Button(label=">")
    left=Button(label="<")
    northwest=Button(label='^<')
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
                            HGroup (Item("position", show_label=False,resizable = True),Spring(resizable = True), Item("identity", show_label=False,resizable = True)),
                            HGroup (Item("cal", show_label=False,resizable = True), Item("rm", show_label=False,resizable = True),Item("setzero", show_label=False,resizable = True)),
                            HGroup(Item("upup", show_label=False, resizable = True)),
                            HGroup(Item('northwest',show_label=False,resizable = True),Item("up", show_label=False, resizable = True),Item('northeast',show_label=False,resizable = True)),
                            HGroup(Item("leftleft",  resizable = True,show_label=False), Item("left",  resizable = True,show_label=False), Spring(resizable = True),Item("right", resizable = True, show_label=False),Item("rightright", resizable = True, show_label=False)),
                            HGroup(Item('southwest',show_label=False,resizable = True),Item("down", show_label=False, resizable = True),Item('southeast',show_label=False,resizable = True)),
                            HGroup(Item("downdown", show_label=False, resizable = True)),
                            HGroup(Item("rmovex",label="x"),Item("rmovey",label="y"),Item("rmove",resizable=True,show_label=False)),
                            HGroup(Item('stop',show_label=False,resizable=True),Item('status',show_label=False,resizable=True))),
            Item("ausgabe",style="readonly"),
            Item("checkbox"),
            buttons = [OKButton, CancelButton,],
            resizable = True, width = 400, height = 400)

    view_menu=View(VGroup(HGroup(Item("cal", show_label=False,resizable = True), Item("rm", show_label=False,resizable = True),Item("setzero", show_label=False,resizable = True)),
                    HGroup(Item("rmovex",label="x"),Item("rmovey",label="y"),Item("rmove",resizable=True,show_label=False)),
                    HGroup(Item('factor1',label='Step range factor'))
                    ),
                    buttons = [OKButton, CancelButton,],
            resizable = True, width = 400, height = 150,
            kind='livemodal'
         )

    def _identity_fired(self):
        self.ausgabe=self.cryo.identify()


    def _position_fired(self):
        self.ausgabe=self.cryo.posi()

    def _cal_fired(self):
        self.ausgabe=self.cryo.cal()

    def _rm_fired(self):
        self.ausgabe=self.cryo.rm()

    def _up_fired(self):
        self.cryo.rbewegen(0,self.y)
        self._position_fired()

    def _down_fired(self):
        self.cryo.rbewegen(0,-self.y)
        self._position_fired()

    def _left_fired(self):
        self.cryo.rbewegen(-self.x,0)
        self._position_fired()


    def _right_fired(self):
        self.cryo.rbewegen(self.x,0)
        self._position_fired()

    def _northwest_fired(self):
        self.cryo.rbewegen(-self.x,self.y)
        self._position_fired()


    def _northeast_fired(self):
        self.cryo.rbewegen(self.x,self.y)
        self._position_fired()


    def _southwest_fired(self):
        self.cryo.rbewegen(-self.x,-self.y)
        self._position_fired()


    def _southeast_fired(self):
        self.cryo.rbewegen(self.x,-self.y)
        self._position_fired()


    def _downdown_fired(self):
        self.cryo.rbewegen(0,-self.y*self.factor1)
        self._position_fired()

    def _leftleft_fired(self):
          self.cryo.rbewegen(-self.x*self.factor1,0)
          self._position_fired()

    def _rightright_fired(self):
        self.cryo.rbewegen(self.x*self.factor1,0)
        self._position_fired()

    def _upup_fired(self):
        self.cryo.rbewegen(0,self.y*self.factor1)
        self._position_fired()

    def _rmove_fired(self):
        self.x=self.rmovex
        self.y=self.rmovey

    def _move_fired(self):
        self.cryo.bewegen(self.movex,self.movey)
        self.ausgabe=self.cryo.posi()

    def _setzero_fired(self):
        self.cryo.setpos(self.movex,self.movey)

    def _stop_fired(self):
        self.cryo.stop()

    def _status_fired(self):
        self.ausgabe=self.cryo.status()

    def _checkbox_changed(self):
        self.cryo.toggle_simulation("Cryo")
        if not self.cryo.checkbox:
            self.refresh_cryo_gui()

    def refresh_cryo_gui(self):
        position=self.cryo.posi()
        [self.movex,self.movey]=self.cryo.convert_output(position)


if __name__=="__main__":
    main=CryoGUI()
    main.configure_traits()
    if main.cryo.simulation==0:
        print"schliessen cryo"
        main.cryo.close()

