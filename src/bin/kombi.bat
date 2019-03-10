@ECHO OFF
cd %~dp0

REM rem library
pushd ..
set PYTHONPATH=%CD%\lib;%PYTHONPATH%
popd

REM figuring out which python is going to be used for the
REM execution
IF [%KOMBI_PYTHON_EXECUTABLE%] == [] (
    set KOMBI_PYTHON_EXECUTABLE=python
)

REM in case kombi command is not defined we run the cli
IF [%kombiCommand%] == [] (
    set kombiCommand="import kombi; kombi.init()"
)

REM executing GUI
%KOMBI_PYTHON_EXECUTABLE% -c %kombiCommand% %*
