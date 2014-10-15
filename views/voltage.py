from traits.api import *
from traitsui.api import *
import time
from time import sleep

import controls.voltage
import thread


class VoltageGUI(HasTraits):

    icVoltage = controls.voltage.Voltage()

    Voltage = Range(low=0.,high=5.,value=2.5,editor=RangeEditor(evaluate=float,auto_set=False,mode='text'))
    UP = Button()
    DOWN = Button()
    Setzero = Button(label="set zero")
    Input=Button(label="Input")
    read=Button(label="read")
    output = Str()
    test = Button(label="elapsed time 1")
    simulation=Bool(True, label="Simulation")
    toggle_active = False

    traits_view = View(HGroup(
                    Item('Voltage', show_label=False),
                    VGroup(
                        Item("UP", show_label=False),
                        Item("DOWN", show_label=False))),
                HGroup(
                    Item('Setzero', show_label=False),
                    Item('read',show_label=False),
                    ),
                HGroup(
                    Item('output',show_label=True, style='readonly')),
                HGroup(
                    Item('test',show_label=True)),
                Item('simulation', show_label=True),
                resizable = True,
                width = 220,
                height = 200)

    sim_view = View(Item('simulation', show_label=True, label='Simulate Voltmeter'))

    def _Voltage_changed(self):
        self.icVoltage.setvoltage(self.Voltage)

    def _UP_fired(self):
        try:
            self.Voltage +=0.1
        except:
            self.Voltage = 5

    def _DOWN_fired(self):
        try:
            self.Voltage -=0.1
        except:
            self.Voltage = 0

    def _Setzero_fired(self):
        self.Voltage = 0

    def _read_fired(self):
        self.output=str(self.icVoltage.read_voltage())

    def _simulation_changed(self):
        if not self.toggle_active:
            self.toggle_active = True
            thread.start_new_thread(self.toggle_simulation,())

    def toggle_simulation(self):
        self.simulation = self.icVoltage.toggle_simulation()
        self.toggle_active = False

    def _test_fired(self):
        start = time.clock()
        error=0
        for i in range(100):
            print i
            temp=self.icVoltage.read_voltage()
            print temp
            if temp==0:
                error=error+1
        ende = time.clock()
        print str(error)+' number of errors'
        print "the test function read  runs %1.2f s" % (ende - start)




if __name__ == '__main__':
    main=VoltageGUI()
    main.configure_traits()
    if not main.icVoltage.simulation:
        print"close Voltage"
        main.icVoltage.close()
