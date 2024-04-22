cmake_minimum_required(VERSION 3.5.0)

#-----------------------------------------------------------------------------
set(EXTENSION_NAME SlicerLayoutButtons)
set(EXTENSION_HOMEPAGE "https://github.com/QIICR/SlicerLayoutButtons")
set(EXTENSION_CATEGORY "Informatics")
set(EXTENSION_CONTRIBUTORS "Christian Herz (SPL, BWH), Andrey Fedorov (SPL, BWH)")
set(EXTENSION_DESCRIPTION "Simplified widget for accessing volumes and labelmaps displayed in slice views.

This extension provides a user interface with buttons organized the same way as the Slicer slice views are aligned. The user can directly select foreground/background volume and label map to be displayed in the associated slice view.")
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

set(DEPENDENCIES_ADDITIONAL_MODULE_PATHS
  ${SlicerDevelopmentToolbox_DIR}/${Slicer_QTSCRIPTEDMODULES_LIB_DIR}
  )

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
  WITH_GENERIC_TESTS
  )

#-----------------------------------------------------------------------------
if(BUILD_TESTING)
  add_subdirectory(Testing)
endif()

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
