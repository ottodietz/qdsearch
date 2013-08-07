
from traits.api import *
from traitsui.api import *
from traitsui.menu import OKButton, CancelButton
import thread
from enthought.pyface.api import error,warning,information
import time
from ctypes import *
import pickle
import numpy
from enable.api import BaseTool
from enthought.chaco.api import Plot, ArrayPlotData
from enthought.enable.component_editor import ComponentEditor
from enthought.chaco.tools.api import PanTool, ZoomTool
from enthought.traits.ui.file_dialog  \
    import open_file,save_file


import window_cryo
reload( window_cryo)

import window_spectrometer
reload (window_spectrometer)

import window_camera
reload (window_camera)

from  window_spectrometer import SpectrometerGUI
from  window_cryo import CryoGUI
from window_camera import CameraGUI

call_menu_cryo = Action(name='cryo menu', accelerator='Ctrl+c', action='call_cryo_menu')
call_menu_spectrometer = Action(name='spectrometer menu', accelerator='Ctrl+p', action='call_spectrometer_menu')
save_to=Action(name='Save as',action='save_to')
open_to=Action(name='open...',action='open_to')

printen = Action(name='test Print',accelerator="Ctrl+t",
    action='test_function')

menu = MenuBar(Menu(CloseAction,save_to,open_to, name='File'),
    Menu(UndoAction, RedoAction,printen,
    name='Edit'),
    Menu(call_menu_spectrometer,name='Spectrometer'),
    Menu(call_menu_cryo,name='Cryo'),
    Menu(HelpAction, name='Help'))

class MainWindowHandler(Handler):
    def close(self, info, isok):
        # Return True to indicate that it is OK to close the window.#
        if main.camera_instance.checkbox_camera:
            return True
        else:
            main.camera_instance.cooler=False
            if main.camera_instance.camera.gettemperature() >-1:
                return True
            else:
                print'Please wait until the temperature of the camera is above 0 degrees'

class PlotTool(BaseTool):

    def normal_left_dclick(self, event):
        [x,y]=self.component.map_data((event.x,event.y))
        x=round(x,3)
        y=round(y,3)
        print x
        print y

    def normal_mouse_move(self,event):
        [x,y]=self.component.map_data((event.x,event.y))
        main.plot_spectrum(x,y,'current')

    def normal_right_down(self,event):
        [x,y]=self.component.map_data((event.x,event.y))
        main.plot_spectrum(x,y,'compare')


