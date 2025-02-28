@ECHO OFF
@title=Kombi Output

REM kombi ui command
set kombiCommand="import kombiqt; kombiqt.init()"

cd %~dp0
call kombi.bat %*
