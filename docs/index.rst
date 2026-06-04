*******************
Omero Microscope QC
*******************

This python module allows for batch processing of images used for quality control
of microscopes based upon `QUAREP-LiMi's <https://quarep.org/>`_ recommendations.

It uses `OMERO <https://www.openmicroscopy.org/omero/>`_ and the ImageJ plugin
`MetroloJ_QC <https://github.com/MontpellierRessourcesImagerie/MetroloJ_QC>`_
(run via `pyImageJ <https://github.com/imagej/pyimagej>`_) to perform
resolution, co-registration and stage precision analysis on bead images and a
custom script for Z-drive accuracy run on images of a "3D Crossing stairs"
pattern on an `Argolight <https://argolight.com/>`_ calibration slide. Images
are pulled directly from an OMERO server with results attached to the same
images. These attachments can then be loaded into the feets-db microscopy QC
database.

.. toctree::
   :maxdepth: 2

   installation
   usage
   key_value_pairs
   api
