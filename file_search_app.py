import tkinter as tk
from tkinter import ttk, scrolledtext
import os
from pathlib import Path
import threading
import queue

class FileSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Search")
        self.root.geometry("1200x600")
        
        # Create main frame
        main_frame = ttk.Frame(root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Search entry
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search_change)
        search_entry = ttk.Entry(main_frame, textvariable=self.search_var, width=50)
        search_entry.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Left frame for list
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Listbox for results
        self.result_list = tk.Listbox(left_frame, width=70, height=30)
        self.result_list.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar for listbox
        list_scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.result_list.yview)
        list_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.result_list.configure(yscrollcommand=list_scrollbar.set)
        
        # Right frame for content
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        
        # Text area for file content
        self.content_text = scrolledtext.ScrolledText(right_frame, width=70, height=30)
        self.content_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        
        # Bind listbox selection event
        self.result_list.bind('<<ListboxSelect>>', self.on_select_file)
        
        # Search queue and thread
        self.search_queue = queue.Queue()
        self.search_thread = None
        self.search_running = False
        
    def on_search_change(self, *args):
        search_term = self.search_var.get().strip()
        if search_term:
            self.start_search(search_term)
        else:
            self.result_list.delete(0, tk.END)
            self.content_text.delete('1.0', tk.END)
            
    def start_search(self, search_term):
        # Cancel previous search if running
        if self.search_running:
            self.search_running = False
            if self.search_thread:
                self.search_thread.join()
        
        # Clear previous results
        self.result_list.delete(0, tk.END)
        self.content_text.delete('1.0', tk.END)
        
        # Start new search
        self.search_running = True
        self.search_thread = threading.Thread(target=self.search_files, args=(search_term,))
        self.search_thread.daemon = True
        self.search_thread.start()
        
    def search_files(self, search_term):
        search_path = Path("D:/Work/Cursor/cursor-test")
        try:
            for root, _, files in os.walk(search_path):
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
            
    def add_result(self, file_path):
        self.result_list.insert(tk.END, file_path)
        self.result_list.see(tk.END)
        
    def on_select_file(self, event):
        selection = self.result_list.curselection()
        if not selection:
            return
            
        file_path = self.result_list.get(selection[0])
        if file_path.startswith("Error:"):
            self.content_text.delete('1.0', tk.END)
            self.content_text.insert('1.0', file_path)
            return
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.content_text.delete('1.0', tk.END)
                self.content_text.insert('1.0', content)
        except Exception as e:
            self.content_text.delete('1.0', tk.END)
            self.content_text.insert('1.0', "Error reading file: {}".format(str(e)))

if __name__ == "__main__":
    root = tk.Tk()
    app = FileSearchApp(root)
    root.mainloop() 