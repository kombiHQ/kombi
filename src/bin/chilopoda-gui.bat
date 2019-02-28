@ECHO OFF
@title=Chilopoda Output

REM chilopoda ui command
set chilopodaCommand="import chilopodaqt; chilopodaqt.init()"

cd %~dp0
call chilopoda.bat %*
