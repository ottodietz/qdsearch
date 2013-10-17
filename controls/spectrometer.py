from traits.api import*
from traitsui.api import*
from numpy import arange,linspace,sin
import time
from chaco.tools.api import PanTool, ZoomTool
from pyface.api import error,warning,information
import thread

import simserial
reload(simserial)

class Spectro(simserial.SimSerial):
    # for simulation
    nm=float(0)
    nm_je_min=float(10.0)
    commando_position="last"
    EOL='\r'

    def _QMGRATING(self):
        self.buffer='?GRATING  '+ '1' +'  ok \r'
        print self.buffer

    def _QMGRATINGS(self):
        self.buffer='?GRATINGS\r'\
          + '1 1800 g/mm BLZ=  750NM \r'\
          + '2 1800 g/mm BLZ=  750NM \r'\
          + '3 1800 g/mm BLZ=  750NM \r'\
          + '4 1800 g/mm BLZ=  750NM \r'\
          + '5 1800 g/mm BLZ=  750NM \r'\
          + '6 1800 g/mm BLZ=  750NM \r'\
          + '8 1800 g/mm BLZ=  750NM \r'\
          + '8 1800 g/mm BLZ=  750NM \r'\
          + '9 Not Installed\r'\
          + 'ok\r'
        print "QM_GRATINGS:",self.buffer
##
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
            print self.readline()

    def _NMslashMIN(self,string):
        self.buffer=string+" ok"
        a=string.find(" ")
        self.nm_je_min=float(string[0:a])

    def output_velocity(self):
        self.flushInput()
        self.write("?NM/MIN \r")
        tmp=self.readline()
        a=tmp.split(" ")
        print a[2]
        return(float(a[2]))

    def _QMNMslashMIN(self,string):
        self.buffer='  '+str(self.nm_je_min)+'  '

    def output_position(self):
        self.flushInput()
        self.write("?NM \r")
        tmp=self.readline()
        a=tmp.split(" ")
        print a[2]
        return float(a[2])

    def _QMNM(self,string):
        self.buffer='  '+str(self.nm)+'  '



    def grating_change(self,grat):
        print grat
        self.write(grat+" GRATING \r")

    def exit_mirror_change(self,mirror):
        self.write("EXIT-MIRROR \r")
        self.write(mirror+" \r")

    def convert_output(self,tmp):
        #import pdb;pdb.set_trace()
        a=tmp.split(" ")
        if len(a)<3:
            error(parent=None, title="error", message= "fehler: falscher string sollte Konvertiert werden: "+ str(a))
            return(tmp)
        print "Konvertiere:", a
        return(float(a[2]))

    def waiting(self):
        """Ueberprueft ob Spektrometer ans aim gekommen ist"""
        self.flushInput()
        finish=False
        while (not finish):
            temp=self.readline()
            if temp.find("ok") !=-1:
                print "spectrometer ready"
                finish=True
            time.sleep(1)

    def get_until_okay(self,cmd):
        self.flushInput()
        self.write(cmd + ' ' + self.EOL )
        result = []
        temp = self.readline()
        result.append(temp)

        while temp.find("ok") == -1:
            print temp
            temp = self.readline()
            result.append(temp)

        if len(result) == 1:
            return result[0]
        return result

    def output_grating(self):
        grating=[]
        self.flushInput()
        grating = self.get_until_okay("?GRATINGS")
        print "Gratings:", grating
        """fragt das current grating ab"""
        grating_current = self.get_until_okay("?GRATING")
        print "Grating_current:",grating_current
        grating_current = int(grating_current.split('  ')[1])
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


