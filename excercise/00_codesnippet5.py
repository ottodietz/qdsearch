from traits.api import *
from traitsui.api import View,Item,ButtonEditor

class Counter(HasTraits):
    value = Int()
    add_one = Button()
    test = Button()

    def _test_fired(self):
        self._add_one_fired()
    
    def _add_one_fired(self):
        self.value +=1
    view = View('value',Item('test',show_label=False),Item('add_one',show_label=False))
Counter().configure_traits()
