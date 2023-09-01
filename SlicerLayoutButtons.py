import slicer
import qt
import vtk

from collections import OrderedDict
from slicer.ScriptedLoadableModule import *
from SlicerDevelopmentToolboxUtils.mixins import ModuleWidgetMixin

import xml.etree.ElementTree as ET


class SlicerLayoutButtons(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "SlicerLayoutButtons"
    self.parent.categories = ["Informatics"]
    self.parent.dependencies = ["SlicerDevelopmentToolbox"]
    self.parent.contributors = ["Christian Herz (SPL), Andrey Fedorov (SPL)"]
    self.parent.helpText = """
    This extension provides a user interface with buttons organized the same way as the Slicer slice views are aligned. 
    The user can directly select foreground/background volume and labelmap to be displayed in the associated slice view.
    """
    self.parent.acknowledgementText = """
    This work was supported in part by the National Cancer Institute funding to the
    Quantitative Image Informatics for Cancer Research (QIICR) (U24 CA180918).
    """


class SlicerLayoutButtonsWidget(ModuleWidgetMixin, ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """
  LABEL_INFO = ("Label", "vtkMRMLLabelMapVolumeNode")
  FOREGROUND_INFO = ("Foreground", "vtkMRMLScalarVolumeNode")
  BACKGROUND_INFO = ("Background", "vtkMRMLScalarVolumeNode")

  _AVAILABLE_LAYERS = OrderedDict([LABEL_INFO, FOREGROUND_INFO, BACKGROUND_INFO])

  def setDisplayAllLayers(self):
    self._AVAILABLE_LAYERS = OrderedDict([self.LABEL_INFO, self.FOREGROUND_INFO, self.BACKGROUND_INFO])
    self._onLayoutChanged()

  def setDisplayLabelOnly(self):
    self._AVAILABLE_LAYERS = OrderedDict([self.LABEL_INFO])
    self._onLayoutChanged()

  def setDisplayForegroundOnly(self):
    self._AVAILABLE_LAYERS = OrderedDict([self.FOREGROUND_INFO])
    self._onLayoutChanged()

  def setDisplayBackgroundOnly(self):
    self._AVAILABLE_LAYERS = OrderedDict([self.BACKGROUND_INFO])
    self._onLayoutChanged()

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
    for layerName, volumeClass in dictionary.items():
      getterName = self.getCompositeGetterNameForLayer(layerName)
      if not hasattr(slicer.vtkMRMLSliceCompositeNode, getterName):
        raise ValueError("{0} is not valid. Method {1} does not exist in {2}".format(layerName, getterName,
                                                                                     slicer.vtkMRMLSliceCompositeNode))
      elif not hasattr(slicer, volumeClass):
        raise ValueError("VolumeClass {} is not valid or doesn't exist.".format(volumeClass))
    self._layerNameVolumeClassPairs = dictionary
    self._onLayoutChanged()

  @staticmethod
  def setElementSizePolicy(element):
    sizePolicy = qt.QSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
    sizePolicy.setHorizontalStretch(0)
    sizePolicy.setVerticalStretch(0)
    sizePolicy.setHeightForWidth(element.sizePolicy.hasHeightForWidth())
    element.setSizePolicy(sizePolicy)

  @staticmethod
  def removeButtonLabels(button):
    for child in [c for c in button.children() if isinstance(c, qt.QWidget)]:
      try:
        child.delete()
      except AttributeError:
        pass

  @staticmethod
  def getColorFromProperties(element):
    for elemProp in element:
      if elemProp.get("name") == "viewcolor":
        return elemProp.text
    return None

  @staticmethod
  def getAvailableVolumes(volumeClassName):
    # TODO: override this for setting specific images only
    return slicer.util.getNodesByClass(volumeClassName)

  @staticmethod
  def getCompositeGetterNameForLayer(layerName):
    return "Get{}VolumeID".format(layerName)

  @staticmethod
  def getCompositeSetterNameForLayer(layerName):
    return "Set{}VolumeID".format(layerName)

  def __init__(self, parent=None):
    self._layoutLogic = self.layoutManager.layoutLogic()
    self._layoutNode = self._layoutLogic.GetLayoutNode()
    self._fitSliceToAll = False
    self._truncateLength = 10

    self._layerNameVolumeClassPairs = self._AVAILABLE_LAYERS
    self._buttons = []
    self._propertyNames = ["_fitSliceToAll", "_truncateLength", "layerNameVolumeClassPairs"]

    ScriptedLoadableModuleWidget.__init__(self, parent)

  def hideReloadAndTestArea(self):
    if self.developerMode:
      self.reloadCollapsibleButton.hide()

  def setTruncateLength(self, length):
    self._truncateLength = length
    self._onLayoutChanged()

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
    if self.layoutManager:
      self.layoutManager.layoutChanged.disconnect(self._onLayoutChanged)
    self._removeLayoutButtons()

  def enter(self):
    self._onLayoutChanged()

  def exit(self):
    self.cleanup()

  def onReload(self):
    self.cleanup()
    super(SlicerLayoutButtonsWidget, self).onReload()

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    self.buttonWidget = qt.QWidget()
    self.buttonWidget.setLayout(qt.QVBoxLayout())
    self._addLayoutButtons()
    self.layout.addWidget(self.buttonWidget)
    self.layout.addStretch(1)
    self._setupConnections()

  def _addLayoutButtons(self):
    try:
      root = ET.fromstring(self._layoutNode.GetCurrentLayoutDescription())
      self.buttonLayoutGroup = self._createLayoutFromDescription(root)
      self._setupModifiedObservers()
    except AttributeError as exc:
      print(exc)
      label = qt.QLabel("Layout not supported")
      label.setStyleSheet("qproperty-alignment: AlignCenter;")
      self.buttonLayoutGroup = self.createVLayout([label])
    finally:
      self.buttonWidget.layout().addWidget(self.buttonLayoutGroup)
      self.buttonLayoutGroup.setStyleSheet(".QWidget{border: 1px solid black;}")

  def _setupConnections(self):
    self.layoutManager.layoutChanged.connect(self._onLayoutChanged)
    slicer.app.connect('aboutToQuit()', self.cleanup)

  def _onLayoutChanged(self, layout=None):
    try:
      self._removeLayoutButtons()
      self._layerNameVolumeClassPairs = self._AVAILABLE_LAYERS
      self._addLayoutButtons()
    except (AttributeError, ValueError):
      pass

  def _createLayoutFromDescription(self, layout):
    widget = self.createVLayout([]) if layout.get("type") == "vertical" else self.createHLayout([])
    for item in layout:
      for child in item:
        if child.tag == "layout":
          widget.layout().addWidget(self._createLayoutFromDescription(child))
        elif child.tag == "view":
          button = self._createButtonForView(child)
          widget.layout().addWidget(button)
    return widget

  def _setupModifiedObservers(self):
    self.removeModifiedObservers()
    for button in [b for b in self._buttons if b.isEnabled()]:
      _, cNode = self.getWidgetAndCompositeNodeByName(button.name)
      self.compositeObservers[cNode] = cNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onCompositeNodeModified)

  def onCompositeNodeModified(self, caller, event):
    button = self.getButton(caller.GetSingletonTag())
    self._generateName(button)
    slicer.app.processEvents()

  def getButton(self, viewName):
    return next((b for b in self._buttons if b.name == viewName), None)

  def removeModifiedObservers(self):
    if not hasattr(self, "compositeObservers"):
      self.compositeObservers = {}
    for cNode, tag in self.compositeObservers.items():
      cNode.RemoveObserver(tag)
    self.compositeObservers = {}

  def _createButtonForView(self, child):
    name = child.get("singletontag")
    viewClass = child.get("class")
    isSliceNode = viewClass == "vtkMRMLSliceNode"
    button = self.createButton(name, name=name, enabled=isSliceNode)
    button.setStyleSheet("QPushButton,QMenu{background-color:%s;}" % self.getColorFromProperties(child))
    self._buttons.append(button)
    self.setElementSizePolicy(button)
    if isSliceNode:
      self._generateName(button)
      self._addMenu(button)
    return button

  def _generateName(self, button):
    self._preconfigureButton(button)

    elements = []
    for layerName in self._layerNameVolumeClassPairs.keys():
      _, cNode = self.getWidgetAndCompositeNodeByName(button.name)
      currentVolumeID = getattr(cNode, self.getCompositeGetterNameForLayer(layerName))()
      volumeName = "None"
      if currentVolumeID:
        volumeNode = slicer.mrmlScene.GetNodeByID(currentVolumeID)
        if volumeNode:
          volumeName = volumeNode.GetName()
      text = (volumeName[:self._truncateLength] + '..') if len(volumeName) > self._truncateLength else volumeName
      element = qt.QLabel("{}: {}".format(layerName[0], text))
      element.setToolTip("{}: {}".format(layerName[0], volumeName))
      elements.append(element)

    widget = self.createVLayout(elements)
    widget.setStyleSheet("QWidget{border: 0px solid black;}")
    button.layout().addWidget(widget)

  def _preconfigureButton(self, button):
    button.text = ""
    if button.layout():
      self.removeButtonLabels(button)
    else:
      button.setLayout(qt.QVBoxLayout())
    button.layout().setSizeConstraint(qt.QLayout.SetMinimumSize)
    self.setElementSizePolicy(button)

  def _addMenu(self, button):
    menu = qt.QMenu(button)
    menu.name = button.name
    button.setMenu(menu)
    menu.aboutToShow.connect(lambda m=menu: self._onMenuSelected(m))

  def _onMenuSelected(self, menu):
    menu.clear()
    if len(self._layerNameVolumeClassPairs) > 1:
      for layerName, volumeClass in self._layerNameVolumeClassPairs.items():
        self._addSubMenu(menu, layerName, volumeClass)
    else:
      for layerName, volumeClass in self._layerNameVolumeClassPairs.items():
        self._addActions(menu, layerName, volumeClass)

  def _addSubMenu(self, menu, layer, volumeClass):
    subMenuBackground = qt.QMenu(layer, menu)
    subMenuBackground.name = menu.name
    menu.addMenu(subMenuBackground)
    self._addActions(subMenuBackground, layer, volumeClass)

  def _addActions(self, menu, layer, volumeClass):
    actionGroup = qt.QActionGroup(menu)
    actionGroup.setExclusive(True)

    _, cNode = self.getWidgetAndCompositeNodeByName(menu.name)
    for volume in [None]+self.getAvailableVolumes(volumeClassName=volumeClass):
      action = qt.QAction(volume.GetName() if volume else "None", actionGroup)
      menu.addAction(action)
      actionGroup.addAction(action)
      action.setCheckable(True)
      action.triggered.connect(lambda triggered, l=layer, n=menu.name,v=volume: self._onImageSelectedFromMenu(l, n, v))
      currentVolumeID = getattr(cNode, self.getCompositeGetterNameForLayer(layer))()
      imageID = volume.GetID() if volume else volume
      if currentVolumeID == imageID:
        action.setChecked(True)

  def _onImageSelectedFromMenu(self, layer, viewName, volume):
    widget, cNode = self.getWidgetAndCompositeNodeByName(viewName)
    getattr(cNode, self.getCompositeSetterNameForLayer(layer))(volume.GetID() if volume else None)
    if self._fitSliceToAll:
      widget.sliceLogic().FitSliceToAll()

  def getWidgetAndCompositeNodeByName(self, name):
    widget = self.layoutManager.sliceWidget(name)
    return widget, widget.mrmlSliceCompositeNode()

  def _removeLayoutButtons(self):
    try:
      self.removeModifiedObservers()
      self.buttonWidget.layout().removeWidget(self.buttonLayoutGroup)
      self.buttonLayoutGroup.delete()
    except AttributeError:
      pass
    finally:
      self._buttons = []
      self.menus = []