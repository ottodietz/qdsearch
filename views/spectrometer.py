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

import controls.voltage
reload(controls.voltage)

import views.camera
reload (views.camera)

class SpectrometerGUI(HasTraits):
    ivolt=controls.voltage.Voltage('COM9', 115200, timeout=1)
    ispectro=controls.spectrometer.Spectro('COM4', 9600, timeout=1)
    measurement_process=False
    acquisition_process=False
    refresh_active=False
    icamera=Instance(views.camera.CameraGUI,()) # () here, or _icamera_default below

    plot = Instance(Plot)

    abort=Button()
    goto=Button()
    nm=Button()
    nm_controlled=Button(label=">NM")
    nmjemin=Button(label="nm/min")
    search_maximum=Button(label="search maximum")
    output_nmjemin=Button(label="output nm/min")
    measured_values=[]
    wavelength=[]

    grating_value=List([" 1"," 2"," 3"," 4"])
    current_grating=Str
    exit_mirror_value=List(["front (CCD)","side (APDs)"]) # List notwendig sonst wird drop down nicht aktualisiert
    current_exit_mirror=Str

    input_nm=CFloat(0.0)
    input_nmjemin=CFloat(10.0)
    checkbox_ispectrometer=Bool(True, label="Simulation Spectrometer")
    checkbox_voltmeter=Bool(True,label="Simulation Voltmeter")
    input_goto=CFloat(0.0)
    scan_bereich=CFloat(3)
    position=Button(label="?nm")
    acquisition_button=Button(label='acquisition')
    abort_acquisition=Button()

    output=Str(label="output")
    """for menu"""
    continuous_acquisition=Bool(False)
    waittime=CFloat(2,desc='time between two acquisitions')
    mi_camera = Action(name='camera menu', accelerator='Ctrl+p', action='call_camera_menu')
    camera_menu=Menu(mi_camera,name='Camera')


    traits_view=View(
            HGroup(
             VGroup(
              HGroup(Item("input_goto",show_label=False),Item("goto",show_label=False),
               Item("scan_bereich",label="+/-",show_label=True,width=-20.0),
               Item("search_maximum",show_label=False,enabled_when='acquisition_process==False'),enabled_when='measurement_process==False'),
              HGroup(Item("input_nm",show_label=False,enabled_when='measurement_process==False'),
               Item("nm",show_label=False,enabled_when='measurement_process==False'),
               Item("nm_controlled",show_label=False,enabled_when='measurement_process==False'),Spring(),Item('abort',show_label=False)),
              HGroup(
                  Item("input_nmjemin",show_label=False),
                  Item("nmjemin",show_label=False),enabled_when='measurement_process==False'),
              HGroup(
                  Item("position",show_label=False),Spring(),
                  Item("output_nmjemin",show_label=False),enabled_when='measurement_process==False'),
                  Item('current_grating', editor=EnumEditor(name='grating_value'), label='Gratings',enabled_when='measurement_process==False'),
              HGroup(Item("current_exit_mirror",editor=EnumEditor(name='exit_mirror_value')),
                     Spring(),enabled_when='measurement_process==False'),
         Item("output",style="readonly"),
         HGroup(Item("checkbox_ispectrometer"), Item("checkbox_voltmeter"),enabled_when='measurement_process==False'),

         HGroup(Item('icamera',show_label=False, style = 'custom'),enabled_when='acquisition_process==False'),
         HGroup(Item('acquisition_button',show_label=False),Item('abort_acquisition',show_label=False),Item('continuous_acquisition')),
         ),
        Item("plot",editor=ComponentEditor(),show_label=False)), 
       menubar=MenuBar(camera_menu), width=750,height=600,buttons = [OKButton,], resizable = True)
    
#    view_menu=View(
#            Item('camera_menu_instance',show_label=False, style = 'custom'),  
#            Item('continuous_acquisition'), Item('waittime',label='waitting time'),
#                        buttons = [ 'OK' ],resizable=True,kind='livemodal')


    def call_camera_menu(self):
       self.icamera.configure_traits(view='menu_view')


    def __init__(self):
        self.refresh_active=True
        if len(self.grating_value)>0:
            self.current_grating=self.grating_value[0]
        if len(self.exit_mirror_value)>0:
            self.current_exit_mirror=self.exit_mirror_value[0]
        self.refresh_active=False
    
