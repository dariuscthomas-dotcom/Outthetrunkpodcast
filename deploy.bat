@echo off
echo ===========================================
echo 1/3 Running Python generator script...
echo ===========================================
python generate_pages.py

echo.
echo ===========================================
echo 2/3 Committing updated files to Git...
echo ===========================================
git add .
git commit -m "Update site layout, host hierarchy, and archives"

echo.
echo ===========================================
echo 3/3 Pushing changes to remote repository...
echo ===========================================
git push

echo.
echo ===========================================
echo Complete! Pushed to GitHub.
echo ===========================================
pause