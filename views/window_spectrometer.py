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
    messvorgang=False
    aktualisieren_deaktiv=True

    plot = Instance(Plot)

    testbutton=Button()
    goto=Button()
    nm=Button()
    nm_kontrolle=Button(label=">NM")
    nmjemin=Button(label="nm/min")
    maximum_suchen=Button(label="Maximum suchen")
    ausgabe_nmjemin=Button(label="Ausgabe nm/min")
    messwerte=[]
    wellenlaenge=[]

    grating_value=List([" 1"," 2"," 3"," 4"])
    current_grating=Str
    exit_mirror_value=List(["front","side"]) # List notwendig sonst wird drop down nicht aktualisiert
    current_exit_mirror=Str

    eingabe_nm=CFloat(0.0)
    eingabe_nmjemin=CFloat(10.0)
    checkbox_spektrometer=Bool(True, label="Simulation Spektrometer")
    checkbox_voltmeter=Bool(True,label="Simulation Voltmeter")
    eingabe_goto=CFloat(0.0)
    scan_bereich=CFloat(3)
    position=Button(label="?nm")

    ausgabe=Str(label="Ausgabe")


    traits_view=View(HGroup(VGroup(HGroup(Item("eingabe_goto",show_label=False),Item("goto",show_label=False),
                                        Item("scan_bereich",show_label=False),Item("maximum_suchen",show_label=False)),
                                     HGroup(Item("eingabe_nm",show_label=False),Item("nm",show_label=False),Item("nm_kontrolle",show_label=False)),
                                     HGroup(Item("eingabe_nmjemin",show_label=False),Item("nmjemin",show_label=False)),
                                     HGroup(Item("position",show_label=False),Spring(),Item("ausgabe_nmjemin",show_label=False)),
                                     Item('current_grating', editor=EnumEditor(name='grating_value'), label='Gratings'),
                                         HGroup(Item("current_exit_mirror",editor=EnumEditor(name='exit_mirror_value')),Spring()),
                                     Item("ausgabe",style="readonly"),
                                     HGroup(Item("checkbox_spektrometer"), Item("checkbox_voltmeter"))
                                     ),
                            Item("plot",editor=ComponentEditor(),show_label=False)),
                     width=750,height=350,buttons = [OKButton,], resizable = True,title="Spektrometer")


    def do_print(self):
        print ("hier ist ein test print")

    def __init__(self):
        self.aktualisieren_deaktiv=False
        if len(self.grating_value)>0:
            self.current_grating=self.grating_value[0]
        if len(self.exit_mirror_value)>0:
            self.current_exit_mirror=self.exit_mirror_value[0]
        self.aktualisieren_deaktiv=True

    def _goto_fired(self):
        if self.eingabe_goto>1000:
            warning(parent=None, title="warning", message="zu gro?e Eingabe fuer die Wellenlaenge: muss zwischen 0 und 1000 nm liegen  ")
            self.eingabe_goto=1000
        elif self.eingabe_goto<0:
            warning(parent=None, title="warning", message="zu kleine Eingabe fuer die Wellenlaenge: muss zwischen 0 und 1000 nm liegen  ")
            self.eingabe_goto=0
        else:
            self.spectro.wavelength_goto(self.eingabe_goto)
            self.spectro.warten()

    def _nm_fired(self):
        if self.eingabe_nm>1000:
            warning(parent=None, title="warning", message="zu gro?e Eingabe fuer die Wellenlaenge: muss zwischen 0 und 1000 nm liegen  ")
            self.eingabe_nm=1000
        elif self.eingabe_nm<0:
            warning(parent=None, title="warning", message="zu kleine Eingabe fuer die Wellenlaenge: muss zwischen 0 und 1000 nm liegen  ")
            self.eingabe_nm=0
        else:
            self.spectro.wavelength_durchlauf(self.eingabe_nm)
            self.spectro.warten()

    def _nm_kontrolle_fired(self):
        if self.eingabe_nm>1000:
            warning(parent=None, title="warning", message="zu gro?e Eingabe fuer die Wellenlaenge: muss zwischen 0 und 1000 nm liegen  ")
            self.eingabe_nm=1000
        elif self.eingabe_nm<0:
            warning(parent=None, title="warning", message="zu kleine Eingabe fuer die Wellenlaenge: muss zwischen 0 und 1000 nm liegen  ")
            self.eingabe_nm=0
        else:
            self.spectro.wavelength_durchlauf_kontrolle(self.eingabe_nm)

    def _nmjemin_fired(self):
        self.spectro.geschwindigkeit(self.eingabe_nmjemin)

    def _position_fired(self):
        self.ausgabe=self.spectro.ausgabe_position()

    def _identify_fired(self):
        self.ausgabe=self.spectro.ident()

    def _ausgabe_nmjemin_fired(self):
        self.ausgabe=self.spectro.ausgabe_geschwindigkeit()


    def _current_grating_changed(self):
       if self.aktualisieren_deaktiv: # ueberprueft ob der Wert wegen einer aktualisierung geaendert worden ist, dann kein Befehl senden
         self.spectro.grating_aendern(self.current_grating[1])


    def _current_exit_mirror_changed(self):
        if self.aktualisieren_deaktiv:
            self.spectro.exit_mirror_aendern(self.current_exit_mirror)



    def _maximum_suchen_fired(self):
        if self.messvorgang==False:
            startwert=self.eingabe_goto-self.scan_bereich/2.0
            endwert=self.eingabe_goto+self.scan_bereich/2.0
            if startwert <0:
                startwert=0
            thread.start_new_thread(self.messen,(startwert,endwert,))
        else:
            information(parent=None, title="information", message="es laeuft schon ein Messvorgang, dieser muss zuerst beendet werden bevor ein neuer starten kann")


    def messen(self,startwert,endwert):
        self.spectro.wavelength_goto(startwert)
        self.spectro.warten()
        self.spectro.wavelength_durchlauf_kontrolle(endwert)
        self.messvorgang=True
        start=time.clock()
        self.messwerte=[]
        self.wellenlaenge=[]
        fertig=False

        while not fertig:
            self.messwerte.append(self.ivolt.messen())
            ende=time.clock()
            self.wellenlaenge.append(float(self.spectro.ausgabe_position()))
            self.zeichnen(self.wellenlaenge,self.messwerte)

            """die beiden Abbruchbedingungen, wenn die Wellaenge fast gr??er als der Endwert ist oder aber die letzen beiden eingelessenen Wellenl?ngen identisch sind"""

            if max(self.wellenlaenge)>=endwert-0.01:
                    fertig=True
            if len(self.wellenlaenge)>2:
                if self.wellenlaenge[len(self.wellenlaenge)-2]==self.wellenlaenge[len(self.wellenlaenge)-1]:
                    fertig=True

        maximum=max(self.messwerte) # sucht das groesste element der liste
        ort_maximum=self.messwerte.index(maximum) # sucht den ort in der Liste von der Zahl maximum
        self.spectro.mono_stop()
        self.messvorgang=False
        print self.wellenlaenge[ort_maximum]
        self.spectro.wavelength_goto(self.wellenlaenge[ort_maximum]) # geht an ort des Maximums zurueck


    def zeichnen(self,x_achse,y_achse):
        plotdata = ArrayPlotData(x=x_achse, y=y_achse)
        plot = Plot(plotdata)
        plot.plot(("x", "y"), type="line", color="blue")
        #plot.title="title"
        plot.x_axis.title="Wellenlaenge [nm]"
        plot.y_axis.title="Intensitaet"
        plot.overlays.append(ZoomTool(component=plot,tool_mode="box", always_on=False)) # damit man im Plot zoomen kann
        plot.tools.append(PanTool(plot, constrain_key="shift")) # damit man mit der Maus den Plot verschieben kann
        self.plot = plot


    def _checkbox_spektrometer_changed(self):
        self.spectro.toggle_simulation("spektrometer")
        if not self.checkbox_spektrometer:
            self.spektrometer_gui_aktualisieren()

    def _checkbox_voltmeter_changed(self):
        self.ivolt.toggle_simulation("voltmeter")


    def spektrometer_gui_aktualisieren(self):
        self.aktualisieren_deaktiv=False
        position=self.spectro.ausgabe_position()
        self.eingabe_nm=position
        self.eingabe_goto=position
        self.eingabe_nmjemin=self.spectro.ausgabe_geschwindigkeit()
        self.gratings_auslesen()
        self.exit_mirror_auslesen()
        self.aktualisieren_deaktiv=True


    def gratings_auslesen(self):
        (self.grating_value,aktuell)=self.spectro.ausgabe_grating() #aktuell als zweite ausgabe hinzuschreiben
        self.current_grating=self.grating_value[aktuell-1] # -1 da Grating bei 1 anfaengt zu zaehlen und List bei 0

    def exit_mirror_auslesen(self):
        self.current_exit_mirror=self.spectro.ausgabe_exit_mirror()


if __name__=="__main__":
    main=SpectrometerGUI()
    main.configure_traits()
    if main.spectro.simulation==0:
        print"schliessen"
        main.spectro.close()
    if main.ivolt.simulation==0:
        print"schliessen Voltage"
        main.ivolt.close()