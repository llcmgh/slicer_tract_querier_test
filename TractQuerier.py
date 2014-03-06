
from __main__ import vtk, qt, ctk, slicer
import unittest
from itertools import izip
from vtk.util import numpy_support as ns
import numpy as np

#
# global variables 
#
tractography_file_name='C:\\Users\\Georgios\\workspace\\tract_querier\\OutputFiberBundle.vtk'
atlas_file_name='C:\\Users\\Georgios\\workspace\\tract_querier\\parc.nii.gz'
queries_string='C:\\Users\Georgios\\workspace\\tract_querier\\queries\\wmql_1_cst.qry'

#
# TractQuerier
#
class TractQuerier:
  def __init__(self, parent):
    parent.title = "Tract Querier"
    parent.categories = []
    parent.dependencies = []
    parent.contributors = ["Lichen Liang (MGH)",
                           "Steve Pieper (Isomics)"
                           ] # replace with "Firstname Lastname (Org)"
    parent.helpText = """
    TractQuerier
    """
    parent.acknowledgementText = """
    This file was originally developed by ....""" # replace with organization, grant and thanks.
    self.parent = parent
    try:
       slicer.selfTests
    except AttributeError:
       slicer.selfTests = {}
    slicer.selfTests['TractQuerier'] = self.runTest
 
  def runTest(self):
     tester = TractQuerierTest()
     tester.runTest()
#
# TractQuerierWidget
#

class TractQuerierWidget:
  def __init__(self, parent = None):
    if not parent:
      self.parent = slicer.qMRMLWidget()
      self.parent.setLayout(qt.QVBoxLayout())
      self.parent.setMRMLScene(slicer.mrmlScene)
    else:
      self.parent = parent
    self.layout = self.parent.layout()
    if not parent:
      self.setup()
      self.parent.show()

  def setup(self):
     # Instantiate and connect widgets ...
 
     # Collapsible button
     parametersCollapsibleButton = ctk.ctkCollapsibleButton()
     parametersCollapsibleButton.text = "Parameters"
     self.layout.addWidget(parametersCollapsibleButton)
 
     # Layout within the parameters collapsible button
     parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)
 
     # fiber
     self.fiberSelector = slicer.qMRMLNodeComboBox(parametersCollapsibleButton)
     self.fiberSelector.nodeTypes = ( ("vtkMRMLFiberBundleNode"), "" )
     self.fiberSelector.selectNodeUponCreation = False
     self.fiberSelector.addEnabled = False
     self.fiberSelector.removeEnabled = False
     self.fiberSelector.noneEnabled = True
     self.fiberSelector.showHidden = False
     self.fiberSelector.showChildNodeTypes = False
     self.fiberSelector.setMRMLScene( slicer.mrmlScene )
     self.fiberSelector.setToolTip( "Pick the full-brain tractography in VTK format: It must be a vtkPolyData object where all the cells are lines." )
     parametersFormLayout.addRow("Fiber Bundle", self.fiberSelector)
 
     # label map
     self.labelSelector = slicer.qMRMLNodeComboBox(parametersCollapsibleButton)
     self.labelSelector.nodeTypes = ( ("vtkMRMLScalarVolumeNode"), "" )
     #self.labelSelector.addAttribute( "vtkMRMLScalarVolumeNode", "LabelMap", 1 )
     self.labelSelector.selectNodeUponCreation = False
     self.labelSelector.addEnabled = False
     self.labelSelector.removeEnabled = False
     self.labelSelector.noneEnabled = True
     self.labelSelector.showHidden = False
     self.labelSelector.showChildNodeTypes = False
     self.labelSelector.setMRMLScene( slicer.mrmlScene )
     self.labelSelector.setToolTip( "Pick A brain parcellation, obtained from freesurfer in the same space as the full-brain tractography." )
     parametersFormLayout.addRow("Brain Parcellation ", self.labelSelector)
 
     # query script 
     self.queryScript = qt.QTextEdit()
     self.queryScript.setToolTip( "WMQL query text." )
     #self.labelValue.setValue(1)
     parametersFormLayout.addWidget(self.queryScript)
 
     # apply
     self.applyButton = qt.QPushButton(parametersCollapsibleButton)
     self.applyButton.text = "Apply"
     parametersFormLayout.addWidget(self.applyButton)
 
     self.applyButton.connect('clicked()', self.onApply)
 
     # Add vertical spacer
     self.layout.addStretch(1)      
      
      
  def onApply(self):
    fiberNode = self.fiberSelector.currentNode()
    labelNode = self.labelSelector.currentNode()
    queryScript=self.queryScript.plainText
    print queryScript
    
    if not fiberNode and not labelNode:
       qt.QMessageBox.critical(slicer.util.mainWindow(), 'FiberBundleToLabelMap', "Must select fiber bundle and label map")
       return
    run(fiberNode, labelNode,queryScript)

from optparse import OptionParser
import os
import sys

def run(fiberNode,parcNode,queryScript):
    parser=OptionParser()
    (options, args) = parser.parse_args()

    options.bounding_box_affine_transform=None
    options.length_threshold=2
    options.threshold=0
    options.interactive=False
    options.query_selection=''

    global np
    global tract_querier
    import numpy as np
