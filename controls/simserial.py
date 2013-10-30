import serial
import time
import re

class SimSerial(serial.Serial):
    CMD = None
    device=""
    number_of_EOL=str
    EOL=''

    simulation=True
    initargs=str()
    initkwargs=str()
    buffer=str()
    posx=float(1.0)
    posy=float(1.0)

    def __init__(self,*args,**kwargs):
        self.initkwargs=kwargs
        self.initargs=args

    def toggle_simulation(self):
        """ toggle simulation of serial device. Returns new state of simulation """
        temp = True
        if self.simulation:
            temp=False
            try:
                serial.Serial.__init__(self, *self.initargs, **self.initkwargs)
                print("simulation off")
            except:
                temp=True
                print("couldn't switch simulation off")
        else:
            temp=True
            self.close()
            print("simulation on")
        print "simserial toggle returns",temp
        return temp

    def write(self,string,inter_char_delay=None,*args,**kwargs):
        #import pdb; pdb.set_trace()
        if self.simulation:
            name=self.search_function_name(string)
            #import pdb;pdb.set_trace()
            try:
                getattr(self,name)(string.rstrip())
            except:
                try:
                    getattr(self,name)()
                except:
                    import sys
                    print sys.exc_info()
                    self._DEFAULT(string)
            print "buffer, due to write:", repr(self.buffer)
        else:
            if inter_char_delay:
                for char in string:
                    serial.Serial.write(self,char,*args,**kwargs)
                    time.sleep(inter_char_delay)
                print "ACHTUNG SimSerial.write nicht getestet"
            else: 
                serial.Serial.write(self,string,*args,**kwargs)

    def _DEFAULT(self,string):
        print "No simulation function for " + repr(self.search_function_name(string)) + " implemented in " + str(self.__class__)

    def sim_output(self,string):
        self.buffer += string + self.EOL

    def read(self,number=1):
        if self.simulation:
            # gebe die ersten number zeichen aus buffer zurueck
            print "WARNING: SimSerial.read() not implemented!"
            buftemp = self.buffer.split(' ')
            for i in range(10):
                try:
                    temp  = float(buftemp[i])
                    break
                except:
                    print "read simulation buffer"
            return temp
        else:
            return(serial.Serial.read(self,number))


    def readline(self):
        if self.simulation:
            splitbuf = self.buffer.splitlines()

            if len(splitbuf) > 0:

                ret = splitbuf[0]

                if len(splitbuf) > 1:
                    self.buffer = self.EOL.join(splitbuf[1:])+self.EOL
                else:
                    self.buffer = ''
                return ret

            else:
                print 'Warning: Readline on empty buffer'
        else:
            return(serial.Serial.readline(self))

    def flushInput(self):
        if not self.simulation:
            #import pdb;pdb.set_trace()
            serial.Serial.flushInput(self)
        else:
            self.buffer=str()

    def flushOutput(self):
        if not self.simulation:
            serial.Serial.flushOutput(self)

    def inWaiting(self):
        if not self.simulation:
            return(serial.Serial.inWaiting(self))
        else: return(len(self.buffer))

    def search_function_name(self,command):
#        if self.EOL!='':
#            command=command.replace(' '+self.EOL,'')
#        command=command.split(' ')
#        if self.commando_position=='first':
#            name=command[0]
#        else:
#            name=command[-1]
        name= re.search(self.CMD,command) 
        name=self.replace_special_characters(name)
        name='_'+name
        return(name)
    
    def search_function_parameters(self,command):
        name =re.search(self.PARMS,command)
        name.self.replace_special_characters(name)
        return(name)

    def replace_special_characters(self,name):
        _sign=['?','!','+','-','<','>','/',' ','\r']
        _replace=['QM','EM','plus','minus','less','greater','slash','','']
        for i in range(len(_sign)):
            name=name.replace(_sign[i],_replace[i])
        return(name)
