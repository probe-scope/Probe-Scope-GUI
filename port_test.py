import serial
import ProbeScopeInterface
import random

def rand_nums():
	nums = list()
	while len(nums) < 10:
		i = random.randrange(255)
		if i not in [ProbeScopeInterface.START_OF_MESSAGE, ProbeScopeInterface.END_OF_MESSAGE, ProbeScopeInterface.ESCAPE_CHAR]:
			nums.append(i)
	return nums

if __name__ == '__main__':
	test_samples_arr = [0x1E, 0x52, 0x73, 0x4C, 0x0A, 0x00, 0x00, 0x00, 0x44, 0x01, 0x02, 0x03, 0x0F, 0x05, 0x06, 0x07,
						0x08, 0x09, 0x0A, 0x04]
	port = serial.Serial("COM3")
	port.timeout = 0

	print(test_samples_arr[-11:-1])

	while True:
		mess = port.read(4)
		if len(mess) > 0:
			mess = [int(i) for i in mess]
			print(mess)
		if mess == ProbeScopeInterface.REQUEST_SAMPLE_DATA_COMMAND:
			test_samples_arr[-11:-1] = rand_nums()
			port.write(test_samples_arr)
