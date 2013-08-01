
from traits.api import *
from traitsui.api import *
from traitsui.menu import OKButton, CancelButton
import thread
from enthought.pyface.api import error,warning,information
import time
from ctypes import *


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
    x1=CFloat(2)
    x2=CFloat(2)
    y1=CFloat(2)
    y2=CFloat(2.025)
    width_sample=CFloat(0.025)
    height_sample=CFloat(0.025)
    wavelength=CFloat(500)
    threshold_voltage=CFloat(3)
    scan_sample=Button()
    abort=Button()
    tests=Button()
    finished=True

    spectrometer_instance = Instance( SpectrometerGUI, () )
    cryo_instance=Instance(CryoGUI,())
    camera_instance=Instance(CameraGUI,())

    scanning=Group(Item('textfield',label='Step width by scanning',style='readonly'),
                        HGroup(Item('x1'),Spring(),Item('x2')),
                        HGroup(Item('y1'),Spring(),Item('y2')),
                        HGroup(Item('width_sample',label='width_sample (x)'),Spring(),Item('height_sample',label='height_sample (y)')),
                        HGroup(Item('wavelength'),Spring(),Item('threshold_voltage')),
                        HGroup(Item('scan_sample',show_label=False),Item('abort',show_label=False),Item('tests',show_label=False)),
                        )

    inst_group = Group(
        Item('cryo_instance', style = 'custom',show_label=False,label="cryo",),
        Item('spectrometer_instance', style = 'custom',show_label=False, label="spectrometer",),
        VGroup(scanning,Item('camera_instance',style='custom',show_label=False),label='scan sample'),
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
        print self.spectrometer_instance.exit_mirror_value


    def call_cryo_menu(self):
       self.cryo_instance.configure_traits(view='view_menu')

    def call_spectrometer_menu(self):
        print 'the spectrometer menu will follow'
       #self.spectrometer_instance.configure_traits(view='view_menu')

    def _scan_sample_fired(self):
        thread.start_new_thread(self.scanning,())

    def scanning(self):
        if self.camera_instance.camera.init_aktiv:
            information(parent=None, title="please wait", message="The initialization of the camera is running. Please wait until the initialization is finished.")
        else:
            simu=True
            if simu:
                print 'this function will follow!'
            else:
                """x1 muss kleiner x2 sein analog y2"""
                self.searching=True
                self.finished=False
                """nimmt werde aus GUI zum abgleich ob angekommen"""
                x1=self.x1
                y1=self.y1
                x2=self.x2
                y2=self.y2
                """temporaere start und zielwerte"""
                x_start=x1
                y_start=y1
                x_target=x1
                y_target=y2

                x_koords=[]
                y_koords=[]
                spectra=[]
                sign=1 #wird spaeter berechnet wenn einegabe der gr??e  keine rolle mehr spielt

                """Werte aus GUI einlesen, damit suche weiter l?uft auch wenn GUI ge?nert wird"""
                width=self.width_sample #x-koordinaten abstand
                height=self.height_sample #  y koordinaten abstand
                threshold_voltage=self.threshold_voltage # Schwellenspannung

                self.cryo_instance.cryo.move(x_start,y_start) #faehrt zum startpunkt
                if self.spectrometer_instance.current_exit_mirror=='front': #ueberprueft ob spiegel umgeklappt bzw falls nicht klappt er ihn um
                     self.spectrometer_instance.spectro.exit_mirror_change('side')
                self.cryo_instance.cryo.waiting() #wartet bis cryo dort angekommen
                self.cryo_instance.cryo.move(x_target,y_target)#faengt an zum ersten ziel zu fahren

                """ ein Thread aufmachen fuer den Teil if threshold_voltage < ... und einen fuer den while if not self.cryo_instance.cryo.status() teil ,
                sodass sie parallel laufen koennen"""
                while not self.finished:
                    while self.searching:
                        if threshold_voltage < self.spectrometer_instance.ivolt.read_voltage(): # vergleicht schwellenspannung mit aktueller
                            self.cryo_instance.cryo.stop() # stopt cryo
                            self.spectrometer_instance.spectro.exit_mirror_change('front') # klappt spiegel vom spectro auf kamera um
                            spectrum=self.camera_instance.camera.acqisition() # nimmt das spektrum auf
                            self.spectrometer_instance.spectro.exit_mirror_change('side') # klappt spiegel vom spectro auf ausgang um
                            [x,y]=self.cryo_instance.cryo.convert_output(self.cryo_instance.cryo.position()) #speichert die aktuellen koordinaten ab
                            x_koords.append(x)
                            y_koords.append(y)
                            spectra.append(spectrum)
                            """hier auf Richtung des Cryos achten, mitehilfe von sign 2 verschiedene Bedigungen schaffen!"""
                            if (y+sign*height<y_target and sign==1):
                                self.cryo_instance.cryo.move(x,y+sign*height) # faehrt stueck weiter um von QD weg zusein
                                print ' achte darauf dass das Vorzeichen beim wegfahren ist noch nicht definiert!!!'
                                self.cryo_instance.cryo.waiting() # wartet bis cryo vom QD weg ist
                                """aufpassen, dass er waerend er vom QD weg faehrt nicht ueber das ende hinaus (also x/y_target) faehrt"""
                                self.cryo_instance.cryo.move(x_target,y_target) # faehrt weiter
                                print 'faehrt weiter'
                            else:
                                self.searching=False
                            self.searching=True # da wenn cryo.status parallel abgefragt wird es auf False gesetz worden ist vremutlich muss der ganze thread dann neu gestartet werden
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

                        self.cryo_instance.cryo.move(x_target,y_target) # new target
                        self.searching=True
                print 'searching finish'


            """"dann folgt noch auslesen der Koordinaten und alles abspeicerhn"""


    def _tests_fired(self): # tests the movement of the cryo
       thread.start_new_thread(self.test,())

    def test(self):
                """this function works without voltmeter! it uses random values for the voltage"""
                """x1 muss kleiner x2 sein analog y2"""
                self.searching=True
                self.finished=False
                """nimmt werde aus GUI zum abgleich ob angekommen"""
                x1=self.x1
                y1=self.y1
                x2=self.x2
                y2=self.y2
                """temporaere start und zielwerte"""
                x_start=x1
                y_start=y1
                x_target=x1
                y_target=y2

                x_koords=[]
                y_koords=[]
                spectra=[]
                sign=1 #wird spaeter berechnet wenn einegabe der gr??e  keine rolle mehr spielt

                """Werte aus GUI einlesen, damit suche weiter l?uft auch wenn GUI ge?nert wird"""
                width=self.width_sample #x-koordinaten abstand
                height=self.height_sample #  y koordinaten abstand
                threshold_voltage=self.threshold_voltage # Schwellenspannung

                self.cryo_instance.cryo.move(x_start,y_start) #faehrt zum startpunkt
                print 'testet ob die spiegel umgeklappt sind'
                if self.spectrometer_instance.current_exit_mirror=='front':
                     print 'spiegel war nicht umgeklappt' #ueberprueft ob spiegel umgeklappt bzw falls nicht klappt er ihn um
                     self.spectrometer_instance.spectro.exit_mirror_change('side')
                print 'spiegel umklappen fertig'
                self.cryo_instance.cryo.waiting() #wartet bis cryo dort angekommen
                self.cryo_instance.cryo.move(x_target,y_target)#faengt an zum ersten ziel zu fahren

                """ ein Thread aufmachen fuer den Teil if threshold_voltage < ... und einen fuer den while if not self.cryo_instance.cryo.status() teil ,
                sodass sie parallel laufen koennen"""
                while not self.finished:
                    while self.searching:
                        if threshold_voltage < self.spectrometer_instance.ivolt.measure(): # vergleicht schwellenspannung mit aktueller
                            print 'Spannung wurde erreicht'
                            self.cryo_instance.cryo.stop() # stopt cryo
                            self.spectrometer_instance.spectro.exit_mirror_change('front') # klappt spiegel vom spectro auf kamera um
                            print 'spiegel wurde umgeklappt'
                            spectrum=self.camera_instance.camera.acqisition()
                            self.spectrometer_instance.spectro.exit_mirror_change('side') # klappt spiegel vom spectro auf ausgang um
                            print 'spiegel wurde umgeklappt'
                            [x,y]=self.cryo_instance.cryo.convert_output(self.cryo_instance.cryo.position()) #speichert die aktuellen koordinaten ab
                            print 'koords abgespeichert'
                            x_koords.append(x)
                            y_koords.append(y)
                            spectra.append(spectrum)
                            """hier auf Richtung des Cryos achten, mitehilfe von sign 2 verschiedene Bedigungen schaffen!"""
                            if  (y+sign*height<y_target and sign==1):
                                self.cryo_instance.cryo.move(x,y+sign*height) # faehrt stueck weiter um von QD weg zusein
                                print ' achte darauf dass das Vorzeichen beim wegfahren ist noch nicht definiert!!!'
                                self.cryo_instance.cryo.waiting() # wartet bis cryo vom QD weg ist
                                """aufpassen, dass er waerend er vom QD weg faehrt nicht ueber das ende hinaus (also x/y_target) faehrt"""
                                self.cryo_instance.cryo.move(x_target,y_target) # faehrt weiter
                                print 'faehrt weiter'
                            else:
                                self.searching=False
                            #self.searching=True # da wenn cryo.status parallel abgefragt wird es auf False gesetz worden ist vremutlich muss der ganze thread dann neu gestartet werden
                        if not self.cryo_instance.cryo.status():
                            self.searching=False

                    """ the comparasion is with calculated values it would be better to take the actuall postion of the cryo"""
                    """by calculating they are internal rounding erros and than it run one time more than it should"""
                    print x_target
                    print y_target
                    if (x_target>=x2 and (y_target>=y2 or y_target<=y1)) or self.finished: #check if end coordinates are reached
                        print 'setfinished'
                        self.finished=True
                    else:
                        """instead of calculating new values relative move could be used"""
                        # calculates x value for next searching
                        x_start=x_target
                        x_target=x_target+width
                        print 'x_target'+str(x_target)
                        self.cryo_instance.cryo.move(x_target,y_target) #goes to new x coordinate
                        self.cryo_instance.cryo.waiting()

                         # calculates y value for next searching
                        temp=y_start
                        y_start=y_target
                        y_target=temp
                        print 'y_target'+ str(y_target)

                        self.cryo_instance.cryo.move(x_target,y_target) # new target
                        self.searching=True
                print 'x koords'
                print x_koords
                print 'ykoords'
                print y_koords
                print spectra
                print 'searching finish'


    def _abort_fired(self):
        self.finished=True
        self.searching=False
        self.cryo_instance.cryo.stop() #stopt cryo
        #self.spectrometer_instance.spectro.mono_stop()# stoppt spectrometer wobei das garnicht an sein sollte
        print 'abort'



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