class MainWindow(HasTraits):
    file_name=File('measurement/spectra.pick')

    """for scanning sample"""
    textfield=Str()
    x1=CFloat(2.05)
    x2=CFloat(2.15)
    y1=CFloat(2.1)
    y2=CFloat(2.2)
    width_sample=CFloat(0.025)
    height_sample=CFloat(0.025)
    wavelength=CFloat(500)
    threshold_voltage=CFloat(3)
    scan_sample=Button()
    scan_sample_step=Button()
    abort=Button()
    finished=True
    x_koords=[]
    y_koords=[]
    spectra=[]

    plot=Instance(Plot)
    plot_current=Instance(Plot)
    plot_compare=Instance(Plot)

    spectrometer_instance = Instance( SpectrometerGUI, () )
    cryo_instance=Instance(CryoGUI,())
    camera_instance=Instance(CameraGUI,())

    scanning=Group(Item('textfield',label='Step width by scanning',style='readonly'),
                        HGroup(Item('x1'),Spring(),Item('x2')),
                        HGroup(Item('y1'),Spring(),Item('y2')),
                        HGroup(Item('width_sample',label='width_sample (x)'),Spring(),Item('height_sample',label='height_sample (y)')),
                        HGroup(Item('wavelength'),Spring(),Item('threshold_voltage')),
                        HGroup(Item('scan_sample',show_label=False),Item('scan_sample_step',show_label=False),Item('abort',show_label=False)),
                        )

    inst_group = Group(
        Item('cryo_instance', style = 'custom',show_label=False,label="cryo",),
        Item('spectrometer_instance', style = 'custom',show_label=False, label="spectrometer",),
        VGroup(scanning,Item('camera_instance',style='custom',show_label=False),label='scan sample'),
        HGroup(Item('plot',editor=ComponentEditor(),show_label=False,height=100,width =200),
            VGroup(Item('plot_current',editor=ComponentEditor(),show_label=False,width =10,height=20),Item('plot_compare',editor=ComponentEditor(),show_label=False,width =10,height=20)),label='plots'),
        layout='tabbed')

    traits_view = View(
        inst_group,
     menubar=menu,
    title   = 'qdsearch',
    buttons = [ 'OK' ],
    handler=MainWindowHandler(),
    resizable = True
    )

    def test_function(self):
        print"test"

    def call_cryo_menu(self):
       self.cryo_instance.configure_traits(view='view_menu')

    def call_spectrometer_menu(self):
        print 'the spectrometer menu will follow'
       #self.spectrometer_instance.configure_traits(view='view_menu')

    def _scan_sample_fired(self):
        thread.start_new_thread(self.scanning,())

    def scanning(self):
        if self.camera_instance.camera.init_active:
            information(parent=None, title="please wait", message="The initialization of the camera is running. Please wait until the initialization is finished.")
        else:
            self.x_koords=[]
            self.y_koords=[]
            self.spectra=[]
            self.searching=True
            self.finished=False
            x1=self.x1
            y1=self.y1
            x2=self.x2
            y2=self.y2
            if x1>x2:
                temp=x1
                x1=x2
                x2=temp
            x_start=x1
            y_start=y1
            x_target=x1
            y_target=y2

            f = open(self.file_name, "w") # creates new file
            f.close()

            if y_start<y_target:
                sign=1
            else:
                sign=-1
            width=self.width_sample #x-koordinaten abstand
            height=self.height_sample #  y koordinaten abstand
            threshold_voltage=self.threshold_voltage # Schwellenspannung

            self.cryo_instance.cryo.move(x_start,y_start) #faehrt zum startpunkt
            if self.spectrometer_instance.current_exit_mirror=='front': #ueberprueft ob spiegel umgeklappt bzw falls nicht klappt er ihn um
                 self.spectrometer_instance.current_exit_mirror='side'#self.spectrometer_instance.exit_mirror_value[1
            self.cryo_instance.cryo.waiting() #wartet bis cryo dort angekommen


            self.cryo_instance.cryo.move(x_target,y_target)#faengt an zum ersten ziel zu fahren
            """ ein Thread aufmachen fuer den Teil if threshold_voltage < ... und einen fuer den while if not self.cryo_instance.cryo.status() teil ,
            sodass sie parallel laufen koennen"""
            while not self.finished:
                while self.searching:
                    if threshold_voltage < self.spectrometer_instance.ivolt.measure(): # vergleicht schwellenspannung mit aktueller
                        self.cryo_instance.cryo.stop() # stopt cryo
                        self.take_spectrum()
                        self.plotten()
                        [x,y]=self.cryo_instance.cryo.convert_output(self.cryo_instance.cryo.position()) #die werte koennten aus zu letzt gespeicherten oder aber von take spectrum uebergeben werden
                        if  (y+sign*height<y_target and sign==1) or(y+sign*height>y_target and sign==-1):
                            self.cryo_instance.cryo.move(x,y+sign*height) # faehrt stueck weiter um von QD weg zusein
                            self.cryo_instance.cryo.waiting() # wartet bis cryo vom QD weg ist
                            self.cryo_instance.cryo.move(x_target,y_target) # faehrt weiter
                            print 'faehrt weiter'
                        else:
                            self.searching=False
                       # self.searching=True # da wenn cryo.status parallel abgefragt wird es auf False gesetz worden ist vremutlich muss der ganze thread dann neu gestartet werden
                    if not self.cryo_instance.cryo.status():
                        self.searching=False

                """ the comparasion is with calculated values it would be better to take the actuall postion of the cryo"""
                """by calculating they are internal rounding erros and than it run one time more than it should"""
                if (x_target>=x2 and (y_target>=y2 or y_target<=y1)) or self.finished: #check if end coordinates are reached
                    self.finished=True
                else:
                    """instead of calculating new values relative move could be used"""
                    # calculates x value for next searching
                    x_start=x_target
                    x_target=x_target+width
                    self.cryo_instance.cryo.move(x_target,y_target) #goes to new x coordinate
                    self.cryo_instance.cryo.waiting()

                     # calculates y value for next searching
                    temp=y_start
                    y_start=y_target
                    y_target=temp
                    sign=sign*-1

                    self.cryo_instance.cryo.move(x_target,y_target) # new target
                    self.searching=True
            print 'searching finish'

    def _scan_sample_step_fired(self):
        thread.start_new_thread(self.scanning_step,())

    def scanning_step(self):
        if self.camera_instance.camera.init_active:
            information(parent=None, title="please wait", message="The initialization of the camera is running. Please wait until the initialization is finished.")
        else:
            self.searching=True
            self.finished=False
            x1=self.x1
            self.x_koords=[]
            self.y_koords=[]
            self.spectra=[]
            y1=self.y1
            x2=self.x2
            y2=self.y2
            if x1>x2:
                temp=x1
                x1=x2
                x2=temp
            x_start=x1
            y_start=y1
            x_target=x1
            y_target=y2
            f = open(self.file_name, "w") # creates new file
            f.close()

            if y_start<y_target:
                sign=1
            else:
                sign=-1
            width=self.width_sample #x-koordinaten abstand
            height=self.height_sample #  y koordinaten abstand
            threshold_voltage=self.threshold_voltage # Schwellenspannung

            self.cryo_instance.cryo.move(x_start,y_start) #faehrt zum startpunkt
            if self.spectrometer_instance.current_exit_mirror=='front': #ueberprueft ob spiegel umgeklappt bzw falls nicht klappt er ihn um
                 self.spectrometer_instance.current_exit_mirror='side'#self.spectrometer_instance.exit_mirror_value[1
            self.cryo_instance.cryo.waiting() #wartet bis cryo dort angekommen
            [x,y]=self.cryo_instance.cryo.convert_output(self.cryo_instance.cryo.position())


            """ ein Thread aufmachen fuer den Teil if threshold_voltage < ... und einen fuer den while if not self.cryo_instance.cryo.status() teil ,
            sodass sie parallel laufen koennen"""
            while not self.finished:
                while ((y<y_target and sign==1) or (y>y_target and sign==-1)) and not self.finished:
                    if threshold_voltage < self.spectrometer_instance.ivolt.measure(): # vergleicht schwellenspannung mit aktueller
                            self.take_spectrum()
                            self.plotten()
                    [x,y]=self.cryo_instance.cryo.convert_output(self.cryo_instance.cryo.position()) #die werte koennten aus zu letzt gespeicherten oder aber von take spectrum uebergeben werden
                    if  (y<y_target and sign==1) or(y>y_target and sign==-1):
                        print 'faehrt'
                        self.cryo_instance.cryo.move(x,y+sign*height) # faehrt stueck weiter um von QD weg zusein
                        self.cryo_instance.cryo.waiting()

                """ the comparasion is with calculated values it would be better to take the actuall postion of the cryo"""
                """by calculating they are internal rounding erros and than it run one time more than it should"""
                if (x_target>=x2 and (y_target>=y2 or y_target<=y1)) or self.finished: #check if end coordinates are reached
                    self.finished=True
                else:
                    """instead of calculating new values relative move could be used"""
                    # calculates x value for next searching
                    x_start=x_target
                    x_target=x_target+width
                    [x,y]=self.cryo_instance.cryo.convert_output(self.cryo_instance.cryo.position())
                    self.cryo_instance.cryo.move(x_target,y_target) #goes to new x coordinate
                    self.cryo_instance.cryo.waiting()
                    [x,y]=self.cryo_instance.cryo.convert_output(self.cryo_instance.cryo.position())

                     # calculates y value for next searching
                    temp=y_start
                    y_start=y_target
                    y_target=temp
                    sign=sign*-1
            print 'searching finish'


    def _abort_fired(self):
        self.finished=True
        self.searching=False
        self.cryo_instance.cryo.stop() #stopt cryo
        print 'abort'

    def take_spectrum(self):
        spectrum=[]
        self.spectrometer_instance.current_exit_mirror='front' # klappt spiegel vom spectro auf kamera um
        time.sleep(0.5) # for slowing mirrors
        if not self.camera_instance.checkbox_camera:
            c_spectrum=self.camera_instance.camera.acqisition() # nimmt das spektrum auf
        else:
            c_spectrum=(c_float * 5)(1, 2,5,6)
            time.sleep(1) # for slowing mirrors
        for i in range(len(c_spectrum)):
            spectrum.append(c_spectrum[i])
        self.spectrometer_instance.current_exit_mirror='side' # klappt spiegel vom spectro auf ausgang um
        [x,y]=self.cryo_instance.cryo.convert_output(self.cryo_instance.cryo.position()) #speichert die aktuellen koordinaten ab
        self.x_koords.append(x)
        self.y_koords.append(y)
        self.spectra.append(spectrum)
        self.save_to_file(x,y,spectrum)
        spectrum=[]

    def save_to_file(self,x,y,spectrum):
        f = open(self.file_name, "a")
        pickle.dump([x,y,spectrum],f)
        f.close()

    def plotten(self):
        plotdata = ArrayPlotData(x=self.x_koords, y=self.y_koords)
        plot = Plot(plotdata)
        plot.plot(("x", "y"), type="scatter", color="blue")
        plot.title = ""
        plot.overlays.append(ZoomTool(component=plot,tool_mode="box", always_on=False)) # damit man im Plot zoomen kann
        plot.tools.append(PanTool(plot, constrain_key="shift")) # damit man mit der Maus den Plot verschieben kann
        plot.tools.append(PlotTool(component=plot))
        self.plot=plot

    def create_wavelength_for_plotting(self,number_y_values):
        """ this function calculates the measured wavelength because the camera can not differentiate between the different wavelength, the calculation is done
        with measured values thereby the maximum and minum wavelength of the camera for a center wavelenght of 900 nm was measured. The different between the max/min value
        and the center wavelength gives the values xless/xmore. The order of the gratings are 600, 1200,1800. Note that these values are wavelength depened.
        900 nm was choosen because it was in the interesting range for the measurement."""
        x_less=[40.97,16.96,6.91] # values for different gratings: 600,1200,1800
        x_more=[40.7,16.4,6.49]
        if self.spectrometer_instance.current_grating.find(' 600')!=-1:
            i=0
        elif self.spectrometer_instance.current_grating.find(' 1200')!=-1:
            i=1
        elif self.spectrometer_instance.current_grating.find(' 1800')!=-1:
            i=2
        try:
            x_min=self.spectrometer_instance.input_nm-x_less[i]
            x_max=self.spectrometer_instance.input_nm+x_more[i]

        except:
            x_min=0
            x_max=number_y_values
        stepwise=(x_max-x_min)/float(number_y_values)
        x_axis=numpy.arange(x_min,x_max,stepwise)
        return(x_axis)

    def plot_spectrum(self,x,y,field):
        tol=0.001
        for i in range(len(self.x_koords)):
            x_gap=abs(x-self.x_koords[i])
            y_gap=abs(y-self.y_koords[i])
            if x_gap <tol and y_gap<tol:
                spectrum=self.spectra[i]
                wavelength=self.create_wavelength_for_plotting(len(spectrum))
                plotdata = ArrayPlotData(x=wavelength, y=spectrum)
                plot = Plot(plotdata)
                plot.plot(("x", "y"), type="scatter", color="blue")
                plot.title = 'spectrum of QD ' +str(self.x_koords[i])+' '+str(self.y_koords[i])
                plot.overlays.append(ZoomTool(component=plot,tool_mode="box", always_on=False)) # damit man im Plot zoomen kann
                plot.tools.append(PanTool(plot, constrain_key="shift")) # damit man mit der Maus den Plot verschieben kann
                if field=='current':
                    self.plot_current=plot
                if field=='compare':
                    self.plot_compare=plot

    def load(self):
        f = open(self.file_name, "r")
        reading=True
        value=[]
        while reading:
            try:
                value.append(pickle.load(f))
            except:
                reading=False
        f.close()
        x=[]
        y=[]
        spectrum=[]
        for i in range(len(value)):
            x.append(value[i][0])
            y.append(value[i][1])
            spectrum.append(value[i][2])
        self.x_koords=x
        self.y_koords=y
        self.spectra=spectrum
        print self.x_koords
        print self.y_koords
        print self.spectra
        self.plotten()

    def save_to(self):
        file_name = save_file()
        if file_name != '':
            self.file_name = file_name
        self.save_file()

    def open_to(self):
        file_name = open_file()
        if file_name != '':
            self.file_name = file_name
        self.load()

    def save_file(self):
        f = open(self.file_name, "w")
        for i in range(len(self.x_koords)):
            pickle.dump([self.x_koords[i],self.y_koords[i],self.spectra[i]],f)
        f.close()





main = MainWindow()
if __name__ == '__main__':
    main.configure_traits()
    if not main.cryo_instance.cryo.simulation:
        print"close cryo"
        main.cryo_instance.cryo.close()
    if not main. spectrometer_instance.spectro.simulation:
        print"close spectro"
        main.spectrometer_instance.spectro.close()
    if not main.spectrometer_instance.ivolt.simulation:
        print"close Voltage"
        main.spectrometer_instance.ivolt.close()
    if not main.camera_instance.checkbox_camera:
        main.camera_instance.camera.close()