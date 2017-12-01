import os

from PySide import QtGui, QtCore

from quantiphyse.gui.widgets import QpWidget, TitleWidget
from quantiphyse.utils import debug
from quantiphyse.utils.exceptions import QpException
from quantiphyse.utils.batch import run_batch, check_batch

class BatchBuilderWidget(QpWidget):
    """
    Simple widget for building and running batch files
    """
    def __init__(self, **kwargs):
        super(BatchBuilderWidget, self).__init__(name="Batch Builder", icon="batch", 
                                                 desc="Simple helper for building and running batch files", **kwargs)
        
    def init_ui(self):
        vbox = QtGui.QVBoxLayout()
        self.setLayout(vbox)

        title = TitleWidget(self, title="Batch Builder", subtitle=self.description, batch_btn=False)
        vbox.addWidget(title)

        self.proc_edit = QtGui.QPlainTextEdit()
        self.proc_edit.textChanged.connect(self._validate)
        vbox.addWidget(self.proc_edit)

        hbox = QtGui.QHBoxLayout()
        #self.new_case_btn = QtGui.QPushButton("New Case")
        #hbox.addWidget(self.new_case_btn)
        #hbox.setAlignment(self.new_case_btn, QtCore.Qt.AlignTop)

        self.reset_btn = QtGui.QPushButton("Reset")
        self.reset_btn.clicked.connect(self._reset)
        hbox.addWidget(self.reset_btn)
        hbox.addStretch(1)

        self.run_btn = QtGui.QPushButton("Run")
        self.run_btn.clicked.connect(self._run)
        hbox.addWidget(self.run_btn)

        self.save_btn = QtGui.QPushButton("Save")
        self.save_btn.clicked.connect(self._save)
        hbox.addWidget(self.save_btn)
        vbox.addLayout(hbox)

        self.proc_warn = QtGui.QLabel("")
        self.proc_warn.setStyleSheet("QLabel { color : red; }")
        vbox.addWidget(self.proc_warn)

        self.default_dir = os.getcwd()
        self.changed = False
        self._reset()

    def activate(self):
        self.ivm.sig_main_data.connect(self._update)
        self.ivm.sig_all_data.connect(self._update)
        self.ivm.sig_all_rois.connect(self._update)
        self._update()

    def deactivate(self):
        self.ivm.sig_main_data.disconnect(self._update)
        self.ivm.sig_all_data.disconnect(self._update)
        self.ivm.sig_all_rois.disconnect(self._update)

    def _update(self):
        if not self.changed:
            self._reset()

    def _reset(self):
        if self.changed and self.proc_edit.toPlainText().strip() != "":
            ok = QtGui.QMessageBox.warning(self, "Reset to current data", 
                                        "Changes to batch file will be lost",
                                        QtGui.QMessageBox.Ok | QtGui.QMessageBox.Cancel)
            if not ok: return
        
        t = ""
        if self.ivm.main is not None:
            filedata = [d for d in self.ivm.data.values() if hasattr(d, "fname") and d.fname is not None]
            filerois= [d for d in self.ivm.rois.values() if hasattr(d, "fname") and d.fname is not None]
            
            casedir = os.getcwd()
            if hasattr(self.ivm.main, "fname"):
                casedir = os.path.dirname(self.ivm.main.fname)

            t += "OutputFolder: qp_out\n"
            t += "Debug: False\n"
            t += "\n"
            t += "Processing:\n"
            t += "  - Load:\n"
            t += "      data:\n"
            for qpd in filedata:
                d, f = os.path.split(qpd.fname)
                if d == casedir:
                    path = f
                else:
                    path = qpd.fname
                t += "        %s: %s\n" % (path, qpd.name)
            t += "      rois:\n"
            for qpd in filerois:
                d, f = os.path.split(qpd.fname)
                if d == casedir:
                    path = f
                else:
                    path = qpd.fname
                t += "        %s: %s\n" % (path, qpd.name)
            t += "\n"
            t += "  # Additional processing steps go here\n"
            t += "\n"
            t += "  - SaveAllExcept:\n"
            for d in filedata:
                t += "      %s:\n" % d.name
            for d in filerois:
                t += "      %s:\n" % d.name
            t += "\n"

            t += "Cases:\n"
            t += "  Case1:\n"
            t += "    Folder: %s\n" % casedir
            t += "\n"

        self.proc_edit.setPlainText(t)
        self.changed = False
        self.reset_btn.setEnabled(False)

    def _validate(self):
        self.changed = True
        self.reset_btn.setEnabled(True)
        t = self.proc_edit.toPlainText()
        self.proc_warn.setText("")
        if '\t' in self.proc_edit.toPlainText():
            self.proc_warn.setText("Tabs detected")
        else:
            try:
                warnings = check_batch(code=t)
                self.proc_warn.setText("\n".join([w for w in warnings]))
            except Exception, e:
                self.proc_warn.setText("Invalid YAML: %s" % str(e))

    def _run(self):
        run_batch(code=self.proc_edit.toPlainText())

    def _save(self):
        fname, _ = QtGui.QFileDialog.getSaveFileName(self, 'Save batch file', 
                                                     dir=self.default_dir, 
                                                     filter="YAML files (*.yaml)")
        if fname != '':
            f = open(fname, "w")
            try:
                f.write(self.proc_edit.toPlainText())
            finally:
                f.close()
        else: # Cancelled
            pass