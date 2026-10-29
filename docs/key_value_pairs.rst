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
   * - .. _qc-processed:

       ``QC_Processed``
     - Boolean
     - True, False
     - Automatically populated by ``omero_microscope_qc`` when analysis has been completed.
   * - .. _microscope-type:

       ``microscope_type``
     - Text
     - WideField, CLSM, Spinning Disc Confocal, Multiphoton
     - Type of microscope.
   * - .. _pinhole-size-au:

       ``pinhole_size_AU``
     - Number
     - Any number
     - Pinhole size set in Airy Units. Required for CLSM microscopes.
   * - .. _use-rois:

       ``use_rois``
     - Boolean
     - True, False
     - Whether to process using OMERO ROIs or the entire image.
   * - .. _generate-rois:

       ``generate_rois``
     - Boolean
     - True, False
     - Whether to automatically generate OMERO ROIs with one bead per ROI. Also requires ``crop_size`` to be set.
   * - .. _crop-size:

       ``crop_size``
     - Number
     - Any number
     - Size of the crop used by ``generate_rois`` in scaled units.
   * - .. _skip-analysis:

       ``Skip_Analysis``
     - Boolean
     - True, False
     - Whether to skip analysis of this dataset/image. Useful for excluding images that are not suitable for analysis.

MetroloJ_QC Values
------------------

These values match class attributes for the ``MetroloJDialog`` class and
correspond to most settings available in the GUI version of the plugin.

