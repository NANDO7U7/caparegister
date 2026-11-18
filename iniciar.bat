@echo off
setlocal
pushd "%~dp0" || goto error
if not exist ".venv\Scripts\activate.bat" (
    echo Primero ejecuta instalar.bat para preparar el entorno de SIGECAP.
    goto fail
)
if not exist ".venv\Scripts\python.exe" (
    echo Falta el ejecutable de Python del entorno. Pide a soporte que repare .venv.
    goto fail
)
call ".venv\Scripts\activate.bat" || goto fail
".venv\Scripts\python.exe" "sigecap\local_windows.py" iniciar || goto fail
popd
exit /b 0

:fail
popd
:error
echo No se pudo iniciar SIGECAP. Revisa el mensaje anterior.
pause
exit /b 1
