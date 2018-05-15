"""
Quantiphyse - Widget which displays list of all data loaded

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import print_function, division, absolute_import

from PySide import QtGui, QtCore
from quantiphyse.gui.widgets import QpWidget, HelpButton, TextViewerDialog
from quantiphyse.utils import debug, get_icon, get_version, get_local_file
from quantiphyse import __contrib__, __acknowledge__

SUMMARY = """
The GUI enables analysis of an MRI volume, and multiple ROIs and data 
with pharmacokinetic modelling, subregion analysis and statistics included. 
Please use help (?) buttons for more online information on each widget and the entire GUI.

""" + \
"Creators: " + ", ".join([author for author in __contrib__]) + \
"\nAcknowlegements: " + ", ".join([ack for ack in __acknowledge__])

class OverviewWidget(QpWidget):

    def __init__(self, **kwargs):
        super(OverviewWidget, self).__init__(name="Volumes", icon="volumes", desc="Overview of volumes loaded", group="DEFAULT", position=0, **kwargs)

    def init_ui(self):
        layout = QtGui.QVBoxLayout()

        hbox = QtGui.QHBoxLayout()
        pixmap = QtGui.QPixmap(get_icon("quantiphyse_75.png"))
        lpic = QtGui.QLabel(self)
        lpic.setPixmap(pixmap)
        hbox.addWidget(lpic)
        hbox.addStretch(1)
        b1 = HelpButton(self)
        hbox.addWidget(b1)
        layout.addLayout(hbox)

        ta = QtGui.QLabel(SUMMARY)
        ta.setWordWrap(True)
        layout.addWidget(ta)

        box = QtGui.QGroupBox()
        hbox = QtGui.QHBoxLayout()
        box.setLayout(hbox)
        disc = QtGui.QLabel("<font size=2> Disclaimer: This software has been developed for research purposes only, and "
                          "should not be used as a diagnostic tool. The authors or distributors will not be "
                          "responsible for any direct, indirect, special, incidental, or consequential damages "
                          "arising of the use of this software. By using the this software you agree to this disclaimer."
                          "<p>"
                          "Please read the Quantiphyse License for more information")
        disc.setWordWrap(True)
        hbox.addWidget(disc, 10)
        license_btn = QtGui.QPushButton("License")
        license_btn.clicked.connect(self._view_license)
        hbox.addWidget(license_btn)
        layout.addWidget(box)

        self.vols = DataListWidget(self)
        layout.addWidget(self.vols)

        hbox = QtGui.QHBoxLayout()
        btn = QtGui.QPushButton("Rename")
        btn.clicked.connect(self.rename)
        hbox.addWidget(btn)
        btn = QtGui.QPushButton("Delete")
        btn.clicked.connect(self.delete)
        hbox.addWidget(btn)
        btn = QtGui.QPushButton("Set as main data")
        btn.clicked.connect(self.set_main)
        hbox.addWidget(btn)
        layout.addLayout(hbox)

        self.setLayout(layout)

    def _view_license(self):
        license_file = get_local_file("licence.md")
        with open(license_file, "r") as f:
            text = f.read()
        dlg = TextViewerDialog(self, "Quantiphyse License", text=text)
        dlg.exec_()

    def delete(self):
        if self.vols.selected is not None:
            ok = QtGui.QMessageBox.warning(self, "Delete data", "Delete '%s'?" % self.vols.selected,
                                            QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
            if ok:
                if self.vols.selected_type.startswith("Data"):
                    self.ivm.delete_data(self.vols.selected)
                elif self.vols.selected_type == "ROI":
                    self.ivm.delete_roi(self.vols.selected)
                else:                
                    # Delete main volume by doing a reset
                    self.ivm.reset()

    def rename(self):
        if self.vols.selected is not None:
            text, result = QtGui.QInputDialog.getText(self, "Renaming '%s'" % self.vols.selected, "New name", 
                                                      QtGui.QLineEdit.Normal, self.vols.selected)
            if result:
                if self.vols.selected_type.startswith("Data"):
                    self.ivm.rename_data(self.vols.selected, text)
                elif self.vols.selected_type == "ROI":
                    self.ivm.rename_roi(self.vols.selected, text)
                else:
                    # Nothing else should care about the name of the main volume
                    self.ivm.main.name = text
                    self.vols.update_list(None)

    def set_main(self):
        if self.vols.selected is not None:
            self.ivm.set_main_data(self.vols.selected)
            
class DataListWidget(QtGui.QTableWidget):
    """
    Table showing loaded volumes
    """
    def __init__(self, parent):
        super(DataListWidget, self).__init__(parent)
        self.ivm = parent.ivm
        self.setColumnCount(3)
        self.setHorizontalHeaderLabels(["Name", "Type", "File"])
        header = self.horizontalHeader();
        header.setResizeMode(2, QtGui.QHeaderView.Stretch);
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.setSelectionMode(QtGui.QAbstractItemView.NoSelection)
        self.setEditTriggers(QtGui.QAbstractItemView.NoEditTriggers)
        self.cellClicked.connect(self.clicked)
        self.ivm.sig_main_data.connect(self.update_list)
        self.ivm.sig_current_data.connect(self.update_list)
        self.ivm.sig_all_data.connect(self.update_list)
        self.ivm.sig_current_roi.connect(self.update_list)
        self.ivm.sig_all_rois.connect(self.update_list)
        self.selected = None
        self.selected_type = None

    def get_name(self, vol):
        if vol.fname is not None:
            name = vol.fname
        else:
            name = vol.name
        return name

    def add_volume(self, row, vol_type, vol, current=False):
        self.setItem(row, 0, QtGui.QTableWidgetItem(vol.name))
        self.setItem(row, 1, QtGui.QTableWidgetItem(vol_type))
        item = self.item(row, 0)
        if vol.fname is not None:
            self.setItem(row, 2, QtGui.QTableWidgetItem(vol.fname))
            if item is not None:
                item.setToolTip(vol.fname)
        if current:
            if item is not None:
                font = self.item(row, 0).font()
                font.setBold(True)
                self.item(row, 0).setFont(font)
                self.item(row, 1).setFont(font)
                if vol.fname is not None: self.item(row, 2).setFont(font)
        
    def update_list(self, list1):
        try:
            self.blockSignals(True)
            n = len(self.ivm.data) + len(self.ivm.rois)
            self.setRowCount(n)
            row = 0
            for name in sorted(self.ivm.data.keys()):
                ovl = self.ivm.data[name]
                t = "Data"
                if self.ivm.main is not None and self.ivm.main.name == ovl.name:
                    t += "*"
                self.add_volume(row, t, ovl, self.ivm.is_current_data(ovl))
                row += 1
            for name in sorted(self.ivm.rois.keys()):
                roi = self.ivm.rois[name]
                self.add_volume(row, "ROI", roi, self.ivm.is_current_roi(roi))
                row += 1
        finally:
            self.blockSignals(False)

    def clicked(self, row, col):
        self.selected_type = self.item(row, 1).text()
        self.selected = self.item(row, 0).text()
        if self.selected_type.startswith("Data"):
            self.ivm.set_current_data(self.selected)
        elif self.selected_type == "ROI":
            self.ivm.set_current_roi(self.selected)

QP_WIDGETS =  [OverviewWidget]
