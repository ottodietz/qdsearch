
from enthought.traits.api import*
from enthought.traits.ui.api import*
import time


from SimSerial import SimSerial

class Cryo(SimSerial):
    commando_position="last"
    number_of_EOL=1 # if they are two characters written together (without space) it is one EOL

    def identify(self):
        self.flushInput()
        self.write("identify \r")
        temp=self.readline()
        return(temp)

    #simulation identify
    def _identify(self,string):
        self.buffer="identify"

    def position(self):
        self.flushInput()
        self.write("p \r")
        temp=self.readline()
        return(temp)

    #simulation position
    def _p(self,string):
        self.buffer="0 "+"0 "+str(self.posx)+" "+str(self.posy)+' '

    # relative move
    def rmove(self,x,y):
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
    def move(self,x,y):
        self.write("0 0 "+str(x)+" "+str(y)+" m \r")

    # simulation direct move
    def _m(self,string):
        a=string.find(" ")
        b=string.find(" ",a+1)
        c=string.find(" ",b+1)
        d=string.find(" ",c+1)
        self.posx=float(string[b:c])
        self.posy=float(string[c+1:d+1])

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
        return(int(tmp[0]))

    def _st(self,string):
        self.buffer='0'

    def stop(self):
        self.write('\x03 \r') #ctrl +c

    def convert_output(self,string):
        print string
        string=string.replace('    ','')
        a=string.find(" ")
        b=string.find(" ",a+1)
        c=string.find(" ",b+1)
        d=string.find(" ",c+1)
        x=float(string[b:c])
        y=float(string[c+1:d])
        return(x,y)

    def waiting(self):
        running=True
        while running :
            running=int(self.status())
            print 'waiting'
            time.sleep(0.5)
        print 'finished'












