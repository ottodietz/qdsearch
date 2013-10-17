#!/usr/bin/env python
# -*- coding: utf-8 -*-

from traits.api import *
from traitsui.api import *
from traitsui.menu import OKButton, CancelButton
from chaco.api import Plot, ArrayPlotData
from numpy import arange,linspace,sin
from enable.component_editor import ComponentEditor
import thread
import time
from chaco.tools.api import PanTool, ZoomTool
from pyface.api import error,warning,information
from ctypes import *
import random

import controls.spectrometer
reload(controls.spectrometer)
import controls.spectrometer

import controls.voltage
reload(controls.voltage)

class SpectrometerGUI(HasTraits):
    ivolt=controls.voltage.Voltage('COM9', 115200, timeout=1)
    ispectro=controls.spectrometer.Spectro('COM4', 9600, timeout=1)

    measurement_process=False
    acquisition_process=False
    refresh_active=False

    plot = Instance(Plot,())

    goto=Button()
    sweep=Button()
    search_maximum=Button(label="search maximum")

    # 0.002 nm ist kleinster Schritt
    jogup = Button()
    jogdown = Button()

    centerwvl=Range(0.0,1000.0,894.35,mode='text')
    scan_bereich=CFloat(3)

    slot_width_in = Range(10,3000,1)
    slot_width_out = Range(10,3000,1)

    measured_values=[]
    wavelength=[]

    grating_value=List([" 1"," 2"," 3"," 4"])
    current_grating=Str()
    exit_mirror_value=List(["front (CCD)","side (APDs)"]) # List notwendig sonst wird drop down nicht aktualisiert
    exit_mirror=Str()

    speed=CFloat(50.0)
    simulate_spectrometer=Bool(True, label="Simulation Spectrometer")
    simulate_voltmeter=Bool(True,label="Simulation Voltmeter")

    str_nmmin = Str('nm/min')
    str_at = Str('@')
    str_nm = Str('nm')
    str_pm = Str('+/-')

    hide = {'enabled_when':'measurement_process==False'}

    search_max_label = Str('search maximum')



    traits_view=View(
            HGroup(
             VGroup(
              HGroup(Item("centerwvl",show_label=False),Item("goto",label='goto',show_label=False),
                     VGroup(Item('jogup',label='up',show_label=False),Item('jogdown',label='down',show_label=False))
                     ,**hide),
              VGrid(Item('sweep',label='sweep',show_label=False,**hide),
                     Item('str_at',show_label=False,style='readonly'),
                     Item('speed',show_label=False,width=-60,editor=TextEditor(auto_set=False),**hide),
                     Item('str_nmmin',show_label=False,style='readonly'),
                     Item("search_maximum",show_label=False,editor=ButtonEditor(label_value
                         = 'search_max_label')),
                     Item('str_pm',show_label=False,style='readonly'),
                     Item('scan_bereich',show_label=False,**hide),
                     Item('str_nm',show_label=False,style='readonly'), columns=4
                     ),
              Item('current_grating', editor=EnumEditor(name='grating_value'), label='Gratings',**hide),
              Item("exit_mirror",editor=EnumEditor(name='exit_mirror_value'),**hide),
              HGroup(Item('slot_width_in', label='Slot width in/out',enabled_when='False'),
                     Item('slot_width_out', show_label=False, enabled_when='False'),
                     **hide
                    ),
              Item('simulate_spectrometer',**hide),Item('simulate_voltmeter',**hide)
              ),
             Item("plot",editor=ComponentEditor(),show_label=False)
            ),
            width=750,height=600,buttons = [OKButton,], resizable = True)


    def __init__(self):
        self.refresh_active=True
        if len(self.grating_value)>0:
            self.current_grating=self.grating_value[0]
        if len(self.exit_mirror_value)>0:
            self.exit_mirror=self.exit_mirror_value[0]
        self.refresh_active=False


    def _goto_fired(self):
        self.ispectrometer_gui_refresh()
        self.ispectro.wavelength_goto(self.centerwvl)
        self.ispectro.waiting()


    def _sweep_fired(self):
                self.ispectro.wavelength_uncontrolled_nm(self.centerwvl)
                self.ispectro.waiting()



    def _speed_changed(self):
        print "speed changed: " + str(self.speed)
        self.ispectro.velocity(self.speed)

    def _jogup_fired(self):
        self.centerwvl += 0.001
        self._goto_fired()

    def _jogdown_fired(self):
        self.centerwvl -= 0.001
        self._goto_fired()


    def _position_fired(self):
            self.output=self.ispectro.output_position()


    def _identify_fired(self):
            self.output=self.ispectro.ident()


    def _output_speed_fired(self):
            self.output=self.ispectro.output_velocity()


    def _current_grating_changed(self):
       if not self.refresh_active: # ueberprueft ob der Wert wegen einer aktualisierung geaendert worden ist, dann kein Befehl senden
         self.ispectro.grating_change(self.current_grating[1])

    def _exit_mirror_changed(self):
        if not self.refresh_active:
            if self.exit_mirror=='front (CCD)':
                self.ispectro.exit_mirror_change('front')
            else:
                self.ispectro.exit_mirror_change('side')

    def _search_maximum_fired(self):
            if self.measurement_process:
                self.measurement_process = False
            else:
                start_value=self.centerwvl-self.scan_bereich
                end_value=self.centerwvl+self.scan_bereich
                if start_value <0:
                    start_value=0
                    end_value=self.scan_bereich
                thread.start_new_thread(self.measure,(start_value,end_value,))

    def measure(self,start_value,end_value):
        self.search_max_label='abort'
        self.ispectro.wavelength_goto(start_value)
        self.ispectro.waiting()
        self.ispectro.wavelength_controlled_nm(end_value)
        self.measurement_process=True
        start=time.clock()
        self.measured_values=[]
        self.wavelength=[]

        while self.measurement_process:
            self.measured_values.append(self.ivolt.measure())
            ende=time.clock()
            time.sleep(1) # without the method is to fast for the ispectrometer
            self.wavelength.append(float(self.ispectro.output_position()))
            self.draw(self.wavelength,self.measured_values)

            """die beiden Abbruchbedingungen, wenn die Wellaenge fast gr??er als der end_value ist oder aber die letzen beiden eingelessenen Wellenl?ngen identisch sind"""

            if max(self.wavelength)>=end_value-0.01:
                    self.measurement_process=False
            if len(self.wavelength)>2:
                if self.wavelength[len(self.wavelength)-2]==self.wavelength[len(self.wavelength)-1]:
                    self.measurement_process=False

        maximum=max(self.measured_values) # sucht das groesste element der liste
        wavelength_maximum=self.measured_values.index(maximum) # sucht den ort in der Liste von der Zahl maximum
        self.ispectro.mono_stop()
        self.measurement_process=False
        print self.wavelength[wavelength_maximum]
        self.ispectro.wavelength_goto(self.wavelength[wavelength_maximum]) # geht an ort des Maximums zurueck
        self.search_max_label='search maximum'


    def draw(self,x_achse,y_achse):
        plotdata = ArrayPlotData(x=x_achse, y=y_achse)
        plot = Plot(plotdata)
        plot.plot(("x", "y"), type="line", color="blue")
        #plot.title="title"
        plot.x_axis.title="Wavelength [nm]"
        plot.y_axis.title="Intensity [V]"
        plot.overlays.append(ZoomTool(component=plot,tool_mode="box", always_on=False)) # damit man im Plot zoomen kann
        plot.tools.append(PanTool(plot, constrain_key="shift")) # damit man mit der Maus den Plot verschieben kann
        self.plot = plot


    def _simulate_spectrometer_changed(self):
        self.ispectro.toggle_simulation()
        if not self.simulate_spectrometer:
            self.ispectrometer_gui_refresh()

    def _simulate_voltmeter_changed(self):
        self.ivolt.toggle_simulation()

    def ispectrometer_gui_refresh(self):
        self.refresh_active=True
        position=self.ispectro.output_position()
        self.centerwvl=position
        self.speed=self.ispectro.output_velocity()
        self.read_gratings()
        self.read_exit_mirror()
        self.refresh_active=False


    def read_gratings(self):
        #import pdb;pdb.set_trace()
        (self.grating_value,aktuell)=self.ispectro.output_grating() #aktuell als zweite output hinzuschreiben
        self.current_grating=self.grating_value[aktuell-1] # -1 da Grating bei 1 anfaengt zu zaehlen und List bei 0

    def read_exit_mirror(self):
        exit_mirror=self.ispectro.output_exit_mirror()
        if exit_mirror=='front':
            self.exit_mirror=self.exit_mirror_value[0]
        else:
            self.exit_mirror=self.exit_mirror_value[1]
    def _abort_fired(self):
        self.ispectro.mono_stop()
        self.measurement_process=False

if __name__=="__main__":
    main=SpectrometerGUI()
    main.configure_traits()
    if not main.ispectro.simulation:
        print"close ispectrometer"
        main.ispectro.close()
    if not main.ivolt.simulation:
        print"close controls.voltage"
        main.ivolt.close()
