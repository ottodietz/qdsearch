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
import math
import numpy as np
from time import sleep
from ctypes import *


import controls.camera
#refresh (controls.camera)
import views.cryo
#refresh (views.cryo)
import views.voltage
#refresh (views.voltage)
import views.spectrometer
#refresh (views.spectrometer)

from pyface.api import error,warning,information

class CameraGUI(HasTraits):
    icCamera = controls.camera.Camera()

    acq_active = False
    toggle_active = False

    simulation=Bool(True)
    nmscale = Bool(True)
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
    ivSpectro = Instance(views.spectrometer.SpectroGUI)
    icSpectro = Instance(controls.spectrometer.Spectro)

    """menu"""
    exposuretime=Range(low=0.0001,high=10,value=icCamera.exposuretime_init,editor=TextEditor(evaluate=float,auto_set=False))
#List(list()),first make from dict_list an list then convert to a Traits List
    Vshiftspeed_keys = List(list(icCamera.Vshiftspeed_keys))
    Hshiftspeed_keys = List(list(icCamera.Hshiftspeed_keys))
    readmode_keys = List(list(icCamera.readmode_keys))
    acquisitionmode_keys = List(list(icCamera.acquisitionmode_keys))
    readmode = Str(icCamera.readmode_init)
    Vshiftspeed = Str(icCamera.Vshiftspeed_init)
    Hshiftspeed = Str(icCamera.Hshiftspeed_init)
    acquisitionmode = Str(icCamera.acquisitionmode_init)
    output=Str()
    plot = Instance(Plot,())
    
    def _icCryo_default(self):
        return self.ivCryo.icCryo
    
    def _icVoltage_default(self):
        return self.ivVoltage.icVoltage

    def _icSpectro_default(self):
        return self.ivSpectro.icSpectro

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
                            Item('readmode', label="Read Mode",editor=EnumEditor(name='readmode_keys')),
                            Item('acquisitionmode', label="Acquisition Mode",editor=EnumEditor(name='acquisitionmode_keys')),
                            Item('Vshiftspeed',label="Vertical Speed",editor=EnumEditor(name='Vshiftspeed_keys')),
                            Item('Hshiftspeed',label="Horizontal Speed",editor=EnumEditor(name='Hshiftspeed_keys')),
                            Item('nmscale',label="Plot in nm"),
),
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
        
        scaleinnm=self.create_wavelength_for_plotting()
        scaleinpx=np.linspace(0,1023,1024)

        titlepxx = "Pixel [px]"
        titlepxy = "Counts [arb. unit]"
        titlenmx = "Wavelength [nm]"
        titlenmy = "Counts [arb. unit]"

        #range for img_plot
        x1px = 0
        x2px = 1023
        y1px = 0
        y2px = 127
        x1nm = scaleinnm[0]
        x2nm = scaleinnm[1024] #because create_wavelength returns len(scaleinm)=1025 .. mistake ..need to fix?
        y1nm = 0
        y2nm = 127

        if self.nmscale:
            xtitle = titlenmx
            ytitle = titlenmy
            scale = scaleinnm
            if self.icCamera.readmode_current == "Image":
                ytitle = titlepxx #because in image mode y is in px!
            x1 = x1nm
            x2 = x2nm
            y1 = y1nm
            y2 = y2nm
 
        else:
            xtitle = titlepxx
            ytitle = titlepxy
            scale = scaleinpx
            x1 = x1px
            x2 = x2px
            y1 = y1px
            y2 = y2px
        
        
        if self.icCamera.readmode_current == 'Full Vertical Binning':
            plotdata = ArrayPlotData(x = scale , y=self.line[:])
            plot = Plot(plotdata)
            plot.plot(("x","y"),type="line",  color="blue")
        if self.icCamera.readmode_current == 'Image':
            dataarray = [[self.line[i][j] for j in range(1024)] for i in range(128)]
#            import pdb; pdb.set_trace()
            plotdata = ArrayPlotData(imagedata = dataarray) #self.line now has an image stored! since an image comes from acquisition
            plot = Plot(plotdata)
            plot.img_plot("imagedata",xbounds=(x1,x2),ybounds=(y1,y2), colormap = jet)
 
        plot.title = ""
        plot.overlays.append(ZoomTool(component=plot,tool_mode="box", always_on=False))
        plot.tools.append(PanTool(plot, constrain_key="shift"))
        #plot.tools.append(PlotTool(component=plot))
        #plot.range2d.x_range.low=self.x1
        #plot.range2d.x_range.high=self.x2
        #plot.range2d.y_range.low=self.y1
        #plot.range2d.y_range.high=self.y2
        plot.x_axis.title=xtitle
        plot.y_axis.title=ytitle
        self.plot=plot



# dispersion of the gratings in theory  
    def calculate_dispersion(self,wavelength,grooves):
        m=1 #grating order
        x=8.548 #spectro value: half angle
        f=486 # focal length
        phi=math.degrees(math.asin((m*wavelength*grooves/(2*10**6*math.cos(math.radians(x))))))
        dispersion=math.cos(math.radians(x+phi))*10**6/(grooves*f*m)
        return dispersion


# for calculating the scale of plot in nm, if needed
    def create_wavelength_for_plotting(self):
        wavelength=[]
        pixel=1024
        grooves=self.ivSpectro.current_grating.split(' ')
        grooves=int([x for x in grooves if x][1])
        for i in range(pixel+1):
            wavelength.append(i)
        width=26*10**-3
        wavelength[pixel/2]=self.ivSpectro.centerwvl
        for i in range(pixel/2):
            wavelength[pixel/2-i-1]=wavelength[pixel/2-i]-width*self.calculate_dispersion(wavelength[pixel/2-i],grooves)
            wavelength[pixel/2+i+1]=wavelength[pixel/2+i]+width*self.calculate_dispersion(wavelength[pixel/2+i],grooves)
        return wavelength


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
        self.icCamera.setreadmode(self.readmode)

    def _Hshiftspeed_changed(self):
        self.icCamera.setHshiftspeed(self.Hshiftspeed)
    
    def _Vshiftspeed_changed(self):
        self.icCamera.setVshiftspeed(self.Vshiftspeed)
    
    def _acquisitionmode_changed(self):
        self.icCamera.setacquisitionmode(self.acquisitionmode)

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
    main=CameraGUI(ivCryo = views.cryo.CryoGUI(), ivVoltage = views.voltage.VoltageGUI(), ivSpectro = views.spectrometer.SpectroGUI)
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
    if not main.icSpectro.simulation:
        print "SPECTRO CLOSE"
        main.icSpectro.close()
