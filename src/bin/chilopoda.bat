@ECHO OFF
@title=Chilopoda Output
cd %~dp0
REM rem library
pushd ..
set PYTHONPATH=%CD%\lib;%PYTHONPATH%
popd

REM figuring out which python is going to be used for the
REM execution
IF "%CHILOPODA_PYTHON_EXECUTABLE%"=="" (
    set CHILOPODA_PYTHON_EXECUTABLE=python
)

REM executing GUI
%CHILOPODA_PYTHON_EXECUTABLE% %~dp0chilopoda-gui.py %*
