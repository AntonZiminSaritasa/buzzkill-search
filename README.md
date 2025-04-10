# Buzzkill Search

**Disclaimer**: All code in this project is written by Cursor AI. The project is licensed under the MIT License.

Note: Three files in this project were created by a human:
- `.gitignore`
- `prompts.md`
- `2025-03-27_145518.png`

A fast file search utility for Windows that allows you to search through files by content and name.

![Buzzkill Search Screenshot](2025-03-27_145518.png)

## Features

- Fast file search using parallel processing
- File content preview with line numbers
- File name filtering using glob patterns (e.g., *.txt, *.py)
- Recent directories list
- Binary file detection and skipping
- Support for various text encodings
- Responsive UI with proper error handling

## Requirements

- Python 3.x
- tkinter (Python's standard GUI library)
- Windows OS or Linux with X11

## Installation

1. Clone the repository

2. Install Python and tkinter:
   - Windows: Python installer includes tkinter
   - Ubuntu/Debian:
     ```
     sudo apt-get update
     sudo apt-get install python3-tk
     ```
   - Fedora:
     ```
     sudo dnf install python3-tkinter
     ```
   - Arch Linux:
     ```
     sudo pacman -S tk
     ```

3. No additional dependencies required - the program uses only Python standard library modules

## Usage

Run the program:
```
python3 buzzkill_search.py
```

### Search Features

- Enter text in the search box to search file contents
- Use the file filter to search by file name pattern (e.g., *.txt)
- Select a directory using the "Change Directory" button
- Click on a file in the list to view its contents
- Right-click a file to reveal it in File Explorer

### File Filter Examples

- `*.txt` - Show only text files
- `*.py` - Show only Python files
- `test_*.py` - Show Python files starting with "test_"
- `*.{txt,py}` - Show both text and Python files

## Disclaimer

All code in this project is written by Cursor AI. The project is licensed under the MIT License. 