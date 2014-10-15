#!/usr/bin/env python
# -*- coding: utf-8 -*-

from traits.api import *
from traitsui.api import *
from traits.util import refresh
from traitsui.menu import OKButton, CancelButton
import thread
from pyface.api import information
import time
#from ctypes import *
import pickle as pickle
import numpy as np
from threading import Thread
from enable.api import BaseTool
from time import sleep
import sys

from chaco.api import Plot, ArrayPlotData, AbstractDataRange

from chaco.axis import PlotAxis

from enable.component_editor import ComponentEditor

from chaco.tools.api import PanTool, ZoomTool

from traitsui.file_dialog import open_file,save_file

import views.cryo
# refresh(views.cryo)

import views.spectrometer
# refresh (views.spectrometer)

import views.camera
# refresh (views.camera)

import views.voltage
# refresh (views.voltage)

import controls
# refresh (controls.cryo)

"""events on the plot"""
class PlotTool(BaseTool):
    def normal_left_dclick(self, event):
        [x,y]=self.component.map_data((event.x,event.y))
        main.move_cryo(x,y)

    def normal_mouse_move(self,event):
        [x,y]=self.component.map_data((event.x,event.y))
        main.plot_spectrum(x,y,'current')

    def normal_right_down(self,event):
        print "right mouse"
        [x,y]=self.component.map_data((event.x,event.y))
        main.plot_spectrum(x,y,'compare')

class counts_thread(Thread):
    def run(self):
        while not self.wants_abort:
            self.caller.counts =  self.caller.icVoltage.measure()/self.VoltPerCount
            # we need a waitstate! If not, our gui is constantly updating
            sleep(0.1)