.. list-table::
   :header-rows: 1
   :widths: 18 12 15 10 45

   * - Key
     - Value Type
     - Accepted Values
     - Default Value
     - Description
   * - .. _ex-wavelengths:

       ``ex_wavelengths``
     - List of Numbers
     - Any
     - None
     - Excitation wavelengths for each channel. Put as a comma separated list of numbers (for example 405,488,561,640).
   * - .. _em-wavelengths:

       ``em_wavelengths``
     - List of Numbers
     - Any
     - None
     - Emission wavelengths for each channel. Put as a comma separated list of numbers (for example 405,488,561,640).
   * - .. _operator:

       ``operator``
     - Text
     - Any
     - Empty
     - Name of the operator that generated and analysed the data.
   * - .. _reportname:

       ``reportName``
     - Text
     - Any
     - Empty
     - Tool name of the report, displayed as "tool" in the analysis parameter table.
   * - .. _reporttype:

       ``reportType``
     - Text
     - fi, bfi, cv, cam, pp, bpp, coa, bcoa, zp, pos
     - Empty
     - Abbreviation of the report type of tool associated with ``MetroloJDialog``.
   * - .. _title:

       ``title``
     - Text
     - Any
     - Empty
     - Name of the report as given by the user, displayed below the tool icon in the PDF file.
   * - .. _bitdepth:

       ``bitDepth``
     - Integer
     - Any
     - 16
     - Dynamic range of the image in bits (real bit depth used to encode intensities).
   * - .. _microtype:

       ``microType``
     - Integer
     - 0, 1, 2, 3
     - 0
     - Microscope type index derived from the microscope type rolling menu. Inputs correspond to 0=WideField, 1=CLSM, 2=Spinning Disc Confocal, 3=Multiphoton.
   * - .. _detectortype:

       ``detectorType``
     - Integer
     - 0, 1, 2, 3
     - 0
     - Detector type index derived from the detector type rolling menu. Inputs correspond to 0=CCD, 1=EMCCD, 2=SCMOS, 3=PMTHYD.
   * - .. _errordialogcanceled:

       ``errorDialogCanceled``
     - Boolean
     - True, False
     - False
     - Whether the error dialog was canceled.
   * - .. _dimensionorder:

       ``dimensionOrder``
     - Integer
     - Any
     - 0
     - The input data dimension order, derived from the dimension order rolling menu.
   * - .. _filtersets:

       ``filterSets``
     - Text
     - Any
     - None
     - Names of the filter sets used in the field illumination tool.
   * - .. _na:

       ``NA``
     - Number
     - Any
     - 1.4
     - Objective numerical aperture, as given in the objective NA field of the field illumination, coalignment, Z profiler and PSF profiler tools dialogs.
   * - .. _pinhole:

       ``pinhole``
     - Number
     - Any
     - 1.0
     - Pinhole size in Airy Units, as given in the pinhole(AU) field of the dialog. Only used when ``microType`` is 1 (CONFOCAL).
   * - .. _refractiveindex:

       ``refractiveIndex``
     - Number
     - Any
     - 1.515
     - Objective immersion medium refractive index, as given in the Objective im. med. refractive index field of the field illumination, coalignment, Z profiler and PSF profiler tools dialogs.
   * - .. _detectornames:

       ``detectorNames``
     - Text
     - Any
     - None
     - Names of the different detectors used for each channel (for example PMT1, PMT2, etc).
   * - .. _date:

       ``date``
     - Text
     - Any
     - Empty
     - Date when the report was generated.
   * - .. _sampleinfo:

       ``sampleInfo``
     - Text
     - Any
     - Empty
     - Sample information provided by the user.
   * - .. _comments:

       ``comments``
     - Text
     - Any
     - Empty
     - Comments provided by the user.
   * - .. _saturationchoice:

       ``saturationChoice``
     - Boolean
     - True, False
     - False
     - Whether to discard (True) or not (False) saturated channels from the analysis.
   * - .. _fitformula:

       ``fitFormula``
     - Integer
     - Any
     - 12
     - Fit formula integer used in the CurveFitter plugin.
   * - .. _usebeads:

       ``useBeads``
     - Boolean
     - True, False
     - False
     - Whether the analysis image is a bead image (for example coalignment, PSF Profiler).
   * - .. _addcross:

       ``addCross``
     - Boolean
     - True, False
     - False
     - Whether to add a cross to locate the centers on the detected bead side-view panels.
   * - .. _addroi:

       ``addRoi``
     - Boolean
     - True, False
     - False
     - Whether to add the detected bead ROIs to the detected bead side-view panels.
   * - .. _addtext:

       ``addText``
     - Boolean
     - True, False
     - False
     - Whether to add text to the detected bead side-view panels.
   * - .. _resize:

       ``resize``
     - Boolean
     - True, False
     - False
     - Whether to resize the XZ and YZ detected bead side-view panels to a 1:1 ratio.
   * - .. _beaddetectionthreshold:

       ``beadDetectionThreshold``
     - Text
     - Any
     - Empty
     - Bead threshold used to threshold the image to identify big (for example drift, coalignment) beads.
   * - .. _centerdetectionmethodindex:

       ``centerDetectionMethodIndex``
     - Integer
     - 0, 1, 2
     - 0
     - Center detection method ID for detecting the center of big (for example coalignment, drift) beads. ELLIPSES=0, CENTROID=1, MAX_INTENSITY=2.
   * - .. _oneparticle:

       ``oneParticle``
     - Boolean
     - True, False
     - False
     - Whether to use single-particle center detection mode.
   * - .. _multiplebeads:

       ``multipleBeads``
     - Boolean
     - True, False
     - False
     - Whether images contain multiple beads (True) or a single bead (False).
   * - .. _beadchannel:

       ``beadChannel``
     - Integer
     - 1 - Max channels
     - 0
     - Channel ID used to identify beads (when ``multipleBeads`` is True).
   * - .. _beadsize:

       ``beadSize``
     - Number
     - Any
     - 0.0
     - Bead diameter in um used for bead identification/exclusion (when ``multipleBeads`` is True).
   * - .. _cropfactor:

       ``cropFactor``
     - Number
     - Any
     - 0.0
     - Crop factor used to compute the crop box size (``cropFactor`` x ``beadSize``).
   * - .. _beadmindistancetotopbottom:

       ``beadMinDistanceToTopBottom``
     - Number
     - Any
     - 2.0
     - Minimum distance in um of the upper and lower bead edges to the top and bottom of the stack respectively.
   * - .. _doubletmode:

       ``doubletMode``
     - Boolean
     - True, False
     - False
     - Whether to exclude big bead (for example coalignment) doublets from coalignment analysis (when ``multipleBeads`` is True).
   * - .. _prominence:

       ``prominence``
     - Number
     - Any
     - 100.0
     - Prominence value of the find maxima plugin used to identify small (PSF) beads (when ``multipleBeads`` is True).
   * - .. _innerannulusedgedistancetobead:

       ``innerAnnulusEdgeDistanceToBead``
     - Number
     - Any
     - 0.5
     - Distance in um from the outer edge of the bead to the inner edge of the background annulus.
   * - .. _annulusthickness:

       ``annulusThickness``
     - Number
     - Any
     - 1.0
     - Annulus thickness in um (distance from inner to outer edges of the annulus).
   * - .. _usetolerance:

       ``useTolerance``
     - Boolean
     - True, False
     - True
     - Whether to apply tolerance values to raw measurements and highlight poor performance.
   * - .. _coalratiotolerance:

       ``coalRatioTolerance``
     - Number
     - Any
     - 1.0
     - Coalignment ratio value above which detectors are considered misaligned (coalignment tool).
   * - .. _xyratiotolerance:

       ``XYratioTolerance``
     - Number
     - Any
     - 1.5
     - Ratio of the lateral resolution value (X or Y) to theoretical values above which the setup performs poorly.
   * - .. _zratiotolerance:

       ``ZratioTolerance``
     - Number
     - Any
     - 2.0
     - Ratio of the axial resolution value to theoretical values above which the setup performs poorly.
   * - .. _uniformitytolerance:

       ``uniformityTolerance``
     - Number
     - Any
     - 50.0
     - Uniformity tolerance value below which the illumination is considered non-homogeneous.
   * - .. _centacctolerance:

       ``centAccTolerance``
     - Number
     - Any
     - 50.0
     - Centering accuracy tolerance value below which the illumination is considered off-centered.
   * - .. _r2threshold:

       ``R2Threshold``
     - Number
     - Any
     - 0.0
     - In batch PSF profiler mode, threshold used to discard poor fitting results from the analysis.
   * - .. _maxgaplength:

       ``maxGapLength``
     - Integer
     - Any
     - 4
     - Maximum length of position gaps in the DriftProfiler report that can be corrected.
   * - .. _useresolutionthresholds:

       ``useResolutionThresholds``
     - Boolean
     - True, False
     - True
     - Whether to use resolution values as a 1D and 2/3D threshold for stabilization time computation. Stage is stabilized if the distance between timepoints is less than the threshold.
   * - .. _isotropicthreshold:

       ``isotropicThreshold``
     - Number
     - Any
     - 0.2
     - Isotropic threshold value (if applied) for stabilization time computation. Stage is stabilized if the distance between timepoints is less than this value.
   * - .. _showprojections:

       ``showProjections``
     - Boolean
     - True, False
     - True
     - Whether to show XY, XZ and YZ (if relevant) projections across time overlaid with detected bead outlines.
   * - .. _showdisplacementfits:

       ``showDisplacementFits``
     - Boolean
     - True, False
     - True
     - Whether to show the fit in the displacement (1D or 2/3D distances) vs elapsed time in the DriftProfiler.
   * - .. _useabsolutevalues:

       ``useAbsoluteValues``
     - Boolean
     - True, False
     - True
     - Whether to set 1D displacement values to absolute displacement (negative 1D distances displayed as positive).
   * - .. _outliers:

       ``outliers``
     - Boolean
     - True, False
     - False
     - In batch mode, whether to remove outliers from a series of n values (applies if n > 5).
   * - .. _outliermode:

       ``outlierMode``
     - Integer
     - Any
     - 0
     - In batch mode, how outliers are calculated.
   * - .. _shorten:

       ``shorten``
     - Boolean
     - True, False
     - True
     - Whether to shorten the analyses (True: short report version, False: long report version).
   * - .. _openpdf:

       ``openPdf``
     - Boolean
     - True, False
     - True
     - Whether to open individual PDF files when batch mode is used.
   * - .. _savepdf:

       ``savePdf``
     - Boolean
     - True, False
     - True
     - Whether to generate and save individual reports as a PDF file.
   * - .. _saveimages:

       ``saveImages``
     - Boolean
     - True, False
     - False
     - Whether to generate and save individual images generated during the analysis.
   * - .. _savespreadsheet:

       ``saveSpreadsheet``
     - Boolean
     - True, False
     - False
     - Whether to generate and save individual reports as an XLS file.
   * - .. _singlechannel:

       ``singleChannel``
     - Integer
     - 1 - Max channels
     - 0
     - The channel to use for analysis when the input image is a multichannel stack.
   * - .. _sqrtchoice:

       ``sqrtChoice``
     - Boolean
     - True, False
     - True
     - Whether to display the PSF XY, XZ and YZ profiles using a square root intensity image.
   * - .. _discardwavelengthspecs:

       ``discardWavelengthSpecs``
     - Boolean
     - True, False
     - True
     - In batch mode, whether to hide wavelength specs from the final batch report when input images have different detectors.
   * - .. _gaussianblurchoice:

       ``gaussianBlurChoice``
     - Boolean
     - True, False
     - True
     - Whether to apply a Gaussian blur before analysis (used when the image is polluted with noise).
   * - .. _thresholdchoice:

       ``thresholdChoice``
     - Boolean
     - True, False
     - True
     - Whether to use a high-intensity threshold (for example 90-100% of max intensity) to identify the maximum intensity zone (True), or use only the maximum intensity pixels (False).
   * - .. _stepwidth:

       ``stepWidth``
     - Number
     - Any
     - 10.0
     - Width for isointensity maps used in the FieldIllumination analyses.
   * - .. _noisechoice:

       ``noiseChoice``
     - Boolean
     - True, False
     - True
     - Whether to perform noise analysis in camera analyses.
   * - .. _conversionfactor:

       ``conversionFactor``
     - Number
     - Any
     - 0.21
     - Detector count to electron conversion factor in camera analyses.
   * - .. _logscaleplot:

       ``logScalePlot``
     - Boolean
     - True, False
     - True
     - Whether to use a log scale (True) or linear scale (False) for noise distribution plots in camera noise analyses.
   * - .. _temperaturechoice:

       ``temperatureChoice``
     - Boolean
     - True, False
     - True
     - Whether to perform hot/warm/cold pixel camera analyses.
   * - .. _computefrequencies:

       ``computeFrequencies``
     - Boolean
     - True, False
     - True
     - Whether to analyse how often hot/warm/cold pixels behave as such in a time series.
   * - .. _fixednoisemaprange:

       ``fixedNoiseMapRange``
     - Boolean
     - True, False
     - True
     - Whether to display NoiseMap images with a fixed intensity range.
   * - .. _maxnoisemapvalue:

       ``maxNoiseMapValue``
     - Number
     - Any
     - 6.0
     - Maximum displayed noise value of the NoiseMap when ``fixedNoiseMapRange`` is True.
   * - .. _hotchoice:

       ``hotChoice``
     - Boolean
     - True, False
     - True
     - Whether to perform warm/cold pixel camera analyses.
   * - .. _temperaturethreshold:

       ``temperatureThreshold``
     - Number
     - Any
     - 20.0
     - Threshold applied to the average intensity above/below which a pixel is considered warm or cold respectively.
   * - .. _loglut:

       ``logLUT``
     - Boolean
     - True, False
     - True
     - Whether to use a log LUT (True) or a linear LUT (False) for NoiseMap images in camera noise analyses.
   * - .. _fixedfrequencymaprange:

       ``fixedFrequencyMapRange``
     - Boolean
     - True, False
     - True
     - Whether to display frequency map images with a fixed intensity range.
   * - .. _maxfrequencymapvalue:

       ``maxFrequencyMapValue``
     - Number
     - Any
     - 3.0
     - Maximum displayed value of the frequency map when ``fixedFrequencyMapRange`` is True.
   * - .. _testdialogoked:

       ``testDialogOKed``
     - Boolean
     - True, False
     -
     - Whether the test dialog was confirmed.
   * - .. _testtype:

       ``testType``
     - Integer
     - 0, 1, 2
     -
     - Test type index.
   * - .. _dimension:

       ``dimension``
     - Text
     - XY, XZ, YZ
     -
     - Selected dimension for the analysis.
   * - .. _testchannel:

       ``testChannel``
     - Integer
     - 1 - Max channels
     -
     - Channel used for the test analysis.
   * - .. _expectednmaxima:

       ``expectednMaxima``
     - Integer
     - Any
     -
     - Expected number of maxima for the test.
   * - .. _maxiterations:

       ``maxIterations``
     - Integer
     - Any
     -
     - Maximum number of iterations for the test.
   * - .. _showprominencesplot:

       ``showProminencesPlot``
     - Boolean
     - True, False
     -
     - Whether to show the prominences plot.
   * - .. _preprocess:

       ``preProcess``
     - Boolean
     - True, False
     -
     - Whether to pre-process the image before the test.
   * - .. _useijautothresholds:

       ``useIJAutothresholds``
     - Boolean
     - True, False
     -
     - Whether to use ImageJ auto-thresholds in the Generate Test Methods.
   * - .. _uselegacythreshold:

       ``useLegacyThreshold``
     - Boolean
     - True, False
     -
     - Whether to use the legacy threshold in the Generate Test Methods.
   * - .. _usekmeansthreshold:

       ``usekMeansThreshold``
     - Boolean
     - True, False
     -
     - Whether to use k-means thresholding in the Generate Test Methods.

