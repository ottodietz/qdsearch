#!/usr/bin/env python
# -*- coding: utf-8 -*-
from traits.api import*
from traitsui.api import*
from traits.util import refresh
from traitsui.menu import OKButton, CancelButton
from enable.api import BaseTool
from chaco.api import Plot, ArrayPlotData, PlotGraphicsContext, jet
from chaco.tools.api import PanTool, ZoomTool
from pyface.api import FileDialog,OK
from enable.component_editor import ComponentEditor
import thread
import threading
import math
import numpy as np
from time import sleep
import time
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

    acqtime = time.localtime #time of acq., will be updated for every acq.
    simulation=Bool(True)
    cooler=Bool(False)
    progress = Str(" \t") #shows progress of what soever process
    mousex = Str("\t\t")
    mousey = Str("\t\t")

    #variables for the scale of the plot
    scaleinnm = [] #empty array for create_wavelenth_for_plotting()
    scaleinpx=np.linspace(0,1023,1024) # pixel are number from 0 to 1023
    scaletype_label = Str('Scale in NM')
    nmscale = Bool(False) # False: scale in pxl
    
    #variables for own calibration
    calib = Bool(False)
    calibwvl = Range(low=0,high=5000,value=894.35,editor=TextEditor(evaluate=float,auto_set=False))
    calibpxl = Range(low=0,high=1023,value=512,editor=TextEditor(evaluate=int,auto_set=False))


    scaletype = Button()
    speeddata = Button(label="Show HS/VS Data")
    single=Button()
    continous_label = Str('Continous')
    continous=Button()
    xyautofocus=Button(label="AF X/Y")
    zautofocus=Button(label="AF Z")
    export=Button(label="Export")

    # Ints that come from a mouse-event on the cameraplot to define the
    # center for the AF
    AFX = Int()
    #defines the radius around the center
    AFRange = int(3)
    #range for the AFs, to be set by afrange()
    _from = int(0)
    _to = int(1023)
    #step size for the AF
    x_step = float(0.0005)
    y_step = float(0.0005)

    #creating all the necessary Instances
    ivCryo = Instance(views.cryo.CryoGUI)
    icCryo = Instance(controls.cryo.Cryo)
    ivVoltage = Instance(views.voltage.VoltageGUI)
    icVoltage = Instance(controls.voltage.Voltage)
    ivSpectro = Instance(views.spectrometer.SpectroGUI)
    icSpectro = Instance(controls.spectrometer.Spectro)

    """menu"""
    exposuretime=Range(low=0.0001,high=10,value=icCamera.exposuretime_init,editor=TextEditor(evaluate=float,auto_set=False))
    settemperature=Range(low=-70,high=20,value=20)
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


    hide = {'enabled_when':'acq_active==False'} #if continous runs disable button
    traits_view=View(HGroup(VGroup(
                            HGroup(
                                    Item('single',label='Single',show_label=False,**hide),
                                    Item('continous',show_label=False,editor=ButtonEditor(label_value='continous_label')),
                                    Item('speeddata',show_label=False,**hide),
                                    Item('xyautofocus',show_label=False,**hide),
                                    Item('zautofocus',show_label=False,**hide),
                                    Item('export',show_label=False,**hide)
                                    ),
                            HGroup(
                                Item('exposuretime'),
                                Item('simulation',label='simulate'),
                                Item('progress',label='Progress',style='readonly'),
                                Item('mousex',label='X ',style='readonly'),
                                Item('mousey',label='Y ',style='readonly')),
                            Item('readmode', label="Read Mode",editor=EnumEditor(name='readmode_keys'),**hide),
                            Item('acquisitionmode', label="Acquisition Mode",editor=EnumEditor(name='acquisitionmode_keys'),**hide),
                            Item('Vshiftspeed',label="Vertical Speed",editor=EnumEditor(name='Vshiftspeed_keys')),
                            Item('Hshiftspeed',label="Horizontal Speed",editor=EnumEditor(name='Hshiftspeed_keys')),
                            HGroup(
                                Item('scaletype',show_label=True,editor=ButtonEditor(label_value='scaletype_label')),
                                Item('calib',label="Calibrate"),
                                Item('calibwvl',label="Wavelength",enabled_when='calib==True'),
                                Item('calibpxl',label="Pixel",enabled_when='calib==True')
                                )
                            ),
                            VGroup(
                                Item('plot',editor=ComponentEditor(size=(50,50)),show_label=False))),
                        resizable = True,
                        height=300, 
                        width=900, 
                        menubar=MenuBar(menu))

    def _single_fired(self):
        self.acquisition()
        self.plot_data()

    def afrange(self):
        """returns range for the AFs we have to define in advance which part of the spectrum we want to maximize because QDs have small peaks in a potentially big ocean of other signals""" 
        if self.AFX: #if mouse event has happend
            start = self.AFX - self.AFRange #center minus the radius
            end = self.AFX + self.AFRange #center plus the radius
        else: #if no center has been chosen, take whole spectrum
            start = 0
            end = 1023
        if self.nmscale: #if scale in in nm show start and end in nm
            print "AF will maximize signal  in the range from "+str(self.scaleinnm[start])+"nm to "+str(self.scaleinnm[end])+"nm"
        else: # if scale is in pxl
            print "AF will maximize signal  in the range from "+str(start)+"px to "+str(end)+"px"
        return start,end

    def _zautofocus_fired(self):
        #needs to be a thread, so that gui can refresh within the thread!!
        thread.start_new_thread(self.zautofocus_thread,())
    

    def zautofocus_thread(self):
        self._from, self._to = self.afrange()
        maxid = 0 #Wert der Spannung bei Maximalen Counts, setze auf -1
        maxcount = 0 #Maximale Counts, setze auf 0
        maxvolt = float(0)
        shift = float(0)
        steps = float(10)
        iterations = int(3) #speed linear in n,2 fast,3exact
        for it in range(iterations):
            shift = shift+maxid*(5./10**(it-1)/steps)
            for i in range(int(steps)):
                volt = float((i+0.5)*5./(10**it)/steps+shift)
                self.ivVoltage.Voltage = volt
                self.acquisition()
                self.progress = str(int(((it+1)*(i+1))*100/(iterations*steps)))
                if int(self.progress)%10 == 0: #plot 10 times
                    self.plot_data()
                if maxcount < max(self.line[self._from:self._to]):
                    maxcount = max(self.line[self._from:self._to])
                    maxvolt = volt
                    maxid = i
        
        print "Im Fokus bei der Spannung %1.1f" % maxvolt
        print "Highest measured count when focusing: %5d" % maxcount
        self.ivVoltage.Voltage = maxvolt
        self.acquisition()
        self.plot_data()


    def _xyautofocus_fired(self):
        #needs to be a thread, so that gui can refresh within the thread
