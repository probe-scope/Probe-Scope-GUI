import struct
import warnings

# Probe Scope

# Global message symbols
START_OF_MESSAGE = 0x1E
END_OF_MESSAGE = 0x04
END_OF_BLOCK = 0x17
ESCAPE_CHAR = 0x1A

# Command and response
COMMAND_MESSAGE = 0x43
COMMAND_RESULT = 0x52

# Commands
REQUEST_SAMPLE_DATA = 0x73
TRIGGERED_COMMAND = 0x74
WRITE_REGISTERS = 0x77
READ_REGISTERS = 0x72

SAMPLE_DATA_LENGTH = 0x4C
SAMPLE_DATA_FIELD_INDICATOR = 0x44

LENGTH_FIELD_INDICATOR = 0x4C
DATA_FIELD_INDICATOR = 0x44
ADDRESS_FIELD_INDICATOR = 0x41

# Commands to send
REQUEST_SAMPLE_DATA_COMMAND = [START_OF_MESSAGE, COMMAND_MESSAGE, REQUEST_SAMPLE_DATA, END_OF_MESSAGE]


class ParserWarning(UserWarning):
	pass


class ProbeScopeSamples(object):
	def __init__(self, samples):
		self.samples = [-256 + s if s > 127 else s for s in samples]


class ProbeScopeWriteResponse(object):
	def __init__(self, data_len):
		self.data_len = data_len

	def __len__(self):
		return self.data_len


class ProbeScopeReadResponse(object):
	def __init__(self, data):
		self.data = data


class ProbeScopeTriggered(object):
	pass


class ProbeScopeParser(object):
	def __init__(self):
		self.packet_dict = {
			COMMAND_MESSAGE: self.parse_command,
			COMMAND_RESULT: self.parse_response
		}

		self.command_result_dict = {
			REQUEST_SAMPLE_DATA: self.parse_sample_response,
			TRIGGERED_COMMAND: self.parse_sample_response,  # same message as a response
			WRITE_REGISTERS: self.parse_write_reg_response,
			READ_REGISTERS: self.parse_read_reg_response
		}

		self.command_dict = {
			TRIGGERED_COMMAND: self.parse_triggered
		}

		self.receiving_message = False
		self.escape_char = False
		self.char_buff = list()

	def parse_sample_response(self):
		if self.char_buff[2] != SAMPLE_DATA_LENGTH:
			warnings.warn("Warning Sample Data Length Field Indicator invalid! {}".format(self.char_buff),
						  ParserWarning)
		if self.char_buff[7] != SAMPLE_DATA_FIELD_INDICATOR:
			warnings.warn("Warning Sample Data Field Indicator invalid! {}".format(self.char_buff),
						  ParserWarning)

		num_samples = int.from_bytes(self.char_buff[3:6], byteorder='little')

		if len(self.char_buff) - 8 != num_samples:
			warnings.warn(
				"Warning {} samples not the same as indicated {}".format(len(self.char_buff) - 8, num_samples),
				ParserWarning)

		samples = self.char_buff[8:]
		self.char_buff = list()
		return ProbeScopeSamples(samples)

	def parse_write_reg_response(self):
		print(bytes(self.char_buff[3:7]))
		ret = ProbeScopeWriteResponse(struct.unpack("<I", bytes(self.char_buff[3:7])))
		self.char_buff = list()
		return ret

	def parse_read_reg_response(self):
		data_len = struct.unpack("<I", self.char_buff[4:8])
		if len(self.char_buff) != data_len + 10:
			warnings.warn("Returned less data then they said they would! {} vs the stated {}".format(data_len, len(
				self.char_buff) - 10), ParserWarning)
		ret = ProbeScopeReadResponse(self.char_buff[9:-1])
		self.char_buff = list()
		return ret

	def parse_response(self):
		try:
			return self.command_result_dict[self.char_buff[1]]()
		except KeyError:
			warnings.warn("Unknown command response {}".format(self.char_buff), ParserWarning)
			self.char_buff = list()
			return None

	def parse_command(self):
		try:
			return self.command_dict[self.char_buff[1]]()
		except KeyError:
			warnings.warn("Unknown command {}".format(self.char_buff), ParserWarning)
			self.char_buff = list()
			return None

	def parse_triggered(self):
		return ProbeScopeTriggered()

	def parse_message(self):
		try:
			return self.packet_dict[self.char_buff[0]]()
		except KeyError:
			warnings.warn("Unknown message format {}".format(self.char_buff), ParserWarning)
			self.char_buff = list()
			return None

	def read_char(self, char):
		if not self.receiving_message:
			if char == START_OF_MESSAGE:
				self.receiving_message = True
			else:
				self.escape_char = False
				warnings.warn("Unexpected char between messages! {}".format(char), ParserWarning)
		else:
			if self.escape_char:
				self.char_buff.append(char)
				self.escape_char = False
			elif char == ESCAPE_CHAR:
				self.escape_char = True
			elif char == END_OF_MESSAGE:
				self.receiving_message = False
				return self.parse_message()
			else:
				self.char_buff.append(char)
		return None


