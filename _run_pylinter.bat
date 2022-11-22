ECHO OFF
chcp 65001
cls


:loop
cls
pylint main_prog.pyw --output-format=colorized
pause
goto loop
