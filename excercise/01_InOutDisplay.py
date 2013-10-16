from traits.api import *
from traitsui.api import *

class InOutDisplay(HasTraits):
	UP=Button(label=u'\u2191')
	DOWN=Button(label=u'\u2193')
	Input = Str()
	Output = Str()


	view=View(HGroup(VGroup(),VGroup(Item("UP", show_label=False, resizable = True), Item("DOWN", show_label=False, resizable=True)),width=300, height=300))

InOutDisplay().configure_traits()
