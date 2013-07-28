from enthought.traits.api import *
from enthought.traits.ui.api import *
from traitsui.menu import OKButton, CancelButton
from enthought.chaco.api import Plot, ArrayPlotData
from numpy import arange,linspace,sin
from enthought.enable.component_editor import ComponentEditor
import thread
import time
from enthought.chaco.tools.api import PanTool, ZoomTool
from enthought.pyface.api import error,warning,information

import control_spectrometer
reload(control_spectrometer)
from control_spectrometer import Spectro

import Voltage
reload(Voltage)
from Voltage import Voltage


class SpectrometerGUI(HasTraits):
    ivolt=Voltage('COM7', 115200, timeout=1)
    spectro=Spectro('COM4', 9600, timeout=1)
    measurement_process=False
    refresh_active=False

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
    exit_mirror_value=List(["front","side"]) # List notwendig sonst wird drop down nicht aktualisiert
    current_exit_mirror=Str

    input_nm=CFloat(0.0)
    input_nmjemin=CFloat(10.0)
    checkbox_spectrometer=Bool(True, label="Simulation Spectrometer")
    checkbox_voltmeter=Bool(True,label="Simulation Voltmeter")
    input_goto=CFloat(0.0)
    scan_bereich=CFloat(3)
    position=Button(label="?nm")

    output=Str(label="output")


    traits_view=View(HGroup(VGroup(HGroup(Item("input_goto",show_label=False),Item("goto",show_label=False),
                                        Item("scan_bereich",show_label=False),Item("search_maximum",show_label=False)),
                                     HGroup(Item("input_nm",show_label=False),Item("nm",show_label=False),
                                            Item("nm_controlled",show_label=False),Spring(),Item('abort',show_label=False)),
                                     HGroup(Item("input_nmjemin",show_label=False),Item("nmjemin",show_label=False)),
                                     HGroup(Item("position",show_label=False),Spring(),Item("output_nmjemin",show_label=False)),
                                     Item('current_grating', editor=EnumEditor(name='grating_value'), label='Gratings'),
                                         HGroup(Item("current_exit_mirror",editor=EnumEditor(name='exit_mirror_value')),Spring()),
                                     Item("output",style="readonly"),
                                     HGroup(Item("checkbox_spectrometer"), Item("checkbox_voltmeter"))
                                    ),
                            Item("plot",editor=ComponentEditor(),show_label=False)),
                     width=750,height=350,buttons = [OKButton,], resizable = True,title="Spectrometer")


    def __init__(self):
        self.refresh_active=True
        if len(self.grating_value)>0:
            self.current_grating=self.grating_value[0]
        if len(self.exit_mirror_value)>0:
            self.current_exit_mirror=self.exit_mirror_value[0]
        self.refresh_active=False

    def _goto_fired(self):
        if self.input_goto>1000:
            warning(parent=None, title="warning", message="zu gro?e input fuer die wavelength: muss zwischen 0 und 1000 nm liegen  ")
            self.input_goto=1000
        elif self.input_goto<0:
            warning(parent=None, title="warning", message="zu kleine input fuer die wavelength: muss zwischen 0 und 1000 nm liegen  ")
            self.input_goto=0
        else:
            self.spectro.wavelength_goto(self.input_goto)
            self.spectro.waiting()

    def _nm_fired(self):
        if self.input_nm>1000:
            warning(parent=None, title="warning", message="zu gro?e input fuer die wavelength: muss zwischen 0 und 1000 nm liegen  ")
            self.input_nm=1000
        elif self.input_nm<0:
            warning(parent=None, title="warning", message="zu kleine input fuer die wavelength: muss zwischen 0 und 1000 nm liegen  ")
            self.input_nm=0
        else:
            self.spectro.wavelength_durchlauf(self.input_nm)
            self.spectro.waiting()

    def _nm_controlled_fired(self):
        if self.input_nm>1000:
            warning(parent=None, title="warning", message="zu gro?e input fuer die wavelength: muss zwischen 0 und 1000 nm liegen  ")
            self.input_nm=1000
        elif self.input_nm<0:
            warning(parent=None, title="warning", message="zu kleine input fuer die wavelength: muss zwischen 0 und 1000 nm liegen  ")
            self.input_nm=0
        else:
            self.spectro.wavelength_durchlauf_controlled(self.input_nm)

    def _nmjemin_fired(self):
        self.spectro.velocity(self.input_nmjemin)

    def _position_fired(self):
        self.output=self.spectro.output_position()

    def _identify_fired(self):
        self.output=self.spectro.ident()

    def _output_nmjemin_fired(self):
        self.output=self.spectro.output_velocity()


    def _current_grating_changed(self):
       if not self.refresh_active: # ueberprueft ob der Wert wegen einer aktualisierung geaendert worden ist, dann kein Befehl senden
         self.spectro.grating_change(self.current_grating[1])


    def _current_exit_mirror_changed(self):
        if not self.refresh_active:
            self.spectro.exit_mirror_change(self.current_exit_mirror)



    def _search_maximum_fired(self):
        if not self.measurement_process:
            start_value=self.input_goto-self.scan_bereich/2.0
            end_value=self.input_goto+self.scan_bereich/2.0
            if start_value <0:
                start_value=0
            thread.start_new_thread(self.measure,(start_value,end_value,))
        else:
            information(parent=None, title="information", message="es laeuft schon ein Messvorgang, dieser muss zuerst beendet werden bevor ein neuer starten kann")


    def measure(self,start_value,end_value):
        self.spectro.wavelength_goto(start_value)
        self.spectro.waiting()
        self.spectro.wavelength_durchlauf_controlled(end_value)
        self.measurement_process=True
        start=time.clock()
        self.measured_values=[]
        self.wavelength=[]
        self.measurement_process=True

        while self.measurement_process:
            self.measured_values.append(self.ivolt.measure())
            ende=time.clock()
            self.wavelength.append(float(self.spectro.output_position()))
            self.draw(self.wavelength,self.measured_values)

            """die beiden Abbruchbedingungen, wenn die Wellaenge fast gr??er als der end_value ist oder aber die letzen beiden eingelessenen Wellenl?ngen identisch sind"""

            if max(self.wavelength)>=end_value-0.01:
                    self.measurement_process=False
            if len(self.wavelength)>2:
                if self.wavelength[len(self.wavelength)-2]==self.wavelength[len(self.wavelength)-1]:
                    self.measurement_process=False

        maximum=max(self.measured_values) # sucht das groesste element der liste
        wavelength_maximum=self.measured_values.index(maximum) # sucht den ort in der Liste von der Zahl maximum
        self.spectro.mono_stop()
        self.measurement_process=False
        print self.wavelength[wavelength_maximum]
        self.spectro.wavelength_goto(self.wavelength[wavelength_maximum]) # geht an ort des Maximums zurueck


    def draw(self,x_achse,y_achse):
        plotdata = ArrayPlotData(x=x_achse, y=y_achse)
        plot = Plot(plotdata)
        plot.plot(("x", "y"), type="line", color="blue")
        #plot.title="title"
        plot.x_axis.title="wavelength [nm]"
        plot.y_axis.title="intensity"
        plot.overlays.append(ZoomTool(component=plot,tool_mode="box", always_on=False)) # damit man im Plot zoomen kann
        plot.tools.append(PanTool(plot, constrain_key="shift")) # damit man mit der Maus den Plot verschieben kann
        self.plot = plot


    def _checkbox_spectrometer_changed(self):
        self.spectro.toggle_simulation("spektrometer")
        if not self.checkbox_spektrometer:
            self.spectrometer_gui_refresh()

    def _checkbox_voltmeter_changed(self):
        self.ivolt.toggle_simulation("voltmeter")


    def spectrometer_gui_refresh(self):
        self.refresh_active=True
        position=self.spectro.output_position()
        self.input_nm=position
        self.input_goto=position
        self.input_nmjemin=self.spectro.output_velocity()
        self.read_gratings()
        self.read_exit_mirror()
        self.refresh_active=False


    def read_gratings(self):
        (self.grating_value,aktuell)=self.spectro.output_grating() #aktuell als zweite output hinzuschreiben
        self.current_grating=self.grating_value[aktuell-1] # -1 da Grating bei 1 anfaengt zu zaehlen und List bei 0

    def read_exit_mirror(self):
        self.current_exit_mirror=self.spectro.output_exit_mirror()

    def _abort_fired(self):
        self.spectro.mono_stop()
        self.measurement_process=False




if __name__=="__main__":
    main=SpectrometerGUI()
    main.configure_traits()
    if main.spectro.simulation==0:
        print"close spectrometer"
        main.spectro.close()
    if main.ivolt.simulation==0:
        print"close Voltage"
        main.ivolt.close()