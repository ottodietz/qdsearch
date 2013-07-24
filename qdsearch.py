
from traits.api import *
from traitsui.api import *
from traitsui.menu import OKButton, CancelButton

import window_cryo
reload( window_cryo)

import window_spectrometer
reload (window_spectrometer)

from  window_spectrometer import SpectrometerGUI
from  window_cryo import CryoGUI

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

    spectrometer_instance = Instance( SpectrometerGUI, () )
    cryo_instance=Instance(CryoGUI,())
    inst_group = Group(
        Item('cryo_instance', style = 'custom',show_label=False,label="cryo",),
        Item('spectrometer_instance', style = 'custom',show_label=False, label="spektrometer",),
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

    def call_cryo_menu(self):
       self.cryo_instance.configure_traits(view='view_menu')

    def call_spectrometer_menu(self):
        print 'the spectrometer menu will follow'
       #self.spectrometer_instance.configure_traits(view='view_menu')

main = MainWindow()
if __name__ == '__main__':
    main.configure_traits()
    if main.cryo_instance.cryo.simulation==0:
        print"schliessen cryo"
        main.cryo_instance.cryo.close()
    if main. spectrometer_instance.spectro.simulation==0:
        print"schliessen spectro"
        main. spectrometer_instance.spectro.close()
    if main. spectrometer_instance.ivolt.simulation==0:
        print"schliessen Voltage"
        main. spectrometer_instance.ivolt.close()