@echo off
echo ===========================================
echo 1/3 Running Python generator script...
echo ===========================================
python generate_pages.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Python generator script failed. Deployment aborted.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ===========================================
echo 2/3 Committing updated files to Git...
echo ===========================================
git add .
git commit -m "Update site layout, fixed links, and refreshed archive pages"

echo.
echo ===========================================
echo 3/3 Pushing changes to remote repository...
echo ===========================================
git push origin HEAD

echo.
echo ===========================================
echo Complete! Pushed to GitHub.
echo ===========================================
pause