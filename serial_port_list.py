# code from here: https://stackoverflow.com/questions/35724405/pyserial-get-the-name-of-the-device-behind-a-com-port

import serial
import serial.tools.list_ports


def listPorts():
	"""!
	@brief Provide a list of names of serial ports that can be opened as well as a
	a list of Arduino models.
	@return A tuple of the port list and a corresponding list of device descriptions
	"""

	ports = list(serial.tools.list_ports.comports())

	resultPorts = []
	descriptions = []
	for port in ports:
		print(port.description)


	return (resultPorts, descriptions)

if __name__ == '__main__':
    print(listPorts())