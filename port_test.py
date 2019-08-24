import numpy as np
import serial
from ProbeScopeInterface import *


def ProbeScopeMakeSamples(samples):
	output = bytearray()
	output.extend([
		START_OF_MESSAGE,
		COMMAND_RESULT,
		REQUEST_SAMPLE_DATA,
	])
	output.append(LENGTH_FIELD_INDICATOR)
	output.extend(ProbeScopeEscapeBytes(struct.pack("<I", len(samples))))
	output.append(DATA_FIELD_INDICATOR)
	output.extend(ProbeScopeEscapeBytes(samples))
	output.append(END_OF_MESSAGE)

	return output


if __name__ == '__main__':
	port = serial.Serial("COM3")
	port.timeout = 0

	while True:
		mess = port.read(4)
		if len(mess) > 0:
			mess = [int(i) for i in mess]
			print(mess)
		if mess == REQUEST_SAMPLE_DATA_COMMAND:
			points = 1000
			type_info = np.iinfo(np.int8)

			arr = np.linspace(-np.pi, np.pi, points)
			y = np.sin(arr)*123
			y += np.random.normal(0, 4, points)
			y = np.clip(y, type_info.min, type_info.max)
			y = y.astype(np.int8).tobytes()
			port.write(ProbeScopeMakeSamples(y))
