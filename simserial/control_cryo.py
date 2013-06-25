
from enthought.traits.api import*
from enthought.traits.ui.api import*

import SimSerial
reload(SimSerial)
from SimSerial import SimSerial

class Cryo(SimSerial):
    device="cryo"
    # names of the device functions
    functionnames=['identify','rm','calc','p','r','m','testingname']
    # the end of line command for the functions
    endofline=[' \r',' \r',' \r',' \r',' \r',' \r']

   # registersimfunc('identify',_identify)
    def identify(self):
        self.write("identify \r")
        temp=self.readline()
        return(temp)

    def posi(self):
        self.write("p \r")
        temp=self.readline()
        return(temp)

    # relative Bewegung
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


    """for simulation"""

    def _identify(self):
        self.buffer="identify"

    def _m(self,string):
        a=string.find(" ")
        b=string.find(" ",a+1)
        c=string.find(" ",b+1)
        d=string.find(" ",c+1)
        self.posx=float(string[b:c])
        self.posy=float(string[c+1:d])

    def _p(self):
        self.buffer=str(self.posx)+" "+str(self.posy)

    def _r(self,string):
        a=string.find(" ")
        b=string.find(" ",a+1)
        c=string.find(" ",b+1)
        d=string.find(" ",c+1)
        self.posx+=float(string[b:c])
        self.posy+=float(string[c+1:d])




