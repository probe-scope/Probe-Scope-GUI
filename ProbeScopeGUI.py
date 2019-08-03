import sys
import time

import numpy as np
import pyqtgraph
import serial
import serial.tools.list_ports
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QCheckBox, QGridLayout, QGroupBox, QHBoxLayout, QPushButton, QStyleFactory, \
	QVBoxLayout, QWidget, QMainWindow, QComboBox, QLabel


class SelfPopulatingComboBox(QComboBox):
	popupAboutToBeShown = QtCore.pyqtSignal()

	def showPopup(self):
		self.popupAboutToBeShown.emit()
		super(SelfPopulatingComboBox, self).showPopup()


class SerialThread(QtCore.QThread):
	def __init__(self, serial_port, serial_lock, parent=None):
		QtCore.QThread.__init__(self, parent)
		self.serial_port = serial_port
		self.serial_lock = serial_lock

	def run(self):
		while True:
			time.sleep(1)
			self.serial_lock.lock()
			print("Serial Obj:"+str(self.serial_port))
			self.serial_lock.unlock()


class WidgetGallery(QMainWindow):
	def __init__(self, parent=None):
		super(WidgetGallery, self).__init__(parent)

		self.originalPalette = QApplication.palette()

		QApplication.setStyle(QStyleFactory.create("Fusion"))

		serial_label = QLabel()
		serial_label.setText("Serial Port:")

		self.Serial_Handel = serial.Serial()
		self.serial_lock = QtCore.QMutex()

		self.serial_thread = SerialThread(self.Serial_Handel, self.serial_lock)
		self.serial_thread.start()

		self.Serial_Port_Box = SelfPopulatingComboBox()
		self.Serial_Port_Box.view().setMinimumWidth(30)
		self.port_list = dict()
		self.Serial_Port_Box.popupAboutToBeShown.connect(self.update_ports)
		self.Serial_Port_Box.currentIndexChanged.connect(self.selected_port)

		disableWidgetsCheckBox = QCheckBox("&Disable widgets")

		# create plot
		self.main_plot = pyqtgraph.PlotWidget()

		self.curve = self.main_plot.plot()
		self.curve.setPen((200, 200, 100))

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

	def update_plot(self):
		num_points = 5000

		x = np.linspace(-5, 5, num_points)
		y = np.sin(x) * 3 + np.random.normal(size=num_points)

		self.curve.setData(x, y)

	def autorange_plot(self):
		self.main_plot.autoRange()

	def update_ports(self):
		self.port_list = dict()

		# add dummy NC entry
		self.port_list[" - "] = None

		for port in serial.tools.list_ports.comports():
			self.port_list[str(port.description)] = port.device

		self.Serial_Port_Box.clear()
		self.Serial_Port_Box.addItems(self.port_list.keys())

	def selected_port(self):
		selected_port = self.Serial_Port_Box.currentText()
		print("Selected:" + selected_port)

		if self.serial_lock.tryLock(2000):  # Wait 2 seconds
			if selected_port is '' or self.port_list[selected_port] is None:
				# Selected dummy object
				self.Serial_Handel.close()
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
		updatePushButton.clicked.connect(self.update_plot)

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
