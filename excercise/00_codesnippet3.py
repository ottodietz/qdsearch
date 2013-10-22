from traits.api import *
import wx

class Counter(HasTraits):
	value = Int()
	Str = String()

Counter().edit_traits()
wx.PySimpleApp().MainLoop()

