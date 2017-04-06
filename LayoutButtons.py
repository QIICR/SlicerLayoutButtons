from collections import OrderedDict
from slicer.ScriptedLoadableModule import *
from SlicerProstateUtils.mixins import *

import xml.etree.ElementTree as ET


class LayoutButtons(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "LayoutButtons"
    self.parent.categories = ["Examples"]
    self.parent.dependencies = ["SlicerProstate"]
    self.parent.contributors = ["Christian Herz (SPL)"]
    self.parent.helpText = """
    This extensions provides an user interface with buttons the same way as the Slicer slice
    views are aligned. Users can click a button and select a foreground/background volume
    to be displayed in the associated slice view.
    """
    self.parent.acknowledgementText = """
    This work was supported in part by the National Cancer Institute funding to the
    Quantitative Image Informatics for Cancer Research (QIICR) (U24 CA180918).
    """ # replace with organization, grant and thanks.


class LayoutButtonsWidget(ModuleWidgetMixin, ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  _AVAILABLE_LAYERS = OrderedDict([("Label", "vtkMRMLLabelMapVolumeNode"),
                                   ("Foreground", "vtkMRMLScalarVolumeNode"),
                                   ("Background", "vtkMRMLScalarVolumeNode")])

  @property
  def layerNameVolumeClassPairs(self):
    return self._layerNameVolumeClassPairs

  @layerNameVolumeClassPairs.setter
  def layerNameVolumeClassPairs(self, dictionary):
    """
      example:
        from collections import OrderedDict
        {object}.layerNameVolumeClassPairs = OrderedDict([("Label", "vtkMRMLLabelMapVolumeNode")])
    """
    if not isinstance(dictionary, OrderedDict):
      raise ValueError("Parameter needs to be a %s" % str(OrderedDict))
    for layerName, volumeClass in dictionary.iteritems():
      getterName = self.getCompositeGetterNameForLayer(layerName)
      if not hasattr(slicer.vtkMRMLSliceCompositeNode, getterName):
        raise ValueError("{0} is not valid. Method {1} does not exist in {2}".format(layerName, getterName,
                                                                                     slicer.vtkMRMLSliceCompositeNode))
      elif not hasattr(slicer, volumeClass):
        raise ValueError("VolumeClass {} is not valid or doesn't exist.".format(volumeClass))
    self._layerNameVolumeClassPairs = dictionary
    self.onLayoutChanged()

  def getCompositeGetterNameForLayer(self, layerName):
    return "Get{}VolumeID".format(layerName)

  def getCompositeSetterNameForLayer(self, layerName):
    return "Set{}VolumeID".format(layerName)

  def __init__(self, parent=None):
    ScriptedLoadableModuleWidget.__init__(self, parent)
    self.layoutLogic = self.layoutManager.layoutLogic()
    self.lNode = self.layoutLogic.GetLayoutNode()

    self.fitSliceToAll = False
    self.truncateLength = 10

    self._layerNameVolumeClassPairs = self._AVAILABLE_LAYERS
    self._buttons = []
    self._setupPropertyNames()

  def setTruncateLength(self, length):
    self.truncateLength = length
    self.onLayoutChanged()

  def _setupPropertyNames(self):
    self._propertyNames = ["fitSliceToAll", "truncateLength", "layerNameVolumeClassPairs"]

  def setVisibleLayers(self, layerNames):
    allowedLayerNames = self._AVAILABLE_LAYERS.keys()

    def checkLayerNames(names):
      for name in names:
        if not name.istitle(): raise ValueError("'%s': All layer names need to start with a capital letter" % name)
        if not name in allowedLayerNames: raise KeyError("Unknown layer name {0}. {0} does not exist. Available layers:"
                                                         " {1}".format(name, str(allowedLayerNames)))
    checkLayerNames(layerNames)
    layerSubset = self._AVAILABLE_LAYERS.fromkeys(layerNames)
    for layerName in layerNames:
      layerSubset[layerName] = self._AVAILABLE_LAYERS[layerName]
    self.layerNameVolumeClassPairs = layerSubset

  def getProperties(self):
    return [{"attributeName": name, "value": getattr(self, name)} for name in self._propertyNames]

  def cleanup(self):
    self.layoutManager.layoutChanged.disconnect(self.onLayoutChanged)
    self.removeLayoutButtons()

  def enter(self):
    self.onLayoutChanged()

  def exit(self):
    self.cleanup()

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    self.buttonWidget = qt.QWidget()
    self.buttonWidget.setLayout(qt.QVBoxLayout())
    self.addLayoutButtons()
    self.layout.addWidget(self.buttonWidget)
    self.layout.addStretch(1)
    self.setupConnections()

  def addLayoutButtons(self):
    root = ET.fromstring(self.lNode.GetCurrentLayoutDescription())
    assert root.tag == "layout"
    self.buttonLayoutGroup = self.createLayoutFromDescription(root)
    self.buttonWidget.layout().addWidget(self.buttonLayoutGroup)
    self.setupModifiedObservers()

  def createLayoutFromDescription(self, layout):
    widget = self.createVLayout([]) if layout.get("type") == "vertical" else self.createHLayout([])
    widget.setStyleSheet(".QWidget{border: 1px solid black;}")
    for item in layout.getchildren():
      for child in item.getchildren():
        if child.tag == "layout":
          widget.layout().addWidget(self.createLayoutFromDescription(child))
        elif child.tag == "view":
          button = self.createButtonForView(child)
          widget.layout().addWidget(button)
    return widget

  def setupModifiedObservers(self):
    self.removeModifiedObservers()
    for button in [b for b in self._buttons if b.isEnabled()]:
      _, cNode = self.getWidgetAndCompositeNodeByName(button.name)
      self.compositeObservers[cNode] = cNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onCompositeNodeModified)

  def onCompositeNodeModified(self, caller, event):
    button = self.getButton(caller.GetSingletonTag())
    self.generateName(button)

  def getButton(self, viewName):
    return next((b for b in self._buttons if b.name == viewName), None)

  def removeModifiedObservers(self):
    if not hasattr(self, "compositeObservers"):
      self.compositeObservers = {}
    for cNode, tag in self.compositeObservers.iteritems():
      cNode.RemoveObserver(tag)
    self.compositeObservers = {}

  def createButtonForView(self, child):
    name = child.get("singletontag")
    viewClass = child.get("class")
    isSliceNode = viewClass not in ["vtkMRMLChartViewNode", "vtkMRMLViewNode", "vtkMRMLTableViewNode"]
    button = self.createButton(name, name=name, enabled=isSliceNode)
    button.setStyleSheet("QPushButton,QMenu{background-color:%s;}" % self.getColorFromProperties(child))
    self._buttons.append(button)
    self.setElementSizePolicy(button)
    if isSliceNode:
      self.generateName(button)
      self.addMenu(button)
    return button

  def setElementSizePolicy(self, element):
    sizePolicy = qt.QSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(element.sizePolicy.hasHeightForWidth())
    element.setSizePolicy(sizePolicy)

  def generateName(self, button):
    button.text = ""
    if button.layout():
      self.removeButtonLabels(button)
    else:
      button.setLayout(qt.QVBoxLayout())

    elements = []
    for idx, layerName in enumerate(self._layerNameVolumeClassPairs.keys()):
      _, cNode = self.getWidgetAndCompositeNodeByName(button.name)
      currentVolumeID = getattr(cNode, self.getCompositeGetterNameForLayer(layerName))()
      if idx > 0:
        # TODO: add vertical line
        pass
      if currentVolumeID:
        volumeNode = slicer.mrmlScene.GetNodeByID(currentVolumeID)
        volumeName = volumeNode.GetName()
        text = (volumeName[:self.truncateLength] + '..') if len(volumeName) > self.truncateLength else volumeName
      else:
        text = "None"
      elements.append(qt.QLabel(text))
    button.layout().setSizeConstraint(qt.QLayout.SetMinimumSize)
    self.setElementSizePolicy(button)
    widget = self.createVLayout(elements)
    widget.setStyleSheet("QWidget{border: 0px solid black;}")
    button.layout().addWidget(widget)

  def removeButtonLabels(self, button):
    for child in [c for c in button.children() if isinstance(c, qt.QWidget)]:
      try:
        child.delete()
      except AttributeError:
        pass

  def getColorFromProperties(self, element):
    for elemProp in element.getchildren():
      if elemProp.get("name") == "viewcolor":
        return elemProp.text
    return None

  def addMenu(self, button):
    menu = qt.QMenu(button)
    menu.name = button.name
    button.setMenu(menu)
    menu.aboutToShow.connect(lambda m=menu: self.onMenuSelected(m))

  def onMenuSelected(self, menu):
    menu.clear()
    for layerName, volumeClass in self._layerNameVolumeClassPairs.iteritems():
      self.addSubMenu(menu, layerName, volumeClass)

  def addSubMenu(self, menu, layer, volumeClass):
    subMenuBackground = qt.QMenu(layer, menu)
    menu.addMenu(subMenuBackground)
    actionGroup = qt.QActionGroup(menu)
    actionGroup.setExclusive(True)

    _, cNode = self.getWidgetAndCompositeNodeByName(menu.name)
    for volume in [None]+self.getAvailableVolumes(volumeClassName=volumeClass):
      action = qt.QAction(volume.GetName() if volume else "None", actionGroup)
      subMenuBackground.addAction(action)
      actionGroup.addAction(action)
      action.setCheckable(True)
      action.triggered.connect(lambda triggered, l=layer, n=menu.name,v=volume: self.onImageSelectedFromMenu(l,n,v))
      currentVolumeID = getattr(cNode, self.getCompositeGetterNameForLayer(layer))()
      imageID = volume.GetID() if volume else volume
      if currentVolumeID == imageID:
        action.setChecked(True)

  def onImageSelectedFromMenu(self, layer, viewName, volume):
    widget, cNode = self.getWidgetAndCompositeNodeByName(viewName)
    getattr(cNode, self.getCompositeSetterNameForLayer(layer))(volume.GetID() if volume else None)
    if self.fitSliceToAll:
      widget.sliceLogic().FitSliceToAll()

  def getWidgetAndCompositeNodeByName(self, name):
    widget = self.layoutManager.sliceWidget(name)
    return widget, widget.mrmlSliceCompositeNode()

  def getAvailableVolumes(self, volumeClassName):
    # TODO: override this for setting specific images only
    return slicer.util.getNodesByClass(volumeClassName)

  def removeLayoutButtons(self):
    self.removeModifiedObservers()
    self.buttonWidget.layout().removeWidget(self.buttonLayoutGroup)
    self.buttonLayoutGroup.delete()
    self._buttons = []
    self.menus = []

  def getVisibleWidgets(self):
    pass

  def setupConnections(self):
    self.layoutManager.layoutChanged.connect(self.onLayoutChanged)

  def onLayoutChanged(self, layout=None):
    self.removeLayoutButtons()
    self.addLayoutButtons()