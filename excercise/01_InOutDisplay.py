from traits.api import *
from traitsui.api import *
from math import *
import numpy as np


class InOutDisplay(HasTraits):
	UP=Button(label=u'\u2191')
	DOWN=Button(label=u'\u2193')
	Input = Int()
	Output = Int()
	findMax = Button(label="Find Maximum")
	pixel = np.linspace(1,1024,1024)
	values = np.linspace(1,1024,1024)
	data = [[pixel],[values]]
#	limitup = 255
#	limitdown = 0

	view=View(HGroup(VGroup(Item("Input", show_label=False, style="custom"),Item("Output", show_label=False, style="custom")),VGroup(Item("findMax", show_label=False, springy=True),Item("UP", show_label=False, resizable = True, springy=True), Item("DOWN", show_label=False, resizable=True, springy=True))),width=400,height=250)

	def _UP_fired(self):
		if not self.Output == 255:
			self.Output +=1
			self.values = np.ones((1,1024))
#			self.values = self.values * random.randint(1,1000)
		else:
			print "end of range"
	def _DOWN_fired(self):
		if not self.Output == 0:
			self.Output -=1
             i           self.values = np.ones((1,1024))
#                        self.values = self.values * random.randint(1,1000)

		else:
			print "end of range"

InOutDisplay().configure_traits()
