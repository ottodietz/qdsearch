from numpy import cos, sin
import numpy as np

class Point(object):
	x = 0.
	y = 0.
	z = 0.

	def rotate_z(self,theta):
		self.x = cos(theta)*self.x + sin(theta)*self.y
		self.y -sin(theta)*self.x + cos(theta)*self.y

p = Point()
p.x = 1
p.rotate_z(np.pi)
print p.x
print p.y
