=====================================================================
Name: 		TrackQuerier Module for Slicer 4
Creator:	.... 
Date:		01.06.2014
Version:	b1.0
Language:	Python
Platforms:	Slicer 4 (MacOS)
=====================================================================

This Module allows users to query fiber tracks with White Matter Query Language (WMQL) 
introduced by Demain Wasssermann et. al. in MICCAI 2013. 
 

1) Download and Install Slicer			http://download.slicer.org/


2) Download TractQuerier Module

  >git clone https://github.com/llcmgh/slicer_tract_querier.git
  >cd slicer_tract_querier

This package contains three dependent packages:
nibabel
bz2.so


3) Load TractQuerier module into Slicer

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
