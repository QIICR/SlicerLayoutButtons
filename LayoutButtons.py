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
    self.parent.title = "LayoutButtons" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Examples"]
    self.parent.dependencies = ["SlicerProstate"]
    self.parent.contributors = ["Christian Herz (SPL)"]
    self.parent.helpText = """
    This is an example of scripted loadable module bundled in an extension.
    It performs a simple thresholding on the input volume and optionally captures a screenshot.
    """
    self.parent.acknowledgementText = """
    This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
    and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.


class LayoutButtonsWidget(ModuleWidgetMixin, ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent=None):
    ScriptedLoadableModuleWidget.__init__(self, parent)
    self.buttons = []
    self.logic = LayoutButtonsLogic()
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

    self.setupConnections()

  def addLayoutButtons(self):
    root = ET.fromstring(self.lNode.GetCurrentLayoutDescription())
    assert root.tag == "layout"
    self.buttonLayoutGroup = self.iterateLayout(root)
    self.buttonWidget.layout().addWidget(self.buttonLayoutGroup)

  def iterateLayout(self, layout):
    widget = self.createVLayout([]) if layout.get("type") == "vertical" else self.createHLayout([])
    widget.setStyleSheet(".QWidget{border: 1px solid black;}")
    for item in layout.getchildren():
      for child in item.getchildren():
        if child.tag == "layout":
          element = self.iterateLayout(child)
        elif child.tag == "view":
          name = child.get("singletontag")
          viewClass = child.get("class")
          isSliceNode = viewClass not in ["vtkMRMLChartViewNode", "vtkMRMLViewNode"]
          element = self.createButton(name, name=name,
                                      enabled=isSliceNode)

          self.buttons.append(element)
          if isSliceNode:
            self.addMenu(element)
        else:
          raise ValueError("%s unknown for parsing layout" % child.tag)
        widget.layout().addWidget(element)
    return widget

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

    cNode = self.getCompositeNodeByName(menu.name)
    for image in [None]+self.getAvailableImages():
      action = qt.QAction(image.GetName() if image else "None", actionGroup)
      subMenuBackground.addAction(action)
      actionGroup.addAction(action)
      action.setCheckable(True)
      action.triggered.connect(lambda triggered, l=layer, n=menu.name,v=image: self.onImageSelectedFromMenu(l,n,v))
      currentVolumeID = getattr(cNode, "Get{}VolumeID".format(layer))()
      imageID = image.GetID() if image else image
      print "{} == {}".format(currentVolumeID, imageID)
      if currentVolumeID == imageID:
        action.setChecked(True)

  def onImageSelectedFromMenu(self, layer, viewName, volume):
    cNode = self.getCompositeNodeByName(viewName)
    getattr(cNode, "Set{}VolumeID".format(layer))(volume.GetID() if volume else None)

  def getCompositeNodeByName(self, name):
    widget = self.layoutManager.sliceWidget(name)
    return widget.mrmlSliceCompositeNode()

  def getAvailableImages(self):
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
    print "layout changed"
    self.removeLayoutButtons()
    self.addLayoutButtons()
    # self.logic


class LayoutButtonsLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent=None):
    ScriptedLoadableModuleLogic.__init__(self, parent)