#        thread.start_new_thread(self._autofocus_hillclimbing_thread,())
#        thread.start_new_thread(self._autofocus_snake_thread,())
#        thread.start_new_thread(self._autofocus_high_res_thread,())
        thread.start_new_thread(self._autofocus_simple_thread,())


    def _autofocus_simple_thread(self):
        self._from,self._to = self.afrange()
        sm = self.icCryo.sm #smalles step of cryo
        self.progress = str(0)
        self.scan_simple(sm,0)
        self.progress = str(50)
        self.scan_simple(0,sm)
        self.progress = str(100)
        print "x-y maximized"
        

    def scan_simple(self,x,y):
        radius = 20 #in what range around the qd to scan
        counts = int(0)
        current = int(0)
        diff = int(0) #difference between highest counts and 2nd highest

        for i in range(radius):
            self.acquisition() #fill self.line with data
            current = max(self.line[self._from:self._to])
            if current >= counts:
                diff = current-counts
                counts = current
            self.plot_data()
            self.icCryo.rmove(x,y)

        for i in range(2*radius):
            self.acquisition() #fill self.line with data
            current = max(self.line[self._from:self._to])
            if current >= counts:
                diff = current-counts
                counts = current
            self.plot_data()
            self.icCryo.rmove(-x,-y)

        for i in range(2*radius):
            self.acquisition() #fill self.line with data
            current = max(self.line[self._from:self._to])
            self.plot_data()
            if current >= counts-diff/2:
                break
            self.icCryo.rmove(x,y)
            

    def _autofocus_snake_thread(self):
        """ goes for a snake like scan, like algorithm in qdsearch for the maximum
of counts in a square around the center of the starting point of the search,
unit: self.x_step """
        
        self._from, self._to = self.afrange()
        xstart,ystart = self.icCryo.pos() #get cryo pos at the start
        sqlen = int(6) #length of the square
        maximum = [0,0,0] #stores x,y and counts of stronges signal measured in scan

        self.acquisition() #fill self.line with data
        maximum[0] = xstart
        maximum[1] = ystart
        maximum[2] = max(self.line[self._from:self._to])
        self.icCryo.rmove(-int(sqlen/2.)*self.x_step,-int(sqlen/2.)*self.y_step)
        x = int(0) #coordinates of the grid in the square
        y = int(0)

        #snake scanning
        for i in range(sqlen):
            for j in range(sqlen):
                self.acquisition()
                current = max(self.line[self._from:self._to])
                if maximum[2] < current:
                    maximum[0]=i
                    maximum[1]=j
                    maximum[2]=current
                self.icCryo.rmove(0,((-1)**(i%2))*self.y_step) #parity change for i 
            self.icCryo.rmove(self.x_step,0)

        if maximum[0] == xstart: #no better spot found
            print "no better point in scan, than where you started!"
            self.icCryo.move(xstart,ystart)

        else: #move to maximum position
            xmax = xstart-int(sqlen/2.)*self.x_step+maximum[0]*self.x_step
            ymax = ystart-int(sqlen/2.)*self.y_step+maximum[1]*self.y_step
            self.icCryo.move(xmax,ymax) #one move() is better that 3 (hysterese)
        print "you found a new position"
        self.acquisition()
        self.plot_data()

    def _autofocus_high_res_thread(self):
        """ hysterese sensitiv hillclimbing + count awareness """
        self._from, self._to = self.afrange()
        sm = self.icCryo.sm #smalles step of cryo
        rd = 5 #radius of search, unit: sm
        #first line: position, second line:mean data
        xdata = [[0 for x in range(2*rd+1)] for x in range(2)] #array with zeros
        ydata = [[0 for x in range(2*rd+1)] for x in range(2)] #array with zeros

        # build datalist in positiv x-direction
        for i in range(rd+1):
            if i != 0:#make a step, just not for i=0
                self.icCryo.rmove(sm,0)
            xdata[0][i] = rd+i
            xdata[1][i] = self.qd_mean()
        #now go back to start pos
        while True: #check if at origin
            self.icCryo.rmove(-sm,0)
            end = self.pos_check(xdata,rd)
            if end == True:
                break
        #build datalist in neg x-direction
        for i in range(rd):
            self.icCryo.rmove(-sm,0)
            xdata[0][rd+i+1] = rd-1-i
            xdata[1][rd+i+1] = self.qd_mean()
        mindex = xdata.index(max(xdata[0]))
        mpos = xdata[0][mindex]
        #now go to the maximum
        while True:
            self.icCryo.rmove(sm,0)
            end = self.pos_check(xdata,mpos)
            if end == True:
                break
        print "x-direction maximized"

        # build datalist in positiv y-direction
        for i in range(rd+1):
            if i != 0:
                self.icCryo.rmove(0,sm)
            ydata[0][i] = rd+i
            ydata[1][i] = self.qd_mean()
        #now go back to start pos
        while True: #check if at origin
            self.icCryo.rmove(0,-sm)
            end = self.pos_check(ydata,rd) #returns True if at new pos
            if end == True:
                break

        #build datalist in neg y-direction
        for i in range(rd):
            self.icCryo.rmove(0,-sm)
            ydata[0][rd+i+1] = rd-1-i
            ydata[1][rd+i+1] = self.qd_mean()
        mindex = ydata.index(max(ydata[0]))
        mpos = ydata[0][mindex]
        #now go to the maximum
        while True:
            self.icCryo.rmove(0,sm)
            end = self.pos_check(ydata,mpos)
            if end == True:
                break
        print "y-direction maximized"


    def pos_check(self,data,pos):
        """ statistically checks if cryo has actually moved to pos """
        mean = self.qd_mean()
        #realpos is index of THE value
        #THE value is the clostest representation in data
        index = min(range(len(data)), key=lambda i: abs(data[i]-mean))
        realpos = int(data[0][index])
        if realpos == pos:
            return True
        else:
            return False

    def qd_mean(self):
        """ returns mean counts of n measurements of the QD """
        for i in range(10):
            accum = []
            self.acquisition()
            accum.append(max(self.line[self._from:self._to]))
        mean = np.mean(accum)
        return mean
    


    def _autofocus_hillclimbing_thread(self):
        """ typical hillclimbing algorithm """
        #be careful x_step is not smallest possible step of cryo
        self._from, self._to = self.afrange()
        xtest = False
        ytest = False
        self.acquisition()
        while not xtest: #Test in die x-Richtung, suchen bis Counts runter
            a = max(self.line[self._from:self._to])
            self.icCryo.rmove(self.x_step,0)
            self.acquisition()
            self.plot_data()
            b = max(self.line[self._from:self._to])
            if b < a:
                self.icCryo.rmove(-self.x_step,0)
                self.acquisition() #damit er wieder das aktuelle max hat
                xtest = True
        xtest=False

        while not xtest: #Test in die -x-Richtung, suchen bis Counts runter
            a = max(self.line[self._from:self._to])
            self.icCryo.rmove(-self.x_step,0)
            self.acquisition()
            self.plot_data()
            b = max(self.line[self._from:self._to])
            if b < a:
                self.icCryo.rmove(self.x_step,0)
                self.acquisition()
                xtest = True

        while not ytest: #Test in die y-Richtung, suchen Counts runter
            a = max(self.line[self._from:self._to])
            self.icCryo.rmove(0,self.y_step)
            self.acquisition()
            self.plot_data()
            b = max(self.line[self._from:self._to])
            if b < a:
                self.icCryo.rmove(0,-self.y_step)
                self.acquisition()
                ytest = True

        ytest = False

        while not ytest: #Test in die -y-Richtung, suchen Counts runter
            a = max(self.line[self._from:self._to])
            self.icCryo.rmove(0,-self.y_step)
            self.acquisition()
            self.plot_data()
            b = max(self.line[self._from:self._to])
            if b < a:
                self.icCryo.rmove(0,self.y_step)
                self.acquisition()
                ytest = True

        self.plot_data()
        print "AF fertig!"


    def plot_data(self):
        self.scaleinnm=self.create_wavelength_for_plotting()

        titlepxx = "Pixel [px]"
        titlepxy = "Counts [arb. unit]"
        titlenmx = "Wavelength [nm]"
        titlenmy = "Counts [arb. unit]"

        #range for img_plot
        x1px = 0
        x2px = 1023
        y1px = 0
        y2px = 127
        x1nm = self.scaleinnm[0]
        x2nm = self.scaleinnm[1023]
        y1nm = 0
        y2nm = 127

        if self.nmscale:
            xtitle = titlenmx
            ytitle = titlenmy
            scale = self.scaleinnm
            if self.icCamera.readmode_current == "Image":
                ytitle = titlepxx #because in image mode y is in px!
            x1 = x1nm
            x2 = x2nm
            y1 = y1nm
            y2 = y2nm
 
        else:
            xtitle = titlepxx
            ytitle = titlepxy
            if self.icCamera.readmode_current == "Image":
                ytitle = titlepxx
            scale = self.scaleinpx
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
            plotdata = ArrayPlotData(imagedata = dataarray) #self.line now has an image stored! since an image comes from acquisition
            plot = Plot(plotdata)
            plot.img_plot("imagedata",xbounds=(x1,x2),ybounds=(y1,y2), colormap = jet)
 
        plot.title = ""
        plot.overlays.append(ZoomTool(component=plot,tool_mode="box", always_on=False))
        plot.tools.append(PanTool(plot, constrain_key="shift"))
        plot.tools.append(CameraGUI_PlotTool(component=plot,caller=self))
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
        #Pixel are numerated from 0 to 1023 as default! useful thing for for-loops
        wavelength=[]
        pixel=1024
        grooves=self.ivSpectro.current_grating.split(' ')
        grooves=int([x for x in grooves if x][1])
        for i in range(pixel):
            wavelength.append(i)
        width=26*10**-3
        
        if not self.calib: #no own calibration so centerwvl from ivspectro is used for center pixel
            wavelength[pixel/2]=self.ivSpectro.centerwvl #be careful wavelength is even, so has no center for precise centerwvl
            for i in range(pixel/2):
                wavelength[pixel/2-i-1]=wavelength[pixel/2-i]-width*self.calculate_dispersion(wavelength[pixel/2-i],grooves)
            for i in range(pixel/2-1): #because 1024 is even, it has no center, so indexshift is needed
                wavelength[pixel/2+i+1]=wavelength[pixel/2+i]+width*self.calculate_dispersion(wavelength[pixel/2+i],grooves)
            return wavelength

        else: #if self.calib == True use this own calibration method for wavelength[]
            wavelength[int(self.calibpxl)]=self.calibwvl #be careful wavelength is even, so has no center for precise centerwvl
            for i in range(self.calibpxl):
                wavelength[self.calibpxl-i-1]=wavelength[self.calibpxl-i]-width*self.calculate_dispersion(wavelength[self.calibpxl-i],grooves)
            for i in range(pixel-self.calibpxl-1): #rest of the pixel which are missing in the first for loop
                wavelength[self.calibpxl+i+1]=wavelength[self.calibpxl+i]+width*self.calculate_dispersion(wavelength[self.calibpxl+i],grooves)
            return wavelength
            

    def _update_acqtime(self):
        self.acqtime = time.localtime()

    def _export_fired(self):
        dialog = FileDialog(action="save as", wildcard='.dat')
        dialog.open()
        if dialog.return_code == OK:
            # prepare plot for saving
            width = 800
            height = 600
            self.plot.outer_bounds = [width, height]
            self.plot.do_layout(force=True)
            gc = PlotGraphicsContext((width, height), dpi=72)
            gc.render_component(self.plot)
     
            #save data,image,description
            timetag = "" #init empty str for later
            directory = dialog.directory
            t = self.acqtime #retrieve time from last aquisition
            timelist = [t.tm_year,t.tm_mon,t.tm_mday,t.tm_hour,t.tm_min,t.tm_sec]
            timelist = map(str,timelist) #convert every entry to str of timelist
            for i in range(len(timelist)): #if sec is eg "5" change to "05"
                if len(timelist[i]) == 1:
                    timelist[i] = "0" + timelist[i]
            timetag = timetag.join(timelist) #make single str of all entries
            filename = timetag + dialog.filename # join timetag and inidivid. name
            print "target directory: " + directory
            gc.save(filename+".png")
            self.wvl = self.create_wavelength_for_plotting()
            x,y = self.icCryo.pos() #get cryo pos
            pos = "Cryo was at pos "+ str(x) + " x " + str(y)+" y"
            with open(filename+'.dat','wb') as f:
                f.write('#'+
                        str(pos)+
                        '\n'+
                        '#\n'+
                        '#\n'+
                        '#\n') #this is for the header
                np.savetxt(f,
                        np.transpose([self.wvl,self.line]),
                        delimiter='\t')
            # pickle(target+'.pkl',info_structure)

    def ensure_init(self):
        if self.icCamera.init_active:
            information(parent=None, title="please wait", message="The initialization of the camera is running. Please wait until the initialization is finished.")
            while self.icCamera.init_active:
                sleep(.5)


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

    def _speeddata_fired(self):
        self.icCamera.speeddata()

    def _scaletype_fired(self):
        if self.nmscale:
            self.scaletype_label = "Scale in NM"
            self.nmscale = False
        else:
            self.scaletype_label = "Scale in Pxl"
            self.nmscale = True  
        self._single_fired() #update the plot 

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

    #fills the data into self.line
    def acquisition(self):
        try:
            self.line=self.icCamera.acquisition(sim_pos=self.icCryo.pos(),sim_volt=self.ivVoltage.Voltage,exptme=self.exposuretime)
        except:
            self.line=self.icCamera.acquisition()
        self._update_acqtime() # saving time of acquisition

    def stop_acq_thread(self):
        if self.acq_active:
            self.acq_active = False
            while self.continous_label == 'Stop':
                sleep(0.1)

    #### Events that handle clicks on plot ###

    def normal_mouse_move(self,event):
        x = float(event.x)
        y = float(event.y)

        if not self.nmscale:
            x = round(x) #closest pixel representation
            y = round(y) #closest count representation
            y = int(y) #no decimal places
            self.mousex = str(x) # str conversion for view
            self.mousey = str(y) # str conversion for view 
        else:  
            a = self.scaleinnm
            #returns index of closest represenation of x in the list of
            #scaleinnm
            x = min(range(len(a)), key=lambda i: abs(a[i]-x))
            y = round(y) #closest count representation
            y = int(y) #no decimal places
            x = a[x] #for getting the wvl of index x
            x = str("%3.3f") % float(x)  
            self.mousex = str(x) # str conversion for listing
            self.mousey = str(y)


    #this def is for getting the center for the AF
    #by a mouseclick on the plot
    def normal_left_down(self, event):
        x = float(event.x)
        
        if not self.nmscale:
            x = round(x) #closest pixel representation
            self.AFX = int(x) # int conversion for listing
            temp = self.AFX
        
        else:
            a = self.scaleinnm
            #returns index of closest represenation of AFX in the list of
            #scaleinnm
            x = min(range(len(a)), key=lambda i: abs(a[i]-x))
            temp = a[x]
            self.AFX = int(x) # int conversion for listing

        print "be careful, you just created a new center for the AF: ",temp

class CameraGUI_PlotTool(BaseTool):

    caller = Instance(CameraGUI)

    def normal_mouse_move(self,event):
        [event.x,event.y]=self.component.map_data((event.x,event.y))
        self.caller.normal_mouse_move(event)

    def normal_left_down(self, event):
        [event.x,event.y]=self.component.map_data((event.x,event.y))
        self.caller.normal_left_down(event)



if __name__=="__main__":
    main=CameraGUI(
                    ivCryo = views.cryo.CryoGUI(), 
                    ivVoltage = views.voltage.VoltageGUI(), 
                    ivSpectro = views.spectrometer.SpectroGUI()
                )
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
