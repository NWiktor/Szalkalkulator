ECHO OFF
chcp 65001
cls

pyinstaller --distpath ./ ^
--onefile main_prog.pyw ^
--specpath .\build\spec
