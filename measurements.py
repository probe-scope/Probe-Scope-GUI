import numpy as np


def meas_pk_pk(samples):
	x = samples[0]
	y = samples[1]
	ret = "{:.2f}V pk-pk".format(max(y) - min(y))
	print(ret)
	return ret

def meas_rms(samples):
	x = samples[0]
	y = samples[1]
	ret = "{:.2f}V RMS".format(np.sqrt(np.mean(y**2)))
	print(ret)
	return ret
