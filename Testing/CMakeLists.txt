set(PYTHON_TEST_SCRIPTS
  ${MODULE_NAME}Tests.py
  )

foreach(python_script ${PYTHON_TEST_SCRIPTS})
  slicer_add_python_unittest(
  SCRIPT ${python_script}
  SLICER_ARGS --additional-module-paths
    ${CMAKE_BINARY_DIR}/${Slicer_QTSCRIPTEDMODULES_LIB_DIR}
    ${DEPENDENCIES_ADDITIONAL_MODULE_PATHS}
  )
endforeach(python_script)

slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}SelfTests
  SCRIPTS ${MODULE_NAME}Tests.py
)
