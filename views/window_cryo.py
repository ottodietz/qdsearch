from enthought.traits.api import*
from enthought.traits.ui.api import*
from traitsui.menu import OKButton, CancelButton

import control_cryo
reload (control_cryo)
from control_cryo import Cryo

class Mainwindow(HasTraits):
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

    position=Button()
    identity=Button()
    cal=Button()
    rm=Button()
    setzero=Button()




    checkbox=Bool(True, label="Simulation")

    x=0.1
    y=0.1

    traits_view=View(
                         VGroup(HGroup(Item("movex",resizable = True,label="x"),Item("movey",resizable = True,label="y"),Item("move",resizable=True,show_label=False)),
                            HGroup (Item("position", show_label=False,resizable = True),Spring(resizable = True), Item("identity", show_label=False,resizable = True)),
                            HGroup (Item("cal", show_label=False,resizable = True), Item("rm", show_label=False,resizable = True),Item("setzero", show_label=False,resizable = True)),
                            HGroup(Spring(resizable = True),Item("up", show_label=False, resizable = True),Spring(resizable = True)),
                            HGroup(Item("left",  resizable = True,show_label=False), Spring(resizable = True),Item("right", resizable = True, show_label=False)),
                            HGroup(Spring(resizable = True),Item("down", show_label=False, resizable = True),Spring(resizable = True)),
                            HGroup(Item("rmovex",label="x"),Item("rmovey",label="y"),Item("rmove",resizable=True,show_label=False))),
            Item("ausgabe",style="readonly"),
            Item("checkbox"),
            buttons = [OKButton, CancelButton,],
            resizable = True, width = 350, height = 300)

    def _identity_fired(self):
            self.ausgabe=self.cryo.ident()


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

    def _rmove_fired(self):
        self.x=self.rmovex
        self.y=self.rmovey
        self._postion_fired()


    def _move_fired(self):
            self.cryo.bewegen(self.movex,self.movey)
            self.ausgabe=self.cryo.posi()

    def _setzero_fired(self):
            self.cryo.setzero(self.movex,self.movey)
            self._postion_fired()


    def _checkbox_changed(self):
        self.cryo.toggle_simulation("Cryo")



main=Mainwindow()
main.configure_traits()
if main.cryo.simulation==0:
    print"schliessen"
    main.cryo.close()