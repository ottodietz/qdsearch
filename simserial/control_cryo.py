
from enthought.traits.api import*
from enthought.traits.ui.api import*

import SimSerial
reload(SimSerial)
from SimSerial import SimSerial

class Cryo(SimSerial):
    new_simulation=True
    commando_position="last"
    number_of_EOL=1 # if they are two characters written together (without space) it is one EOL

    def identify(self):
        self.write("identify \r")
        temp=self.readline()
        return(temp)

    #simulation identify
    def _identify(self,string):
        self.buffer="identify"

    def posi(self):
        self.write("p \r")
        temp=self.readline()
        return(temp)

    #simulation position
    def _p(self,string):
        self.buffer=str(self.posx)+" "+str(self.posy)

    # relative move
    def rbewegen(self,x,y):
        self.write("0 0 "+str(x)+" "+str(y)+" r \r")

    # simulation relativ move
    def _r(self,string):
        a=string.find(" ")
        b=string.find(" ",a+1)
        c=string.find(" ",b+1)
        d=string.find(" ",c+1)
        self.posx+=float(string[b:c])
        self.posy+=float(string[c+1:d])

    # direct move
    def bewegen(self,x,y):
        self.write("0 0 "+str(x)+" "+str(y)+" m \r")

    # simulation direct move
    def _m(self,string):
        a=string.find(" ")
        b=string.find(" ",a+1)
        c=string.find(" ",b+1)
        d=string.find(" ",c+1)
        self.posx=float(string[b:c])
        self.posy=float(string[c+1:d])

    # rangemeasure, postive Limits
    def rm(self):
        self.write("rm \r")

    # rangemeasure, negative Limits
    def cal(self):
        self.write("cal \r")


    # set current position
    def setzero(self,x,y):
        self.write("0 0 "+str(x)+" "+str(y)+" setpos \r")

    def _setpos(self,string):
        self.posx = 0.0
        self.posy = 0.0








