"""
Quantiphyse - Tests for supervoxel clustering widget

Copyright (c) 2013-2018 University of Oxford
"""
import unittest 

import numpy as np

from quantiphyse.test.widget_test import WidgetTest

from .widgets import PerfSlicWidget

NUM_SV = 4
NAME = "test_sv"
NUM_PCA = 3
SIGMA = 0.5
COMP = 0.2

class PerfSlicWidgetTest(WidgetTest):

    def widget_class(self):
        return PerfSlicWidget

    def testNoData(self):
        """ User clicks the generate buttons with no data"""
        self.harmless_click(self.w.gen_btn)

    def test3dData(self):
        self.ivm.add_data(self.data_3d, grid=self.grid, name="data_3d")
        self.w.ovl.setCurrentIndex(0)
        self.processEvents()
        self.assertFalse(self.w.n_comp.spin.isVisible())

        self.w.compactness.spin.setValue(COMP)
        self.w.sigma.spin.setValue(SIGMA)
        self.w.n_supervoxels.spin.setValue(NUM_SV)
        self.w.output_name.setText(NAME)

        self.harmless_click(self.w.gen_btn)
        self.processEvents()

        self.assertTrue(NAME in self.ivm.rois)
        self.assertEquals(self.ivm.current_roi.name, NAME)
        # Don't check regions as we know this doesn't work. Really you shouldn't be running
        # supervoxels without an ROI, we are just checking it handles it gracefully if you do
        #self.assertEquals(len(self.ivm.rois[NAME].regions), NUM_SV)
        self.assertFalse(self.error)

    def test3dDataMask(self):
        self.ivm.add_roi(self.mask, grid=self.grid, name="mask")
        self.w.ovl.setCurrentIndex(0)
        self.test3dData()
        self.assertEquals(len(self.ivm.rois[NAME].regions), NUM_SV)
        # Supervoxel value is always zero outside the ROI
        sv = self.ivm.rois[NAME].raw()
        self.assertTrue(np.all(sv[self.mask == 0] == 0))
        self.assertFalse(self.error)

    def test4dData(self):
        self.ivm.add_data(self.data_4d, grid=self.grid, name="data_4d")
        self.w.ovl.setCurrentIndex(0)
        self.w.roi.setCurrentIndex(0)
        self.processEvents()
        self.assertTrue(self.w.n_comp.spin.isEnabled())

        self.w.compactness.spin.setValue(COMP)
        self.w.n_comp.spin.setValue(NUM_PCA)
        self.w.sigma.spin.setValue(SIGMA)
        self.w.n_supervoxels.spin.setValue(NUM_SV)
        self.w.output_name.setText(NAME)

        self.harmless_click(self.w.gen_btn)
        self.processEvents()

        self.assertTrue(NAME in self.ivm.rois)
        self.assertEquals(self.ivm.current_roi.name, NAME)
        # Don't check regions as we know this doesn't work. Really you shouldn't be running
        # supervoxels without an ROI, we are just checking it handles it gracefully if you do
        #self.assertEquals(len(self.ivm.rois[NAME].regions), NUM_SV)
        self.assertFalse(self.error)

    def test4dDataMask(self):
        self.ivm.add_roi(self.mask, grid=self.grid, name="mask")
        self.w.ovl.setCurrentIndex(0)
        self.w.roi.setCurrentIndex(0)
        self.test4dData()
        self.assertEquals(len(self.ivm.rois[NAME].regions), NUM_SV)
        # Supervoxel value is always zero outside the ROI
        sv = self.ivm.rois[NAME].raw()
        self.assertTrue(np.all(sv[self.mask == 0] == 0))
        self.assertFalse(self.error)

if __name__ == '__main__':
    unittest.main()
