import qt
import ctk
import slicer
import sys
import re


from slicer.ScriptedLoadableModule import ScriptedLoadableModuleTest, ScriptedLoadableModuleWidget


__all__ = ['SlicerLayoutButtonsTestsClass']


class SlicerLayoutButtonsTests:

  def __init__(self, parent):
    parent.title = "SlicerLayoutButtons Tests"
    parent.categories = ["Testing.TestCases"]
    parent.dependencies = ["SlicerLayoutButtons"]
    parent.contributors = ["Christian Herz (SPL, BWH), Andrey Fedorov (SPL, BWH)"]
    parent.helpText = """
    """
    parent.acknowledgementText = """Surgical Planning Laboratory, Brigham and Women's Hospital, Harvard
                                    Medical School, Boston, USA This work was supported in part by the National
                                    Institutes of Health through grants U24 CA180918,
                                    R01 CA111288 and P41 EB015898."""
    self.parent = parent

    try:
      slicer.selfTests
    except AttributeError:
      slicer.selfTests = {}
    slicer.selfTests['SlicerLayoutButtons'] = self.runTest

  def runTest(self):
    tester = SlicerLayoutButtonsTestsClass()
    tester.runTest()


class SlicerLayoutButtonsTestsWidget(ScriptedLoadableModuleWidget):

  def __init__(self, parent=None):
    ScriptedLoadableModuleWidget.__init__(self, parent)

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    self.testsCollapsibleButton = ctk.ctkCollapsibleButton()
    self.testsCollapsibleButton.setLayout(qt.QFormLayout())
    self.testsCollapsibleButton.text = "Slicer Layout Buttons Tests"
    self.layout.addWidget(self.testsCollapsibleButton)
    self.generateButtons()

  def generateButtons(self):

    def onButtonPressed(button):
      tester = getattr(sys.modules[__name__], button.name)()
      tester.runTest()

    buttons = []
    for testName in __all__:
      b = qt.QPushButton(testName)
      b.name = testName
      self.testsCollapsibleButton.layout().addWidget(b)
      buttons.append(b)

    map(lambda b: b.clicked.connect(lambda clicked: onButtonPressed(b)), buttons)


class SlicerLayoutButtonsTestsClass(ScriptedLoadableModuleTest):

  def runTest(self):
    self.delayDisplay('Starting %s' % self.__class__.__name__)
    self.test_all_layouts()
    self.delayDisplay('Test passed!')

  def test_all_layouts(self):
    lm = slicer.app.layoutManager()
    lm.selectModule("SlicerLayoutButtons")
    layoutNode = slicer.vtkMRMLLayoutNode
    for layout in [k for k in layoutNode.__dict__.keys() if re.match(r'^SlicerLayout(.)+(View)$', k)]:
      self.delayDisplay('Testing Layout: %s' % layout, 200)
      lm.setLayout(getattr(layoutNode, layout))
