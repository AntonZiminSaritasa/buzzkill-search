# File Search App

A fast and efficient file search application with instant search capabilities and file content preview.

## Features

- **Instant Search**: Real-time file search as you type
- **File Content Preview**: View file contents with line numbers
- **Directory Navigation**: Easy directory selection and navigation
- **File Size Limits**: Automatic handling of large files (>10MB)
- **Status Bar**: Shows full file path of selected files
- **File Explorer Integration**: Quick access to files in Windows Explorer
- **Last Directory Memory**: Remembers your last searched directory
- **Modern UI**: Clean and intuitive interface with proper styling

## Requirements

- Python 3.x
- Windows OS (uses Windows-specific features for file explorer integration)
- Required Python packages:
  - `tkinter` (usually comes with Python)
  - `pathlib` (usually comes with Python)

## How It Works

1. **Search Interface**:
   - Enter your search term in the search box
   - Results appear instantly as you type
   - Files are filtered based on your search term

2. **File Selection**:
   - Click on any file in the results list to view its contents
   - The full file path is shown in the status bar
   - Use the "Reveal in Explorer" button to open the file location

3. **Content Display**:
   - File contents are shown with line numbers
   - Large files (>10MB) are automatically truncated
   - Horizontal and vertical scrolling support
   - Syntax highlighting for better readability

4. **Directory Management**:
   - Use the "Browse" button to select search directories
   - The app remembers your last searched directory
   - Directory selection is saved between sessions

## Usage

1. Launch the application
2. Select a directory to search in (or use the last used directory)
3. Type your search term in the search box
4. Click on files in the results list to view their contents
5. Use the "Reveal in Explorer" button to open file locations

## Technical Details

- Uses Tkinter for the GUI
- Implements efficient file searching with pathlib
- Handles large files gracefully with chunked reading
- Maintains a clean separation between UI and search logic
- Uses threading to prevent UI freezing during searches

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

Anton Zimin 