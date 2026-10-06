@echo off

for /r "%~dp0" %%F in (normalize.py) do (
    if exist "%%~fF" (
        pushd "%%~dpF" || exit /b 1
        py -3 "%%~fF"
        if errorlevel 1 (
            popd
            exit /b 1
        )
        popd
    )
)

echo Done.
pause