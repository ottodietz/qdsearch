from enthought.traits.api import *
from enthought.traits.ui.api import *

main=CryoGUI()
main.configure_traits()
high=CFloat(1.0)
low=CFloat(1.0)
up=Button(label=u'\u2191')
down=Button(label=u'\u2193')
traits_view = View(
	Item('up', show_lable=False)
)
