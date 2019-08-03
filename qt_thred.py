import numpy as np
import sys
import pyqtgraph
from PyQt5 import QtGui
from PyQt5.QtCore import QDateTime, Qt, QTimer
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateTimeEdit,
							 QDial, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
							 QProgressBar, QPushButton, QScrollBar, QSizePolicy,
							 QSlider, QSpinBox, QStyleFactory, QTableWidget, QTabWidget, QTextEdit,
							 QVBoxLayout, QWidget, QMainWindow)


class WidgetGallery(QMainWindow):
	def __init__(self, parent=None):
		super(WidgetGallery, self).__init__(parent)

		self.originalPalette = QApplication.palette()

		QApplication.setStyle(QStyleFactory.create("Fusion"))

		disableWidgetsCheckBox = QCheckBox("&Disable widgets")

		# create plot
		self.main_plot = pyqtgraph.PlotWidget()

		self.curve = self.main_plot.plot()
		self.curve.setPen((200, 200, 100))

		self.createControlGroupBox()
		self.createControlGroupBox()

		topLayout = QHBoxLayout()
		topLayout.addStretch(1)
		topLayout.addWidget(disableWidgetsCheckBox)

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
		x = np.linspace(-5, 5, 5000)
		y = np.sin(x) * 3 + np.random.normal(size=(5000))

		self.curve.setData(x, y)

	def autorange_plot(self):
		self.main_plot.autoRange()

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