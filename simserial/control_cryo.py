
from enthought.traits.api import*
from enthought.traits.ui.api import*

import SimSerial
reload(SimSerial)
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
        self.write("0 0 "+str(x)+" "+str(y)+" r \r")

    # direkte Bewegen
    def bewegen(self,x,y):
        self.write("0 0 "+str(x)+" "+str(y)+" m \r")

    # rangemeasure, postive Limits
    def rm(self):
        self.write("rm \r")

    # rangemeasure, negative Limits
    def cal(self):
        self.write("cal \r")


    # set current position
    def setzero(self,x,y):
        self.write("0 0 "+str(x)+" "+str(y)+" setpos \r")
        self.x = 0.0
        self.y = 0.0


