from math import *
from scipy.special import jn
from numpy import *

class Dinges(object):
    x =linspace(1,1,10)
    y =linspace(1,1,10)
    myargs = ['x']
    y = sin(*myargs)
    print y

