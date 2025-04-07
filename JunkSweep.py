import sys
import subprocess
import importlib
import os
import time
import logging
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import shutil

# Setup logging
logging.basicConfig(filename='junksweep.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# List of required modules
REQUIRED_MODULES = ['pyinstaller', 'tkinter', 'subprocess', 'importlib', 'threading', 'shutil']

# Function to check and install modules
def install_module(module_name):
    try:
        importlib.import_module(module_name)
        logging.info(f"{module_name} is already installed")
    except ImportError:
        print(f"{module_name} not found. Attempting to install...")
        logging.info(f"Installing {module_name}")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", module_name])
            print(f"{module_name} installed successfully!")
            logging.info(f"{module_name} installed")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {module_name}: {e}")
            logging.error(f"Failed to install {module_name}: {e}")
            sys.exit(1)

# Auto-install all required modules if running as .py
def check_and_install_modules():
    if not getattr(sys, 'frozen', False):  # Only run when not frozen (i.e., not .exe)
        for module in REQUIRED_MODULES:
            install_module(module)

# Function to build the .exe using PyInstaller
def build_exe():
    exe_path = os.path.join(os.path.dirname(__file__), "dist", "JunkSweep.exe")
    if not os.path.exists(exe_path):
        print("Building JunkSweep.exe with PyInstaller...")
        logging.info("Starting PyInstaller build")
        try:
            pyinstaller_path = os.path.join(os.path.dirname(sys.executable), "Scripts", "pyinstaller.exe")
            if not os.path.exists(pyinstaller_path):
                print("PyInstaller executable not found.")
                logging.error("PyInstaller not found at expected path")
                sys.exit(1)
            
            cmd = [
                pyinstaller_path,
                "--onefile",
                "--noconsole",
                "--hidden-import=tkinter",
                "--hidden-import=subprocess",
                "--hidden-import=importlib",
                os.path.abspath(__file__)
            ]
            subprocess.run(cmd, check=True)
            print(f"JunkSweep.exe created at: {exe_path}")
            logging.info(f"JunkSweep.exe built successfully at {exe_path}")
            time.sleep(2)
            if os.path.exists(exe_path):
                subprocess.Popen([exe_path])
                sys.exit(0)
        except subprocess.CalledProcessError as e:
            print(f"Failed to build JunkSweep.exe: {e}")
            logging.error(f"PyInstaller failed: {e}")
            sys.exit(1)
    else:
        print("JunkSweep.exe already exists. Proceeding...")
        logging.info("JunkSweep.exe already exists, skipping build")

# Check and install modules, then build .exe if running as .py
if not getattr(sys, 'frozen', False):  # Running as .py
    check_and_install_modules()
    build_exe()

# Set working directory for frozen .exe
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))

# Main Application Class
class JunkCleanerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JunkSweep")
        self.root.geometry("800x600")
        
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(pady=10, expand=True, fill="both")

        self.setup_junk_tab()

    def setup_junk_tab(self):
        junk_frame = ttk.Frame(self.notebook)
        self.notebook.add(junk_frame, text="Junk File Manager")

        # Junk file commands
        cmd_frame = ttk.LabelFrame(junk_frame, text="Junk File Operations")
        cmd_frame.pack(pady=5, padx=5, fill="x")

        junk_commands = [
            ("Temp Files", "dir %temp%", "del /q /f %temp%\\*.*"),
            ("Windows Temp", "dir %windir%\\Temp", "del /q /f %windir%\\Temp\\*.*"),
            ("Prefetch", "dir %windir%\\Prefetch", "del /q /f %windir%\\Prefetch\\*.*"),
            ("Recent Files", "dir %appdata%\\Microsoft\\Windows\\Recent", 
             "del /q /f %appdata%\\Microsoft\\Windows\\Recent\\*.*")
        ]

        for name, list_cmd, del_cmd in junk_commands:
            frame = ttk.Frame(cmd_frame)
            frame.pack(fill="x", pady=2)
            
            ttk.Button(frame, text=f"List {name}",
                      command=lambda c=list_cmd: self.run_command(c)).pack(side="left", padx=5)
            ttk.Button(frame, text=f"Delete {name}",
                      command=lambda c=del_cmd: self.delete_command(c)).pack(side="left", padx=5)

        # Recycle Bin controls
        recycle_frame = ttk.LabelFrame(junk_frame, text="Recycle Bin")
        recycle_frame.pack(pady=5, padx=5, fill="x")
        
        ttk.Button(recycle_frame, text="List Recycle Bin",
                  command=lambda: self.run_command('dir $Recycle.Bin /s')).pack(side="left", padx=5)
        ttk.Button(recycle_frame, text="Empty Recycle Bin",
                  command=self.empty_recycle_bin).pack(side="left", padx=5)

        self.output = scrolledtext.ScrolledText(junk_frame, height=20)
        self.output.pack(pady=5, padx=5, fill="both", expand=True)

    def run_command(self, command):
        def thread_func():
            try:
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                self.output.delete(1.0, tk.END)
                self.output.insert(tk.END, result.stdout or "Command executed.\n")
                if result.stderr:
                    self.output.insert(tk.END, f"\nErrors:\n{result.stderr}")
            except Exception as e:
                self.output.delete(1.0, tk.END)
                self.output.insert(tk.END, f"Error: {str(e)}")
        
        threading.Thread(target=thread_func, daemon=True).start()

    def delete_command(self, command):
        def thread_func():
            if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete these files?"):
                try:
                    result = subprocess.run(command, shell=True, capture_output=True, text=True)
                    self.output.delete(1.0, tk.END)
                    self.output.insert(tk.END, "Files deleted successfully.\n")
                    if result.stderr:
                        self.output.insert(tk.END, f"\nErrors:\n{result.stderr}")
                except Exception as e:
                    self.output.delete(1.0, tk.END)
                    self.output.insert(tk.END, f"Error: {str(e)}")
        
        threading.Thread(target=thread_func, daemon=True).start()

    def empty_recycle_bin(self):
        def thread_func():
            if messagebox.askyesno("Confirm Empty", "Are you sure you want to empty the Recycle Bin?"):
                try:
                    command = 'powershell -command "Clear-RecycleBin -Force"'
                    subprocess.run(command, shell=True, capture_output=True, text=True)
                    self.output.delete(1.0, tk.END)
                    self.output.insert(tk.END, "Recycle Bin emptied successfully.\n")
                except Exception as e:
                    self.output.delete(1.0, tk.END)
                    self.output.insert(tk.END, f"Error: {str(e)}")
        
        threading.Thread(target=thread_func, daemon=True).start()

# Main execution
try:
    root = tk.Tk()
    app = JunkCleanerApp(root)
    root.mainloop()
except Exception as e:
    logging.error(f"GUI initialization failed: {e}")
    sys.exit(1)