
from traits.api import*
from traitsui.api import*
import time


from simserial import SimSerial

class Cryo(SimSerial):
    CMD = ''
    PARMS = ''
    EOL='\r'# if they are two characters written together (without space) it is one EOL

    def identify(self):
        self.flushInput()
        self.write("identify \r")
        temp=self.readline()
        return(temp)

    #simulation identify
    def _identify(self,string):
        self.buffer="identify"

    def pos(self):
        self.flushInput()
        self.write("p \r")
        string=self.readline()
        string=string.replace('    ','')
        string=string.split(' ')
        x=float(string[2])
        y=float(string[3])
        return x,y

    #simulation position
    def _p(self,string):
        self.buffer="0 "+"0 "+str(self.posx)+" "+str(self.posy)+' '

    # relative move
    def rmove(self,x,y):
        self.write("0 0 "+str(x)+" "+str(y)+" r \r")

    # simulation relativ move
    def _r(self,string):
        string=string.split(' ')
        self.posx+=float(string[2])
        self.posy+=float(string[3])

    # direct move
    def move(self,x,y):
        self.write("0 0 "+str(x)+" "+str(y)+" m \r")

    # simulation direct move
    def _m(self,string):
        string=string.split(' ')
        self.posx=float(string[2])
        self.posy=float(string[3])

    # rangemeasure, postive Limits
    def rm(self):
        self.write("rm \r")

    # rangemeasure, negative Limits
    def cal(self):
        self.write("cal \r")

    # set current position
    def setpos(self,x,y):
        self.write("0 0 "+str(x)+" "+str(y)+" setpos \r")

    def _setpos(self,string):
        self.posx = 0.0
        self.posy = 0.0

    def status(self):
        """0 if cryo is finished and 1 if it is working. Number is saved in the first character [0]."""
        self.flushInput()
        self.write('st \r')
        tmp=self.readline()
        return  int(tmp[0])

    def _st(self,string):
        self.buffer='0'

    def stop(self):
        self.write('\x03 \r') #ctrl +c

    def waiting(self):
        running=True
        while running :
            running=int(self.status())
            time.sleep(0.5)












