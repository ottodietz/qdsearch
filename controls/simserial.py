import serial
import time


class SimSerial(serial.Serial):
    commando_position="first"
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
            self.simulation=False
            try:
                serial.Serial.__init__(self, *self.initargs, **self.initkwargs)
                print("simulation off")
            except:
                self.simulation=True
                print("couldn't switch simulation off")
        else:
            self.simulation=True
            self.close()
            print("simulation on")
        print "toggle returns"
        print self.simulation
        return self.simulation

    def write(self,string,*args,**kwargs):
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
        if self.EOL!='':
            command=command.replace(' '+self.EOL,'')
        command=command.split(' ')
        if self.commando_position=='first':
            name=command[0]
        else:
            name=command[-1]
        name=self.replace_special_characters(name)
        name='_'+name
        return(name)

    def replace_special_characters(self,name):
        _sign=['?','!','+','-','<','>','/',' ','\r']
        _replace=['QM','EM','plus','minus','less','greater','slash','','']
        for i in range(len(_sign)):
            name=name.replace(_sign[i],_replace[i])
        return(name)
