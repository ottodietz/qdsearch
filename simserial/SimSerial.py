import serial
import time


class SimSerial(serial.Serial):
    commando_position="first"
    device=""
    number_of_EOL=1

    simulation=True
    initargs=str()
    initkwargs=str()
    buffer=str()
    posx=float(1.0)
    posy=float(1.0)


    def __init__(self,*args,**kwargs):
        self.initkwargs=kwargs
        self.initargs=args


        """ Beide Moeglichkeiten um den Port zu oeffnen
            #serial.Serial.__init__(self, *args, **kwargs)
            #super(SimSerial,self).__init__(*args, **kwargs) """

    def toggle_simulation(self):
        if self.simulation:
            self.simulation=False
            print("simulation off")
            super(SimSerial,self).__init__(*self.initargs,**self.initkwargs)
        else:
            self.simulation=True
            self.close()
            print("simulation on")


    def write(self,string):
        if self.simulation==True:
            name=self.search_function_name(string)
            try:
                    getattr(self,name)(string)
            except:
                try:
                    getattr(self,name)()
                except:
                    pass
                    #print('No simulation function found.')
        else:
            #serial.Serial.write(self,string)
            super(SimSerial,self).write(string)

    def readline(self):
        if self.simulation:
            return(str(self.buffer))
        else:
            #return(serial.Serial.readline(self))
            return(super(SimSerial,self).readline())# besser: aber noch ausprobieren

    def flushInput(self):
        if not self.simulation:
            serial.Serial.flushInput(self)
            #super(SimSerial,self).flushOutput()

    def flushOutput(self):
        if not self.simulation:
            serial.Serial.flushOutput(self)
        else:
            self.buffer=str

    def inWaiting(self):
        if not self.simulation:
            return(serial.Serial.inWaiting(self))
        else: return(len(self.buffer))

    def search_function_name(self,command):
        spaces = []
        position = 0
        for x in command:
            if x == ' ':
                spaces.append(position)
            position += 1
        if len(spaces)>1 and self.commando_position=="last":
            name='_'+command[spaces[len(spaces)-self.number_of_EOL-1]+1:spaces[len(spaces)-self.number_of_EOL]]
        elif   len(spaces)>1 and self.commando_position=="first":
            name='_'+command[0:spaces[0]]
        elif spaces==[]:
            name='_'+command
        else:
            name='_'+command[0:spaces[0]]
        name=self.replace_special_characters(name)
        return(name)

    def replace_special_characters(self,name):
        _sign=['?','!','+','-','<','>','/']
        _replace=['QM','EM','plus','minus','less','greater','slash']
        for i in range(len(_sign)):
            name=name.replace(_sign[i],_replace[i])
        return(name)
