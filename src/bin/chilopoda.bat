@ECHO OFF
cd %~dp0

REM rem library
pushd ..
set PYTHONPATH=%CD%\lib;%PYTHONPATH%
popd

REM figuring out which python is going to be used for the
REM execution
IF [%CHILOPODA_PYTHON_EXECUTABLE%] == [] (
    set CHILOPODA_PYTHON_EXECUTABLE=python
)

REM in case chilopoda command is not defined we run the cli
IF [%chilopodaCommand%] == [] (
    set chilopodaCommand="import chilopoda; chilopoda.init()"
)

REM executing GUI
%CHILOPODA_PYTHON_EXECUTABLE% -c %chilopodaCommand% %*