class MainWindow(HasTraits):
    VoltPerCount = 0.002 # 2mv/Count
    autosave_filename = 'measurement/autosave.pkl'
    untoggleall = Button(label='Deactivate all Sim') #For toggling all simulations of all devices

    """for creating the menu"""
    call_menu_scan_sample=Action(name='scansample',action='call_scan_sample_menu')
    save_to=Action(name='Save as',action='save_to')
    open_to=Action(name='open...',action='open_to')
    reload_all=Action(name='reload modules',action='reload_all')
    file_menu = Menu(save_to,open_to,reload_all, CloseAction,name='File')
    scan_sample_menu=Menu(call_menu_scan_sample,name='scan_sample')
    file_name=File('measurement/spectra.pick')

    """for setting"""
    toleranz=CFloat(0.001,desc='gives the toleranzradius for mouse move and click on the plot ')
    offset=CFloat(12)

    """for scanning sample"""
    textfield=Str()
    x1=CFloat(2.05)
    x2=CFloat(2.15)
    y1=CFloat(2.1)
    y2=CFloat(2.2)
    x_stepsize=CFloat(0.025)
    y_stepsize=CFloat(0.025)
    threshold_counts=CFloat(2000)
    counts=CFloat(125)
    scan_sample=Button()
    scan_sample_step=Button()
    scan_range_set=Button()
    abort=Button()
    plotrangestart = Range(low=0,high=1000,value=884,editor=TextEditor(evaluate=int,auto_set=False))
    plotrangemarker = Range(low=0.,high=1000.,value=894.35,editor=TextEditor(evaluate=float,auto_set=False))
    plotrangeend = Range(low=0,high=1000,value=904,editor=TextEditor(evaluate=int,auto_set=False))
    plotrangey = Range(low=0,high=16000,value=5000,editor=TextEditor(evaluate=int,auto_set=False))
    plotrangeset = Button(label="Set")
    plotsetalways = Bool(False)
    finished=True
    x_koords=[]
    y_koords=[]
    used_grating   = []
    used_centerwvl = []
    apd_counts = []
    spectra=[]
    wavelength=CFloat(0)
    plot=Instance(Plot,())
    plot_current=Instance(Plot,())
    plot_compare=Instance(Plot,())
    counts_thread = counts_thread()

    ivSpectro      = Instance(views.spectrometer.SpectroGUI)
    icSpectro      = Instance(controls.spectrometer.Spectro)
    ivCryo         = Instance(views.cryo.CryoGUI)
    icCryo         = Instance(controls.cryo.Cryo)
    ivVoltage      = Instance(views.voltage.VoltageGUI)
    icVoltage      = Instance(controls.voltage.Voltage)
    ivCamera       = Instance(views.camera.CameraGUI)# No ",()" as below, Instance is created in _default
    icCamera       = Instance(controls.camera.Camera)

    def _ivCamera_default(self):
        print "CAMERA INIT"
        return views.camera.CameraGUI(ivCryo=self.ivCryo, ivVoltage=self.ivVoltage, ivSpectro=self.ivSpectro )

    def _ivCryo_default(self):
        print "CRYO INIT"
        return views.cryo.CryoGUI()

    def _ivSpectro_default(self):
        print "SPECTRO INIT"
        return views.spectrometer.SpectroGUI(ivVoltage=self.ivVoltage)

    def _ivVoltage_default(self):
        print "VOLTAGE INIT"
        return views.voltage.VoltageGUI()

    def _icVoltage_default(self):
        return self.ivVoltage.icVoltage

    def _icCamera_default(self):
        return self.ivCamera.icCamera

    def _icCryo_default(self):
        return self.ivCryo.icCryo

    def _icSpectro_default(self):
        return self.ivSpectro.icSpectro

    hide_during_scan = { 'enabled_when': 'finished==True'}
    hide_no_scan = { 'enabled_when': 'finished==False'}
    hide = { 'enabled_when': 'False'}

    scan_ctrl=VGrid(

                Label('Scan'),
                Label('from'),
                Label('to'),
                Label('stepsize [mm]'),
                Label('counts'),
                Label('threshold'),
                '0',
                Label('x:'),
                Item('x1',show_label=False,**hide_during_scan),
                Item('x2',show_label=False,**hide_during_scan),
                Item('x_stepsize',show_label=False,**hide_during_scan),
                Item('counts',show_label=False,editor=TextEditor(format_str='%5.0f', evaluate=float),**hide),
                Item('threshold_counts',show_label=False,editor=TextEditor(format_str='%5.0f',evaluate=float),**hide_during_scan),
                '0',
                Label('y:'),
                Item('y1',show_label=False,**hide_during_scan),
                Item('y2',show_label=False,**hide_during_scan),
                Item('y_stepsize',show_label=False,**hide_during_scan),
                Item('scan_sample_step',label='Scan',show_label=False,**hide_during_scan),
                Item('abort',show_label=False,**hide_no_scan),

                columns = 7
                  )


    scan_plotctrl=VGrid(

                Label('Start'),
                Label('Marker'),
                Label('End'),
                Label('Count Range'),
                '0','0',
                Item('plotrangestart', style = 'simple',show_label=False),
                Item('plotrangemarker', style = 'text', show_label=False),
                Item('plotrangeend', style = 'simple', show_label=False),
                Item('plotrangey', style = 'text', show_label=False),
                Item('plotsetalways', style = 'simple',label='keep', show_label=True),
                Item('plotrangeset', style ='simple',show_label=False),

                columns=6
                )

    device_tab = HSplit(
        Item('ivCryo',    editor=InstanceEditor( label="Cryostat",kind='live'), \
                show_label=False, enabled_when='finished==True'),
        Item('ivSpectro', editor=InstanceEditor( label="Spectrometer",   kind='live'), show_label=False),
        Item('ivCamera',  editor=InstanceEditor( label="Camera",        kind='live'), show_label=False),
        Item('ivVoltage', editor=InstanceEditor( label="Voltmeter",     kind='live'), show_label=False),
        Item('untoggleall', show_label=False),
        )


    scan_sample_group=VGroup(HGroup(
            VGroup(
                Item('plot',editor=ComponentEditor(size=(200,200)),show_label=False),
                scan_ctrl
                ),
            VGroup(
                Item('plot_current',editor=ComponentEditor(size=(100,200)),show_label=False),
                scan_plotctrl,
                Item('plot_compare',editor=ComponentEditor(size=(100,200)),show_label=False)
                ),

            show_border=True),device_tab)

    traits_view = View(
        scan_sample_group,
        menubar=MenuBar(file_menu,views.cryo.CryoGUI.menu,scan_sample_menu),
        title   = 'qdsearch',
#        buttons = [ 'OK' ],
        resizable = True,
#        width=300
    )

    setting_view=View(Item('toleranz'),Item('offset'),
                        buttons = [OKButton, CancelButton,],
                        kind='livemodal')

    def __init__(self,*args,**kwargs):
        self.initkwargs=kwargs
        self.initargs=args
        super(MainWindow,self).__init__(*self.initargs,**self.initkwargs)
        self.run_counts_thread()

    def _untoggleall_fired(self):
        self.ivVoltage.simulation = False
        sleep(0.2)
        self.ivCryo.simulation = False
        sleep(0.2)
        self.ivSpectro.simulation = False
        sleep(1.5)
        self.ivCamera.simulation = False

