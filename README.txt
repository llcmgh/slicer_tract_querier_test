=====================================================================
Name: 		TrackQuerier Module for Slicer 4
Creator:	.... 
Date:		01.06.2014
Version:	b1.0
Language:	Python
Platforms:	Slicer 4 (Windows, Mac OS X, Linux)
=====================================================================

This Module allows users to query fiber tracks with White Matter Query Language (WMQL) 
introduced by Demain Wasssermann et. al. in MICCAI 2013. 
 

1) Download and Install Slicer			http://download.slicer.org/


2) Download TractQuerier Module

  >git clone https://github.com/llcmgh/slicer_tract_querier.git
  >cd slicer_tract_querier

This package contains three dependent packages:
numpy.MacOS.64
nibabel
bz2.so

3) Remove numpy1.4 and Install numpy1.7
Note: Slicer4 comes with numpy1.4, but our module needs numpy1.7
locate your numpy1.4 path, usually it is '/Applications/Slicer.app/Contents/lib/Python/lib/python2.7/site-packages/numpy'
  >rm -rf /Applications/Slicer.app/Contents/lib/Python/lib/python2.7/site-packages/numpy
  >cp -r numpy.MacOS.64 /Applications/Slicer.app/Contents/lib/Python/lib/python2.7/site-packages/numpy


4) Load TractQuerier module into Slicer

   Start Slicer

	Slicer -> Edit -> Application Settings -> Modules -> 
	Additional module paths ->
	Add slicer_tract_querier to the path
	
	Restart Slicer after adding the path
	
----------

Usage of the module :
(1) A tractography in VTK format: It must be a vtkPolyData object where all the cells are lines.
(2) A brain parcellation, obtained from freesurfer in the same space as the full-brain tractography.
(3) A WMQL query script typed in the EditBox

----------
