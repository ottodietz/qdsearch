from SimSerial import SimSerial
import time
import random
import math

class Voltage(SimSerial):

    def blinken(self):
        self.write("B")

    def lesen(self):
        temp=''
        self.flushInput()
        self.flushOutput()


        while (temp.find("Voltage")==-1):
            self.write("V")
            time.sleep(0.1)
            temp=self.readline()

        spannung=temp[9:14]
        return(float(spannung))


    def gauss_func(self,N, sigma, mu,x1,x2):
        """erzeugt Werte in einer Liste von einer Gau?funktion aufruf mit
         N: Skalierung der Hoehe, sigma: varianz, mu: Erwartungswert, x1: erster Wert, x2 letzer Wert"""

        vorfaktor = N / (sigma * math.sqrt(2*math.pi))
        s = -1.0 / (2 * sigma * sigma)
        b=list()
        while x1<x2:
            b.append(vorfaktor * math.exp(s * (x1 - mu)*(x1 - mu)))
            x1=x1+1
        return b

    def messen(self):

        if  self.simulation:
            messwert=random.randint(1,20)
            time.sleep(0.2)
            #zufalls_werte=random.sample(liste,700) # fuer irgendwelche zufallswerte
           # messwerte=self.gauss_func(random.randint(0,200),random.randint(0,200),random.randint(0, 700),startwert,endwert+1) # Fuer Zufallswerte in Gausskurvenfor
        else:
            messwert=self.lesen()
        return(messwert)