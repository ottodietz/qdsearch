from random import *
import numpy as np

class RandData():

	Data = []

	def shuffle(self):
		self.Data = [randint(1,1000) for i in self.Data]
		return self.Data


