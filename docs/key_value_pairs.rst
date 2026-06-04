Key Value Pairs
===============

This document contains valid key value pairs that can be assigned to
projects/datasets/images in order to be parsed by ``omero_microscope_qc``.

Spelling and spaces must **exactly match** those listed in the key and accepted
values fields.

omero_microscope_qc Values
--------------------------

These values have specific uses by the ``omero_microscope_qc`` module.

.. list-table::
   :header-rows: 1
   :widths: 18 12 20 50

   * - Key
     - Value Type
     - Accepted Values
     - Description
   * - ``QC_Processed``
     - Boolean
     - True, False
     - Automatically populated by ``omero_microscope_qc`` when analysis has been completed.
   * - ``microscope_type``
     - Text
     - WideField, CLSM, Spinning Disc Confocal, Multiphoton
     - Type of microscope.
   * - ``pinhole_size_AU``
     - Number
     - Any number
     - Pinhole size set in Airy Units. Required for CLSM microscopes.
   * - ``use_rois``
     - Boolean
     - True, False
     - Whether to process using OMERO ROIs or the entire image.
   * - ``generate_rois``
     - Boolean
     - True, False
     - Whether to automatically generate OMERO ROIs with one bead per ROI. Also requires ``crop_size`` to be set.
   * - ``crop_size``
     - Number
     - Any number
     - Size of the crop used by ``generate_rois`` in scaled units.

MetroloJ_QC Values
------------------

These values match class attributes for the ``MetroloJDialog`` class and
correspond to most settings available in the GUI version of the plugin.

