$ErrorActionPreference = "Stop"
.\.venv\Scripts\python.exe -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Tests failed" }
Remove-Item -Recurse -Force dist, build -ErrorAction SilentlyContinue
.\.venv\Scripts\python.exe -m PyInstaller `
  --onefile --windowed --name OmniConvert `
  --collect-all imageio_ffmpeg `
  main.py
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }
Write-Host "Built: dist\OmniConvert.exe"