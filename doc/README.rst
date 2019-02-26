

================
|qp| Quantiphyse 
================

.. |qp| image:: screenshots/qp_logo.png 
    :height: 48px

.. image:: screenshots/sample_image.png
    :scale: 30%
    :align: right


Quantiphyse is a viewing and analysis tool for 3D and 4D biomedical data. It is particularly suited 
for physiological or functional imaging data comprised of multi volumes in a 4D (time-) series 
and/or multimodal imaging data. Quantiphyse is built around the concept of making spatially 
resolved measurements of physical or physiological processes from imaging data using either 
model-based or model-free methods, in a large part exploiting Bayesian inference techniques.
Quantiphyse can analyse data both voxelwise or within regions of interest that may be manually or 
automatically created, e.g. supervoxel or clustering methods. 

.. image:: screenshots/collage.png
    :scale: 50%
    :align: left

Features
--------

 - 2D orthographic viewing and navigation of data, regions of interest (ROIs) and overlays
 - Universal analysis tools including clustering, supervoxel generation and curve comparison
 - Tools for CEST, ASL, DCE and DSC-MRI analysis and modelling
 - Integration with selected FSL tools
 - ROI generation
 - Registration and motion correction
 - Extensible via plugins

License
-------
© 2017-2019 University of Oxford

Quantiphyse is **free for non commercial** use. The license details are displayed on first
use and the ``LICENSE`` file is included in the distribution. For further information contact
the `OUI Software Store <https://process.innovation.ox.ac.uk/software>`_. If you are 
interested in commercial licensing you shold contact OUI in the first instance. 

Tutorials
---------

 - `ASL-MRI tutorial <asl_tutorial.html>`_
 - `CEST-MRI tutorial <cest_tutorial.html>`_

Download
--------

Quantiphyse is available on PyPi - see :ref:`install`.

Major releases of Quantiphyse are also available via the `Oxford University Innovation Software 
Store <https://process.innovation.ox.ac.uk/software>`_. The packages held by OUI have no 
external dependencies and can be installed on Windows, Mac and Linux. They may lag behind
the current PyPi release in terms of functionality.

Plugins
-------

Some of the functionality described in this documentation requires the installation of plugins.
The following plugins are available:

 - ``quantiphyse-dce`` - DCE modelling
 - ``quantiphyse-fabber`` - Bayesian model fitting - required for various specialised tools
 - ``quantiphyse-fsl`` - Interface to selected FSL tools (requires FSL installation)
 - ``quantiphyse-cest`` - CEST-MRI modelling (requires ``quantiphyse-fabber``)
 - ``quantiphyse-asl`` - ASL-MRI modelling (requires FSL installation and ``quantiphyse-fabber``)
 - ``quantiphyse-dsc`` - DSC-MRI modellingg (requires ``quantiphyse-fabber``)
 - ``quantiphyse-t1`` - T1 mapping (requires ``quantiphyse-fabber``)

Plugins are installed from PyPi, e.g.::

    pip install quantiphyse-dce

They will be automatically detected and added to Quantiphyse next time you run it. The packages
available on the OUI software store have all plugins included which were available at the 
time of release.

User Guide
----------

Basic functions
===============

.. toctree::
   :maxdepth: 2

   overview
   getting_started
   overlay_stats
   modelfit
   
Generic analysis and processing tools
=====================================

.. toctree::
   :maxdepth: 1

   compare
   curve_compare
   simple_maths
   reg
   smoothing
   cluster
   sv
   roi_analysis
   roibuilder
   mean_values
   hist
   rp
   
Tools from plugins
==================

.. toctree::
   :maxdepth: 1

   t1
   pk
   cest
   asl_overview

Advanced Tools
==============

.. toctree::
   :maxdepth: 1

   batch
   console
   nifti_extension
   faq
   
Bugs/Issues
-----------

Please report bug, issues, feature requests or other comments to the  `current maintainer: <mailto:martin.craig@eng.ox.ac.uk>`_

Contributors
------------

 - `Martin Craig <mailto:martin.craig@eng.ox.ac.uk>`_ (Current maintainer)
 - `Ben Irving <mailto:mail@birving.com>`_ (Original author)
 - `Michael Chappell <mailto:michael.chappell@eng.ox.ac.uk>`_
 - Paula Croal

Acknowledgements
----------------

 - Julia Schnabel
 - Sir Mike Brady

Images copyright 2018 University of Oxford
