import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import os
from pathlib import Path
import threading
import queue
import json
import subprocess
from win32com.shell import shell, shellcon
import win32api
import win32con
import win32ui
import win32gui
from PIL import Image, ImageTk
import io

class LineNumberedText(tk.Text):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # Create line numbers text widget
        self.line_numbers = tk.Text(master, width=4, padx=3, takefocus=0, border=0,
                                  background='lightgray', state='disabled', wrap=tk.NONE)
        self.line_numbers.grid(row=0, column=0, sticky=(tk.N, tk.S))
        
        # Configure the main text widget
        self.grid(row=0, column=1, sticky=(tk.N, tk.S, tk.E, tk.W))
        
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
            self.line_numbers.insert(tk.END, '{0}\n'.format(i))
        self.line_numbers.config(state='disabled')
        
        # Sync scrollbars
        self.line_numbers.yview_moveto(self.yview()[0])
        
    def configure(self, **kwargs):
        super().configure(**kwargs)
        self._update_line_numbers()
        
    def update_content(self, content):
        self.delete('1.0', tk.END)
        self.insert('1.0', content)
        self._update_line_numbers()

class IconListbox(tk.Listbox):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.icons = {}  # Cache for file icons
        self.paths = {}  # Cache for full file paths
        
    def insert_with_icon(self, index, file_path):
        try:
            # Get or create icon for the file
            icon = self._get_file_icon(file_path)
            if icon:
                super().insert(index, " " + os.path.basename(file_path))  # Add space for icon
                self.icons[index] = icon
                self.paths[index] = file_path
            else:
                super().insert(index, os.path.basename(file_path))
                self.paths[index] = file_path
        except Exception as e:
            print("Error inserting file {0}: {1}".format(file_path, e))
            super().insert(index, os.path.basename(file_path))
            self.paths[index] = file_path
            
    def delete_all(self):
        self.icons.clear()
        self.paths.clear()
        self.delete(0, tk.END)
        
    def get_full_path(self, index):
        return self.paths.get(index)
        
    def _get_file_icon(self, file_path):
        try:
            # Get file info
            flags = shellcon.SHGFI_ICON | shellcon.SHGFI_SMALLICON
            file_info = shell.SHGetFileInfo(file_path, 0, flags)
            
            # Get icon handle
            icon_handle = file_info[0]
            if not icon_handle:
                return None
                
            # Create DC and bitmap
            hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
            hbmp = win32ui.CreateBitmap()
            hbmp.CreateCompatibleBitmap(hdc, 16, 16)
            hdc = hdc.CreateCompatibleDC()
            hdc.SelectObject(hbmp)
            
            # Draw icon
            win32gui.DrawIconEx(hdc.GetHandleOutput(), 0, 0, icon_handle, 16, 16, 0, None, win32con.DI_NORMAL)
            
            # Convert bitmap to bytes
            bmpstr = hbmp.GetBitmapBits(True)
            
            # Create PIL Image
            img = Image.frombuffer('RGBA', (16, 16), bmpstr, 'raw', 'BGRA', 0, 1)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)
            
            # Clean up
            win32gui.DeleteObject(hbmp.GetHandle())
            hdc.DeleteDC()
            win32gui.DestroyIcon(icon_handle)
            
            return photo
        except Exception as e:
            print("Error getting icon for {0}: {1}".format(file_path, e))
            return None

class FileSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Search")
        self.root.geometry("1200x600")
        
        # Configure root window grid weights
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)
        
        # Load last directory
        self.last_dir_file = "last_directory.json"
        self.search_path = self.load_last_directory()
        
        # Memory limits
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.max_results = 1000  # Maximum number of results to show
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure main frame grid weights
        main_frame.grid_rowconfigure(2, weight=1)
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
        
        # Search frame
        search_frame = ttk.Frame(main_frame)
        search_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Configure search frame grid weights
        search_frame.grid_columnconfigure(0, weight=1)
        
        # Search entry
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=50)
        search_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Cancel button (initially disabled)
        self.cancel_button = ttk.Button(search_frame, text="Cancel Search", command=self.cancel_search, state='disabled')
        self.cancel_button.grid(row=0, column=1, padx=(10, 0))
        
        # Left frame for list
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure left frame grid weights
        left_frame.grid_rowconfigure(0, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)
        
        # Listbox for results with icons
        self.result_list = IconListbox(left_frame, width=70, height=30, exportselection=False)
        self.result_list.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar for listbox
        list_scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.result_list.yview)
        list_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.result_list.configure(yscrollcommand=list_scrollbar.set)
        
        # Right frame for content
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        
        # Configure right frame grid weights
        right_frame.grid_rowconfigure(0, weight=1)
        right_frame.grid_columnconfigure(1, weight=1)
        
        # Text area for file content with line numbers
        self.content_text = LineNumberedText(right_frame, width=70, height=30, wrap=tk.NONE)
        
        # Add horizontal scrollbar for text area
        text_scrollbar = ttk.Scrollbar(right_frame, orient=tk.HORIZONTAL, command=self.content_text.xview)
        text_scrollbar.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E))
        self.content_text.configure(xscrollcommand=text_scrollbar.set)
        
        # Bind listbox selection event
        self.result_list.bind('<<ListboxSelect>>', self.on_select_file)
        
        # Bind right-click event
        self.result_list.bind('<Button-3>', self.show_context_menu)
        
        # Bind focus events to maintain listbox selection
        self.result_list.bind('<FocusOut>', self._on_listbox_focus_out)
        self.content_text.bind('<FocusIn>', self._on_text_focus_in)
        self.content_text.bind('<FocusOut>', self._on_text_focus_out)
        
        # Create context menu
        self.context_menu = tk.Menu(root, tearoff=0)
        self.context_menu.add_command(label="Reveal in File Explorer", command=self.reveal_in_explorer)
        
        # Store last selection
        self._last_selection = None
        
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
        
    def _on_listbox_focus_out(self, event):
        # Store the current selection
        self._last_selection = self.result_list.curselection()
        
    def _on_text_focus_in(self, event):
        # Restore the listbox selection if it exists
        if self._last_selection:
            self.result_list.selection_set(self._last_selection[0])
            self.result_list.see(self._last_selection[0])
            
    def _on_text_focus_out(self, event):
        # Restore the listbox selection if it exists
        if self._last_selection:
            self.result_list.selection_set(self._last_selection[0])
            self.result_list.see(self._last_selection[0])
            
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
            
        # Get the full file path from the paths cache
        file_path = self.result_list.get_full_path(selection[0])
        if file_path.startswith("Error:"):
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
            print("Error opening folder: {0}".format(e))
            
    def cancel_search(self):
        if self.search_running:
            self.search_running = False
            self.cancel_button.config(state='disabled')
            if self.search_thread:
                self.search_thread.join(timeout=1.0)  # Wait up to 1 second for thread to finish
            self.search_thread = None
            self.result_count = 0
            
    def load_last_directory(self):
        try:
            if os.path.exists(self.last_dir_file):
                with open(self.last_dir_file, 'r') as f:
                    data = json.load(f)
                    if os.path.exists(data.get('last_directory', '')):
                        return data['last_directory']
        except Exception:
            pass
        return "D:/Work/Cursor/cursor-test"
        
    def save_last_directory(self):
        try:
            with open(self.last_dir_file, 'w') as f:
                json.dump({'last_directory': self.search_path}, f)
        except Exception:
            pass
            
    def pick_directory(self):
        directory = filedialog.askdirectory(initialdir=self.search_path)
        if directory:
            self.search_path = directory
            self.dir_label.config(text="Search Directory: " + self.search_path)
            self.save_last_directory()
            # Clear previous results
            self.result_list.delete_all()
            self.content_text.delete('1.0', tk.END)
            self.cancel_search()  # Cancel any ongoing search
            self.result_count = 0
        
    def on_search_change(self, *args):
        # Cancel any pending search
        if self.search_after_id:
            self.root.after_cancel(self.search_after_id)
        
        # Get current search term
        search_term = self.search_var.get().strip()
        
        # If search term is empty, clear results immediately
        if not search_term:
            self.result_list.delete_all()
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
        self.result_list.delete_all()
        self.content_text.delete('1.0', tk.END)
        self.result_count = 0
        
        # Enable cancel button
        self.cancel_button.config(state='normal')
        
        # Start new search
        self.search_running = True
        self.search_thread = threading.Thread(target=self.search_files, args=(search_term,))
        self.search_thread.daemon = True
        self.search_thread.start()
        
    def search_files(self, search_term):
        try:
            for root, _, files in os.walk(self.search_path):
                if not self.search_running:
                    break
                    
                for file in files:
                    if not self.search_running:
                        break
                        
                    file_path = Path(root) / file
                    try:
                        # Check file size before reading
                        if file_path.stat().st_size > self.max_file_size:
                            continue
                            
                        # Check if we've reached the maximum number of results
                        if self.result_count >= self.max_results:
                            self.root.after(0, self.add_result, f"Maximum number of results ({self.max_results}) reached.")
                            return
                            
                        with open(file_path, 'r', encoding='utf-8') as f:
                            # Read file in chunks to save memory
                            while True:
                                chunk = f.read(8192)  # Read 8KB at a time
                                if not chunk:
                                    break
                                if search_term.lower() in chunk.lower():
                                    self.root.after(0, self.add_result, str(file_path))
                                    self.result_count += 1
                                    break
                    except (UnicodeDecodeError, PermissionError):
                        continue
        except Exception as e:
            self.root.after(0, self.add_result, "Error: {}".format(str(e)))
        finally:
            self.root.after(0, self.cancel_button.config, {'state': 'disabled'})
            
    def add_result(self, file_path):
        if self.search_running:  # Only add if search is still running
            self.result_list.insert_with_icon(tk.END, file_path)
            self.result_list.see(tk.END)
        
    def on_select_file(self, event):
        # Use a lock to prevent multiple simultaneous file selections
        if not self.file_selection_lock.acquire(blocking=False):
            return
            
        try:
            selection = self.result_list.curselection()
            if not selection:
                return
                
            # Store the selection
            self._last_selection = selection
                
            # Get the full file path from the paths cache
            file_path = self.result_list.get_full_path(selection[0])
            if not file_path:
                return
                
            if isinstance(file_path, str) and file_path.startswith("Error:"):
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
            # Check file size before reading
            if Path(file_path).stat().st_size > self.max_file_size:
                self.root.after(0, self.update_content, "File is too large to display (>10MB)")
                return
                
            with open(file_path, 'r', encoding='utf-8') as f:
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
                        
                if self.file_running:  # Only update if we haven't cancelled
                    self.root.after(0, self.update_content, ''.join(content))
        except Exception as e:
            if self.file_running:  # Only update if we haven't cancelled
                self.root.after(0, self.update_content, "Error reading file: {}".format(str(e)))
                
    def update_content(self, content):
        self.content_text.update_content(content)

if __name__ == "__main__":
    root = tk.Tk()
    app = FileSearchApp(root)
    root.mainloop() 