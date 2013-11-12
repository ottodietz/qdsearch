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
        if self.simulation:
            try:
                serial.Serial.__init__(self, *self.initargs, **self.initkwargs)
                self.simulation = False
                print("simulation off")
            except:
                self.simulation = True
                print("couldn't switch simulation off")
        else:
            self.simulation = True
            self.close()
            print("simulation on")
        return self.simulation

    def write(self,string,inter_char_delay=None,*args,**kwargs):
        if self.simulation:
            name=self.search_function_name(string)
            try:
                getattr(self,name)(string.rstrip())
            except:
                try:
                    getattr(self,name)()
                except:
                    import sys
                    print sys.exc_info()
                    self._DEFAULT(string)
            #print "buffer, due to write:", repr(self.buffer)
        else:
            if inter_char_delay:
                for char in string:
                    serial.Serial.write(self,char,*args,**kwargs)
                    time.sleep(inter_char_delay)
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
            temp = re.search('[0-9]+',self.buffer).group(0)
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
        command = self.hot_key_check(command)
        name= re.search(self.CMD,command).group(0) 
        name = self.replace_special_characters(name)
        name='_'+name
        return(name)
    
    def search_function_parameters(self,command):
        name =re.search(self.PARMS,command).group(0)
        name.self.replace_special_characters(name)
        return(name)

    def hot_key_check(self,name):
        _hotkey=['\x03'] #ASCII fuer hotkeys
        _replace=['ctrl+c']
        for i in range(len(_hotkey)):
            name = name.replace(_hotkey[i],_replace[i])
        return name

    def replace_special_characters(self,name):
        _sign=['?','!','+','-','<','>','/',' ','\r']
        _replace=['QM','EM','plus','minus','less','greater','slash','','']
        for i in range(len(_sign)):
            name=name.replace(_sign[i],_replace[i])
        return(name)
