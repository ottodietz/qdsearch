#!/usr/bin/env python
# -*- coding: utf-8 -*-
from traits.api import*
from traitsui.api import*
from traits.util import refresh
from traitsui.menu import OKButton, CancelButton
from chaco.api import Plot, ArrayPlotData, jet
from chaco.tools.api import PanTool, ZoomTool
from enable.component_editor import ComponentEditor
import thread
from time import sleep
from ctypes import *

import controls.camera
#refresh (controls.camera)
import views.cryo
#refresh (views.cryo)
import views.voltage
#refresh (views.voltage)

from pyface.api import error,warning,information

class CameraGUI(HasTraits):
    icCamera = controls.camera.Camera()

    acq_active = False
    toggle_active = False

    simulation=Bool(True)
    cooler=Bool(False)
    test = Button()
    single=Button()
    continous_label = Str('Continous')
    continous=Button()
    autofocus=Button(label="AF X/Y")
    zautofocus=Button(label="AF Z")
    settemperature=Range(low=-70,high=20,value=20)

    x_step = Float(0.001)
    y_step = Float(0.001)
    ivCryo = Instance(views.cryo.CryoGUI)
    icCryo = Instance(controls.cryo.Cryo)
    ivVoltage = Instance(views.voltage.VoltageGUI)
    icVoltage = Instance(controls.voltage.Voltage)

    """menu"""
    acquisitionmode=Int(1)
    exposuretime=Range(low=0.0001,high=10,value=0.1,editor=TextEditor(evaluate=float,auto_set=False))
    Vshiftspeed_value = List(["0","1","2","3"]) #Enum(0,1,2) speeds from 0 to highest
    Hshiftspeed_value = List(["0","1","2"]) #Enum(0,1,2)
    Vshiftspeed = Str("0")
    Hshiftspeed = Str("0")
    readmode_name = List(['Full Vertical Binning','Image'])
    readmode = Str("Full Vertical Binning")

    output=Str()
    plot = Instance(Plot,())
    
    def _icCryo_default(self):
        return self.ivCryo.icCryo
    
    def _icVoltage_default(self):
        return self.ivVoltage.icVoltage

    menu_action = Action(name='camera menu', accelerator='Ctrl+p', action='call_menu')
    mi_reload = Action(
                        name='reload camera module', 
                        accelerator='Ctrl+r',
                        action='reload_camera'
                        )
    menu=Menu(menu_action,mi_reload,name='Camera')

    traits_view=View(HGroup(VGroup(
                            HGroup(
                                    Item('single',label='Single',show_label=False),
                                    Item('continous',show_label=False,editor=ButtonEditor(label_value='continous_label')),
                                    Item('test',show_label=False),
                                    Item('autofocus',show_label=False),
                                    Item('zautofocus',show_label=False)),
                            HGroup(
                                Item('exposuretime'),Item('simulation',label='simulate camera')),
                            Item('readmode',editor=EnumEditor(name='readmode_name')),
                            Item('Vshiftspeed',label="Vertical Speed",editor=EnumEditor(name='Vshiftspeed_value')),
                            Item('Hshiftspeed',label="Horizontal Speed",editor=EnumEditor(name='Hshiftspeed_value'))),
                            VGroup(
                                Item('plot',editor=ComponentEditor(size=(50,50)),show_label=False))),
                       resizable = True, menubar=MenuBar(menu) )

    def _single_fired(self):
        try:
            self.line=self.icCamera.acquisition(sim_pos=self.icCryo.pos(),sim_volt=self.ivVoltage.Voltage,exptme=self.exposuretime)
        except: 
            self.line=self.icCamera.acquisition()
        self.plot_data()

    def _zautofocus_fired(self):
        maxid = -1 #Wert der Spannung bei Maximalen Counts, setze auf -1
        maxcount = 0 #Maximale Counts, setze auf 0
        for i in range(256):
            self.ivVoltage.Voltage = float((i/255.*5.))
            self.line=self.icCamera.acquisition(sim_pos=self.icCryo.pos(),sim_volt=self.ivVoltage.Voltage,exptme=self.exposuretime)   
            if maxcount < max(self.line):
                maxcount = max(self.line)
                maxid = i
            print "Z-Scan bei %03d Prozent!" % int(i/255.*100.)
        print "Im Fokus bei der Spannung %1.1f" % float(maxid/255.*5.)

        self.ivVoltage.Voltage = maxid/255.*5.
        self.line=self.icCamera.acquisition(sim_pos=self.icCryo.pos(),sim_volt=self.ivVoltage.Voltage,exptme=self.exposuretime)
        self.plot_data()

    def _autofocus_fired(self):
        xtest = False
        ytest = False
        try:
            self.line=self.icCamera.acquisition(sim_pos=self.icCryo.pos(),sim_volt=self.ivVoltage.Voltage,exptme=self.exposuretime)
        except:
            self.line=self.icCamera.acquisition()

        while xtest == False: #Test in die x-Richtung, suchen bis Counts runter
            a = max(self.line)
            self.icCryo.rmove(self.x_step,0)
            try:
                self.line=self.icCamera.acquisition(sim_pos=self.icCryo.pos(),sim_volt=self.ivVoltage.Voltage,exptme=self.exposuretime)
            except:
                self.line=self.icCamera.acquisition()
            self.plot_data()
            b = max(self.line)
            if b < a:
                self.icCryo.rmove(-self.x_step,0)
                try: #damit er wieder das aktuelle max hat
                    self.line=self.icCamera.acquisition(sim_pos=self.icCryo.pos(),sim_volt=self.ivVoltage.Voltage,exptme=self.exposuretime)
                except:
                    self.line=self.icCamera.acquisition()
                xtest = True

        xtest=False

        while xtest == False: #Test in die -x-Richtung, suchen bis Counts runter
            a = max(self.line)
            self.icCryo.rmove(-self.x_step,0)
            try:
                self.line=self.icCamera.acquisition(sim_pos=self.icCryo.pos(),sim_volt=self.ivVoltage.Voltage,exptme=self.exposuretime)
            except:
                self.line=self.icCamera.acquisition()
            self.plot_data()
            b = max(self.line)
            if b < a:
                self.icCryo.rmove(self.x_step,0)
                try:
                    self.line=self.icCamera.acquisition(sim_pos=self.icCryo.pos(),sim_volt=self.ivVoltage.Voltage,exptme=self.exposuretime)
                except:
                    self.line=self.icCamera.acquisition()
                xtest = True

        while ytest == False: #Test in die y-Richtung, suchen Counts runter
           a = max(self.line)
           self.icCryo.rmove(0,self.y_step)
           try:
                self.line=self.icCamera.acquisition(sim_pos=self.icCryo.pos(),sim_volt=self.ivVoltage.Voltage,exptme=self.exposuretime)
           except:
                self.line=self.icCamera.acquisition()
           self.plot_data()
           b = max(self.line)
           if b < a:
                self.icCryo.rmove(0,-self.y_step)
                try:
                    self.line=self.icCamera.acquisition(sim_pos=self.icCryo.pos(),sim_volt=self.ivVoltage.Voltage,exptme=self.exposuretime)
                except:
                    self.line=self.icCamera.acquisition()
                ytest = True

        ytest = False

        while ytest == False: #Test in die -y-Richtung, suchen Counts runter
           a = max(self.line)
           self.icCryo.rmove(0,-self.y_step)
           try:
                self.line=self.icCamera.acquisition(sim_pos=self.icCryo.pos(),sim_volt=self.ivVoltage.Voltage,exptme=self.exposuretime)
           except:
                self.line=self.icCamera.acquisition()
           self.plot_data()
           b = max(self.line)
           if b < a:
                self.icCryo.rmove(0,self.y_step)
                try:
                    self.line=self.icCamera.acquisition(sim_pos=self.icCryo.pos(),sim_volt=self.ivVoltage.Voltage,exptme=self.exposuretime)
                except:
                    self.line=self.icCamera.acquisition()
                ytest = True

        self.plot_data()
        print "AF fertig!"


    def plot_data(self):
