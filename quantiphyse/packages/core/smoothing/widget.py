from PySide import QtGui

from quantiphyse.gui.widgets import QpWidget, TitleWidget, OverlayCombo, NumericOption
from quantiphyse.utils import debug
from quantiphyse.utils.exceptions import QpException

from .process import SmoothingProcess
    
class SmoothingWidget(QpWidget):
    """
    Gaussian smoothing widget
    """
    def __init__(self, **kwargs):
        super(SmoothingWidget, self).__init__(name="Smoothing", icon="smooth.png", desc="Gaussian smoothing", **kwargs)
        
    def init_ui(self):
        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox)

        title = TitleWidget(self, title="Data Smoothing", subtitle="Smooth data using a Gaussian kernel")
        vbox.addWidget(title)

        hbox = QtGui.QHBoxLayout()
        gbox = QtGui.QGroupBox()
        gbox.setTitle("Options")
        grid = QtGui.QGridLayout()
        gbox.setLayout(grid)

        grid.addWidget(QtGui.QLabel("Data to smooth"), 0, 0)
        self.data_combo = OverlayCombo(self.ivm)
        self.data_combo.currentIndexChanged.connect(self.data_changed)
        grid.addWidget(self.data_combo, 0, 1)
        self.sigma = NumericOption("Sigma", grid, xpos=0, ypos=1, minval=0, step=0.1, default=1.0)
        grid.addWidget(QtGui.QLabel("Output name"), 2, 0)
        self.output_name = QtGui.QLineEdit()
        grid.addWidget(self.output_name, 2, 1)

        hbox.addWidget(gbox)
        hbox.addStretch(1)
        vbox.addLayout(hbox)

        hbox = QtGui.QHBoxLayout()
        run_btn = QtGui.QPushButton("Run")
        run_btn.clicked.connect(self.run)
        hbox.addWidget(run_btn)
        hbox.addStretch(1)
        vbox.addLayout(hbox)

        vbox.addStretch(1) 
        self.data_changed()  
    
    def data_changed(self):
        self.output_name.setText("%s_smoothed" % self.data_combo.currentText())

    def batch_options(self):
        return "Smooth", {"data" : self.data_combo.currentText(),
                          "sigma" : self.sigma.spin.value(),
                          "output-name" : self.output_name.text()}

    def run(self):
        process = SmoothingProcess(self.ivm)
        process.run(self.batch_options()[1])