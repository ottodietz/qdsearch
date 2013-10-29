from traits.api import *
from traitsui.api import *
import time

import controls.voltage 

class VoltageGUI(HasTraits):

    ivoltage=controls.voltage.Voltage('COM4', 115200, timeout=0.05)

    Voltage = Range(low=0,high=255,value=128,editor=RangeEditor(evaluate=int,auto_set=False,mode='text'))
    UP = Button()
    DOWN = Button()
    Blinken=Button()
    setvoltage = Button(label="set Voltage")
    Setzero = Button(label="set zero")
    Input=Button(label="Input")
    read=Button(label="read")
    read2=Button(label="read2")
    output=Str(label="applied Voltage")
    test=Button(label="elapsed time 1")
    test2=Button(label="elapsed time 2")
    simulation=Bool(True, label="Simulation")
    toggle_activ = False

    view = View(HGroup(
                    Item('Voltage', show_label=False), 
                    VGroup(
                        Item("UP", show_label=False),
                        Item("DOWN", show_label=False))), 
                HGroup(
                    Item('Setzero', show_label=False),
                    Item("Blinken", show_label=False)),
                HGroup(
                    Item('read',show_label=False),
                    Item('read2',show_label=False)),
                HGroup( 
                    Item("output", show_label=True, style="readonly")),
                HGroup(
                    Item('test',show_label=True),
                    Item('test2',show_label=True)),
                Item('simulation', show_label=True),
                resizable = True)

    def _Voltage_changed(self):
        self.ivoltage.setvoltage(self.Voltage)

    def _UP_fired(self):
        if (0 <= self.Voltage < 255):
            self.Voltage +=1
        else:
            self.Voltage = 255

    def _DOWN_fired(self):
        if (0 < self.Voltage <= 255):
            self.Voltage -=1
        else:
            self.Voltage = 0

    def _Setzero_fired(self):
        self.Voltage = 0

    def _read_fired(self):
        if self.simulation == True:
            self.output=str(self.Voltage)
        else:
            self.output=str(self.ivoltage.read_voltage())

    def _read2_fired(self):
        if self.simulation == True:
            self.output=str(self.Voltage)
        else:
            self.output=str(self.ivoltage.read_voltage_new())

    def _Blinken_fired(self):
        self.ivoltage.blink()

    def _simulation_changed(self):
 #       import pdb; pdb.set_trace()i
 #       toggle_activ = True
 #       if
        self.simulation= self.ivoltage.toggle_simulation()

    def _test_fired(self):
        start = time.clock()
        error=0
        for i in range(100):
            print i
            temp=self.ivoltage.read_voltage()
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
            temp=self.ivoltage.read_voltage_new()
            print temp
            if temp==0:
                error=error+1
        ende = time.clock()
        print str(error)+' number of errors'
        print "the test function read new  runs %1.2f s" % (ende - start)



if __name__ == '__main__':
    main=VoltageGUI()
    main.configure_traits()
    if main.ivoltage.simulation==0:
            print"close Voltage"
            main.ivoltage.close()
