@echo off
rem ATLAS - one click and the database WORKS:
rem   1) live searchable website on this machine (browser, SQL, filters)
rem   2) watcher: new files in D:\Database / D:\Audits / attachments -> auto-rebuild
cd /d "%~dp0"
set SCRIPTS=C:\Users\ZAFLA\AppData\Roaming\Python\Python314\Scripts
start "ATLAS-web" cmd /k "%SCRIPTS%\datasette.exe atlas.db -m metadata.json --cors -p 8001"
start "ATLAS-watch" cmd /k "python atlas_watch.py"
echo.
echo   ATLAS is running:
echo     website  -^>  http://localhost:8001
echo     watcher  -^>  rebuilds the DB every 5 min when files change
echo.
echo   Close the two black windows to stop.
pause