#    import nibabel
    import tract_querier

    print "Loading files"
    folders = []
    
    default_folder = tract_querier.default_queries_folder
    folders = [os.getcwd()] + folders + [default_folder]
    print folders
    for folder in folders:
        if not (os.path.exists(folder) and os.path.isdir(folder)):
            parser.error("Error in include folder %s" % folder)
    
    try:
        query_script=queryScript
        query_filename=""

        query_file_body = tract_querier.queries_preprocess(
            query_script,
            filename=query_filename,
            include_folders=folders
        )
        
        tract_querier.queries_syntax_check(query_file_body)
    except tract_querier.TractQuerierSyntaxError, e:
        parser.error(e.value)
    
    #
    #  convert atlas file to numpy.array, must swap x-z to comply with Demian's data input 
    #
    imgOrg= slicer.util.array(parcNode.GetID())
    img=imgOrg.swapaxes(0,2)
    
    affine_ijk_2_ras = vtk.vtkMatrix4x4()
    parcNode.GetRASToIJKMatrix(affine_ijk_2_ras)  
    affine_ijk_2_ras.Invert()
    affine_ijk_2_ras=vtkMatrix_2_array(affine_ijk_2_ras)
     
    #
    #  covert slicer polydata to tract
    #
    polyData = fiberNode.GetPolyData()
    tr = tract_querier.tractography.vtkInterface.vtkPolyData_to_tracts(polyData)
    print 'tract-to-polydata'
    
    #
    #  run tract-querier
    #
    tracts = tr.tracts()    
    tractography_spatial_indexing = tract_querier.TractographySpatialIndexing(
        tracts, img, affine_ijk_2_ras, options.length_threshold, options.threshold
    )
    
    print "Computing queries"
    evaluated_queries = tract_querier.eval_queries(
        query_file_body,
        tractography_spatial_indexing,
    )
    
    query_names = evaluated_queries.keys()
    print query_names
    if options.query_selection != '':
        selected_queries = set(options.query_selection.lower().split(','))
        query_names = list(set(query_names) & set(selected_queries))

    query_names.sort()

    print 'save_query'
    polyDataOut=vtk.vtkAppendPolyData()
    for query_name in query_names:
        tr_out_temp=save_query( query_name, tr, options, evaluated_queries)
        if tr_out_temp is not None:
             tr_polydata=tracts_to_vtkPolyData64(tr_out_temp)
             polyDataOut.AddInput(tr_polydata)
    updateOutputNode(polyDataOut.GetOutput())
    return   

def vtkMatrix_2_array(m):
    import numpy
    out=numpy.zeros(shape=(4,4))
    for i in range(4):
        for j in range(4):
             out[i][j]=m.GetElement(i,j)
    return out
     
def save_query(query_name, tractography, options, evaluated_queries, extension='.vtk', extra_kwargs={}):
    tract_numbers = evaluated_queries[query_name]
    print "\tQuery %s: %.6d" % (query_name, len(tract_numbers))
    tr=None
    if tract_numbers:
        tr=save_tractography_file(
            "",
            tractography,
            tract_numbers,
            extra_kwargs=extra_kwargs
        )
    return tr

def save_tractography_file(filename, tractography, tract_numbers, extra_kwargs={}):
    print 'start save tractography file'
    tract_numbers = list(tract_numbers)

    original_tracts = tractography.original_tracts()
    print tract_numbers
    tracts_to_save = [original_tracts[i] for i in tract_numbers]

    if len(tracts_to_save) == 0:
        return
    
    tracts_data_to_save = {}
    print 'extract key-data'
    for key, data in tractography.original_tracts_data().items():
        tracts_data_to_save[key] = [data[f] for f in tract_numbers]

    if (
        'ActiveTensors' not in tracts_data_to_save and
        'Tensors_' in tracts_data_to_save
    ):
        tracts_data_to_save['ActiveTensors'] = 'Tensors_'
    if (
        'ActiveVectors' not in tracts_data_to_save and
        'Vectors_' in tracts_data_to_save
    ):
        tracts_data_to_save['ActiveVectors'] = 'Vectors_'

    print "tractography.tractorgrapy_to_file"
    
    tr=tract_querier.tractography.Tractography(
            tracts_to_save,
            tracts_data_to_save
        )
    
    return tr

