@echo off
pyinstaller WQBookDownloader.spec
python copy_version.py