#    def call_cryo_menu(self):
#       self.ivCryo.configure_traits(view='view_menu')
#
#    def call_spectrometer_menu(self):
#       self.ivSpectro.configure_traits(view='view_menu')

    def call_scan_sample_menu(self):
        self.configure_traits(view='setting_view')

    def _scan_sample_step_fired(self):
        if self.ivSpectro.measurement_process or self.ivSpectro.acquisition_process:
            information(parent=None,title='please wait', message='Measurement at the spectrometer is running please finish this first.')
        else:
            thread.start_new_thread(self.scanning_step,())


    def _abort_fired(self):
        self.finished=True
        self.icCryo.stop() #stopt cryo
        print 'abort'

    def run_counts_thread(self):
        self.counts_thread.wants_abort = False
        self.counts_thread.caller = self
        self.counts_thread.VoltPerCount = self.VoltPerCount
        self.counts_thread.start()



    def scanning_step(self):

        if self.icCamera.init_active:
            information(parent=None, title="please wait",
             message="The initialization of the camera is running. " + \
             "Please wait until the initialization is finished.")
            return False

        #self.icCryo.cryo_refresh=False
        self.finished=False
        self.x_koords=[]
        self.y_koords=[]
        self.spectra=[]
        self.used_centerwvl=[]
        self.used_grating=[]
        self.apd_counts=[]

        if self.x1>self.x2:
            self.x2,self.x1 = self.x1,self.x2

        if self.y1>self.y2:
            self.y1,self.y2=self.y2,self.y1

        if self.ivSpectro.exit_mirror=='front (CCD)': #ueberprueft ob spiegel umgeklappt bzw falls nicht klappt er ihn um
             self.ivSpectro.exit_mirror='side (APDs)'#self.ivSpectro.exit_mirror_value[1

        self.icCryo.waiting() #wartet bis cryo bereit

        #TODO das hier gehört nach cryo
        # [x,y] = self.icCryo.get_numeric_position()
        #x,y=self.icCryo.convert_output(self.icCryo.position())

        x_pos,y_pos = self.calc_snake_xy_pos()

        for i in range(len(x_pos)):
            if self.finished:
                break # abort condition
            self.icCryo.move(x_pos[i],y_pos[i])
            self.icCryo.waiting()
            # get actuall position, maybe x_pos[i] != x
            x,y=self.icCryo.pos()
            if self.threshold_counts < self.icVoltage.measure()/self.VoltPerCount: # vergleicht schwellenspannung mit aktueller
                self.take_spectrum(x,y)
            self.plot_map(x,y)

        self.finished = True
        print 'searching finish'

    def take_spectrum(self,x,y):
        print "nehme spektrum, warte auf klappspiegel"
        self.ivSpectro.exit_mirror='front (CCD)' # klappt spiegel vom spectro auf kamera um
        sleep(1) # don't switch mirrors too fast!
        try:
            c_spectrum=self.icCamera.acquisition(sim_pos=self.icCryo.pos(),sim_volt=self.ivVoltage.Voltage,exptme=self.ivCamera.exposuretime) # nimmt das spektrum auf
        except:
            c_spectrum=self.icCamera.acquisition() # nimmt das spektrum auf

        spectrum=[]
        for i in range(len(c_spectrum)):
            spectrum.append(c_spectrum[i])

        self.ivSpectro.exit_mirror='side (APDs)' # klappt spiegel vom spectro auf ausgang um

        # warning: we don't check if we are still at the same position!

        self.x_koords.append(x)
        self.y_koords.append(y)
        self.spectra.append(spectrum)
        self.used_centerwvl.append(self.ivSpectro.centerwvl)
        self.used_grating.append(self.ivSpectro.current_grating)
        self.apd_counts.append(self.icVoltage.measure()*500)

        self.file_name = self.autosave_filename
        self.save_file()

    def reload_all(self):
        refresh()
        import pdb;pdb.set_trace()

    def plot_map(self,x,y):
        plotdata = ArrayPlotData(x=self.x_koords, y=self.y_koords,x2=[x],y2=[y])
        plot = Plot(plotdata)
        plot.plot(("x", "y"), type="scatter", color="blue")
        plot.title = ""
        plot.overlays.append(ZoomTool(component=plot,tool_mode="box", always_on=False))
        plot.tools.append(PanTool(plot, constrain_key="shift"))
        plot.tools.append(PlotTool(component=plot))
        plot.plot(('x2','y2'),type='scatter',color='red')
        plot.range2d.x_range.low=self.x1
        plot.range2d.x_range.high=self.x2
        plot.range2d.y_range.low=self.y1
        plot.range2d.y_range.high=self.y2
        plot.x_axis.title="x-Position on sample [mm]"
        plot.y_axis.title="y-Position on sample [mm]"
        self.plot=plot


    def _plotrangeset_fired(self):
        if self.plotrangestart > self.plotrangeend:
            self.plotrangestart, self.plotrangeend = self.plotrangeend, self.plotrangestart#swap val
        if self.plotrangestart == self.plotrangeend:
            self.plotrangestart = 884
            self.plotrangeend = 904
        if self.plotrangemarker>self.plotrangeend or self.plotrangemarker<self.plotrangestart:
            self.plotrangemarker = self.plotrangestart+(self.plotrangeend-self.plotrangestart)/2.
        self.plot_compare.plot(("xm","ym"),type="line", color="red")
        self.plot_current.plot(("xm","ym"),type="line", color="red")
        self.plot_current.range2d.x_range.high = self.plotrangeend
        self.plot_current.range2d.x_range.low = self.plotrangestart
        self.plot_compare.range2d.x_range.high = self.plotrangeend
        self.plot_compare.range2d.x_range.low = self.plotrangestart
        self.plot_current.range2d.y_range.high = self.plotrangey
        self.plot_compare.range2d.y_range.high = self.plotrangey
        self.plot_current.range2d.y_range.low = 0
        self.plot_compare.range2d.y_range.low = 0


    def plot_spectrum(self,x,y,field):
        for i in range(len(self.x_koords)):
            x_gap=abs(x-self.x_koords[i])
            y_gap=abs(y-self.y_koords[i])
            if x_gap <self.toleranz and y_gap<self.toleranz:
                spectrum=self.spectra[i]
                wavelength=self.ivCamera.create_wavelength_for_plotting()
                xm = [self.plotrangemarker,self.plotrangemarker] #for red line in plot
                ym = [0,16000] #self.plotrangey
                plotdata = ArrayPlotData(x=wavelength, y=spectrum,xm=xm,ym=ym)
                plot = Plot(plotdata)
                plot.plot(("x", "y"), type="line", color="blue")
                plot.x_axis.title="Wavelength [nm]"
                plot.y_axis.title="Counts"

                #catch error if apd counts not loaded
                try:
                    apd_counts = str(self.apd_counts[i])
                except:
                    apd_counts = str("0")

                plot.title = 'spectrum of QD ' +str(self.x_koords[i])+' '+str(self.y_koords[i])+' with APD at '+str(apd_counts)
                plot.overlays.append(ZoomTool(component=plot,tool_mode="box", always_on=False)) # damit man im Plot zoomen kann
                plot.tools.append(PanTool(plot, constrain_key="shift")) # damit man mit der Maus den Plot verschieben kann
                if field=='current':
                    self.plot_current=plot
                    if self.plotsetalways:
                        self._plotrangeset_fired()
                if field=='compare':
                    self.plot_compare=plot
                    if self.plotsetalways:
                        self._plotrangeset_fired()

    def move_cryo(self,x,y):
        """looks whether a measured point is close to the plot event"""
        if self.finished:
            for i in range(len(self.x_koords)):
                x_gap=abs(x-self.x_koords[i])
                y_gap=abs(y-self.y_koords[i])
                if x_gap <self.toleranz and y_gap<self.toleranz:
                    self.icCryo.move(self.x_koords[i],self.y_koords[i])
                    break

    def calc_snake_xy_pos(self):
        dist_x = abs(self.x2-self.x1)
        dist_y = abs(self.y2-self.y1)
        a = np.linspace(self.x1,self.x2,dist_x/self.x_stepsize)
        b = np.linspace(self.y1,self.y2,dist_y/self.y_stepsize) # hier war dist_y

        a = a.round(5)
        b = b.round(5)

        stepsa = len(a)
        stepsb = len(b)

        # we go snake-lines, so in the first y-step x=1,2 and in the
        # second y-step (the way back) x=2,1 .
        # Make a containing these two lines
        # a = [1,2] -> [1,2,2,1]
        a = np.array((a,np.flipud(a))).flatten()
        # repeat entire array a. This creates too many lines.
        a = np.tile  (a,stepsb)
        # within one line, y doesn't change, so repeat every element in b
        b = np.repeat(b,stepsa)
        #  discard unecessary elements in a
        a = np.resize(a,len(b))
        return [a,b]

    def save_to(self):
        file_name = save_file()
        print file_name
        if file_name != '':
            self.file_name = file_name
        self.save_file()

    def open_to(self):
        file_name = open_file()
        if file_name != '':
            self.file_name = file_name
        self.load()

    def save_file(self):
        f = open(self.file_name, "wb")

        data = {
            'cryo': {'x1':self.x1,
                     'x2':self.x2,
                     'y1':self.y1,
                     'y2':self.y2,
                     'x_stepsize':self.x_stepsize,
                     'y_stepsize':self.y_stepsize
                    },

            'spectrometer': { 'centerwvl': self.ivSpectro.centerwvl,
                              'grating': self.ivSpectro.current_grating,
                              'slit_width_in': self.ivSpectro.slit_width_in,
                              'slit_width_out': self.ivSpectro.slit_width_out
                            },
            'voltage': {
                    'threshold': self.threshold_counts
                    },

            'camera': {
                    'exposuretime':self.ivCamera.exposuretime,
                    'readmode':self.ivCamera.readmode,
                    'acquisitionmode':self.ivCamera.acquisitionmode,
                    'Vshiftspeed ':self.ivCamera.Vshiftspeed,
                    'Hshiftspeed ':self.ivCamera.Hshiftspeed
                    },

            'values': {
                    'x':self.x_koords,
                    'y':self.y_koords,
                    'spectra': self.spectra,
                    'grating': self.used_grating,
                    'apd-count': self.apd_counts,
                    'centerwvl': self.used_centerwvl
                }
            }

        pickle.dump(data,f)
        f.close()

    def pop(self,data,device,key):

        if device in data:
            if key in data[device]:
                temp = data[device].pop(key)
                return temp
            else:
                error = 'no key ',key,' in device ',device
        else:
            error = 'no device ',device, ' in data'
        print error
        return None



    def load(self):
        f = open(self.file_name, "rb")
        data = pickle.load(f)
        f.close()

        self.x1 = self.pop(data,'cryo','x1')
        self.x2 = self.pop(data,'cryo','x2')
        self.y1 = self.pop(data,'cryo','y1')
        self.y2 = self.pop(data,'cryo','y2')
        self.x_stepsize = self.pop(data,'cryo','x_stepsize')
        self.y_stepsize = self.pop(data,'cryo','y_stepsize')

        self.ivSpectro.centerwvl = self.pop(data,'spectrometer','centerwvl')
        self.ivSpectro.current_grating = self.pop(data,'spectrometer','grating')
        self.ivSpectro.slit_width_in = self.pop(data,'spectrometer','slit_width_in')
        self.ivSpectro.slit_width_out = self.pop(data,'spectrometer','slit_width_out')

        self.threshold_counts = self.pop(data,'voltage','threshold')

        self.ivCamera.exposuretime = self.pop(data,'camera','exposuretime')
        self.ivCamera.readmode = self.pop(data,'camera','readmode')
        self.ivCamera.acquisitionmode = self.pop(data,'camera','acquisitionmode')
        self.ivCamera.Vshiftspeed = self.pop(data,'camera','Vshiftspeed ')
        self.ivCamera.Hshiftspeed = self.pop(data,'camera','Hshiftspeed ')

        self.x_koords = self.pop(data,'values','x')
        self.y_koords = self.pop(data,'values','y')
        self.spectra = self.pop(data,'values','spectra')

        self.plot_map(self.x_koords[0], self.y_koords[0])

        # raise load warning
        self.pop(data,'none','none')
        self.pop(data,'values','none')

        for device in data:
            for key in data[device]:
                print 'Did not load values from file:', device,key

main = MainWindow()
if __name__ == '__main__':

    if sys.platform[0]=="w": #Fuer das reskalieren in windows
        scroll = True
    else:
        scroll = False

    scroll = False

    main.configure_traits(scrollable = scroll)
    main.icCryo.open=False
    main.counts_thread.wants_abort=True
    sleep(1.0)

    if not main.icCryo.simulation:
        print"CLOSE CRYO"
        main.icCryo.close()
        main.ivCryo.cryo_refresh=False
    if not main.icSpectro.simulation:
        print"CLOSE SPECTROMETER"
        main.icSpectro.close()
    if not main.icVoltage.simulation:
        print"CLOSE VOLTAGE"
        main.icVoltage.close()
    main.icCamera.close()


