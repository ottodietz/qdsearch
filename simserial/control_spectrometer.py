from enthought.traits.api import*
from enthought.traits.ui.api import*
from numpy import arange,linspace,sin
import time
from enthought.chaco.tools.api import PanTool, ZoomTool
from enthought.pyface.api import error,warning,information
import thread

from SimSerial import SimSerial

class Spectro(SimSerial):
    # for simulation
    nm=float(0)
    nm_je_min=float(10.0)
    commando_position="last"
    EOL='\r'

    def wavelength_controlled_nm(self,aim):
        aim=round(aim,3) # rundet auf die 3. Nachkommastelle
        if aim <0 or aim >1500:
            print ("falsche input: Wellenlaenge muss zwischen 0 und 1500 liegen ")
        else:
            self.write(str(aim)+" >NM \r")

    def _greaterNM(self,string):
        a=string.find(" ")
        aim=float(string[0:a])
        thread.start_new_thread(self.simulation_controlled_nm,(aim,))

    def simulation_controlled_nm(self,aim):
        self.change_wavelength=True
        if self.nm-aim <0:
            sign=1
        else:
            sign=-1
        start=time.clock()
        startposition=self.nm
        while ((self.nm < aim-0.01 and sign==1) or (self.nm-0.01 > aim and sign==-1) )and self.change_wavelength:
            aktuell=time.clock()
            time.sleep(0.1)
            self.nm=round(startposition+self.nm_je_min*(aktuell-start)/60*sign,3)

    def mono_stop(self):
        self.write("MONO-STOP \r")

    def _MONOminusSTOP(self):
        self.change_wavelength=False

    def wavelength_uncontrolled_nm(self,aim):
        aim=round(aim,3) # rundet auf die 3. Nachkommastelle
        if aim <0 or aim >1000:
            warning(parent=None, title="warning", message="falsche Wert fuer die Wellenlaenge: sie muss zwischen 0 und 1000 nm liegen  ")
        else:
            self.write(str(aim)+" NM \r")

    def _NM(self,string):
        self.buffer=string+" ok"
        space=string.find(" ")
        self.nm=float(string[0:space])


    def wavelength_goto(self,aim):
        aim=round(aim,3)
        if aim <0 or aim >1000:
            warning(parent=None, title="warning", message="falsche Wert fuer die Wellenlaenge: sie muss zwischen 0 und 1000 nm liegen  ")
        else:
            self.write(str(aim)+" GOTO \r")

    def _GOTO(self,string):
        self.buffer=string+" ok"
        a=string.find(" ")
        self.nm=float(string[0:a])

    def velocity(self,tempo):
        tempo=round(tempo,3)
        if tempo<0.010 or tempo>666.666:
            warning(parent=None, title="warning", message="falscher Wert fuer die velocity: sie muss zwischen 0.010 und 666.666 nm/min liegen")
            main.input_nm=500.0
        else:
            self.write(str(tempo)+ " NM/MIN \r")

    def _NMslashMIN(self,string):
        self.buffer=string+" ok"
        a=string.find(" ")
        self.nm_je_min=float(string[0:a])

    def output_velocity(self):
        self.flushInput()
        self.write("?NM/MIN \r")
        tmp=self.readline()
        return(self.convert_output(tmp))

    def _QMNMslashMIN(self,string):
        self.buffer=' '+str(self.nm_je_min)+' '

    def output_position(self):
        self.flushInput()
        self.write("?NM \r")
        tmp=self.readline()
        return(self.convert_output(tmp))

    def _QMNM(self,string):
        self.buffer=' '+str(self.nm)+' '

    def grating_change(self,grat):
        print grat
        self.write(grat+" GRATING \r")

    def exit_mirror_change(self,mirror):
        self.write("EXIT-MIRROR \r")
        self.write(mirror+" \r")

    def convert_output(self,tmp):
        a=tmp.find(" ")
        b=tmp.find(" ",a+2)
        if a<0 or b<0:
            error(parent=None, title="error", message= "fehler: falscher string sollte Konvertiert werden: "+ str(tmp))
            return(tmp)
        else:
            output=tmp[a:b]
            return(output)

    def waiting(self):
        """Ueberprueft ob Spektrometer ans aim gekommen ist"""
        self.flushInput()
        finish=False
        while (not finish):
            temp=self.readline()
            if temp.find("ok") !=-1:
                print "found"
                finish=True
            time.sleep(1)

    def output_grating(self):
        grating=[]
        self.write("?GRATINGS \r")
        self.readline()

        for i in range(9):
            temp=self.readline()
            if temp.find("Not Installed")==-1:
                grating.append(temp)

        """fragt das current grating ab"""
        self.flushInput()
        self.write("?GRATING \r")
        grating_current=self.readline()
        grating_current=int(grating_current[10])
        grating[grating_current-1]=grating[grating_current-1].replace("\x1a", " ") # -1 da Liste bei 0 anfaengt und Grating bei 1
        return(grating,grating_current)

    def output_exit_mirror(self):
        """liest das current stellung des Exit_mirrors aus und gibt sie zur?ck"""
        self.write("EXIT-MIRROR \r")
        time.sleep(0.1)
        self.flushInput()
        self.write("?MIRROR \r")
        test=self.readline()
        if test.find("side")!=-1:
            return("side")
        elif test.find("front")!=-1:
            return("front")
        else:
             print "error by exit mirror"


