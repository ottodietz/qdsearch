
from enthought.traits.api import*
from enthought.traits.ui.api import*
#from traitsui.menu import OKButton, CancelButton
#from enthought.chaco.api import Plot, ArrayPlotData
from numpy import arange,linspace,sin
#from enthought.enable.component_editor import ComponentEditor
import thread
import time
from enthought.chaco.tools.api import PanTool, ZoomTool
from enthought.pyface.api import error,warning,information

##import SimSerial
##reload(SimSerial)
from SimSerial import SimSerial



class Spectro(SimSerial):
    new_simulation=False
    commando_position="last"

    def wavelength_durchlauf_kontrolle(self,ziel):
        ziel=round(ziel,3) # rundet auf die 3. Nachkommastelle
        if ziel <0 or ziel >1000:
            print ("falsche Eingabe: Wellenlaenge muss zwischen 0 und 1000 liegen ")
        else:
            self.write(str(ziel)+" >NM \r")

    def mono_stop(self):
        self.write("MONO-STOP \r")

    def wavelength_durchlauf(self,ziel):
        ziel=round(ziel,3) # rundet auf die 3. Nachkommastelle
        if ziel <0 or ziel >1000:
            warning(parent=None, title="warning", message="falsche Wert fuer die Wellenlaenge: sie muss zwischen 0 und 1000 nm liegen  ")
        else:
            self.write(str(ziel)+" NM \r")

    def wavelength_goto(self,ziel):
        ziel=round(ziel,3)
        if ziel <0 or ziel >1000:
            warning(parent=None, title="warning", message="falsche Wert fuer die Wellenlaenge: sie muss zwischen 0 und 1000 nm liegen  ")
        else:
            self.write(str(ziel)+" GOTO \r")

    def geschwindigkeit(self,v):
        v=round(v,3)
        if v<0.010 or v>666.666:
            warning(parent=None, title="warning", message="falscher Wert fuer die Geschwindigkeit: sie muss zwischen 0.010 und 666.666 nm/min liegen")
            main.eingabe_nm=500.0
        else:
            self.write(str(v)+ " NM/MIN \r")

    def ausgabe_geschwindigkeit(self):
        self.flushInput()
        self.write("?NM/MIN \r")
        tmp=self.readline()
        return(self.konvertiere_ausgabe(tmp))

    def ausgabe_position(self):
        self.flushInput()
        self.write("?NM \r")
        tmp=self.readline()
        print tmp
        return(self.konvertiere_ausgabe(tmp))

    def _questionmarkNM(self,string):
        self.buffer=self.nm


    def grating_aendern(self,grat):
        print grat
        self.write(grat+" GRATING \r")

    def exit_mirror_aendern(self,mirror):
        self.write("EXIT-MIRROR \r")
        self.write(mirror+" \r")

    def konvertiere_ausgabe(self,tmp):
        a=tmp.find(" ")
        b=tmp.find(" ",a+2)
        if a<0 or b<0:
            error(parent=None, title="error", message= "fehler: falscher string sollte Konvertiert werden: "+ str(tmp))
            return(tmp)
        else:
            ausgabe=tmp[a:b]
            return(ausgabe)

    def warten(self):
        """Ueberprueft ob Spektrometer ans ziel gekommen ist"""
        self.flushInput()
        i=0
        fertig=False
        while (not fertig) and (i<20): # i noch als Abbruch drinne, falls die Funktion ins leere laeuft
            print i
            i=i+1
            temp=self.readline()
            print temp
            if temp.find("ok") !=-1:
                print "gefunden"
                fertig=True
            time.sleep(1)

    def ausgabe_grating(self):
        grating=[]
        self.write("?GRATINGS \r")
        self.readline()

        for i in range(9):
            temp=self.readline()
            if temp.find("Not Installed")==-1:
                grating.append(temp)

        """fragt das aktuelle grating ab"""
        self.flushInput()
        self.write("?GRATING \r")
        grating_aktuell=self.readline()
        grating_aktuell=int(grating_aktuell[10])
        grating[grating_aktuell-1]=grating[grating_aktuell-1].replace("\x1a", " ") # -1 da Liste bei 0 anfaengt und Grating bei 1
        return(grating,grating_aktuell)

    def ausgabe_exit_mirror(self):
        """liest das aktuelle stellung des Exit_mirrors aus und gibt sie zur?ck"""
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
             print "fehler"


