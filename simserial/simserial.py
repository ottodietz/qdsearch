from __future__ import division
import serial
import time
import thread

class SimSerial(serial.Serial):
    simulation=True
    initargs=str()
    initkwargs=str()
    buffer=str()
    posx=float(1.0)
    posy=float(1.0)
    nm=float(0)
    nm_je_min=float(10.0)

    def __init__(self,*args,**kwargs):
        self.initkwargs=kwargs
        self.initargs=args



        """ Beide Moeglichkeiten um den Port zu oeffnen
            #serial.Serial.__init__(self, *args, **kwargs)
            #super(SimSerial,self).__init__(*args, **kwargs) """

    def toggle_simulation(self,geraet):
        if self.simulation:
            self.simulation=False
            print("simulation aus")
            super(SimSerial,self).__init__(*self.initargs,**self.initkwargs)

        else:
            self.simulation=True
            serial.Serial.close(self)
            # super(SimSerial,self).close() besser: aber noch ausprobieren
            print("simulation an")


    def write(self,string):
        if self.simulation==True:
            """gehoert zum Cryo"""
            if string=="identify \r":
                self.buffer="identify"

            if string.find(" m \r")!=-1:
               a=string.find(" ")
               b=string.find(" ",a+1)
               c=string.find(" ",b+1)
               d=string.find(" ",c+1)
               self.posx=float(string[b:c])
               self.posy=float(string[c+1:d])


            if string.find(" r \r")!=-1:
               a=string.find(" ")
               b=string.find(" ",a+1)
               c=string.find(" ",b+1)
               d=string.find(" ",c+1)
               self.posx+=float(string[b:c])
               self.posy+=float(string[c+1:d])

            if string=="p \r":
                 self.buffer=str(self.posx)+" "+str(self.posy)

            if string=="cal \r":
                print "hello"
                pass


            """Ab hier Spektrometer"""
            if string.find("NM \r")!=-1 and string.find("?NM")==-1 and string.find(">NM")==-1:
                self.buffer=string+" ok"
                a=string.find(" ")
                self.nm=float(string[0:a])

            if string.find(">NM \r")!=-1 and string.find("?NM")==-1:
                a=string.find(" ")
                ziel=float(string[0:a])
                print "starte thread"
                thread.start_new_thread(self.simulation_durchlauf,(ziel,))

            if string==("?NM \r"):
                self.buffer=self.nm

            if string==("?GRATINGS \r"):
                pass

            if string==("?GRATING \r"):
                pass

            if string==("?MIRROR \r"):
                pass


            if string==("?NM/MIN \r"):
                self.buffer=self.nm_je_min

            if (string.find("GOTO")!=-1):
                self.buffer=string+" ok"
                a=string.find(" ")
                self.nm=float(string[0:a])


            if (string.find("NM/MIN \r")!=-1) and (string.find("?NM/MIN \r")==-1):
                self.buffer=string+" ok"
                a=string.find(" ")
                self.nm_je_min=float(string[0:a])


            if string.find("GRATING \r")!=-1:
                pass

            if string==("EXIT-MIRROR \r"):
                pass

            if string==("SIDE \r"):
                pass

            if string==("FRONT \r"):
                pass

            if string==("MONO-STOP \r"):
                pass



            """Ab hier Voltmessgeraet"""

            if string==("V") and (string.find("\r")==-1):
                print ("Voltage messen")

            if string==("B") and (string.find("\r")==-1) :
                print ("blinken")


            if (string.find("S")==0)  and (string.find("\r")==-1):
                print ("setvoltage")
        else:
                serial.Serial.write(self,string)
                # super(SimSerial,self).write(string) besser: aber noch ausprobieren

        """Achtung: xxx.find("text") liefert eine -1 zur?ck wenn nichts gefunden wurde. Wenn jetzt die L?nge des Strings mit dem verglichen wird genau um 1
            kleiner ist als um was abgezogen wird (zb. len(abc)-4) ist die Bedingung trotzdem erf?llt!"""



    def readline(self):
        if self.simulation:
            return(" "+str(self.buffer)+" ")
        else:
            return(serial.Serial.readline(self))
            # return(super(SimSerial,self).close()) besser: aber noch ausprobieren

    def flushInput(self):
        if not self.simulation:
            serial.Serial.flushInput(self)
            #super(SimSerial,self).flushOutput()



    def simulation_durchlauf(self,ziel):
        if self.nm-ziel <0:
            vorzeichen=1
        else:
            vorzeichen=-1
        start=time.clock()
        aktuell=time.clock()
        startposition=self.nm
        while self.nm < ziel-0.01:
            aktuell=time.clock()
            time.sleep(0.1)
            self.nm=round(startposition+self.nm_je_min*(aktuell-start)/60*vorzeichen,3)
