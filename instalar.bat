@echo off
setlocal
pushd "%~dp0" || goto error
if exist ".venv\Scripts\python.exe" goto dependencies
if exist ".venv" (
    echo El entorno .venv esta incompleto. Pide a soporte que lo repare.
    goto fail
)
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)" >nul 2>&1
if not errorlevel 1 (
    py -3 -m venv ".venv" || goto fail
    goto dependencies
)
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)" >nul 2>&1
if errorlevel 1 (
    echo Instala Python 3.12 o posterior y habilita py o python en PATH.
    goto fail
)
python -m venv ".venv" || goto fail

:dependencies
".venv\Scripts\python.exe" -c "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)" >nul 2>&1
if errorlevel 1 (
    echo El Python de .venv no funciona o es anterior a 3.12. Pide a soporte que lo repare.
    goto fail
)
".venv\Scripts\python.exe" -m pip install -r "sigecap\requirements.txt" || goto fail
".venv\Scripts\python.exe" -m pip check || goto fail
".venv\Scripts\python.exe" "sigecap\local_windows.py" instalar || goto fail
echo Para abrir SIGECAP, haz doble clic en iniciar.bat.
popd
pause
exit /b 0

:fail
popd
:error
echo No se completo la instalacion de SIGECAP. Revisa el mensaje anterior.
pause
exit /b 1
