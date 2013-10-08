from traits.api import *
from traitsui.api import *
import time

import controls.voltage as Voltage
reload(Voltage)

class Volt(HasTraits):

    ivolt=Voltage.Voltage('COM4', 115200, timeout=0.05)

    Voltage = CFloat()
    Setzero = Button()
    Blinken=Button()
    setvoltage=Button()
    lesen=Button()
    lesen2=Button()
    output=Str()
    test=Button("laufezeitentest1")
    test2=Button("laufezeitentest2")
    checkbox=Bool(True)


    view = View('Voltage',Item('setvoltage',show_label=False),
            HGroup(Item('Setzero', show_label=False ),Item("Blinken", show_label=False)),
            HGroup(Item("lesen",show_label=False), Item('lesen2',show_label=False)),
            HGroup( Item("output", show_label=False, style="readonly")),
            HGroup(Item('test',show_label=False),Item('test2',show_label=False)),
            Item('checkbox'),
             resizable = True)

    def _setvoltage_fired(self):
        self.ivolt.setvoltage(self.Voltage)

    def _Setzero_fired(self):
        self.ivolt.setvoltage(0)

    def _lesen_fired(self):
        self.output=str(self.ivolt.read_voltage())

    def _lesen2_fired(self):
        self.output=str(self.ivolt.read_voltage_new())

    def _Blinken_fired(self):
        self.ivolt.blink()

    def _checkbox_changed(self):
        self.ivolt.toggle_simulation()

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
