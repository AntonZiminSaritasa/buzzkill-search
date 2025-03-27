import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import os
from pathlib import Path
import threading
import queue
import json
import time
import subprocess

class FileSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Search")
        self.root.geometry("1200x600")
        
        # Load last directory
        self.last_dir_file = "last_directory.json"
        self.search_path = self.load_last_directory()
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Directory selection frame
        dir_frame = ttk.Frame(main_frame)
        dir_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Directory label
        self.dir_label = ttk.Label(dir_frame, text="Search Directory: " + self.search_path)
        self.dir_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Directory picker button
        dir_button = ttk.Button(dir_frame, text="Change Directory", command=self.pick_directory)
        dir_button.grid(row=0, column=1, padx=(10, 0))
        
        # Search frame
        search_frame = ttk.Frame(main_frame)
        search_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
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
        
        # Listbox for results
        self.result_list = tk.Listbox(left_frame, width=70, height=30)
        self.result_list.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar for listbox
        list_scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.result_list.yview)
        list_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.result_list.configure(yscrollcommand=list_scrollbar.set)
        
        # Right frame for content
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        
        # Text area for file content
        self.content_text = scrolledtext.ScrolledText(right_frame, width=70, height=30)
        self.content_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        dir_frame.columnconfigure(0, weight=1)
        search_frame.columnconfigure(0, weight=1)
        
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
            
        file_path = self.result_list.get(selection[0])
        if file_path.startswith("Error:"):
            return
            
        try:
            # Convert to Path object and get parent directory
            path = Path(file_path)
            folder_path = str(path.parent)
            
            # Open folder in File Explorer
            if os.name == 'nt':  # Windows
                subprocess.run(['explorer', folder_path])
            else:  # Linux/Mac
                subprocess.run(['xdg-open', folder_path])
        except Exception as e:
            print(f"Error opening folder: {e}")
            
    def cancel_search(self):
        if self.search_running:
            self.search_running = False
            self.cancel_button.config(state='disabled')
            if self.search_thread:
                self.search_thread.join(timeout=1.0)  # Wait up to 1 second for thread to finish
            self.search_thread = None
            
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
            self.result_list.delete(0, tk.END)
            self.content_text.delete('1.0', tk.END)
            self.cancel_search()  # Cancel any ongoing search
        
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
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if search_term.lower() in content.lower():
                                self.root.after(0, self.add_result, str(file_path))
                    except (UnicodeDecodeError, PermissionError):
                        continue
        except Exception as e:
            self.root.after(0, self.add_result, "Error: {}".format(str(e)))
        finally:
            self.root.after(0, self.cancel_button.config, {'state': 'disabled'})
            
    def add_result(self, file_path):
        if self.search_running:  # Only add if search is still running
            self.result_list.insert(tk.END, file_path)
            self.result_list.see(tk.END)
        
    def on_select_file(self, event):
        # Use a lock to prevent multiple simultaneous file selections
        if not self.file_selection_lock.acquire(blocking=False):
            return
            
        try:
            selection = self.result_list.curselection()
            if not selection:
                return
                
            file_path = self.result_list.get(selection[0])
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
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if self.file_running:  # Only update if we haven't cancelled
                    self.root.after(0, self.update_content, content)
        except Exception as e:
            if self.file_running:  # Only update if we haven't cancelled
                self.root.after(0, self.update_content, "Error reading file: {}".format(str(e)))
                
    def update_content(self, content):
        self.content_text.delete('1.0', tk.END)
        self.content_text.insert('1.0', content)

if __name__ == "__main__":
    root = tk.Tk()
    app = FileSearchApp(root)
    root.mainloop() 