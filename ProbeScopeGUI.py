import os
import sys
import time
from enum import Enum

# Force pyqtgraph to use PySide2
os.environ["PYQTGRAPH_QT_LIB"] = "PySide2"

import numpy as np
import pyqtgraph
import serial
import serial.tools.list_ports
from PySide2 import QtCore
from PySide2.QtWidgets import QApplication, QCheckBox, QGridLayout, QGroupBox, QHBoxLayout, QPushButton, QStyleFactory, \
	QVBoxLayout, QWidget, QMainWindow, QComboBox, QLabel

import ProbeScopeInterface
import measurements

ADC_STEP = 0.004
ADC_SAMPLE_RATE = 250000000


class SerialState(Enum):
	Waiting_For_Samples = 1


class SelfPopulatingComboBox(QComboBox):
	popupAboutToBeShown = QtCore.Signal()

	def showPopup(self):
		self.popupAboutToBeShown.emit()
		super(SelfPopulatingComboBox, self).showPopup()


class SerialThread(QtCore.QThread):
	def __init__(self, serial_port, serial_lock, command_callback, parent=None):
		QtCore.QThread.__init__(self, parent)
		self.serial_port = serial_port
		self.serial_lock = serial_lock
		self.command_callback = command_callback
		self.parser = ProbeScopeInterface.ProbeScopeParser()

	def run(self):
		while True:
			time.sleep(0.5)
			self.serial_lock.lock()
			if self.serial_port.isOpen():
				data = []
				try:
					data = self.serial_port.read(16000)
				except serial.serialutil.SerialException as e:
					print("Serial broke!")
					self.serial_lock.unlock()
					continue

				for s_char in data:
					res = self.parser.read_char(s_char)
					if res is not None:
						self.command_callback(res)
			# print("Serial Obj:" + str(self.serial_port))
			self.serial_lock.unlock()


