# How to Compile and Execute GooglePhotosMatcher

## Prerequisites

1. **Python 3.7 or higher** installed on your system
2. **pip** (Python package manager)

## Option 1: Run Directly with Python (Quick Testing)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the program:**
   ```bash
   cd files
   python window.py
   ```

## Option 2: Compile to Executable (.exe)

This creates a standalone executable that doesn't require Python to be installed.

1. **Install dependencies including PyInstaller:**
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```

2. **Compile the program:**
   ```bash
   cd files
   pyinstaller --onefile --windowed --icon=photos.ico --name=GPMatcher window.py
   ```

   Explanation of flags:
   - `--onefile`: Creates a single executable file
   - `--windowed`: Hides the console window (GUI only)
   - `--icon=photos.ico`: Sets the application icon
   - `--name=GPMatcher`: Names the output file

3. **Find the executable:**
   - The compiled `.exe` will be in the `files/dist/` folder
   - Copy `GPMatcher.exe` to the root directory if desired

4. **Run the executable:**
   - Double-click `GPMatcher.exe` or run from command line:
   ```bash
   dist\GPMatcher.exe
   ```

## Troubleshooting

### Missing Dependencies
If you get import errors, ensure all dependencies are installed:
```bash
pip install Pillow PySimpleGUI piexif win32-setctime
```

### Video Metadata (Optional)
For video metadata support, install ffmpeg:
- Download from: https://ffmpeg.org/download.html
- Add ffmpeg to your system PATH
- If ffmpeg is not available, videos will still be processed but without embedded metadata

### Windows-Specific
- This tool is designed for Windows systems
- The `win32-setctime` dependency is Windows-only

## Quick Start

**For developers/testing:**
```bash
pip install -r requirements.txt
cd files
python window.py
```

**For distribution:**
```bash
pip install -r requirements.txt pyinstaller
cd files
pyinstaller --onefile --windowed --icon=photos.ico --name=GPMatcher window.py
```

The executable will be in `files/dist/GPMatcher.exe`
