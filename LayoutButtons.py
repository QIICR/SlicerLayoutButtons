import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from SlicerProstateUtils.mixins import *

import xml.etree.ElementTree as ET

import logging


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

  def __init__(self, parent=None):
    ScriptedLoadableModuleWidget.__init__(self, parent)
    self.buttons = []
    self.layoutLogic = self.layoutManager.layoutLogic()
    self.lNode = self.layoutLogic.GetLayoutNode()

  def cleanup(self):
    self.layoutManager.layoutChanged.disconnect(self.onLayoutChanged)
    self.removeLayoutButtons()

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

  def createButtonForView(self, child):
    name = child.get("singletontag")
    viewClass = child.get("class")
    isSliceNode = viewClass not in ["vtkMRMLChartViewNode", "vtkMRMLViewNode"]
    button = self.createButton(name, name=name, enabled=isSliceNode)
    button.setSizePolicy(qt.QSizePolicy.Minimum, qt.QSizePolicy.Minimum)
    button.setStyleSheet("QPushButton,QMenu{background-color:%s;}" % self.getColorFromProperties(child))
    self.buttons.append(button)
    if isSliceNode:
      self.addMenu(button)
    return button

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
    self.addSubMenu(menu, "Foreground")
    self.addSubMenu(menu, "Background")

  def addSubMenu(self, menu, layer):
    subMenuBackground = qt.QMenu(layer, menu)
    menu.addMenu(subMenuBackground)
    actionGroup = qt.QActionGroup(menu)
    actionGroup.setExclusive(True)

    _, cNode = self.getCompositeNodeAndWidgetByName(menu.name)
    for volume in [None]+self.getAvailableScalarVolumes():
      action = qt.QAction(volume.GetName() if volume else "None", actionGroup)
      subMenuBackground.addAction(action)
      actionGroup.addAction(action)
      action.setCheckable(True)
      action.triggered.connect(lambda triggered, l=layer, n=menu.name,v=volume: self.onImageSelectedFromMenu(l,n,v))
      currentVolumeID = getattr(cNode, "Get{}VolumeID".format(layer))()
      imageID = volume.GetID() if volume else volume
      if currentVolumeID == imageID:
        action.setChecked(True)

  def onImageSelectedFromMenu(self, layer, viewName, volume):
    widget, cNode = self.getCompositeNodeAndWidgetByName(viewName)
    getattr(cNode, "Set{}VolumeID".format(layer))(volume.GetID() if volume else None)
    widget.sliceLogic().FitSliceToAll()

  def getCompositeNodeAndWidgetByName(self, name):
    widget = self.layoutManager.sliceWidget(name)
    return widget, widget.mrmlSliceCompositeNode()

  def getAvailableScalarVolumes(self):
    # TODO: override this for setting specific images only
    return slicer.util.getNodesByClass("vtkMRMLScalarVolumeNode")

  def removeLayoutButtons(self):
    self.buttonWidget.layout().removeWidget(self.buttonLayoutGroup)
    self.buttonLayoutGroup.deleteLater()
    self.buttons = []
    self.menus = []

  def getVisibleWidgets(self):
    pass

  def setupConnections(self):
    self.layoutManager.layoutChanged.connect(self.onLayoutChanged)

  def onLayoutChanged(self):
    self.removeLayoutButtons()
    self.addLayoutButtons()
