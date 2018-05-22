"""
Quantiphyse - Data management framework

Copyright (c) 2013-2018 University of Oxford
"""

from __future__ import division, print_function

import keyword
import re

from PySide import QtCore

import numpy as np

from quantiphyse.utils import debug, QpException

from .qpdata import QpData
from .load_save import NumpyData

class ImageVolumeManagement(QtCore.QObject):
    """
    Holds all image datas used in analysis

    Has to inherit from a Qt base class that supports signals
    """
    # Signals

    # Change to main data
    sig_main_data = QtCore.Signal(object)

    # Change to current data
    sig_current_data = QtCore.Signal(object)

    # Change to set of data (e.g. new one added)
    sig_all_data = QtCore.Signal(list)

    # Change to current ROI
    sig_current_roi = QtCore.Signal(object)

    # Change to set of ROIs (e.g. new one added)
    sig_all_rois = QtCore.Signal(list)

    def __init__(self):
        super(ImageVolumeManagement, self).__init__()
        self.reset()

    def reset(self):
        """
        Reset to empty, signalling any connected widgets
        """
        # Main background data
        self.main = None

        # Map from name to data object
        self.data = {}

        # Current data object
        self.current_data = None

        # Map from name to ROI object
        self.rois = {}

        # Current ROI object
        self.current_roi = None

        # Processing extras
        self.extras = {}

        self.sig_main_data.emit(None)
        self.sig_current_data.emit(None)
        self.sig_current_roi.emit(None)
        self.sig_all_rois.emit([])
        self.sig_all_data.emit([])

    def suggest_name(self, name, ensure_unique=True):
        """
        Suggest a name for new data that is suitable for use as a Python variable.
        If required, ensure name does not clash with existing names
        """
        # Remove invalid characters
        name = re.sub('[^0-9a-zA-Z_]', '', name)

        # Remove leading characters until we find a letter or underscore
        name = re.sub('^[^a-zA-Z_]+', '', name)

        # Add underscore if it's a keyword
        if keyword.iskeyword(name):
            name += "_"

        # Make it unique
        num = 1
        test_name = name
        while 1:
            if not ensure_unique or (test_name not in self.data and test_name not in self.rois):
                break
            num += 1
            test_name = "%s_%i" % (name, num)
        return test_name

    def _valid_name(self, name):
        if name is None or not re.match(r'[a-z_]\w*$', name, re.I) or keyword.iskeyword(name):
            raise QpException("'%s' is not a valid name" % name)

    def set_main_data(self, name):
        self._data_exists(name)
        self.main = self.data[name]
        self.sig_main_data.emit(self.main)

    def add_data(self, data, name=None, grid=None, make_current=False, make_main=None):
        if isinstance(data, np.ndarray):
            if grid is None or name is None:
                raise RuntimeError("add_data: Numpy data must have a name and a grid")
            data = NumpyData(data, grid, name)
        elif not isinstance(data, QpData):
            raise QpException("add_data: data must be Numpy array or QpData")

        if name is not None:
            data.name = name

        self._valid_name(data.name)
        self.data[data.name] = data
        
        # Make main data if requested, or if not specified and it is the first data
        if make_main is None:
            make_main = self.main is None
        if make_main:
            self.set_main_data(data.name)

        self.sig_all_data.emit(self.data.keys())

        # Make current if requested, or if not specified and it is the first non-main data
        if make_current is None:
            make_current = self.current_data is None and not make_main
        if make_current:
            self.set_current_data(data.name)

    def add_roi(self, roi, name=None, grid=None, make_current=False):
        if isinstance(roi, np.ndarray):
            if grid is None or name is None:
                raise RuntimeError("add_roi: Numpy data must have a name and a grid")
            roi = NumpyData(roi, grid, name, roi=True)
        elif not isinstance(roi, QpData):
            raise QpException("add_roi: data must be Numpy array or QpData")

        if name is not None:
            roi.name = name
        roi.set_roi(True)

        self._valid_name(roi.name)
        self.rois[roi.name] = roi

        self.sig_all_rois.emit(self.rois.keys())

        if make_current:
            self.set_current_roi(roi.name)
            
    def _data_exists(self, name):
        if name not in self.data:
            raise RuntimeError("Data '%s' does not exist" % name)

    def _roi_exists(self, name):
        if name not in self.rois:
            raise RuntimeError("ROI '%s' does not exist" % name)

    def is_main_data(self, qpd):
        return self.main is not None and qpd is not None and self.main.name == qpd.name

    def is_current_data(self, qpd):
        return self.current_data is not None and qpd is not None and self.current_data.name == qpd.name

    def is_current_roi(self, roi):
        return self.current_roi is not None and roi is not None and self.current_roi.name == roi.name
        
    def set_current_data(self, name):
        if name is not None:
            self._data_exists(name)
            self.current_data = self.data[name]
        else:
            self.current_data = None
        self.sig_current_data.emit(self.current_data)

    def rename_data(self, name, newname):
        self._data_exists(name)
        qpd = self.data[name]
        qpd.name = newname
        self.data[newname] = qpd
        del self.data[name]
        self.sig_all_data.emit(self.data.keys())

    def rename_roi(self, name, newname):
        self._roi_exists(name)
        roi = self.rois[name]
        roi.name = newname
        self.rois[newname] = roi
        del self.rois[name]
        self.sig_all_rois.emit(self.rois.keys())

    def delete_data(self, name):
        self._data_exists(name)
        del self.data[name]
        if self.current_data is not None and self.current_data.name == name:
            self.current_data = None
            self.sig_current_data.emit(None)
        if self.main is not None and self.main.name == name:
            self.main = None
            self.sig_main_data.emit(None)
        self.sig_all_data.emit(self.data.keys())

    def delete_roi(self, name):
        self._roi_exists(name)
        del self.rois[name]
        if self.current_roi.name == name:
            self.current_roi = None
            self.sig_current_roi.emit(None)
        self.sig_all_rois.emit(self.rois.keys())

    def set_current_roi(self, name):
        if name is not None:
            self._roi_exists(name)
            self.current_roi = self.rois[name]
        else:
            self.current_roi = None
        self.sig_current_roi.emit(self.current_roi)

    def add_extra(self, name, obj):
        """
        Add an 'extra', which can be any result of a process which
        is not voxel data, e.g. a number, table, etc.

        Extras are only required to support str() conversion so they
        can be written to a file

        :param name: Name to give the extra. If an extra already exists with this name
                     it will be overwritten
        :param obj: Object which should support str() conversion
        """
        self.extras[name] = obj

    def values(self, pos, grid=None):
        """
        Get all the 3D data values at the current position

        :param pos: Position as a 3D or 4D vector. If 4D last value is the volume index
                    (0 for 3D). If ``grid`` not specified, position is in world space
        :param grid: If specified, interpret position in this ``DataGrid`` co-ordinate space.
        :return: Dictionary of data name : value
        """
        values = {}

        # loop over all loaded data and save values in a dictionary
        for name, qpd in self.data.items():
            if qpd.nvols == 1:
                values[name] = qpd.value(pos, grid)
                
        return values

    def timeseries(self, pos, grid=None):
        """
        Return time/volume series curves for all 4D data items
       
        :param pos: Position as a 3D or 4D vector. If 4D last value is the volume index
                    (0 for 3D). If ``grid`` not specified, position is in world space
        :param grid: If specified, interpret position in this ``DataGrid`` co-ordinate space.
        :return: Dictionary of data name : sequence of values
        """
        timeseries = {}
        for qpd in self.data.values():
            if qpd.nvols > 1:
                timeseries[qpd.name] = qpd.timeseries(pos, grid)
                
        return timeseries