#    def _icamera_default(self):
#        print "init_camera"
#        return views.camera.CameraGUI();

    def _goto_fired(self):
        if self.input_goto>1000:
            warning(parent=None, title="warning", message="zu gro?e input fuer die wavelength: muss zwischen 0 und 1000 nm liegen  ")
            self.input_goto=1000
        elif self.input_goto<0:
            warning(parent=None, title="warning", message="zu kleine input fuer die wavelength: muss zwischen 0 und 1000 nm liegen  ")
            self.input_goto=0
        else:
                self.input_nm=self.input_goto
                self.ispectro.wavelength_goto(self.input_goto)
                self.ispectro.waiting()


    def _nm_fired(self):
        if self.input_nm>1000:
            warning(parent=None, title="warning", message="zu gro?e input fuer die wavelength: muss zwischen 0 und 1000 nm liegen  ")
            self.input_nm=1000
        elif self.input_nm<0:
            warning(parent=None, title="warning", message="zu kleine input fuer die wavelength: muss zwischen 0 und 1000 nm liegen  ")
            self.input_nm=0
        else:
                self.input_goto=self.input_nm
                self.ispectro.wavelength_uncontrolled_nm(self.input_nm)
                self.ispectro.waiting()



    def _nm_controlled_fired(self):
        if self.input_nm>1000:
            warning(parent=None, title="warning", message="zu gro?e input fuer die wavelength: muss zwischen 0 und 1000 nm liegen  ")
            self.input_nm=1000
        elif self.input_nm<0:
            warning(parent=None, title="warning", message="zu kleine input fuer die wavelength: muss zwischen 0 und 1000 nm liegen  ")
            self.input_nm=0
        else:
            self.input_goto=self.input_nm
            self.ispectro.wavelength_controlled_nm(self.input_nm)


    def _nmjemin_fired(self):
            self.ispectro.velocity(self.input_nmjemin)


    def _position_fired(self):
            self.output=self.ispectro.output_position()


    def _identify_fired(self):
            self.output=self.ispectro.ident()


    def _output_nmjemin_fired(self):
            self.output=self.ispectro.output_velocity()


    def _current_grating_changed(self):
       if not self.refresh_active: # ueberprueft ob der Wert wegen einer aktualisierung geaendert worden ist, dann kein Befehl senden
         self.ispectro.grating_change(self.current_grating[1])

    def _current_exit_mirror_changed(self):
        if not self.refresh_active:
            if self.current_exit_mirror=='front (CCD)':
                self.ispectro.exit_mirror_change('front')
            else:
                self.ispectro.exit_mirror_change('side')

    def _search_maximum_fired(self):
            start_value=self.input_goto-self.scan_bereich
            end_value=self.input_goto+self.scan_bereich
            if start_value <0:                
                start_value=0
                end_value=self.scan_bereich
            thread.start_new_thread(self.measure,(start_value,end_value,))

    def measure(self,start_value,end_value):
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


    def _checkbox_ispectrometer_changed(self):
        self.ispectro.toggle_simulation()
        if not self.checkbox_ispectrometer:
            self.ispectrometer_gui_refresh()

    def _checkbox_voltmeter_changed(self):
        self.ivolt.toggle_simulation()

    def ispectrometer_gui_refresh(self):
        self.refresh_active=True
        position=self.ispectro.output_position()
        self.input_nm=position
        self.input_goto=position
        self.input_nmjemin=self.ispectro.output_velocity()
        self.read_gratings()
        self.read_exit_mirror()
        self.refresh_active=False


    def read_gratings(self):
        (self.grating_value,aktuell)=self.ispectro.output_grating() #aktuell als zweite output hinzuschreiben
        self.current_grating=self.grating_value[aktuell-1] # -1 da Grating bei 1 anfaengt zu zaehlen und List bei 0

    def read_exit_mirror(self):
        exit_mirror=self.ispectro.output_exit_mirror()
        if exit_mirror=='front':
            self.current_exit_mirror=self.exit_mirror_value[0]
        else:
            self.current_exit_mirror=self.exit_mirror_value[1]
    def _abort_fired(self):
        self.ispectro.mono_stop()
        self.measurement_process=False

    def plot_spectrum(self):
        spectrum=[]
        if not self.icamera.checkbox_camera:
            c_spectrum=self.icamera.camera.acquisition() # nimmt das spektrum auf
        else:
            points=random.sample(range(100),5)
            c_spectrum=(c_int * 5)(points[1],points[2],points[3],points[4],points[0])
        for i in range(len(c_spectrum)):
            spectrum.append(c_spectrum[i])
        wavelength=range(len(spectrum))
        plotdata = ArrayPlotData(x=wavelength, y=spectrum)
        plot = Plot(plotdata)
        plot.plot(("x", "y"), type="line", color="blue")
        self.plot=plot

    def _acquisition_button_fired(self):
         thread.start_new_thread(self.acquisition,())

    def acquisition(self):
        self.acquisition_process=True
        
        # continous acquisition: do loop
        while(self.continuous_acquisition and self.acquisition_process):
                self.plot_spectrum()

        # single shot and continous acquisition is over: do a single shot
        self.plot_spectrum()
        self.acquisition_process=False

    def _abort_acquisition_fired(self):
        self.acquisition_process=False

if __name__=="__main__":
    main=SpectrometerGUI()
    main.configure_traits()
    if not main.ispectro.simulation:
        print"close ispectrometer"
        main.ispectro.close()
    if not main.ivolt.simulation:
        print"close controls.voltage"
        main.ivolt.close()
