"""
Buzzkill Search - A fast file search utility

Disclaimer: All code in this project is written by Cursor AI. The project is licensed under the MIT License.
"""

import tkinter as tk
from tkinter import ttk, filedialog
import os
import json
import threading
from pathlib import Path
import subprocess
import time
import queue
import re
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import mmap

class LineNumberedText(tk.Text):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Create line numbers text widget
        self.line_numbers = tk.Text(master, width=4, padx=3, takefocus=0, border=0,
                                  background='lightgray', state='disabled', wrap=tk.NONE)
        self.line_numbers.grid(row=0, column=0, sticky=(tk.N, tk.S))
        
        # Configure the main text widget
        self.grid(row=0, column=1, sticky=(tk.N, tk.S, tk.E, tk.W))
        
        # Configure grid weights for proper resizing
        master.grid_columnconfigure(1, weight=1)
        master.grid_rowconfigure(0, weight=1)
        
        # Bind events
        self.bind('<Key>', self._on_key)
        self.bind('<MouseWheel>', self._on_mousewheel)
        self.bind('<Button-4>', self._on_mousewheel)
        self.bind('<Button-5>', self._on_mousewheel)
        
        # Store reference to listbox
        self.listbox = None
        
        # Initial line numbers
        self._update_line_numbers()
        
    def set_listbox(self, listbox):
        self.listbox = listbox
        
    def _on_key(self, event):
        self._update_line_numbers()
        return None
        
    def _on_mousewheel(self, event):
        self._update_line_numbers()
        return None
        
    def _update_line_numbers(self):
        # Get the number of lines
        lines = self.get('1.0', tk.END).count('\n')
        
        # Update line numbers
        self.line_numbers.config(state='normal')
        self.line_numbers.delete('1.0', tk.END)
        for i in range(1, lines + 1):
            self.line_numbers.insert(tk.END, f'{i}\n')
        self.line_numbers.config(state='disabled')
        
        # Sync scrollbars
        self.line_numbers.yview_moveto(self.yview()[0])
        
    def configure(self, **kwargs):
        super().configure(**kwargs)
        self._update_line_numbers()
        
    def update_content(self, content):
        try:
            # Enable text widget temporarily
            self.configure(state='normal')
            
            # Clear existing content
            self.delete('1.0', tk.END)
            
            # Insert new content
            self.insert('1.0', content)
            
            # Update line numbers
            self._update_line_numbers()
            
            # Ensure the text area is visible
            self.see('1.0')
            
            # Make text widget read-only again
            self.configure(state='disabled')
            
        except Exception as e:
            print(f"Error updating content: {e}")

class FileSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Buzzkill Search")
        self.root.geometry("1200x600")
        
        # Configure root window grid weights
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)
        
        # Load last directory and recent directories
        self.last_dir_file = os.path.join(os.path.expanduser("~"), ".buzzkill_search", "last_directory.json")
        self.search_path = self.load_last_directory()
        self.recent_dirs = self.load_recent_directories()
        
        # Memory limits
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.max_results = 1000  # Maximum number of results to show
        
        # Initialize file paths dictionary
        self.file_paths = {}
        
        # Spinner
        self.spinner_running = False
        self.spinner_index = 0
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure main frame grid weights
        main_frame.grid_rowconfigure(3, weight=1)  # Changed from 2 to 3 to match new layout
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)
        
        # Directory selection frame
        dir_frame = ttk.Frame(main_frame)
        dir_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Configure dir frame grid weights
        dir_frame.grid_columnconfigure(0, weight=1)
        
        # Directory label
        self.dir_label = ttk.Label(dir_frame, text="Search Directory: " + self.search_path)
        self.dir_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Directory picker button
        dir_button = ttk.Button(dir_frame, text="Change Directory", command=self.pick_directory)
        dir_button.grid(row=0, column=1, padx=(10, 0))
        dir_button.configure(state='normal')  # Ensure button is enabled
        
        # Search frame
        search_frame = ttk.Frame(main_frame)
        search_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Configure search frame grid weights
        search_frame.grid_columnconfigure(0, weight=1)
        search_frame.grid_columnconfigure(1, weight=1)
        
        # Search entry
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=50)
        search_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # File name filter entry
        self.filter_var = tk.StringVar()
        self.filter_var.trace('w', self.on_search_change)
        filter_label = ttk.Label(search_frame, text="File filter:")
        filter_label.grid(row=0, column=1, sticky=(tk.W), padx=(10, 5))
        filter_entry = ttk.Entry(search_frame, textvariable=self.filter_var, width=20)
        filter_entry.grid(row=0, column=2, sticky=(tk.W, tk.E))
        
        # Cancel button (initially disabled)
        self.cancel_button = ttk.Button(search_frame, text="Cancel Search", command=self.cancel_search, state='disabled')
        self.cancel_button.grid(row=0, column=3, padx=(10, 0))
        
        # Left frame for list
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure left frame grid weights
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        
        # Listbox for results
        self.result_list = tk.Listbox(left_frame, width=70, height=30, exportselection=False)
        self.result_list.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar for listbox
        list_scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.result_list.yview)
        list_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.result_list.configure(yscrollcommand=list_scrollbar.set)
        
        # Right frame for content
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=3, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        
        # Configure right frame grid weights
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_columnconfigure(1, weight=1)  # Changed from 0 to 1 to match LineNumberedText layout
        
        # Text area for file content with line numbers
        self.content_text = LineNumberedText(right_frame, width=70, height=30, wrap=tk.NONE)
        
        # Add vertical scrollbar for text area
        text_v_scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.content_text.yview)
        text_v_scrollbar.grid(row=0, column=2, sticky=(tk.N, tk.S))
        self.content_text.configure(yscrollcommand=text_v_scrollbar.set)
        
        # Add horizontal scrollbar for text area
        text_scrollbar = ttk.Scrollbar(right_frame, orient=tk.HORIZONTAL, command=self.content_text.xview)
        text_scrollbar.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E))  # Updated columnspan to include vertical scrollbar
        self.content_text.configure(xscrollcommand=text_scrollbar.set)
        
        # Add status bar at the bottom
        self.status_bar = ttk.Label(main_frame, text="", anchor=tk.W, padding=(5, 2))
        self.status_bar.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Configure text area with proper styling
        self.content_text.configure(
            font=('Courier', 10),
            background='white',
            foreground='black',
            insertbackground='black',
            selectbackground='#0078D7',
            selectforeground='white'
        )
        self.content_text.line_numbers.configure(
            font=('Courier', 10),
            background='#F0F0F0',
            foreground='#666666'
        )
        
        # Test text display
        self.content_text.delete('1.0', tk.END)
        self.content_text.insert('1.0', "Ready to display file content...")
        self.content_text._update_line_numbers()
        
        # Bind listbox selection event
        self.result_list.bind('<<ListboxSelect>>', self.on_select_file)
        
        # Bind right-click event
        self.result_list.bind('<Button-3>', self.show_context_menu)
        
        # Create context menu
        self.context_menu = tk.Menu(root, tearoff=0)
        self.context_menu.add_command(label="Reveal in File Explorer", command=self.reveal_in_explorer)
        
        # Search queue and thread
        self.search_queue = queue.Queue()
        self.search_thread = None
        self.search_running = False
        
        # File reading queue and thread
        self.file_queue = queue.Queue()
        self.file_thread = None
        self.file_running = False
        
        # Search debouncing
        self.search_after_id = None
        self.last_search_term = ""
        
        # File selection lock
        self.file_selection_lock = threading.Lock()
        
        # Result counter
        self.result_count = 0
        
    def show_context_menu(self, event):
        # Get the index of the item under the cursor
        index = self.result_list.nearest(event.y)
        if index >= 0:
            self.result_list.selection_clear(0, tk.END)
            self.result_list.selection_set(index)
            self.context_menu.post(event.x_root, event.y_root)
            
    def reveal_in_explorer(self):
        selection = self.result_list.curselection()
        if not selection:
            return
            
        # Get the full path from our dictionary
        index = selection[0]
        file_path = self.file_paths.get(index)
        if not file_path or file_path.startswith("Error:"):
            return
            
        try:
            # Convert to Path object and get absolute path
            path = Path(file_path).resolve()
            
            # Open folder in File Explorer with file selected
            if os.name == 'nt':  # Windows
                subprocess.run(['explorer', '/select,', str(path)])
            else:  # Linux/Mac
                subprocess.run(['xdg-open', str(path.parent)])
        except Exception as e:
            print(f"Error opening folder: {e}")
            
    def cancel_search(self):
        if self.search_running:
            self.search_running = False
            self.cancel_button.config(state='disabled')
            if self.search_thread:
                self.search_thread.join(timeout=1.0)  # Wait up to 1 second for thread to finish
            self.search_thread = None
            self.result_count = 0
            # Stop spinner
            self.spinner_running = False
            self.status_bar.config(text="")
            
    def load_last_directory(self):
        try:
            if os.path.exists(self.last_dir_file):
                with open(self.last_dir_file, 'r') as f:
                    data = json.load(f)
                    if os.path.exists(data.get('last_directory', '')):
                        return data['last_directory']
        except Exception:
            pass
        return str(Path.home() / "Documents")
        
    def save_last_directory(self):
        try:
            with open(self.last_dir_file, 'w') as f:
                json.dump({'last_directory': self.search_path}, f)
        except Exception:
            pass
            
    def load_recent_directories(self):
        try:
            if os.path.exists(self.last_dir_file):
                with open(self.last_dir_file, 'r') as f:
                    data = json.load(f)
                    return data.get('recent_directories', [])
        except Exception:
            pass
        return []
        
    def save_recent_directories(self):
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.last_dir_file), exist_ok=True)
            
            # Load existing data
            data = {}
            if os.path.exists(self.last_dir_file):
                with open(self.last_dir_file, 'r') as f:
                    data = json.load(f)
            
            # Update recent directories
            if self.search_path not in self.recent_dirs:
                self.recent_dirs.insert(0, self.search_path)
                # Keep only the 5 most recent directories
                self.recent_dirs = self.recent_dirs[:5]
            
            # Save updated data
            data['last_directory'] = self.search_path
            data['recent_directories'] = self.recent_dirs
            
            with open(self.last_dir_file, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Error saving recent directories: {e}")
            
    def pick_directory(self):
        try:
            # Create a popup menu for recent directories
            menu = tk.Menu(self.root, tearoff=0)
            
            # Add recent directories to menu
            for dir_path in self.recent_dirs:
                if dir_path != self.search_path:  # Don't add current directory
                    menu.add_command(label=dir_path, command=lambda d=dir_path: self.select_directory(d))
            
            # Add separator and browse option
            menu.add_separator()
            menu.add_command(label="Browse...", command=self.browse_directory)
            
            # Get button position
            button = self.root.focus_get()
            if button:
                x = button.winfo_rootx()
                y = button.winfo_rooty() + button.winfo_height()
                menu.post(x, y)
            else:
                # If no button focused, show menu at mouse position
                menu.post(self.root.winfo_pointerx(), self.root.winfo_pointery())
                
        except Exception as e:
            print(f"Error showing directory menu: {e}")
            
    def select_directory(self, directory):
        if os.path.exists(directory):
            self.search_path = directory
            self.dir_label.config(text="Search Directory: " + self.search_path)
            self.save_recent_directories()
            # Clear previous results
            self.result_list.delete(0, tk.END)
            self.content_text.delete('1.0', tk.END)
            self.cancel_search()  # Cancel any ongoing search
            self.result_count = 0
            
    def browse_directory(self):
        directory = filedialog.askdirectory(initialdir=self.search_path)
        if directory:
            self.select_directory(directory)
        
    def on_search_change(self, *args):
        # Cancel any pending search
        if self.search_after_id:
            self.root.after_cancel(self.search_after_id)
        
        # Get current search term
        search_term = self.search_var.get().strip()
        
        # If search term is empty, clear results immediately
        if not search_term:
            self.result_list.delete(0, tk.END)
            self.content_text.delete('1.0', tk.END)
            self.cancel_search()
            self.last_search_term = ""
            self.result_count = 0
            return
            
        # If search term hasn't changed, don't search again
        if search_term == self.last_search_term:
            return
            
        # Schedule new search after delay
        self.search_after_id = self.root.after(500, self.perform_search, search_term)
        
    def perform_search(self, search_term):
        # Update last search term
        self.last_search_term = search_term
        
        # Cancel any running search
        self.cancel_search()
        
        # Clear previous results
        self.result_list.delete(0, tk.END)
        self.content_text.delete('1.0', tk.END)
        self.result_count = 0
        
        # Enable cancel button
        self.cancel_button.config(state='normal')
        
        # Start spinner
        self.spinner_running = True
        self.update_spinner()
        
        # Start new search
        self.search_running = True
        self.search_thread = threading.Thread(target=self.search_files, args=(search_term,))
        self.search_thread.daemon = True
        self.search_thread.start()
        
    def search_files(self, search_term):
        try:
            # Convert search term to lowercase once
            search_term_lower = search_term.lower()
            
            # Get file name filter pattern
            filter_pattern = self.filter_var.get().strip()
            if filter_pattern:
                # Convert glob pattern to regex
                filter_pattern = filter_pattern.replace('*', '.*').replace('?', '.')
                filter_regex = re.compile(filter_pattern, re.IGNORECASE)
            
            # Create sets for fast lookups
            skip_extensions = {'.exe', '.dll', '.pdb', '.cache', '.tmp', '.log', '.bin', '.dat', '.sys', '.msi', '.cab', '.zip', '.rar', '.7z', '.iso', '.img', '.vhd', '.vhdx', '.sdb', '.mui', '.ttf', '.mkv', '.wav', '.raw', '.etl'}
            skip_dirs = {'System32', 'SysWOW64', 'WinSxS', 'assembly', 'Microsoft.NET', 'WindowsApps', 'Installer', 'SoftwareDistribution', 'Prefetch', 'Temp'}
            
            # Create a thread pool for parallel processing
            def process_file(file_path):
                try:
                    # Skip binary and system files early
                    if file_path.suffix.lower() in skip_extensions:
                        return None
                        
                    # Check file size before reading
                    if file_path.stat().st_size > self.max_file_size:
                        return None
                        
                    # Skip empty files
                    if file_path.stat().st_size == 0:
                        return None
                        
                    # Apply file name filter if specified
                    if filter_pattern and not filter_regex.match(file_path.name):
                        return None
                        
                    # Check filename first for faster filtering
                    if search_term_lower in file_path.name.lower():
                        return str(file_path)
                        
                    # For content search, use memory mapping for better performance
                    with open(file_path, 'rb') as f:
                        # Memory map the file for faster reading
                        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                            # Search in chunks of 1MB for better performance
                            chunk_size = 1024 * 1024
                            offset = 0
                            while True:
                                chunk = mm.read(chunk_size)
                                if not chunk:
                                    break
                                # Convert chunk to string once and search
                                chunk_str = chunk.decode('utf-8', errors='ignore')
                                if search_term_lower in chunk_str.lower():
                                    return str(file_path)
                                offset += len(chunk)
                except (UnicodeDecodeError, PermissionError, OSError):
                    pass
                return None

            # Walk through directories and collect files
            files_to_process = []
            search_path = Path(self.search_path).resolve()
            for root, dirs, files in os.walk(str(search_path)):
                if not self.search_running:
                    break
                    
                # Skip system directories
                dirs[:] = [d for d in dirs if d not in skip_dirs]
                
                for file in files:
                    if not self.search_running:
                        break
                    file_path = Path(root) / file
                    files_to_process.append(file_path)
                    
                    # Check if we've reached the maximum number of results
                    if self.result_count >= self.max_results:
                        break

            # Process files in parallel using a thread pool
            with ThreadPoolExecutor(max_workers=min(32, len(files_to_process))) as executor:
                future_to_file = {executor.submit(process_file, file_path): file_path 
                                for file_path in files_to_process}
                
                for future in as_completed(future_to_file):
                    if not self.search_running:
                        break
                        
                    result = future.result()
                    if result:
                        self.root.after(0, self.add_result, result)
                        self.result_count += 1
                        
                        # Check if we've reached the maximum number of results
                        if self.result_count >= self.max_results:
                            break

        except Exception as e:
            self.root.after(0, self.add_result, f"Error: {str(e)}")
        finally:
            self.root.after(0, self.cancel_button.config, {'state': 'disabled'})
            # Stop spinner
            self.root.after(0, lambda: setattr(self, 'spinner_running', False))
            self.root.after(0, lambda: self.status_bar.config(text=""))
            
    def add_result(self, file_path):
        if self.search_running:  # Only add if search is still running
            try:
                # Store full path in a dictionary using index as key
                index = self.result_list.size()
                if not hasattr(self, 'file_paths'):
                    self.file_paths = {}
                self.file_paths[index] = str(file_path)
                
                # Insert just the filename in the listbox
                self.result_list.insert(tk.END, os.path.basename(file_path))
                self.result_list.see(tk.END)
            except Exception as e:
                print(f"Error adding result: {e}")
        
    def on_select_file(self, event):
        # Use a lock to prevent multiple simultaneous file selections
        if not self.file_selection_lock.acquire(blocking=False):
            return
            
        try:
            selection = self.result_list.curselection()
            if not selection:
                self.status_bar.config(text="")
                return
                
            # Get the full path from our dictionary
            index = selection[0]
            file_path = self.file_paths.get(index)
            if not file_path:
                self.status_bar.config(text="")
                return
                
            # Update status bar with full path
            self.status_bar.config(text=file_path)
                
            if file_path.startswith("Error:"):
                self.content_text.delete('1.0', tk.END)
                self.content_text.insert('1.0', file_path)
                return
                
            # Cancel previous file reading if running
            if self.file_running:
                self.file_running = False
                if self.file_thread:
                    self.file_thread.join(timeout=1.0)  # Wait up to 1 second for thread to finish
                self.file_thread = None
            
            # Clear previous content
            self.content_text.delete('1.0', tk.END)
            self.content_text.insert('1.0', "Loading file...")
            
            # Start new file reading thread
            self.file_running = True
            self.file_thread = threading.Thread(target=self.read_file_content, args=(file_path,))
            self.file_thread.daemon = True
            self.file_thread.start()
        finally:
            self.file_selection_lock.release()
        
    def read_file_content(self, file_path):
        try:
            print(f"Reading file: {file_path}")
            # Check file size before reading
            if Path(file_path).stat().st_size > self.max_file_size:
                print("File too large")
                self.root.after(0, lambda: self.content_text.update_content("File is too large to display (>10MB)"))
                return
                
            # Try different encodings in order of preference
            encodings = ['utf-8', 'cp1252', 'latin1', 'iso-8859-1']
            content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        # Read file in chunks to save memory
                        content = []
                        while True:
                            chunk = f.read(8192)  # Read 8KB at a time
                            if not chunk:
                                break
                            content.append(chunk)
                            if len(''.join(content)) > self.max_file_size:
                                content = [''.join(content)[:self.max_file_size] + "\n... (file truncated)"]
                                break
                    break  # If we get here, the encoding worked
                except UnicodeDecodeError:
                    continue  # Try next encoding
                    
            if content is None:
                raise UnicodeDecodeError(f"Could not decode file with any of the encodings: {encodings}")
                        
            if self.file_running:  # Only update if we haven't cancelled
                print(f"Updating content for {file_path}")
                final_content = ''.join(content)
                print(f"Content length: {len(final_content)}")
                self.root.after(0, lambda: self.content_text.update_content(final_content))
        except Exception as e:
            error_msg = str(e)
            print(f"Error reading file {file_path}: {error_msg}")
            if self.file_running:  # Only update if we haven't cancelled
                self.root.after(0, lambda msg=error_msg: self.content_text.update_content(f"Error reading file: {msg}"))
                
    def update_spinner(self):
        if self.spinner_running:
            self.spinner_index = (self.spinner_index + 1) % len(self.spinner_chars)
            self.status_bar.config(text=f"Searching... {self.spinner_chars[self.spinner_index]}")
            self.root.after(100, self.update_spinner)

if __name__ == "__main__":
    root = tk.Tk()
    app = FileSearchApp(root)
    root.mainloop() 