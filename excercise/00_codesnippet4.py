from traits.api import *
from traitsui.api import *

class EchoBox(HasTraits):

	Input = Str()
	output = Str()

	def _Input_changed(self):
		self.output = self.Input

	view = View(Item('Input'),Item('output', show_label=False),width=300,height=300)
	
    	def _anytrait_changed(self, name, old, new):
         print 'The %s trait changed from %s to %s ' % (name, old, new)

EchoBox().configure_traits()
