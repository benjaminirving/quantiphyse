"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

- Data management framework

"""

from __future__ import division, print_function

import sys
import os
import math
import warnings
import glob

from PySide import QtCore, QtGui
from matplotlib import cm

import nibabel as nib
import dcmstack
import numpy as np
import nrrd

from pkview.volumes.io import QpVolume, FileMetadata

class ImageVolumeManagement(QtCore.QAbstractItemModel):
    """
    ImageVolumeManagement
    1) Holds all image volumes used in analysis
    2) Better support for switching volumes instead of having a single volume hardcoded

    Has to inherit from a Qt base class that supports signals
    Note that the correct QT Model/View structure has not been set up but is intended in future
    """
    # Signals

    # Change to main volume
    sig_main_volume = QtCore.Signal(QpVolume)

    # Change to current overlay
    sig_current_overlay = QtCore.Signal(QpVolume)

    # Change to set of overlays (e.g. new one added)
    sig_all_overlays = QtCore.Signal(list)

    # Change to current ROI
    sig_current_roi = QtCore.Signal(QpVolume)

    # Change to set of ROIs (e.g. new one added)
    sig_all_rois = QtCore.Signal(list)

    def __init__(self):
        super(ImageVolumeManagement, self).__init__()
        self.reset()

    def reset(self):
        """
        Reset to empty, signalling any connected widgets
        """
        # Main background image
        self.vol = None

        self.voxel_sizes = [1.0, 1.0, 1.0]
        self.shape = []

        # Map from name to overlay object
        self.overlays = {}

        # Current overlay object
        self.current_overlay = None

        # Map from name to ROI object
        self.rois = {}

        # Processing artifacts
        self.artifacts = {}

        # Current ROI object
        self.current_roi = None

        # Current position of the cross hair as an array
        self.cim_pos = np.array([0, 0, 0, 0], dtype=np.int)

        self.sig_main_volume.emit(self.vol)
        self.sig_current_overlay.emit(self.current_overlay)
        self.sig_current_roi.emit(self.current_roi)
        self.sig_all_rois.emit(self.rois.keys())
        self.sig_all_overlays.emit(self.overlays.keys())

    def check_shape(self, shape):
        ndim = min(len(self.shape), len(shape))
        if (list(self.shape[:ndim]) != list(shape[:ndim])):
            raise RuntimeError("First %i Dimensions must be %s - they are %s" % (ndim, self.shape[:ndim], shape[:ndim]))

    def update_shape(self, shape):
        self.check_shape(shape)
        for d in range(len(self.shape), min(len(shape), 4)):
            self.shape.append(shape[d])

    def set_main_volume(self, name):
        self._overlay_exists(name)
        
        self.vol = self.overlays[name]
        self.voxel_sizes = self.vol.md.voxel_sizes
        self.update_shape(self.vol.shape)

        self.cim_pos = [int(d/2) for d in self.vol.shape]
        if self.vol.ndim == 3: self.cim_pos.append(0)
        self.sig_main_volume.emit(self.vol)

    def add_overlay(self, name, ov, make_current=False, make_main=False, signal=True):
        ov = ov.view(QpVolume)
        if ov.md is None:
            ov.md = FileMetadata(ov, name=name, affine=self.vol.md.affine, voxel_sizes=self.vol.md.voxel_sizes)
        self.update_shape(ov.shape)

        self.overlays[name] = ov
        
        if signal:
            self.sig_all_overlays.emit(self.overlays.keys())

        if make_current:
            self.set_current_overlay(name, signal)

        # Make main volume if requested, or if the first volume, or if the first 4d volume
        if make_main or self.vol is None or (ov.ndim == 4 and self.vol.ndim == 3):
            self.set_main_volume(name)

    def add_roi(self, name, roi, make_current=False, signal=True):
        roi = roi.astype(np.int32).view(QpVolume)
        if roi.md is None:
            roi.md = FileMetadata(roi, name=name, affine=self.vol.md.affine, voxel_sizes=self.vol.md.voxel_sizes)

        if roi.md.range[0] < 0 or roi.md.range[1] > 2**32:
            raise RuntimeError("ROI must contain values between 0 and 2**32")

        if not np.equal(np.mod(roi, 1), 0).any():
           raise RuntimeError("ROI contains non-integer values.")

        roi.set_as_roi()
        self.update_shape(roi.shape)
        self.rois[name] = roi

        if signal:
            self.sig_all_rois.emit(self.rois.keys())
        if make_current:
            self.set_current_roi(name, signal)

    def _overlay_exists(self, name, invert=False):
        if name not in self.overlays:
            raise RuntimeError("Overlay %s does not exist" % name)

    def _roi_exists(self, name):
        if name not in self.rois:
            raise RuntimeError("ROI %s does not exist" % name)

    def is_current_overlay(self, ovl):
        return self.current_overlay is not None and ovl is not None and self.current_overlay.md.name == ovl.md.name

    def is_current_roi(self, roi):
        return self.current_roi is not None and roi is not None and self.current_roi.md.name == roi.md.name
        
    def set_current_overlay(self, name, signal=True):
        self._overlay_exists(name)
        self.current_overlay = self.overlays[name]
        if signal: self.sig_current_overlay.emit(self.current_overlay)

    def rename_overlay(self, name, newname, signal=True):
        self._overlay_exists(name)
        ovl = self.overlays[name]
        ovl.md.name = newname
        self.overlays[newname] = ovl
        del self.overlays[name]
        if signal: self.sig_all_overlays.emit(self.overlays.keys())

    def rename_roi(self, name, newname, signal=True):
        self._roi_exists(name)
        roi = self.rois[name]
        roi.md.name = newname
        self.rois[newname] = roi
        del self.rois[name]
        if signal: self.sig_all_rois.emit(self.rois.keys())

    def delete_overlay(self, name, signal=True):
        self._overlay_exists(name)
        del self.overlays[name]
        if signal: self.sig_all_overlays.emit(self.overlays.keys())
        if self.current_overlay.md.name == name:
            self.current_overlay = None
            if signal: self.sig_current_overlay.emit(None)

    def delete_roi(self, name, signal=True):
        self._roi_exists(name)
        del self.rois[name]
        if signal: self.sig_all_rois.emit(self.rois.keys())
        if self.current_roi.md.name == name:
            self.current_roi = None
            if signal: self.sig_current_roi.emit(None)

    def set_current_roi(self, name, signal=True):
        self._roi_exists(name)
        self.current_roi = self.rois[name]
        if signal:
            self.sig_current_roi.emit(self.current_roi)

    def get_overlay_value_curr_pos(self):
        """
        Get all the overlay values at the current position
        """
        overlay_value = {}

        # loop over all loaded overlays and save values in a dictionary
        for name, ovl in self.overlays.items():
            if ovl.ndim == 3:
                overlay_value[name] = ovl[self.cim_pos[0], self.cim_pos[1], self.cim_pos[2]]

        return overlay_value

    def get_current_enhancement(self):
        """
        Return enhancement curves for all 4D overlays whose 4th dimension matches that of the main volume
        """
        if self.vol is None: return [], {}
        if self.vol.ndim != 4: raise RuntimeError("Main volume is not 4D")

        main_sig = self.vol[self.cim_pos[0], self.cim_pos[1], self.cim_pos[2], :]
        ovl_sig = {}

        for ovl in self.overlays.values():
            if ovl.ndim == 4 and (ovl.shape[3] == self.vol.shape[3]):
                ovl_sig[ovl.md.name] = ovl[self.cim_pos[0], self.cim_pos[1], self.cim_pos[2], :]

        return main_sig, ovl_sig

    def add_artifact(self, name, obj):
        """
        Add an 'artifact', which can be any result of a process which
        is not voxel data, e.g. a number, table, etc.

        Artifacts are only required to support str() conversion so they
        can be written to a file
        """
        self.artifacts[name] = obj

    def set_blank_annotation(self):
        """
        - Initialise the annotation overlay
        - Set the annotation overlay to be the current overlay
        """
        ov = Overlay("annotation", np.zeros(self.vol.shape[:3]))
        # little hack to normalise the image from 0 to 10 by listing possible labels in the corner
        for ii in range(11):
            ov[0, ii] = ii

        self.add_overlay(ov, make_current=True, signal=True)

