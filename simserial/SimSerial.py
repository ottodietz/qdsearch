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
            super(SimSerial,self).write(string)

    def readline(self):
        if self.simulation:
            return(str(self.buffer))
        else:
            return(super(SimSerial,self).readline())

    def flushInput(self):
        if not self.simulation:
            serial.Serial.flushInput(self)

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
        _sign=['?','!','+','-','<','>','/']
        _replace=['QM','EM','plus','minus','less','greater','slash']
        for i in range(len(_sign)):
            name=name.replace(_sign[i],_replace[i])
        return(name)