def tracts_to_vtkPolyData64(tracts, tracts_data={}, lines_indices=None):
  #  if isinstance(tracts, Tractography):
    tracts_data = tracts.tracts_data()
    tracts = tracts.tracts()
    lengths = [len(p) for p in tracts]
    line_starts = ns.numpy.r_[0, ns.numpy.cumsum(lengths)]
    if lines_indices is None:
        lines_indices = [
            ns.numpy.arange(length) + line_start
            for length, line_start in izip(lengths, line_starts)
        ]

    ids = ns.numpy.hstack([
        ns.numpy.r_[c[0], c[1]]
        for c in izip(lengths, lines_indices)
    ])
    ids=np.int64(ids)
    vtk_ids = ns.numpy_to_vtkIdTypeArray(ids, deep=True)

    cell_array = vtk.vtkCellArray()
    cell_array.SetCells(len(tracts), vtk_ids)
    points = ns.numpy.vstack(tracts).astype(
        ns.get_vtk_to_numpy_typemap()[vtk.VTK_DOUBLE]
    )
    points_array = ns.numpy_to_vtk(points, deep=True)

    poly_data = vtk.vtkPolyData()
    vtk_points = vtk.vtkPoints()
    vtk_points.SetData(points_array)
    poly_data.SetPoints(vtk_points)
    poly_data.SetLines(cell_array)

    saved_keys = set()
    for key, value in tracts_data.items():
        if key in saved_keys:
            continue
        if key.startswith('Active'):
            saved_keys.add(value)
            name = value
            value = tracts_data[value]
        else:
            name = key

        if len(value) == len(tracts):
            if value[0].ndim == 1:
                value_ = ns.numpy.hstack(value)[:, None]
            else:
                value_ = ns.numpy.vstack(value)
        elif len(value) == len(points):
            value_ = value
        else:
            raise ValueError(
                "Data in %s does not have the correct number of items")

        vtk_value = ns.numpy_to_vtk(np.ascontiguousarray(value_), deep=True)
        vtk_value.SetName(name)
        if key == 'ActiveScalars' or key == 'Scalars_':
            poly_data.GetPointData().SetScalars(vtk_value)
        elif key == 'ActiveVectors' or key == 'Vectors_':
            poly_data.GetPointData().SetVectors(vtk_value)
        elif key == 'ActiveTensors' or key == 'Tensors_':
            poly_data.GetPointData().SetTensors(vtk_value)
        else:
            poly_data.GetPointData().AddArray(vtk_value)

    poly_data.BuildCells()

    return poly_data

def updateOutputNode(polydata):
    # clear scene
    scene=slicer.mrmlScene
    scene.Clear(0)
    
    # create fiber node
    fiber=slicer.vtkMRMLModelNode()
    fiber.SetScene(scene)
    fiber.SetName("QueryTract")
    fiber.SetAndObservePolyData(polydata)
    
    # create display model fiber node
    fiberDisplay=slicer.vtkMRMLModelDisplayNode()
    fiberDisplay.SetScene(scene)
    scene.AddNode(fiberDisplay)
    fiber.SetAndObserveDisplayNodeID(fiberDisplay.GetID())
    
    # add to scene
    fiberDisplay.SetInputPolyData(polydata)
    scene.AddNode(fiber)

class TractQuerierTest(unittest.TestCase):
   """
   This is the test case for your scripted module.
   """

   def delayDisplay(self,message,msec=1000):
     """This utility method displays a small dialog and waits.
     This does two things: 1) it lets the event loop catch up
     to the state of the test so that rendering and widget updates
     have all taken place before the test continues and 2) it
     shows the user/developer/tester the state of the test
     so that we'll know when it breaks.
     """
     print(message)
     self.info = qt.QDialog()
     self.infoLayout = qt.QVBoxLayout()
     self.info.setLayout(self.infoLayout)
     self.label = qt.QLabel(message,self.info)
     self.infoLayout.addWidget(self.label)
     qt.QTimer.singleShot(msec, self.info.close)
     self.info.exec_()
 
   def setUp(self):
     """ Do whatever is needed to reset the state - typically a scene clear will be enough.
     """
     slicer.mrmlScene.Clear(0)
 
   def runTest(self):
     """Run as few or as many tests as needed here.
     """
     self.setUp()
     self.test_TractQuerier()
 
   def test_TractQuerier(self):
     self.applicationLogic = slicer.app.applicationLogic()
     self.volumesLogic = slicer.modules.volumes.logic()
 
     self.delayDisplay("Starting the test")
     #
     # first, get some data
     #
     import urllib
     downloads = (
         ('http://midas.kitware.com/bitstream/view/17622', 'parc.nii.gz', slicer.util.loadVolume),
         ('http://midas.kitware.com/bitstream/view/17624', 'fiber.vtp', slicer.util.loadFiberBundle),
         )
     
     for url,name,loader in downloads:
       filePath = slicer.app.temporaryPath + '/' + name
       #if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
       print('Requesting download %s from %s...\n' % (name, url))
       urllib.urlretrieve(url, filePath)
       if loader:
         print('Loading %s...\n' % (name,))
         loader(filePath)

     query_url='http://midas.kitware.com/bitstream/view/17625'
     filepath=slicer.app.temporaryPath + '/' + 'test.qry'
     urllib.urlretrieve(query_url,filepath)     
     query_script = file(filepath).read()
     print query_script
     self.delayDisplay('Finished with download and loading\n')
 
     labelNode = slicer.util.getNode(pattern="parc")
     fiberNode = slicer.util.getNode(pattern="fiber")
     self.delayDisplay("Running query, please wait ...")
     run(fiberNode, labelNode, query_script)
     self.delayDisplay('Test passed!')

       