.. list-table::
   :header-rows: 1
   :widths: 18 12 20 50

   * - Key
     - Value Type
     - Accepted Values
     - Description
   * - ``operator``
     - Text
     - Any
     - Name of the operator that generated and analysed the data.
   * - ``reportName``
     - Text
     - Any
     - Tool name of the report, displayed as "tool" in the analysis parameter table.
   * - ``reportType``
     - Text
     - fi, bfi, cv, cam, pp, bpp, coa, bcoa, zp, pos
     - Abbreviation of the report type of tool associated with ``MetroloJDialog``.
   * - ``title``
     - Text
     - Any
     - Name of the report as given by the user, displayed below the tool icon in the PDF file.
   * - ``bitDepth``
     - Integer
     - Any
     - Dynamic range of the image in bits (real bit depth used to encode intensities).
   * - ``microType``
     - Integer
     - 0, 1, 2, 3
     - Microscope type index derived from the microscope type rolling menu. Inputs correspond to 0=WideField, 1=CLSM, 2=Spinning Disc Confocal, 3=Multiphoton.
   * - ``detectorType``
     - Integer
     - 0, 1, 2, 3
     - Detector type index derived from the detector type rolling menu. Inputs correspond to 0=CCD, 1=EMCCD, 2=SCMOS, 3=PMTHYD.
   * - ``errorDialogCanceled``
     - Boolean
     - True, False
     - Whether the error dialog was canceled.
   * - ``dimensionOrder``
     - Integer
     - Any
     - The input data dimension order, derived from the dimension order rolling menu.
   * - ``filterSets``
     - Text
     - Any
     - Names of the filter sets used in the field illumination tool.
   * - ``NA``
     - Number
     - Any
     - Objective numerical aperture, as given in the objective NA field of the field illumination, coalignment, Z profiler and PSF profiler tools dialogs.
   * - ``pinhole``
     - Number
     - Any
     - Pinhole size in Airy Units, as given in the pinhole(AU) field of the dialog. Only used when ``microType`` is 1 (CONFOCAL).
   * - ``refractiveIndex``
     - Number
     - Any
     - Objective immersion medium refractive index, as given in the Objective im. med. refractive index field of the field illumination, coalignment, Z profiler and PSF profiler tools dialogs.
   * - ``detectorNames``
     - Text
     - Any
     - Names of the different detectors used for each channel (for example PMT1, PMT2, etc).
   * - ``date``
     - Text
     - Any
     - Date when the report was generated.
   * - ``sampleInfo``
     - Text
     - Any
     - Sample information provided by the user.
   * - ``comments``
     - Text
     - Any
     - Comments provided by the user.
   * - ``saturationChoice``
     - Boolean
     - True, False
     - Whether to discard (True) or not (False) saturated channels from the analysis.
   * - ``fitFormula``
     - Integer
     - Any
     - Fit formula integer used in the CurveFitter plugin.
   * - ``useBeads``
     - Boolean
     - True, False
     - Whether the analysis image is a bead image (for example coalignment, PSF Profiler).
   * - ``addCross``
     - Boolean
     - True, False
     - Whether to add a cross to locate the centers on the detected bead side-view panels.
   * - ``addRoi``
     - Boolean
     - True, False
     - Whether to add the detected bead ROIs to the detected bead side-view panels.
   * - ``addText``
     - Boolean
     - True, False
     - Whether to add text to the detected bead side-view panels.
   * - ``resize``
     - Boolean
     - True, False
     - Whether to resize the XZ and YZ detected bead side-view panels to a 1:1 ratio.
   * - ``beadDetectionThreshold``
     - Text
     - Any
     - Bead threshold used to threshold the image to identify big (for example drift, coalignment) beads.
   * - ``centerDetectionMethodIndex``
     - Integer
     - 0, 1, 2
     - Center detection method ID for detecting the center of big (for example coalignment, drift) beads. ELLIPSES=0, CENTROID=1, MAX_INTENSITY=2.
   * - ``oneParticle``
     - Boolean
     - True, False
     - Whether to use single-particle center detection mode.
   * - ``multipleBeads``
     - Boolean
     - True, False
     - Whether images contain multiple beads (True) or a single bead (False).
   * - ``beadChannel``
     - Integer
     - 1 - Max channels
     - Channel ID used to identify beads (when ``multipleBeads`` is True).
   * - ``beadSize``
     - Number
     - Any
     - Bead diameter in um used for bead identification/exclusion (when ``multipleBeads`` is True).
   * - ``cropFactor``
     - Number
     - Any
     - Crop factor used to compute the crop box size (``cropFactor`` x ``beadSize``).
   * - ``beadMinDistanceToTopBottom``
     - Number
     - Any
     - Minimum distance in um of the upper and lower bead edges to the top and bottom of the stack respectively.
   * - ``doubletMode``
     - Boolean
     - True, False
     - Whether to exclude big bead (for example coalignment) doublets from coalignment analysis (when ``multipleBeads`` is True).
   * - ``prominence``
     - Number
     - Any
     - Prominence value of the find maxima plugin used to identify small (PSF) beads (when ``multipleBeads`` is True).
   * - ``innerAnnulusEdgeDistanceToBead``
     - Number
     - Any
     - Distance in um from the outer edge of the bead to the inner edge of the background annulus.
   * - ``annulusThickness``
     - Number
     - Any
     - Annulus thickness in um (distance from inner to outer edges of the annulus).
   * - ``useTolerance``
     - Boolean
     - True, False
     - Whether to apply tolerance values to raw measurements and highlight poor performance.
   * - ``coalRatioTolerance``
     - Number
     - Any
     - Coalignment ratio value above which detectors are considered misaligned (coalignment tool).
   * - ``XYratioTolerance``
     - Number
     - Any
     - Ratio of the lateral resolution value (X or Y) to theoretical values above which the setup performs poorly.
   * - ``ZratioTolerance``
     - Number
     - Any
     - Ratio of the axial resolution value to theoretical values above which the setup performs poorly.
   * - ``uniformityTolerance``
     - Number
     - Any
     - Uniformity tolerance value below which the illumination is considered non-homogeneous.
   * - ``centAccTolerance``
     - Number
     - Any
     - Centering accuracy tolerance value below which the illumination is considered off-centered.
   * - ``R2Threshold``
     - Number
     - Any
     - In batch PSF profiler mode, threshold used to discard poor fitting results from the analysis.
   * - ``maxGapLength``
     - Integer
     - Any
     - Maximum length of position gaps in the DriftProfiler report that can be corrected.
   * - ``useResolutionThresholds``
     - Boolean
     - True, False
     - Whether to use resolution values as a 1D and 2/3D threshold for stabilization time computation. Stage is stabilized if the distance between timepoints is less than the threshold.
   * - ``isotropicThreshold``
     - Number
     - Any
     - Isotropic threshold value (if applied) for stabilization time computation. Stage is stabilized if the distance between timepoints is less than this value.
   * - ``showProjections``
     - Boolean
     - True, False
     - Whether to show XY, XZ and YZ (if relevant) projections across time overlaid with detected bead outlines.
   * - ``showDisplacementFits``
     - Boolean
     - True, False
     - Whether to show the fit in the displacement (1D or 2/3D distances) vs elapsed time in the DriftProfiler.
   * - ``useAbsoluteValues``
     - Boolean
     - True, False
     - Whether to set 1D displacement values to absolute displacement (negative 1D distances displayed as positive).
   * - ``outliers``
     - Boolean
     - True, False
     - In batch mode, whether to remove outliers from a series of n values (applies if n > 5).
   * - ``outlierMode``
     - Integer
     - Any
     - In batch mode, how outliers are calculated.
   * - ``shorten``
     - Boolean
     - True, False
     - Whether to shorten the analyses (True: short report version, False: long report version).
   * - ``openPdf``
     - Boolean
     - True, False
     - Whether to open individual PDF files when batch mode is used.
   * - ``savePdf``
     - Boolean
     - True, False
     - Whether to generate and save individual reports as a PDF file.
   * - ``saveImages``
     - Boolean
     - True, False
     - Whether to generate and save individual images generated during the analysis.
   * - ``saveSpreadsheet``
     - Boolean
     - True, False
     - Whether to generate and save individual reports as an XLS file.
   * - ``singleChannel``
     - Integer
     - 1 - Max channels
     - The channel to use for analysis when the input image is a multichannel stack.
   * - ``sqrtChoice``
     - Boolean
     - True, False
     - Whether to display the PSF XY, XZ and YZ profiles using a square root intensity image.
   * - ``discardWavelengthSpecs``
     - Boolean
     - True, False
     - In batch mode, whether to hide wavelength specs from the final batch report when input images have different detectors.
   * - ``gaussianBlurChoice``
     - Boolean
     - True, False
     - Whether to apply a Gaussian blur before analysis (used when the image is polluted with noise).
   * - ``thresholdChoice``
     - Boolean
     - True, False
     - Whether to use a high-intensity threshold (for example 90-100% of max intensity) to identify the maximum intensity zone (True), or use only the maximum intensity pixels (False).
   * - ``stepWidth``
     - Number
     - Any
     - Width for isointensity maps used in the FieldIllumination analyses.
   * - ``noiseChoice``
     - Boolean
     - True, False
     - Whether to perform noise analysis in camera analyses.
   * - ``conversionFactor``
     - Number
     - Any
     - Detector count to electron conversion factor in camera analyses.
   * - ``logScalePlot``
     - Boolean
     - True, False
     - Whether to use a log scale (True) or linear scale (False) for noise distribution plots in camera noise analyses.
   * - ``temperatureChoice``
     - Boolean
     - True, False
     - Whether to perform hot/warm/cold pixel camera analyses.
   * - ``computeFrequencies``
     - Boolean
     - True, False
     - Whether to analyse how often hot/warm/cold pixels behave as such in a time series.
   * - ``fixedNoiseMapRange``
     - Boolean
     - True, False
     - Whether to display NoiseMap images with a fixed intensity range.
   * - ``maxNoiseMapValue``
     - Number
     - Any
     - Maximum displayed noise value of the NoiseMap when ``fixedNoiseMapRange`` is True.
   * - ``hotChoice``
     - Boolean
     - True, False
     - Whether to perform warm/cold pixel camera analyses.
   * - ``temperatureThreshold``
     - Number
     - Any
     - Threshold applied to the average intensity above/below which a pixel is considered warm or cold respectively.
   * - ``logLUT``
     - Boolean
     - True, False
     - Whether to use a log LUT (True) or a linear LUT (False) for NoiseMap images in camera noise analyses.
   * - ``fixedFrequencyMapRange``
     - Boolean
     - True, False
     - Whether to display frequency map images with a fixed intensity range.
   * - ``maxFrequencyMapValue``
     - Number
     - Any
     - Maximum displayed value of the frequency map when ``fixedFrequencyMapRange`` is True.
   * - ``testDialogOKed``
     - Boolean
     - True, False
     - Whether the test dialog was confirmed.
   * - ``testType``
     - Integer
     - 0, 1, 2
     - Test type index.
   * - ``dimension``
     - Text
     - XY, XZ, YZ
     - Selected dimension for the analysis.
   * - ``testChannel``
     - Integer
     - 1 - Max channels
     - Channel used for the test analysis.
   * - ``expectednMaxima``
     - Integer
     - Any
     - Expected number of maxima for the test.
   * - ``maxIterations``
     - Integer
     - Any
     - Maximum number of iterations for the test.
   * - ``showProminencesPlot``
     - Boolean
     - True, False
     - Whether to show the prominences plot.
   * - ``preProcess``
     - Boolean
     - True, False
     - Whether to pre-process the image before the test.
   * - ``useIJAutothresholds``
     - Boolean
     - True, False
     - Whether to use ImageJ auto-thresholds in the Generate Test Methods.
   * - ``useLegacyThreshold``
     - Boolean
     - True, False
     - Whether to use the legacy threshold in the Generate Test Methods.
   * - ``usekMeansThreshold``
     - Boolean
     - True, False
     - Whether to use k-means thresholding in the Generate Test Methods.