def ProbeScopeRegisterWrite(data_address, data):
	"""
	Return formatted register write command

	:param data_address: Int field address
	:type data_address: int
	:param data: Array of bytes or byte like things
	:type data: bytearray
	:return: regester write command
	:rtype: bytearray
	"""
	data = bytearray(data)
	data_len = len(data)

	output = bytearray()
	output.extend([
		START_OF_MESSAGE,
		COMMAND_MESSAGE,
		WRITE_REGISTERS
	])
	output.append(ADDRESS_FIELD_INDICATOR)
	output.extend(ProbeScopeEscapeBytes(struct.pack("<I", data_address)))
	output.append(LENGTH_FIELD_INDICATOR)
	output.extend(ProbeScopeEscapeBytes(struct.pack("<I", data_len)))
	output.append(DATA_FIELD_INDICATOR)
	output.extend(ProbeScopeEscapeBytes(data))
	output.append(END_OF_MESSAGE)

	return output


def ProbeScopeRegisterRead(address, len):
	output = bytearray()
	output.extend([
		START_OF_MESSAGE,
		COMMAND_MESSAGE,
		READ_REGISTERS,
	])
	output.append(ADDRESS_FIELD_INDICATOR)
	output.extend(ProbeScopeEscapeBytes(struct.pack("<I", address)))
	output.append(LENGTH_FIELD_INDICATOR)
	output.extend(ProbeScopeEscapeBytes(struct.pack("<I", len)))
	output.append(END_OF_MESSAGE)

	return output


def ProbeScopeEscapeBytes(data):
	out = bytearray()
	for d in data:
		if d in [ESCAPE_CHAR, START_OF_MESSAGE, END_OF_MESSAGE, END_OF_BLOCK]:
			out.extend(bytes([ESCAPE_CHAR, d]))
		else:
			out.extend(bytes([d]))
	return out


def ProbeScopeInitDAC():
	return ProbeScopeRegisterWrite(0x4000, b'\xAA')


def ProbeScopeSetDAC(a, b, c, d):
	return ProbeScopeRegisterWrite(0x4002, struct.pack("<HHHH", a, b, c, d))


def ProbeScopeSetVGA():
	return ProbeScopeRegisterWrite(0x3000, bytearray([255, 255]))

if __name__ == '__main__':
	test_samples_arr = [0x1E, 0x52, 0x73, 0x4C, 0x0A, 0x00, 0x00, 0x00, 0x44, 0x01, 0x02, 0x03, 0x0F, 0x05, 0x06, 0x07,
						0x08, 0x09, 0x0A, 0x04]
	parser = ProbeScopeParser()
	for car in test_samples_arr:
		res = parser.read_char(car)
		if res is not None:
			print(res.samples)
