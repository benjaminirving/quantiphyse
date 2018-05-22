"""
Quantiphyse - classes which draw data views

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, unicode_literals, absolute_import, print_function

import collections

from PySide import QtCore, QtGui
import numpy as np

import pyqtgraph as pg

from quantiphyse.utils import get_lut, get_pencol, debug, get_icon
from quantiphyse.data import OrthoSlice, DataGrid
from quantiphyse.gui.widgets import OptionsButton, RoiCombo, OverlayCombo

from .HistogramWidget import MultiImageHistogramWidget

class MaskableImage(pg.ImageItem):
    """
    Minor addition to ImageItem to allow it to be masked by an RoiView
    """
    def __init__(self, image=None, **kwargs):
        pg.ImageItem.__init__(self, image, **kwargs)
        self.mask = None
        self.boundary = DataView.BOUNDARY_TRANS
        self.border = None

    def setBoundaryMode(self, mode):
        """
        Set the boundary mode, i.e. how data outside the colour map
        range is treated. It can be made transparent or clamped to
        the max/min colour

        :param mode: DataView.BOUNDARY_TRANS or DataView.BOUNDARY_CLAMP
        """
        self.boundary = mode

    def render(self):
        """
        Custom masked renderer based on PyQtGraph code
        """
        if self.image is None or self.image.size == 0:
            return
        if isinstance(self.lut, collections.Callable):
            lut = self.lut(self.image)
        else:
            lut = self.lut

        argb, alpha = pg.functions.makeARGB(self.image, lut=lut, levels=self.levels)
        if self.image.size > 1:
            if self.mask is not None:
                argb[:, :, 3][self.mask == 0] = 0

            if self.boundary == DataView.BOUNDARY_TRANS:
                # Make out of range values transparent
                trans = np.logical_or(self.image < self.levels[0], self.image > self.levels[1])
                argb[:, :, 3][trans] = 0

        self.qimage = pg.functions.makeQImage(argb, alpha)

class DataView(QtCore.QObject):
    """
    View of a data item
    """

    BOUNDARY_TRANS = 0
    BOUNDARY_CLAMP = 1

    # Signals when view parameters are changed
    sig_view_changed = QtCore.Signal(object)

    # Signals when the view items need to be redrawn
    sig_redraw = QtCore.Signal(object)

    def __init__(self, ivm):
        super(DataView, self).__init__()
        self.ivm = ivm

        self.default_options = {}
        self.cached_options = {}
        self.redraw_options = []
        self.data = None
        self.opts = dict(self.default_options)
        self.sig_view_changed.connect(self.update)

    def set(self, name, value):
        self.opts[name] = value
        self.sig_view_changed.emit(self)
        if name in self.redraw_options:
            self.sig_redraw.emit(self)

    def redraw(self, vb, slice_plane, slice_vol):
        """
        Redraw graphics items associated with the specified pg.ViewBox

        :param vb: pg.ViewBox to redraw
        :param slice_plane: OrthoSlice defining the slice to draw
        :param slice_vol: Index of the volume to use
        """
        pass

    def update(self):
        """
        Update existing graphics items for view parameters without redrawing
        """
        pass

class ImageDataView(DataView):
    """
    View of data rendered as an image slice
    """

    def __init__(self, ivm):
        super(ImageDataView, self).__init__(ivm)
        self.default_options = {
            "visible" : True,
            "roi_only" : False,
            "boundary" : self.BOUNDARY_CLAMP,
            "alpha" : 255,
            "cmap" : "grey",
            "cmap_range" : None,
            "z_value" : -1,
            "interp_order" : 0,
        }
        self.opts = dict(self.default_options)
        self.redraw_options += ["visible", "roi_only", "z_value", "interp_order"]
        self.imgs = {}
        self.histogram = None
        self.mask = None

    def redraw(self, vb, slice_plane, slice_vol):
        img = self._get_img(vb)
        self.update()
        if img.isVisible():
            slicedata, slicemask, scale, offset = self.data.slice_data(slice_plane, vol=slice_vol, interp_order=self.opts["interp_order"])
            img.setTransform(QtGui.QTransform(scale[0, 0], scale[0, 1], scale[1, 0], scale[1, 1],
                                              offset[0], offset[1]))
            img.setImage(slicedata, autoLevels=False)

            if self.mask is not None and self.opts["roi_only"]:
                maskdata, _, _, _ = self.mask.slice_data(slice_plane)
                img.mask = np.logical_and(maskdata, slicemask)
            else:
                img.mask = slicemask
       
    def update(self):
        for img in self.imgs.values():
            img.setVisible(self.data is not None and self.opts["visible"])
            img.setZValue(self.opts["z_value"])
            img.setBoundaryMode(self.opts["boundary"])
            img.setLevels(self.opts["cmap_range"])

    def _get_img(self, vb):
        if vb.name not in self.imgs:
            img = MaskableImage(border='k')
            vb.addItem(img)
            self.imgs[vb.name] = img
            if self.histogram is not None:
                self.histogram.add_img(img)
        return self.imgs[vb.name]
 
    def _init_opts(self):
        """
        Retrieve view options from cache or use defaults
        """
        if self.data is not None:
            if self.data.name not in self.cached_options:
                self.cached_options[self.data.name] = dict(self.default_options)
            self.opts = self.cached_options[self.data.name]
        else:
            self.opts = dict(self.default_options)

    def _init_cmap(self, percentile=100):
        if self.data is not None and self.opts["cmap_range"] is None:
            # Initial colourmap range
            flat = self.data.volume(int(self.data.nvols/2)).flatten()
            if percentile < 100:
                cmap = [flat.min(), np.percentile(flat, percentile)]
                if cmap[0] == cmap[1]:
                    cmap = [flat.min(), flat.max()]
                self.opts["cmap_range"] = cmap
            else:
                self.opts["cmap_range"] = [flat.min(), flat.max()]
    def _cleanup_cache(self, data_items):
        """
        Remove data items which no longer exist from the option cache
        """
        for key in self.cached_options.keys():
            if key not in data_items:
                del self.cached_options[key]

class MainDataView(ImageDataView):
    """
    View of main data
    """

    def __init__(self, ivm):
        super(MainDataView, self).__init__(ivm)
        self.ivm.sig_main_data.connect(self._main_data_changed)
        self.ivm.sig_all_data.connect(self._cleanup_cache)

    def _main_data_changed(self, data):
        self.data = data
        self._init_opts()
        self._init_cmap(percentile=99)
        self.sig_view_changed.emit(self)
        self.sig_redraw.emit(self)

class OverlayView(ImageDataView):
    """
    View of the current overlay

    Stores details about visual parameters, e.g. color map and range
    """

    def __init__(self, ivm):
        super(OverlayView, self).__init__(ivm)

        self.default_options.update({
            "boundary" : self.BOUNDARY_TRANS,
            "cmap" : "jet",
            "z_value" : 0,
        })
        self._init_opts()

        self.ivm.sig_current_roi.connect(self._current_roi_changed)
        self.ivm.sig_current_data.connect(self._current_data_changed)
        self.ivm.sig_all_data.connect(self._cleanup_cache)

    def _current_roi_changed(self, roi):
        if roi is not None and self.data is not None:
            self.mask = roi.resample(self.data.grid)
        else:
            self.mask = None
        self.sig_view_changed.emit(self)
        self.sig_redraw.emit(self)

    def _current_data_changed(self, data):
        self.data = data
        self._init_opts()
        self._init_cmap()
        self._current_roi_changed(self.ivm.current_roi)
        self.sig_view_changed.emit(self)
        self.sig_redraw.emit(self)

class RoiView(ImageDataView):
    """
    View of a ROI,

    Stores details about visual parameters, e.g. display style (contour, shaded, etc)
    """

    def __init__(self, ivm):
        super(RoiView, self).__init__(ivm)

        self.default_options.update({
            "shade" : True,
            "contour" : False,
            "alpha" : 150,
            "outline_width" : 3.0,
            "z_value" : 1,
        })
        self._init_opts()
        self.contours = {}
        self.redraw_options += ["shade", "contour", "z_value"]

        self.ivm.sig_current_roi.connect(self._current_roi_changed)
        self.ivm.sig_all_rois.connect(self._cleanup_cache)

    def redraw(self, vb, slice_plane, slice_vol):
        img = self._get_img(vb)
        contours = self._get_contours(vb)
        self.update()
        n_contours = 0
        if self.data is not None:
            slicedata, _, scale, offset = self.data.slice_data(slice_plane)
            transform = QtGui.QTransform(scale[0, 0], scale[0, 1], scale[1, 0], scale[1, 1],
                                         offset[0], offset[1])

            if img.isVisible():
                img.setImage(slicedata, autoLevels=False)
                img.setTransform(transform)

            if self.opts["contour"]:
                # Update data and level for existing contour items, and create new ones if needed
                for val in self.data.regions():
                    pencol = get_pencol(self.data, val)
                    if val != 0:
                        if n_contours == len(contours):
                            contours.append(pg.IsocurveItem())
                            vb.addItem(contours[n_contours])

                        contour = contours[n_contours]
                        contour.setTransform(transform)
                        contour.setData((slicedata == val).astype(np.int))
                        contour.setLevel(1)
                        contour.setPen(pg.mkPen(pencol, width=self.opts["outline_width"]))
                        n_contours += 1

        # Clear data from contours not required - FIXME delete them?
        for idx in range(n_contours, len(contours)):
            contours[idx].setData(None)

    def update(self):
        for img in self.imgs.values():
            img.setVisible(self.data is not None and self.opts["shade"])
            img.setZValue(self.opts["z_value"])
            img.setBoundaryMode(self.opts["boundary"])
            lut = get_lut(self.data, self.opts["alpha"])
            img.setLookupTable(lut)
            img.setLevels([0, len(lut)-1], update=True)
            
    def _get_contours(self, vb):
        if vb.name not in self.contours:
            self.contours[vb.name] = []
        return self.contours[vb.name]

    def _current_roi_changed(self, roi):
        self.data = roi
        self._init_opts()
        self.sig_view_changed.emit(self)
        self.sig_redraw.emit(self)
           
class RoiViewWidget(QtGui.QGroupBox):
    """ Change view options for ROI """
    def __init__(self, ivl, view):
        self.ivl = ivl
        self.ivm = ivl.ivm
        self.view = view

        QtGui.QGroupBox.__init__(self, "ROI")
        grid = QtGui.QGridLayout()
        self.setLayout(grid)

        grid.addWidget(QtGui.QLabel("ROI"), 0, 0)
        self.roi_combo = RoiCombo(self.ivm, none_option=True)
        grid.addWidget(self.roi_combo, 0, 1)
        grid.addWidget(QtGui.QLabel("View"), 1, 0)
        self.roi_view_combo = QtGui.QComboBox()
        self.roi_view_combo.addItem("Shaded")
        self.roi_view_combo.addItem("Contour")
        self.roi_view_combo.addItem("Both")
        self.roi_view_combo.addItem("None")
        grid.addWidget(self.roi_view_combo, 1, 1)
        grid.addWidget(QtGui.QLabel("Alpha"), 2, 0)
        self.roi_alpha_sld = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.roi_alpha_sld.setFocusPolicy(QtCore.Qt.NoFocus)
        self.roi_alpha_sld.setRange(0, 255)
        self.roi_alpha_sld.setValue(150)
        grid.addWidget(self.roi_alpha_sld, 2, 1)
        grid.setRowStretch(3, 1)

        self.roi_combo.currentIndexChanged.connect(self._combo_changed)
        self.roi_view_combo.currentIndexChanged.connect(self._view_changed)
        self.roi_alpha_sld.valueChanged.connect(self._alpha_changed)
        view.sig_view_changed.connect(self._update)

    def _update(self, view):
        if view is not None:
            try:
                self.roi_view_combo.blockSignals(True)
                self.roi_alpha_sld.blockSignals(True)
                self.roi_combo.blockSignals(True)

                if view.opts["shade"] and view.opts["contour"]:
                    self.roi_view_combo.setCurrentIndex(2)
                elif view.opts["shade"]:
                    self.roi_view_combo.setCurrentIndex(0)
                elif view.opts["contour"]:
                    self.roi_view_combo.setCurrentIndex(1)
                else:
                    self.roi_view_combo.setCurrentIndex(3)
                self.roi_alpha_sld.setValue(view.opts["alpha"])

                if view.data is not None:
                    idx = self.roi_combo.findText(view.data.name)
                    self.roi_combo.setCurrentIndex(idx)

            finally:
                self.roi_view_combo.blockSignals(False)
                self.roi_alpha_sld.blockSignals(False)
                self.roi_combo.blockSignals(False)

    def _combo_changed(self, idx):
        if idx > 0:
            roi = self.roi_combo.itemText(idx)
            self.ivl.ivm.set_current_roi(roi)
        else:
            self.ivl.ivm.set_current_roi(None)

    def _view_changed(self, idx):
        self.view.set("shade", idx in (0, 2))
        self.view.set("contour", idx in (1, 2))

    def _alpha_changed(self, alpha):
        """ Set the ROI transparency """
        self.view.set("alpha", alpha)

class OverlayViewWidget(QtGui.QGroupBox):
    """ Change view options for ROI """
    def __init__(self, ivl, view):
        QtGui.QGroupBox.__init__(self, "Overlay")
        self.ivl = ivl
        self.ivm = ivl.ivm
        self.view = view

        grid = QtGui.QGridLayout()
        self.setLayout(grid)

        grid.addWidget(QtGui.QLabel("Overlay"), 0, 0)
        self.overlay_combo = OverlayCombo(self.ivm, none_option=True)
        grid.addWidget(self.overlay_combo, 0, 1)
        grid.addWidget(QtGui.QLabel("View"), 1, 0)
        self.ov_view_combo = QtGui.QComboBox()
        self.ov_view_combo.addItem("All")
        self.ov_view_combo.addItem("Only in ROI")
        self.ov_view_combo.addItem("None")
        grid.addWidget(self.ov_view_combo, 1, 1)
        grid.addWidget(QtGui.QLabel("Color map"), 2, 0)
        hbox = QtGui.QHBoxLayout()
        self.ov_cmap_combo = QtGui.QComboBox()
        self.ov_cmap_combo.addItem("jet")
        self.ov_cmap_combo.addItem("hot")
        self.ov_cmap_combo.addItem("gist_heat")
        self.ov_cmap_combo.addItem("flame")
        self.ov_cmap_combo.addItem("bipolar")
        self.ov_cmap_combo.addItem("spectrum")
        hbox.addWidget(self.ov_cmap_combo)
        self.ov_levels_btn = QtGui.QPushButton()
        self.ov_levels_btn.setIcon(QtGui.QIcon(get_icon("levels.png")))
        self.ov_levels_btn.setFixedSize(16, 16)
        self.ov_levels_btn.setToolTip("Adjust colour map levels")
        self.ov_levels_btn.clicked.connect(self._show_ov_levels)
        self.ov_levels_btn.setEnabled(False)
        hbox.addWidget(self.ov_levels_btn)
        grid.addLayout(hbox, 2, 1)
        grid.addWidget(QtGui.QLabel("Alpha"), 3, 0)
        self.ov_alpha_sld = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.ov_alpha_sld.setFocusPolicy(QtCore.Qt.NoFocus)
        self.ov_alpha_sld.setRange(0, 255)
        self.ov_alpha_sld.setValue(255)
        grid.addWidget(self.ov_alpha_sld, 3, 1)
        grid.setRowStretch(4, 1)

        self.overlay_combo.currentIndexChanged.connect(self._combo_changed)
        self.ov_view_combo.currentIndexChanged.connect(self._view_changed)
        self.ov_cmap_combo.currentIndexChanged.connect(self._cmap_changed)
        self.ov_alpha_sld.valueChanged.connect(self._alpha_changed)
        self.view.sig_view_changed.connect(self._update)

    def _update(self, view):
        widgets = [self.ov_view_combo, self.ov_cmap_combo,
                   self.ov_alpha_sld, self.overlay_combo]
        try:
            for w in widgets:
                w.blockSignals(True)

            if not view.opts["visible"]:
                self.ov_view_combo.setCurrentIndex(2)
            elif view.opts["roi_only"]:
                self.ov_view_combo.setCurrentIndex(1)
            else:
                self.ov_view_combo.setCurrentIndex(0)

            # 'Custom' only appears as a flag to indicate the user has messed with the 
            # LUT using the histogram widget. Otherwise is is hidden
            cmap = view.opts["cmap"]
            if cmap == "custom":
                idx = self.ov_cmap_combo.findText("custom")
                if idx >= 0:
                    self.ov_cmap_combo.setCurrentIndex(idx)
                else:
                    self.ov_cmap_combo.addItem("custom")
                    idx = self.ov_cmap_combo.findText("custom")
                    self.ov_cmap_combo.setCurrentIndex(idx)
            else:
                idx = self.ov_cmap_combo.findText("custom")
                if idx >= 0:
                    self.ov_cmap_combo.removeItem(idx)
                idx = self.ov_cmap_combo.findText(view.opts["cmap"])
                self.ov_cmap_combo.setCurrentIndex(idx)

            self.ov_alpha_sld.setValue(view.opts["alpha"])

            self.ov_levels_btn.setEnabled(view.data is not None)
            if view.data is not None:
                idx = self.overlay_combo.findText(view.data.name)
                debug("New current data: ", view.data.name, idx)
                self.overlay_combo.setCurrentIndex(idx)
            else:
                self.overlay_combo.setCurrentIndex(-1)

        finally:
            for w in widgets:
                w.blockSignals(False)

    def _combo_changed(self, idx):
        if idx > 0:
            ov = self.overlay_combo.itemText(idx)
            self.ivm.set_current_data(ov)
        else:
            self.ivl.ivm.set_current_data(None)

    def _cmap_changed(self, idx):
        cmap = self.ov_cmap_combo.itemText(idx)
        self.view.set("cmap", cmap)

    def _view_changed(self, idx):
        """ Viewing style (all or within ROI only) changed """
        self.view.set("visible", idx in (0, 1))
        self.view.set("roi_only", (idx == 1))

    def _alpha_changed(self, alpha):
        """ Set the data transparency """
        self.view.set("alpha", alpha)

    def _show_ov_levels(self):
        dlg = LevelsDialog(self, self.ivl, self.ivm, self.view)
        dlg.exec_()

class LevelsDialog(QtGui.QDialog):

    def __init__(self, parent, ivl, ivm, view):
        super(LevelsDialog, self).__init__(parent)
        self.ivl = ivl
        self.ivm = ivm
        self.view = view

        self.setWindowTitle("Levels for %s" % view.data.name)
        vbox = QtGui.QVBoxLayout()

        grid = QtGui.QGridLayout()
        self.min_spin = self._add_spin(grid, "Minimum", 0)
        self.max_spin = self._add_spin(grid, "Maximum", 1)   

        grid.addWidget(QtGui.QLabel("Percentage of data range"), 2, 0)
        hbox = QtGui.QHBoxLayout()
        self.percentile_spin = QtGui.QSpinBox()
        self.percentile_spin.setMaximum(100)
        self.percentile_spin.setMinimum(1)
        self.percentile_spin.setValue(100)
        hbox.addWidget(self.percentile_spin)
        btn = QtGui.QPushButton("Reset")
        btn.clicked.connect(self._reset)
        hbox.addWidget(btn)
        self.use_roi = QtGui.QCheckBox("Within ROI")
        hbox.addWidget(self.use_roi)
        grid.addLayout(hbox, 2, 1)

        grid.addWidget(QtGui.QLabel("Values outside range are"), 4, 0)
        self.combo = QtGui.QComboBox()
        self.combo.addItem("Transparent")
        self.combo.addItem("Clamped to max/min colour")
        self.combo.setCurrentIndex(self.view.opts["boundary"])
        self.combo.currentIndexChanged.connect(self._bound_changed)
        grid.addWidget(self.combo, 4, 1)
        vbox.addLayout(grid)

        bbox = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Ok)
        bbox.accepted.connect(self.close)
        vbox.addWidget(bbox)

        self.setLayout(vbox)
    
    def _add_spin(self, grid, label, row):
        grid.addWidget(QtGui.QLabel(label), row, 0)
        spin = QtGui.QDoubleSpinBox()
        spin.setMaximum(1e20)
        spin.setMinimum(-1e20)
        spin.setValue(self.view.opts["cmap_range"][row])
        spin.valueChanged.connect(self._val_changed(row))
        grid.addWidget(spin, row, 1)
        return spin

    def _val_changed(self, row):
        def val_changed(val):
            cmap_range = self.view.opts["cmap_range"]
            cmap_range[row] = val
            self.view.set("cmap_range", cmap_range)
        return val_changed

    def _bound_changed(self, idx):
        self.view.set("boundary", idx)
    
    def _reset(self):
        percentile = float(100 - self.percentile_spin.value()) / 2
        flat = self.view.data.volume(self.ivl.focus()[3]).flatten()
        cmin, cmax = flat.min(), flat.max()
        if percentile > 0:
            if self.use_roi.isChecked() and self.ivm.current_roi is not None:
                flat = self.view.data.mask(self.ivm.current_roi, output_flat=True)
            cmin = np.percentile(flat, percentile)
            cmax = np.percentile(flat, 100-percentile)
        self.min_spin.setValue(cmin)
        self.max_spin.setValue(cmax)
        self.view.set("cmap_range", [cmin, cmax])