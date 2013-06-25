
from traits.api import *
from traitsui.api import *
from traitsui.menu import OKButton, CancelButton

import window_cryo
reload( window_cryo)

import window_spectrometer
reload (window_spectrometer)

from  window_spectrometer import SpectrometerGUI
from  window_cryo import CryoGUI



printen = Action(name='test Print',accelerator="Ctrl+p",
    action='test_function')

menu = MenuBar(Menu(CloseAction, name='File'),
    Menu(UndoAction, RedoAction,printen,
    name='Edit'),
    Menu(HelpAction, name='Help'))


class MainWindow(HasTraits):

    spectrometer_instance = Instance( SpectrometerGUI, () )
    cryo_instance=Instance(CryoGUI,())
    inst_group = Group(
        Item('spectrometer_instance', style = 'custom',show_label=False, label="spektrometer",),
        Item('cryo_instance', style = 'custom',show_label=False,label="cryo",),
        layout='tabbed')

    view = View(
        inst_group,
     menubar=menu,
    title   = 'InstanceEditor',
    buttons = [ 'OK' ],
    resizable = True
    )


    def test_function(self):
        print"test"

main = MainWindow()
if __name__ == '__main__':
    main.configure_traits()