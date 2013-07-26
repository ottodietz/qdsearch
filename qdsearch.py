
from traits.api import *
from traitsui.api import *
from traitsui.menu import OKButton, CancelButton
import thread
from enthought.pyface.api import error,warning,information

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

printen = Action(name='test Print',accelerator="Ctrl+t",
    action='test_function')

menu = MenuBar(Menu(CloseAction, name='File'),
    Menu(UndoAction, RedoAction,printen,
    name='Edit'),
    Menu(call_menu_spectrometer,name='Spectrometer'),
    Menu(call_menu_cryo,name='Cryo'),
    Menu(HelpAction, name='Help'))


class MainWindow(HasTraits):

    """for scanning sample"""
    textfield=Str()
    x1=CFloat(0)
    x2=CFloat(2)
    y1=CFloat(0)
    y2=CFloat(3)
    width_sample=CFloat(0.0025)
    height_sample=CFloat(0.0025)
    wavelength=CFloat(500)
    threshold_voltage=CFloat(2)
    scan_sample=Button()

    spectrometer_instance = Instance( SpectrometerGUI, () )
    cryo_instance=Instance(CryoGUI,())
    camera_instance=Instance(CameraGUI,())

    test=Group(Item('textfield',label='Ausdehnung der Probe',style='readonly'),
                        HGroup(Item('x1'),Spring(),Item('x2')),
                        HGroup(Item('y1'),Spring(),Item('y2')),
                        HGroup(Item('width_sample'),Spring(),Item('height_sample')),
                        HGroup(Item('wavelength'),Spring(),Item('threshold_voltage')),
                        HGroup(Item('scan_sample',show_label=False)),
                        )

    inst_group = Group(
        Item('cryo_instance', style = 'custom',show_label=False,label="cryo",),
        Item('spectrometer_instance', style = 'custom',show_label=False, label="spektrometer",),
        VGroup(test,Item('camera_instance',style='custom',show_label=False),label='scan sample'),
        layout='tabbed')

    traits_view = View(
        inst_group,
     menubar=menu,
    title   = 'qdsearch',
    buttons = [ 'OK' ],
    resizable = True
    )


    def test_function(self):
        print"test"
        thread.start_new_thread(self.cryo_instance.cryo.waiting,())

    def call_cryo_menu(self):
       self.cryo_instance.configure_traits(view='view_menu')

    def call_spectrometer_menu(self):
        print 'the spectrometer menu will follow'
       #self.spectrometer_instance.configure_traits(view='view_menu')

    def _scan_sample_fired(self):
        if self.camera_instance.camera.init_aktiv:
            information(parent=None, title="please wait", message="The initialization of the camera is running. Please wait until the initialization is finished.")
        else:
            simu=True
            if simu:
                print 'in dieser Funktion werden weitere Funktionen folgen!'
            else:
                """x1 muss kleiner x2 sein analog y2"""
                searching=True
                x_start=self.x1
                y_start=self.y1
                x_target=self.x1
                y_target=self.y2
                width=self.width_sample #x-koordinaten abstand
                height=self.height_sample #  y koordinaten abstand
                self.cryo_instance.cryo.move(x_start,y_start) #faehrt zum startpunkt
                """es muss noch der spiegel ?berpr?ft werden und ggf umgeklappt werden"""
                self.cryo_instance.cryo.waiting() #wartet bis dort angekommen

                self.cryo_instance.cryo.move(x_target,y_target)#faengt an zumersten ziel zu fahren
                """ Matrix oder ?hnliches einf?gen in derdie x koords, die y, koords und die Messpunkte gespeichert werden, IDEE=koords ganz hinten
                oder vorne abspeichern"""
                while not finished:
                    while searching:
                        if self.threshold_voltage < self.spectrometer_instance.ivolt.lesen(): # vergleicht schwellenspannung mit aktueller
                            self.cryo_instance.cryo.stop() # stopt cryo
                            self.spectrometer_instance.spectro.exit_mirror_aendern('front') # klappt spiegel vom spectro auf kamera um
                            measurement_data=self.camera_instance.camera.acqisition() # nimmt das spektrum auf
                            self.spectrometer_instance.spectro.exit_mirror_aendern('side') # klappt spiegel vom spectro auf ausgang um
                            [x,y]=self.cryo_instance.cryo.convert_output(self.cryo_instance.cryo.position()) #speichert die aktuellen koordinaten ab
                            self.cryo_instance.cryo.move(x_target,y_target+vorzeichen*height) # faehrt stueck weiter um von QD weg zusein
                            self.cryo_instance.cryo.waiting() # wartet bis cryo vom QD weg ist
                            self.cryo_instance.cryo.move(x_target,y_target) # f?hrt weiter
                        if not self.cryo_instance.cryo.status():
                            searching=False
                        # berechnet xwerte fuer naechsten durchlaf
                        x_start=x_target
                        x_target=x_target+width
                        self.cryo_instance.cryo.move(x_target,y_target) #faehrt zur neuen x koordinate
                        self.cryo_instance.cryo.waiting()
                        # berechnet y werte fuer den naechsten durchlauf
                        y_start=temp
                        y_start=y_target
                        y_target=temp
                        """abfrage aender wenn nicht genau richtigen koords erreicht sind faehrt er ins leere"""
                        if x_start==self.x2 and y_start==self.y2: #schaut ob ende erreicht worden ist
                            finished=True
                        self.cryo_instance.cryo.move(x_target,y_target) # gibt neues ziel an






                    """"dann folgt noch auslesen der Koordinaten und alles abspeicerhn"""








main = MainWindow()
if __name__ == '__main__':
    main.configure_traits()
    if main.cryo_instance.cryo.simulation==0:
        print"close cryo"
        main.cryo_instance.cryo.close()
    if main. spectrometer_instance.spectro.simulation==0:
        print"close spectro"
        main.spectrometer_instance.spectro.close()
    if main.spectrometer_instance.ivolt.simulation==0:
        print"close Voltage"
        main.spectrometer_instance.ivolt.close()