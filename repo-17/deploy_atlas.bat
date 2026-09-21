@echo off
rem ============================================================
rem  ATLAS -> permanent public site. One step.
rem  Usage:  deploy_atlas.bat https://github.com/USERNAME/REPO.git
rem ============================================================
if "%~1"=="" (
  echo.
  echo   First: github.com -^> New repository ^(public, name e.g. "atlas"^)
  echo   Then:  deploy_atlas.bat https://github.com/USERNAME/REPO.git
  echo.
  pause & exit /b 1
)
cd /d "%~dp0"
git remote remove origin 2>nul
git remote add origin %~1
git push -u origin master
echo.
echo   Pushed. One last click in the browser:
echo     Repo -^> Settings -^> Pages -^> Branch: master /(root)^ -^> Save
echo   Your permanent address in ~2 minutes:
echo     https://USERNAME.github.io/REPO/
echo.
pause
