import os
import sys
import time

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

class SelfPopulatingComboBox(QComboBox):
	popupAboutToBeShown = QtCore.Signal()

	def showPopup(self):
		self.popupAboutToBeShown.emit()
		super(SelfPopulatingComboBox, self).showPopup()


class SerialThread(QtCore.QThread):
	def __init__(self, serial_port, serial_lock, plot_data, parent=None):
		QtCore.QThread.__init__(self, parent)
		self.serial_port = serial_port
		self.serial_lock = serial_lock
		self.plot_data = plot_data
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
					if type(res) is ProbeScopeInterface.ProbeScopeSamples:
						print("Plotting!")
						self.plot_data(res)
					elif res is not None:
						print("Got {}!".format(res))
			# print("Serial Obj:" + str(self.serial_port))
			self.serial_lock.unlock()


class WidgetGallery(QMainWindow):
	def __init__(self, parent=None):
		super(WidgetGallery, self).__init__(parent)

		self.originalPalette = QApplication.palette()

		QApplication.setStyle(QStyleFactory.create("Fusion"))

		serial_label = QLabel()
		serial_label.setText("Serial Port:")

		self.Serial_Handel = serial.Serial()
		self.Serial_Handel.timeout = 0
		self.Serial_Handel.baudrate = 115200
		self.serial_lock = QtCore.QMutex()

		self.serial_thread = SerialThread(self.Serial_Handel, self.serial_lock, self.update_plot)
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

		self.createControlGroupBox()
		self.createControlGroupBox()

		topLayout = QHBoxLayout()
		topLayout.addStretch(1)
		topLayout.addWidget(disableWidgetsCheckBox, 1)
		topLayout.addWidget(serial_label)
		topLayout.addWidget(self.Serial_Port_Box, 2)

		mainLayout = QGridLayout()
		mainLayout.addLayout(topLayout, 0, 0, 1, 2)
		mainLayout.addWidget(self.main_plot, 1, 0, 2, 1)
		mainLayout.addWidget(self.ControlGroupBox, 1, 1, 2, 1)
		mainLayout.setRowStretch(1, 1)
		mainLayout.setRowStretch(2, 1)
		mainLayout.setColumnStretch(0, 10)
		mainLayout.setColumnStretch(1, 1)

		self.cent_widget = QWidget(self)
		self.setCentralWidget(self.cent_widget)
		self.cent_widget.setLayout(mainLayout)

		self.setWindowTitle("Styles")

	def get_samples(self):
		self.serial_lock.lock()
		if self.Serial_Handel.isOpen():
			self.Serial_Handel.write(ProbeScopeInterface.REQUEST_SAMPLE_DATA_COMMAND)
		self.serial_lock.unlock()

	def update_plot(self, samples):
		x = np.linspace(-5, 5, len(samples.samples))
		y = samples.samples

		self.curve.setData(x, y)

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
				print("Set Handel to {}".format(self.Serial_Handel))
			self.serial_lock.unlock()
		else:
			print("Failed to get serial port mutex!")
			self.Serial_Port_Box.setCurrentIndex(0)

	def createControlGroupBox(self):
		self.ControlGroupBox = QGroupBox("Controls")

		updatePushButton = QPushButton("Update")
		updatePushButton.setDefault(True)
		updatePushButton.clicked.connect(self.get_samples)

		autoRange = QPushButton("Auto Range")
		autoRange.setDefault(True)
		autoRange.clicked.connect(self.autorange_plot)

		layout = QVBoxLayout()
		layout.addWidget(updatePushButton)
		layout.addWidget(autoRange)
		layout.addStretch(1)
		self.ControlGroupBox.setLayout(layout)


if __name__ == '__main__':
	app = QApplication(sys.argv)
	gallery = WidgetGallery()
	gallery.show()
	sys.exit(app.exec_())