#        import pdb; pdb.set_trace()
        if self.icCamera.readmode_name == 'Full Vertical Binning':
            plotdata = ArrayPlotData(x=self.line[:])
            plot = Plot(plotdata)
            plot.plot(("x"),  color="blue")
        if self.icCamera.readmode_name == 'Image':
            self.line = self.image
            plotdata = ArrayPlotData(imagedata = self.image)           
            plot = Plot(plotdata)
            plot.img_plot("imagedata", colormap = jet)
 
        plot.title = ""
        plot.overlays.append(ZoomTool(component=plot,tool_mode="box", always_on=False))
        plot.tools.append(PanTool(plot, constrain_key="shift"))
        #plot.tools.append(PlotTool(component=plot))
        #plot.range2d.x_range.low=self.x1
        #plot.range2d.x_range.high=self.x2
        #plot.range2d.y_range.low=self.y1
        #plot.range2d.y_range.high=self.y2
        plot.x_axis.title="x-Position on sample [mm]"
        plot.y_axis.title="y-Position on sample [mm]"
        self.plot=plot

    def ensure_init(self):
        if self.icCamera.init_active:
            information(parent=None, title="please wait", message="The initialization of the camera is running. Please wait until the initialization is finished.")
            while self.icCamera.init_active:
                time.sleep(.5)


    def _settemperature_changed(self):
        self.ensure_init()
        self.icCamera.settemperature(self.settemperature)

    def _simulation_changed(self):
        self.stop_acq_thread()
        # wenn es nicht schon läuft, schicke self.toggle_simulate() in den
        # Hintergrund
        if not self.toggle_active:
            self.toggle_active = True
            thread.start_new_thread(self.toggle_simulation,())

    def toggle_simulation(self):
        # camera.toggle_simulation() liefert simulieren = True/False zurück
        self.simulation = self.icCamera.toggle_simulation()
        self.toggle_active = False

    def acq_thread(self):
        self.continous_label = 'Stop'
        while self.acq_active:
            self._single_fired()
        self.continous_label = 'Continous'

    def _test_fired(self):
        self.icCamera.speedinit()

    def _continous_fired(self):
        self.acq_active = not self.acq_active
        if self.acq_active:
            thread.start_new_thread(self.acq_thread,())

    def _cooler_changed(self):
        if self.cooler:
            self.icCamera.cooler_on()
        else:
            self.icCamera.cooler_off()

    def _readmode_changed(self):
        self.icCamera.setreadmode(self.readmode) #=c_long(self.readmode)

    def _Hshiftspeed_changed(self):
        self.icCamera.setHshiftspeed(self.Hshiftspeed)

    def _Vshiftspeed_changed(self):
        self.icCamera.setVshiftspeed(self.Vshiftspeed)

    def _acquisitionmode_changed(self):
        self.icCamera.setacquistionmode(self.acquisitionmode)
        print "acq mode changed"

    def _exposuretime_changed(self):
        self.icCamera.setexposuretime(self.exposuretime)

    def call_menu(self):
        self.configure_traits(view='view_menu')

    def reload_camera(self):
        import pdb; pdb.set_trace()


    def stop_acq_thread(self):
        if self.acq_active:
            self.acq_active = False
            while self.continous_label == 'Stop':
                time.sleep(0.1)

if __name__=="__main__":
    main=CameraGUI(ivCryo = views.cryo.CryoGUI(), ivVoltage = views.voltage.VoltageGUI())
    main.configure_traits()
    if not main.icCamera.simulation:
        print "CAMERA CLOSE"
        main.stop_acq_thread()
        main.icCamera.close()
    if not main.icCryo.simulation:
        print "CRYO CLOSE"
        main.icCryo.close()
    if not main.icVoltage.simulation:
        print "VOLTAGE CLOSE"
        main.icVoltage.close() 
