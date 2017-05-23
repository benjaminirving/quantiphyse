"""
Author: Martin Craig
Copyright (c) 2017 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import, print_function

import numpy as np
from PySide import QtCore, QtGui

from ..QtInherit.dialogs import error_dialog
from ..QtInherit import HelpButton
from ..ImageView import PickMode
from . import PkWidget

class RoiBuilderWidget(PkWidget):
    """
    Widget for building ROIs
    """

    def __init__(self, **kwargs):
        super(RoiBuilderWidget, self).__init__(name="ROI Builder", icon="roibuild", desc="Build ROIs", **kwargs)

    def init_ui(self):
        layout = QtGui.QVBoxLayout()
        
        hbox = QtGui.QHBoxLayout()
        title = QtGui.QLabel("<font size=5>ROI Builder</font>")
        hbox.addWidget(title)
        hbox.addStretch(1)
        help_btn = HelpButton(self, "roi_builder")
        hbox.addWidget(help_btn)
        layout.addLayout(hbox)

        btn = QtGui.QPushButton("Done")
        btn.clicked.connect(self.done_btn_clicked)
        layout.addWidget(btn)

        layout.addStretch(1)
        self.setLayout(layout)

    def activate(self):
        self.ivl.set_picker(PickMode.LASSO)

    def deactivate(self):
        self.ivl.set_picker(PickMode.SINGLE)

    def done_btn_clicked(self):
        roi = self.ivl.picker.get_roi()
        self.ivm.add_roi("ROI_BUILDER", roi)
