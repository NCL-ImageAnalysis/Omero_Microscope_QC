# Key Value Pairs
This document contains valid key value pairs that can be assigned to projects/datasets/images in order to be parsed by omero_microscope_qc. 

Spelling and spaces must **exactly match** those listed in Key or Accepted Values columns.

## omero_microscope_qc values
These values have specific uses by omero_microscope_qc module 
| Key | Value Type | Accepted Values | Description |
| --- | ---------- | --------------- | ----------- |
| QC_Processed | Boolean | True, False | Automatically populated by omero_microscope_qc when analysis has been completed. |
| microscope_type | Text | WideField, CLSM, Spinning Disc Confocal, Multiphoton | Type of microscope |
| pinhole_size_AU | Number | Any Number | Pinhole size set in Airy Units. Required for CLSM microscopes |
| use_rois | Boolean | True, False | Whether to process using OMERO ROIs or the entire image |
| generate_rois | Boolean | True, False | Whether to automatically generate OMERO ROIs with one bead per ROI. Also requires crop_size to be set |
| crop_size | Number | Any Number | Size of the crop used by generate_rois in scaled units |
## MetroloJ_QC values
These values match class attributes for the MetroloJDialog class and corresponds to most settings you can add in the GUI version of the plugin.
| Key | Value Type | Accepted Values | Description |
| --- | ---------- | --------------- | ----------- |
| operator | Text | Any | Name of the operator that generated & analysed the data |
| reportName | Text | 
| reportType | Text | 
| title | Text | 
| ip | class ij.ImagePlus | 
| bitDepth | Integer | 
| microType | Integer | 
| detectorType | Integer | 
| errorDialogCanceled | Boolean | True, False | 
| dimensionOrder | Integer | 
| filterSets | Text | 
| NA | Number | 
| pinhole | Number | 
| refractiveIndex | Number | 
| detectorNames | Text | 
| date | Text | 
| sampleInfo | Text | 
| comments | Text | 
| saturationChoice | Boolean | True, False | 
| fitFormula | Integer | 
| useBeads | Boolean | True, False | 
| addCross | Boolean | True, False | 
| addRoi | Boolean | True, False | 
| addText | Boolean | True, False | 
| resize | Boolean | True, False | 
| overlayColor | class java.awt.Color | 
| beadDetectionThreshold | Text | 
| centerDetectionMethodIndex | Integer | 
| oneParticle | Boolean | True, False | 
| multipleBeads | Boolean | True, False | 
| beadChannel | Integer | 
| beadSize | Number | 
| cropFactor | Number | 
| beadMinDistanceToTopBottom | Number | 
| doubletMode | Boolean | True, False | 
| prominence | Number | 
| innerAnnulusEdgeDistanceToBead | Number | 
| annulusThickness | Number | 
| useTolerance | Boolean | True, False | 
| coalRatioTolerance | Number | 
| XYratioTolerance | Number | 
| ZratioTolerance | Number | 
| uniformityTolerance | Number | 
| centAccTolerance | Number | 
| R2Threshold | Number | 
| maxGapLength | Integer | 
| useResolutionThresholds | Boolean | True, False | 
| isotropicThreshold | Number | 
| showProjections | Boolean | True, False | 
| showDisplacementFits | Boolean | True, False | 
| useAbsoluteValues | Boolean | True, False | 
| outliers | Boolean | True, False | 
| outlierMode | Integer | 
| shorten | Boolean | True, False | 
| openPdf | Boolean | True, False | 
| savePdf | Boolean | True, False | 
| saveImages | Boolean | True, False | 
| saveSpreadsheet | Boolean | True, False | 
| singleChannel | class java.lang.Double | 
| sqrtChoice | Boolean | True, False | 
| discardWavelengthSpecs | Boolean | True, False | 
| gaussianBlurChoice | Boolean | True, False | 
| thresholdChoice | Boolean | True, False | 
| stepWidth | Number | 
| noiseChoice | Boolean | True, False | 
| conversionFactor | Number | 
| logScalePlot | Boolean | True, False | 
| temperatureChoice | Boolean | True, False | 
| computeFrequencies | Boolean | True, False | 
| fixedNoiseMapRange | Boolean | True, False | 
| maxNoiseMapValue | Number | 
| hotChoice | Boolean | True, False | 
| temperatureThreshold | Number | 
| logLUT | Boolean | True, False | 
| fixedFrequencyMapRange | Boolean | True, False | 
| maxFrequencyMapValue | Number | 
| roi | class ij.gui.Roi | 
| testDialogOKed | Boolean | True, False | 
| testType | Integer | 
| dimensions | Text | 
| dimension | Text | 
| testChannel | Integer | 
| expectednMaxima | Integer | 
| maxIterations | Integer | 
| showProminencesPlot | Boolean | True, False | 
| preProcess | Boolean | True, False | 
| useIJAutothresholds | Boolean | True, False | 
| useLegacyThreshold | Boolean | True, False | 
| usekMeansThreshold | Boolean | True, False | 