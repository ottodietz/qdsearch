
from enthought.traits.api import*
from enthought.traits.ui.api import*
from traitsui.menu import OKButton, CancelButton
from SimSerial import SimSerial

class Cryo(SimSerial):

    def ident(self):
        self.write("identify \r")
        temp=self.readline()
        return(temp)

    def posi(self):
        self.write("p \r")
        temp=self.readline()
        return(temp)

    # Relative Bewegung
    def rbewegen(self,x,y):
        self.write(str(x)+" "+str(y)+" "+"0 0 r \r")

    # direkte Bewegen
    def bewegen(self,x,y):
        self.write(str(x)+" "+str(y)+" "+"0 0 m \r")


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

    position=Button()
    identity=Button()



    checkbox=Bool(True, label="Simulation")

    x=0.1
    y=0.1

    traits_view=View(
                         VGroup(HGroup(Item("movex",resizable = True,label="x"),Item("movey",resizable = True,label="y"),Item("move",resizable=True,show_label=False)),
                            HGroup (Item("position", show_label=False,resizable = True),Spring(resizable = True), Item("identity", show_label=False,resizable = True)),
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


    def _up_fired(self):
            self.cryo.rbewegen(0,self.y)


    def _down_fired(self):
            self.cryo.rbewegen(0,-self.y)


    def _left_fired(self):
          self.cryo.rbewegen(-self.x,0)


    def _right_fired(self):
            self.cryo.rbewegen(self.x,0)

    def _rmove_fired(self):
        self.x=self.rmovex
        self.y=self.rmovey


    def _move_fired(self):
            self.cryo.bewegen(self.movex,self.movey)


    def _checkbox_changed(self):
        self.cryo.toggle_simulation("Cryo")



main=CryoGUI()
main.configure_traits()
if main.cryo.simulation==0:
    print"schliessen"
    main.cryo.close()
