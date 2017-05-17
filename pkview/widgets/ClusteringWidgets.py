"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

"""

from __future__ import division, unicode_literals, absolute_import, print_function

import numpy as np
import pyqtgraph as pg
from PySide import QtCore, QtGui
from sklearn.metrics import pairwise

from pkview.QtInherit import HelpButton
from pkview.QtInherit.dialogs import error_dialog
from pkview.analysis.kmeans import KMeansPCAProcess
from pkview.widgets import PkWidget

class CurveClusteringWidget(PkWidget):
    """
    Widget for clustering the tumour into various regions
    """

    # emit reset command t
    sig_emit_reset = QtCore.Signal(bool)

    def __init__(self, **kwargs):
        super(CurveClusteringWidget, self).__init__(name="Curve Cluster", icon="clustering", desc="Generate clusters from enhancement curves", **kwargs)

        # self.setStatusTip("Click points on the 4D volume to see time curve")
        title1 = QtGui.QLabel("<font size=5> PCA clustering of DCE-MRI </font>")
        bhelp = HelpButton(self, "curve_cluster")
        lhelp = QtGui.QHBoxLayout()
        lhelp.addWidget(title1)
        lhelp.addStretch(1)
        lhelp.addWidget(bhelp)

        # self.setStatusTip("Click points on the 4D volume to see time curve")

        self.win1 = pg.GraphicsLayoutWidget()
        self.win1.setBackground(background=None)
        self.p1 = self.win1.addPlot(title="Cluster representative curves")

        # Run clustering button
        self.b1 = QtGui.QPushButton('Run', self)
        self.b1.clicked.connect(self.run_clustering)

        # Number of clusters inside the ROI
        self.combo = QtGui.QSpinBox(self)
        self.combo.setRange(2, 20)
        self.combo.setValue(4)
        # self.combo.activated[str].connect(self.emit_cchoice)
        self.combo.setToolTip("Set the color of the enhancement curve when a point is clicked on the image. "
                         "Allows visualisation of multiple enhancement curves of different colours")

        # Number of PCA modes
        self.combo2 = QtGui.QSpinBox(self)
        self.combo2.setRange(1, 10)
        self.combo2.setValue(3)
        # self.combo.activated[str].connect(self.emit_cchoice)
        self.combo2.setToolTip("Set the color of the enhancement curve when a point is clicked on the image. "
                         "Allows visualisation of multiple enhancement curves of different colours")

        l03 = QtGui.QHBoxLayout()
        l03.addWidget(self.b1)
        l03.addStretch(1)

        space1 = QtGui.QLabel('')

        # Options
        l01 = QtGui.QHBoxLayout()
        l01.addWidget(QtGui.QLabel('Number of clusters:'))
        l01.addWidget(self.combo)
        l01.addStretch(1)

        l02 = QtGui.QHBoxLayout()
        l02.addWidget(QtGui.QLabel('Normalised PCA modes (Advanced):'))
        l02.addWidget(self.combo2)
        l02.addStretch(1)

        l04 = QtGui.QVBoxLayout()
        l04.addLayout(l01)
        l04.addLayout(l02)

        g01 = QtGui.QGroupBox()
        g01.setLayout(l04)
        g01.setTitle('Clustering options')

        l05 = QtGui.QHBoxLayout()
        l05.addLayout(l03)
        l05.addWidget(g01)
        
        self.b4 = QtGui.QPushButton('Advanced options', self)
        self.b4.clicked.connect(self.show_options)

        # Merge options

        self.b2 = QtGui.QPushButton('Merge', self)
        self.b2.clicked.connect(self.run_merge)

        self.b2b = QtGui.QPushButton('AutoMerge', self)
        self.b2b.clicked.connect(self.run_automerge)

        t1 = QtGui.QLabel('Merge region ')
        self.val_m1 = QtGui.QLineEdit('1', self)
        t2 = QtGui.QLabel(' with ')
        self.val_m2 = QtGui.QLineEdit('2', self)

        l_mergev = QtGui.QVBoxLayout()

        l_merge = QtGui.QHBoxLayout()
        l_merge.addWidget(self.b2)
        l_merge.addWidget(t1)
        l_merge.addWidget(self.val_m1)
        l_merge.addWidget(t2)
        l_merge.addWidget(self.val_m2)

        l_merge2 = QtGui.QHBoxLayout()
        l_merge2.addWidget(self.b2b)
        l_merge2.addStretch()

        l_mergev.addLayout(l_merge)
        l_mergev.addLayout(l_merge2)

        self.g_merge = QtGui.QGroupBox()
        self.g_merge.setLayout(l_mergev)
        self.g_merge.setTitle('Editing regions')
        self.g_merge.setVisible(False)

        # Statistics

        self.b_stat = QtGui.QPushButton('Run', self)
        self.b_stat.clicked.connect(self.generate_voxel_stats)

        self.tabmod1 = QtGui.QStandardItemModel()
        self.tab1 = QtGui.QTableView()
        self.tab1.resizeColumnsToContents()
        self.tab1.setModel(self.tabmod1)

        l_stats = QtGui.QHBoxLayout()
        l_stats.addWidget(self.b_stat)
        l_stats.addWidget(self.tab1)

        self.g_stats = QtGui.QGroupBox()
        self.g_stats.setLayout(l_stats)
        self.g_stats.setTitle('Voxel count')
        self.g_stats.setVisible(False)

        # Outer layout
        l1 = QtGui.QVBoxLayout()
        l1.addLayout(lhelp)
        l1.addLayout(l05)
        l1.addWidget(space1)
        l1.addWidget(self.win1)
        l1.addWidget(self.b4)
        l1.addWidget(self.g_merge)
        l1.addWidget(self.g_stats)
        l1.addStretch(1)
        self.setLayout(l1)

        # Initialisation
        # Volume management widget
        self.process = KMeansPCAProcess(self.ivm)

        self.voxel_count_slice = []
        self.voxel_count = []

    def run_clustering(self):
        """
        Run kmeans clustering using normalised PCA modes
        """

        # Check that pkmodelling can be run
        if self.ivm.vol is None:
            error_dialog("No data loaded")
            return

        if self.ivm.current_roi is None:
            error_dialog("An ROI must be loaded")
            return

        # Disable button
        self.b1.setDown(1)
        self.b1.setDisabled(1)

        options = {
            "n-clusters" : self.combo.value(),
            "norm-data" : True,
            "n-pca" : self.combo2.value(),
            "reduction" : "pca",
            "invert-roi" : False,
            "output-name" : "clusters"
        }
        self.process.run(options)

        self._plot()
        print("Done!")

        # enable button again
        self.b1.setDown(0)
        self.b1.setDisabled(0)

    def reset_graph(self):
        """
        Reset and clear the graph
        """
        self.win1.removeItem(self.p1)
        self.p1 = self.win1.addPlot(title="Cluster representative curves")
        self.p1.setLabel('left', "Signal Enhancement")
        self.p1.setLabel('bottom', "Temporal position")

    def _plot(self):
        """
        Plot the cluster curves
        :return:
        """
        # Clear graph
        self.reset_graph()
        curve1 = []
        roi = self.ivm.rois["clusters"]

        # generate the cluster means
        self._generate_cluster_means()

        xx = np.arange(self.label1_cent.shape[1])

        # TODO need to work on fixing the scaling in a similar way to the normalisation of the overlay
        num_clus = (self.labs_un.max())
        le1 = self.p1.addLegend()

        # Plotting using single or multiple plots
        for ii in self.labs_un:
            if np.sum(self.label1_cent[ii, :]) == 0:
                continue

            pencol = roi.get_pencol(ii)
            name1 = "Region " + str(int(ii))
            curve1.append(self.p1.plot(pen=pencol, width=8.0, name=name1))
            curve1[-1].setData(xx, self.label1_cent[ii, :])

            # le1.addItem(curve1[ii], name1)

    def _generate_cluster_means(self):
        """
        Generate the mean curves for each cluster
        Returns:
        """
        roi = self.ivm.rois["clusters"]
        regions = roi.regions

        curves = np.zeros((len(regions), self.ivm.shape[-1]))

        for region in regions:
            mean = np.median(self.ivm.vol[roi == region], axis=(0, 1, 2))
            curves[region, :] = mean1

    def merge1(self, m1, m2):
        # relabel
        self.label1[self.label1 == m1] = m2

        # signal the change
        self.ivm.add_roi('clusters', self.label1, make_current=True)
        self.sig_emit_reset.emit(1)

        # replot
        self._plot()

    def run_merge(self):
        """

        Returns:

        """

        m1 = int(self.val_m1.text())
        m2 = int(self.val_m2.text())
        self.merge1(m1, m2)

    def run_automerge(self):

        # Use PCA features or true curves?

        # Mean features from each cluster

        # Distance matrix between features
        distmat = pairwise.euclidean_distances(self.label1_cent[1:])
        distmat[distmat == 0] = np.inf
        loc1 = np.where(distmat == distmat.min())[0] + 1
        self.merge1(loc1[0], loc1[1])
        self.label1_cent[loc1[0]][0] = -1E6

    def calculate_voxel_count(self):

        """
        Returns:
        """

        self.voxel_count_slice = []
        self.voxel_count = []

        for ii in self.labs_un:
            # Slice 1 count
            self.voxel_count_slice.append(np.sum(self.label1[:, :, self.ivm.cim_pos[2]] == ii))

            # Volume count
            self.voxel_count.append(np.sum(self.label1 == ii))


    @QtCore.Slot()
    def generate_voxel_stats(self):
        """
        Some initial analysis
        (temporary location before moving analysis into a separate framework)
        """

        # get analysis
        self.calculate_voxel_count()
        self.tabmod1.clear()

        self.tabmod1.setVerticalHeaderItem(0, QtGui.QStandardItem("Slice"))
        self.tabmod1.setVerticalHeaderItem(1, QtGui.QStandardItem("Volume"))

        for cc, ii in enumerate(self.labs_un):

            self.tabmod1.setHorizontalHeaderItem(cc, QtGui.QStandardItem("Region " + str(ii)))
            self.tabmod1.setItem(0, cc, QtGui.QStandardItem(str(np.around(self.voxel_count_slice[cc]))))
            self.tabmod1.setItem(1, cc, QtGui.QStandardItem(str(np.around(self.voxel_count[cc]))))
        
    def show_options(self):
        if self.g_merge.isVisible():
            self.g_merge.setVisible(False)
            self.g_stats.setVisible(False)
        else:
            self.g_merge.setVisible(True)
            self.g_stats.setVisible(True)



