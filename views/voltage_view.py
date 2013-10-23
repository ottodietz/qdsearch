from traits.api import *
from traitsui.api import *
import time

import controls.voltage as Voltage
reload(Voltage)

class Volt(HasTraits):

    ivolt=Voltage.Voltage('COM4', 115200, timeout=0.05)

    Voltage = CFloat(128)
    UP = Button()
    DOWN = Button()
    Blinken=Button()
    setvoltage = Button(label="set Voltage")
    Setzero = Button(label="set zero")
    Input=Button(label="Input")
    read=Button(label="read")
    output=Str(label="applied Voltage")
    test=Button(label="elapsed time 1")
    test2=Button(label="elapsed time 2")
    checkbox=Bool(True, label="Simulation")


    view = View(HGroup(Item('Voltage', show_label=False), VGroup(Item("UP",
show_label=False),Item("DOWN", show_label=False))),Item('setvoltage',show_label=False),
            HGroup(Item('Setzero', show_label=True ),Item("Blinken", show_label=False)),
            HGroup(Item("Input",show_label=False), Item('read',show_label=False)),
            HGroup( Item("output", show_label=True, style="readonly")),
            HGroup(Item('test',show_label=True),Item('test2',show_label=True)),
            Item('checkbox', show_label=True),
             resizable = True)

    def _setvoltage_fired(self):
        if self.checkbox == False:
            self.ivolt.setvoltage(self.Voltage)
        else:
            self.output = str(self.Voltage)

    def _UP_fired(self):
        if self.Voltage < 255:
            self.Voltage +=1

    def _DOWN_fired(self):
        if self.Voltage > 0:
            self.Voltage -=1

    def _Setzero_fired(self):
        if self.checkbox == False:
            self.ivolt.setvoltage(0)
        else:
            self.output = str(0)
            self.Voltage = 0

    def _read_fired(self):
        if self.checkbox == True:
            self.output=str(self.Voltage)
        else:
            self.output=str(self.ivolt.read_voltage())

    def _lesen2_fired(self):
        self.output=str(self.ivolt.read_voltage_new())

    def _Blinken_fired(self):
        self.ivolt.blink()

    def _checkbox_changed(self):
        try:
            self.ivolt.toggle_simulation()
        except:
            self.checkbox=True

    def _test_fired(self):
        start = time.clock()
        error=0
        for i in range(100):
            print i
            temp=self.ivolt.read_voltage()
            print temp
            if temp==0:
                error=error+1
        ende = time.clock()
        print str(error)+' number of errors'
        print "the test function read  runs %1.2f s" % (ende - start)


    def _test2_fired(self):
        start = time.clock()
        error=0
        for i in range(100):
            print i
            temp=self.ivolt.read_voltage_new()
            print temp
            if temp==0:
                error=error+1
        ende = time.clock()
        print str(error)+' number of errors'
        print "the test function read new  runs %1.2f s" % (ende - start)




main=Volt()
main.configure_traits()
if main.ivolt.simulation==0:
        print"close Voltage"
        main.ivolt.close()
