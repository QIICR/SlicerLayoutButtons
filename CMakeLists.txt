cmake_minimum_required(VERSION 3.5.0)

#-----------------------------------------------------------------------------
set(EXTENSION_NAME SlicerLayoutButtons)
set(EXTENSION_HOMEPAGE "https://github.com/QIICR/SlicerLayoutButtons")
set(EXTENSION_CATEGORY "Informatics")
set(EXTENSION_CONTRIBUTORS "Christian Herz (SPL), Andrey Fedorov (SPL)")
set(EXTENSION_DESCRIPTION "Simplified widget for accessing volumes and labelmaps displayed in slice views")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/QIICR/SlicerLayoutButtons/master/Resources/Icons/SlicerLayoutButtons.png")
set(EXTENSION_SCREENSHOTURLS "https://raw.githubusercontent.com/QIICR/SlicerLayoutButtons/master/Resources/Screenshots/overview.png")
set(EXTENSION_STATUS "Work in progress")
set(EXTENSION_DEPENDS SlicerDevelopmentToolbox)

#-----------------------------------------------------------------------------

set(MODULE_NAME SlicerLayoutButtons)

find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

find_package(SlicerDevelopmentToolbox REQUIRED)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  )

set(MODULE_PYTHON_RESOURCES
  Resources/Icons/${MODULE_NAME}.png
  )

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
  WITH_GENERIC_TESTS
  )

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})