NanoImagingPack Dectector Values
--------------------------------

These values have specific uses by the ``NanoImagingPack`` module used for detector metrics.

.. list-table::
   :header-rows: 1
   :widths: 18 12 15 10 45

   * - Key
     - Value Type
     - Accepted Values
     - Default Value
     - Description
   * - .. _skip-first:

       ``skip_first``
     - Number
     - Integer
     - 10
     - Number of frames to skip at the beginning of the timelapse.
   * - .. _numbins:

       ``numBins``
     - Number
     - Integer
     - 100
     - Number of bins for the histogram.
   * - .. _histrange:

       ``histRange``
     - List of Numbers
     - Two numbers (min, max)
     - None
     - If provided, the histogram will only be generated over this range.
   * - .. _validrange:

       ``validRange``
     - List of Numbers
     - Two numbers (min, max)
     - None
     - If provided, the gain fit will only be performed over this range of mean values.
   * - .. _linearity-range:

       ``linearity_range``
     - List of Numbers
     - Two numbers (min, max)
     - None
     - If provided, the linearity will only be evaluated over this range.
   * - .. _cameraname:

       ``CameraName``
     - String
     - Any
     - None
     - If provided, sets a plot title with ``CameraName``.
   * - .. _correctbrightness:

       ``correctBrightness``
     - Boolean
     - True, False
     - True
     - Attempt to correct the calibration for a fluctuating illumination brightness.
   * - .. _correctoffsetdrift:

       ``correctOffsetDrift``
     - Boolean
     - True, False
     - True
     - Attempt to correct the calibration for a drifting camera offset.
   * - .. _exclude-hot-cold-pixels:

       ``exclude_hot_cold_pixels``
     - Boolean
     - True, False
     - True
     - Exclude hot and cold pixels from the fit.
   * - .. _noisy-pixel-percentile:

       ``noisy_pixel_percentile``
     - Number
     - 0 - 100
     - 98
     - Only include this percentile of least noisy pixels. Useful for suppressing the effect of RTS noise.
   * - .. _doplot:

       ``doPlot``
     - Boolean
     - True, False
     - True
     - Plot the mean-variance curves.
   * - .. _exportformat:

       ``exportFormat``
     - String
     - png, svg
     - png
     - File format of the exported plots.
   * - .. _brightness-blurring:

       ``brightness_blurring``
     - Boolean
     - True, False
     - True
     - A filter to blur the brightness estimate. Useful for sCMOS sensors.
   * - .. _plotwithbgoffset:

       ``plotWithBgOffset``
     - Boolean
     - True, False
     - True
     - If False, the background value will be subtracted from the pixel ADUs in the plot.
   * - .. _plothist:

       ``plotHist``
     - Boolean
     - True, False
     - False
     - If True, a histogram of brightness bins will be plotted in the plot background.
   * - .. _check-bg:

       ``check_bg``
     - Boolean
     - True, False
     - False
     - If True, the background images will be checked.
   * - .. _saturationimage:

       ``saturationImage``
     - Boolean
     - True, False
     - True
     - If True, the peak of the photon transfer curve will be used to estimate the saturation level and calculate a dynamic range.
