"""

Author: Benjamin Irving (benjamin.irv@gmail.com)
Copyright (c) 2013-2015 University of Oxford, Benjamin Irving

Library for simple analysis of the overlay parameters

Benjamin Irving

"""

import numpy as np


class OverlayAnalysis(object):
    """
    Class for analysing the imported overlay
    """

    def __init__(self, ivm):
        self.ivm = ivm

    def get_summary_stats(self, ovl, roi=None, hist_bins=20, hist_range=None, slice=None):
        """
        Return:
        @m1 mean for each ROI
        @m2 median for each ROI
        @m3 standard deviation for each ROI
        @roi_labels label of each ROI
        """
        # Checks if either ROI or overlay is None
        if roi is not None:
            roi_labels = roi.md.regions
            roi_labels = roi_labels[roi_labels > 0]
        else:
            roi = np.ones(ovl.shape[:3])
            roi_labels = [1,]

        if (ovl is None):
            stat1 = {'mean': [0], 'median': [0], 'std': [0], 'max': [0], 'min': [0]}
            return stat1, roi_labels, np.array([0, 0]), np.array([0, 1])

        stat1 = {'mean': [], 'median': [], 'std': [], 'max': [], 'min': []}
        hist1 = []
        hist1x = []

        if slice is None:
            ovldata = ovl
            roidata = roi
        elif slice == 0:
            slicepos = self.ivm.cim_pos[2]
            ovldata = ovl[:, :, slicepos]
            roidata = roi[:, :, slicepos]
        elif slice == 1:
            slicepos = self.ivm.cim_pos[1]
            ovldata = ovl[:, slicepos, :]
            roidata = roi[:, slicepos, :]
        elif slice == 2:
            slicepos = self.ivm.cim_pos[0]
            ovldata = ovl[slicepos, :, :]
            roidata = roi[slicepos, :, :]
        else:
            raise RuntimeError("Invalid slice: " % slice)

        for ii in roi_labels:
            # Overlay for a single label of the roi
            vroi1 = ovldata[roidata == ii]

            stat1['mean'].append(np.mean(vroi1))
            stat1['median'].append(np.median(vroi1))
            stat1['std'].append(np.std(vroi1))
            stat1['max'].append(np.max(vroi1))
            stat1['min'].append(np.min(vroi1))
            y, x = np.histogram(vroi1, bins=hist_bins, range=hist_range)
            hist1.append(y)
            hist1x.append(x)

        return stat1, roi_labels, hist1, hist1x

    def get_radial_profile(self, bins=30):
        """
        Generate a radial profile curve within an ROI
        """
        if (self.ivm.current_roi is None) or (self.ivm.current_overlay is None):
            return []

        data = self.ivm.current_overlay
        voxel_sizes = self.ivm.voxel_sizes
        roi = self.ivm.current_roi
        centre = self.ivm.cim_pos

        # If overlay is 4d, get current 3d volume
        if len(data.shape) == 4:
            data = data[:, :, :, centre[3]]

        # Generate an array whose entries are integer values of the distance
        # from the centre. Set masked values to distance of -1
        x, y, z = np.indices((data.shape[:3]))
        r = np.sqrt((voxel_sizes[0]*(x - centre[0]))**2 + (voxel_sizes[1]*(y - centre[1]))**2 + (voxel_sizes[2]*(z - centre[2]))**2)
        r[roi==0] = -1

        # Generate histogram by distance, weighted by data and corresponding histogram
        # of distances only (i.e. the number of voxels in each bin)
        minv = r[roi>0].min()
        rpd, edges = np.histogram(r, weights=data, bins=bins, range=(minv, r.max()))
        rpv, junk = np.histogram(r, bins=bins, range=(minv, r.max()))

        # Divide by number of voxels in each bin to get average value by distance.
        # Prevent divide by zero, if there are no voxels in a bin, this is OK because
        # there will be no data either
        rpv[rpv==0] = 1
        rp = rpd / rpv

        xvals = [(edges[i] + edges[i+1])/2 for i in range(len(edges)-1)]
        return rp, xvals, edges