class WidgetGallery(QMainWindow):
	def __init__(self, parent=None):
		super(WidgetGallery, self).__init__(parent)

		# System State
		self.adc_scale = 1
		self.adc_decimation = 1
		self.offset = 0
		self.samples = None

		self.serial_state = None
		self.serial_state_timeout = None

		self.originalPalette = QApplication.palette()

		QApplication.setStyle(QStyleFactory.create("Fusion"))

		serial_label = QLabel()
		serial_label.setText("Serial Port:")

		self.Serial_Handel = serial.Serial()
		self.Serial_Handel.timeout = 0
		self.Serial_Handel.baudrate = 115200
		self.serial_lock = QtCore.QMutex()

		self.serial_thread = SerialThread(self.Serial_Handel, self.serial_lock, self.command_callback)
		self.serial_thread.start()

		self.Serial_Port_Box = SelfPopulatingComboBox()
		self.Serial_Port_Box.view().setMinimumWidth(30)
		self.update_ports()
		self.Serial_Port_Box.setCurrentIndex(0)
		self.port_list = dict()
		self.Serial_Port_Box.popupAboutToBeShown.connect(self.update_ports)
		self.Serial_Port_Box.currentIndexChanged.connect(self.selected_port)

		disableWidgetsCheckBox = QCheckBox("&Disable widgets")

		# create plot
		self.main_plot = pyqtgraph.PlotWidget()

		self.curve = self.main_plot.plot()
		self.curve.setPen((200, 200, 100))
		self.main_plot.getAxis('left').setGrid(255)
		self.main_plot.getAxis('bottom').setGrid(255)
		self.curve.getViewBox().setMouseMode(pyqtgraph.ViewBox.RectMode)

		self.ControlGroupBox = QGroupBox("Controls")
		self.create_control_group_box()

		topLayout = QHBoxLayout()
		topLayout.addStretch(1)
		topLayout.addWidget(disableWidgetsCheckBox, 1)
		topLayout.addWidget(serial_label)
		topLayout.addWidget(self.Serial_Port_Box, 2)

		self.bottom_layout = QHBoxLayout()
		self.bottom_layout.addStretch(1)
		measurement_label = QLabel()
		measurement_label.setText("Measurements:")

		self.measurements_list = list()
		self.measurements_functions = [
			measurements.meas_pk_pk,
			measurements.meas_rms,
			None,
			None
		]

		for i in range(4):
			print("{}: N/A".format(i + 1))
			meas_n = QLabel()
			meas_n.setText("{}: N/A".format(i + 1))
			meas_n.setAlignment(QtCore.Qt.AlignLeft)
			self.measurements_list.append(meas_n)
			self.bottom_layout.addWidget(meas_n, alignment=QtCore.Qt.AlignLeft)

		mainLayout = QGridLayout()
		mainLayout.addLayout(topLayout, 0, 0, 1, 2)
		mainLayout.addWidget(self.main_plot, 1, 0, 2, 1)
		mainLayout.addWidget(self.ControlGroupBox, 1, 1, 2, 1)
		mainLayout.addLayout(self.bottom_layout, 3, 0, 1, 2, alignment=QtCore.Qt.AlignLeft)
		mainLayout.setRowStretch(1, 1)
		mainLayout.setRowStretch(2, 1)
		mainLayout.setColumnStretch(0, 10)
		mainLayout.setColumnStretch(1, 1)

		self.cent_widget = QWidget(self)
		self.setCentralWidget(self.cent_widget)
		self.cent_widget.setLayout(mainLayout)

		self.setWindowTitle("Styles")

	def command_callback(self, command):
		print("Got {}!".format(command))

		if type(command) is ProbeScopeInterface.ProbeScopeSamples:
			print("Plotting!")
			self.update_plot(command)

	def get_samples(self):
		if self.serial_state is SerialState.Waiting_For_Samples:
			if time.time() - self.serial_state_timeout < 0:
				print("Already waiting for samples!")
				return
		elif self.serial_state is not None:
			if time.time() - self.serial_state_timeout < 0:
				print("In another state ({})!".format(self.serial_state))
				return
		if self.serial_lock.tryLock(50):
			if self.Serial_Handel.isOpen():
				self.serial_state = SerialState.Waiting_For_Samples
				self.serial_state_timeout = time.time() + 2
				self.Serial_Handel.write(ProbeScopeInterface.REQUEST_SAMPLE_DATA_COMMAND)
			else:
				print("Serial handel closed, cannot get samples")
			self.serial_lock.unlock()
		else:
			print("Failed to get serial lock! Cannot request samples!")

	def auto_sample(self):
		TIMEOUT = 500
		if not self.autoPushButton.isChecked():
			return

		if self.serial_state_timeout is not None and time.time() - self.serial_state_timeout > 0:
			self.serial_state = None

		if self.serial_state is not None:
			self.auto_sample_timer.start(TIMEOUT)

		if self.serial_lock.tryLock(50):
			if self.Serial_Handel.isOpen():
				self.serial_state = SerialState.Waiting_For_Samples
				self.serial_state_timeout = time.time() + 2
				self.Serial_Handel.write(ProbeScopeInterface.REQUEST_SAMPLE_DATA_COMMAND)
			else:
				print("Serial handel closed, cannot get samples")
			self.serial_lock.unlock()
		else:
			print("Failed to get serial lock! Cannot request samples!")

		self.auto_sample_timer.start(TIMEOUT)

	def update_measurements(self):
		if self.samples is None:
			return
		for i, meas in enumerate(self.measurements_functions):
			if meas is None:
				self.measurements_list[i].setText("{}: N/A".format(i + 1))
			else:
				self.measurements_list[i].setText("{}: {}".format(i + 1, meas(self.samples)))

	def update_plot(self, samples):
		if self.serial_state is SerialState.Waiting_For_Samples:
			self.serial_state = None
		total_len = len(samples.samples) * (1 / (ADC_SAMPLE_RATE / self.adc_decimation))
		x = np.linspace(-(total_len / 2), total_len / 2, len(samples.samples))
		y = np.asarray(samples.samples) * ADC_STEP * self.adc_scale
		self.samples = (x, y)
		self.curve.setData(x, y)
		self.update_measurements()

	def autorange_plot(self):
		self.main_plot.autoRange()

	def update_ports(self):
		self.port_list = dict()

		# add dummy NC entry
		self.port_list[" - "] = None

		for port in serial.tools.list_ports.comports():
			self.port_list["{} ({})".format(port.manufacturer, port.device)] = port.device

		self.Serial_Port_Box.clear()
		self.Serial_Port_Box.addItems(list(self.port_list.keys()))

	def selected_port(self):
		selected_port = self.Serial_Port_Box.currentText()
		print("Selected:" + selected_port)

		if self.serial_lock.tryLock(2000):  # Wait 2 seconds
			if selected_port is '' or self.port_list[selected_port] is None:
				# Selected dummy object
				self.Serial_Handel.close()
				self.Serial_Handel.port = None
			else:
				self.Serial_Handel.port = self.port_list[selected_port]
				self.Serial_Handel.open()
				self.Serial_Handel.write(ProbeScopeInterface.ProbeScopeInitDAC())
				print("Set Handel to {}".format(self.Serial_Handel))
			self.serial_lock.unlock()
		else:
			print("Failed to get serial port mutex!")
			self.Serial_Port_Box.setCurrentIndex(0)

	def create_control_group_box(self):
		updatePushButton = QPushButton("Single")
		updatePushButton.setDefault(True)
		updatePushButton.clicked.connect(self.get_samples)

		self.autoPushButton = QPushButton("Auto")
		self.autoPushButton.setDefault(True)
		self.autoPushButton.setCheckable(True)
		self.autoPushButton.clicked.connect(self.auto_sample)

		self.auto_sample_timer = QtCore.QTimer()
		self.auto_sample_timer.timeout.connect(self.auto_sample)
		self.auto_sample_timer.setSingleShot(True)

		autoRange = QPushButton("Auto Range")
		autoRange.setDefault(True)
		autoRange.clicked.connect(self.autorange_plot)

		layout = QVBoxLayout()
		layout.addWidget(updatePushButton)
		layout.addWidget(self.autoPushButton)
		layout.addWidget(autoRange)
		layout.addStretch(1)
		self.ControlGroupBox.setLayout(layout)


if __name__ == '__main__':
	app = QApplication(sys.argv)
	gallery = WidgetGallery()
	gallery.show()
	sys.exit(app.exec_())
