class ADRF_Ctl(object):
	Write_Lookup = {
		True: '1',
		False: '0'
	}
	Freq_Lookup = dict([(i, format(i, '#08b')[2:]) for i in range(0,64)])
	HighPower_Lookup = {
		True: '1',
		False: '0'
	}
	VGA1_Lookup = {
		15: '00',
		12: '01',
		9: '10'
	}
	VGA2_Lookup = {
		21: '00',
		18: '01',
		15: '10',
		12: '11'
	}
	VGA3_Lookup = {
		21: '00',
		18: '01',
		15: '10',
		12: '11'
	}
	Postamp_Lookup = {
		3: '0',
		9: '1'
	}
	DCOfs_Lookup = {
		True: '1',
		False: '0'
	}

	def __init__(self):
		self._Freq = 0
		self._HighPower = True
		self._VGA1 = 15
		self._VGA2 = 21
		self._VGA3 = 21
		self._Postamp = 3
		self._DCOfs = True

	@property
	def Freq(self):
		return self._Freq

	@Freq.setter
	def Freq(self, set):
		if set not in self.Freq_Lookup.keys():
			raise ValueError("Frequency Setpoint must be from 1 to 64 Mhz or 0 for bypass!")
		self._Freq = set
		if set > 31 or set is 0:
			self._HighPower = True
		else:
			self._HighPower = False

	@property
	def HighPower(self):
		return self._HighPower

	@HighPower.setter
	def HighPower(self, set):
		if set not in self.HighPower_Lookup.keys():
			raise ValueError("High Power Mode must be bool!")
		self._HighPower = set

	@property
	def VGA1(self):
		return self._VGA1

	@VGA1.setter
	def VGA1(self, set):
		if set not in self.VGA1_Lookup.keys():
			raise ValueError("VGA1 has gains 15, 12, and 9dB!")
		self._VGA1 = set

	@property
	def VGA2(self):
		return self._VGA2

	@VGA2.setter
	def VGA2(self, set):
		if set not in self.VGA2_Lookup.keys():
			raise ValueError("VGA2 has gains 21, 18, 15, and 12dB!")
		self._VGA2 = set

	@property
	def VGA3(self):
		return self._VGA3

	@VGA3.setter
	def VGA3(self, set):
		if set not in self.VGA3_Lookup.keys():
			raise ValueError("VGA3 has gains 21, 18, 15, and 12dB!")
		self._VGA3 = set

	@property
	def Postamp(self):
		return self._Postamp

	@Postamp.setter
	def Postamp(self, set):
		if set not in self.Postamp_Lookup.keys():
			raise ValueError("Postamp has gains 9 and 9dB!")
		self._Postamp = set

	@property
	def DCOfs(self):
		return self._DCOfs

	@DCOfs.setter
	def DCOfs(self, set):
		if set not in self.DCOfs_Lookup.keys():
			raise ValueError("DC Offset Enable must be bool!")
		self._DCOfs = set

	def GetMessage(self, Write=True):
		message = ""
		message = message + self.Freq_Lookup[self.Freq]
		message = message + self.HighPower_Lookup[self.HighPower]
		message = message + self.VGA1_Lookup[self.VGA1]
		message = message + self.VGA2_Lookup[self.VGA2]
		message = message + self.VGA3_Lookup[self.VGA3]
		message = message + self.Postamp_Lookup[self.Postamp]
		message = message + self.DCOfs_Lookup[self.DCOfs]
		message = message + self.Write_Lookup[Write]
		message = message[::-1] # Reverse to match SPI transfer order (LSB First)
		message = [int(message[:8], 2), int(message[8:], 2)]
		return message

if __name__ == '__main__':
	temp = ADRF_Ctl()
	print(temp.GetMessage())
