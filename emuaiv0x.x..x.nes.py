import tkinter as tk
from tkinter import filedialog, messagebox
import time
import os
import threading

# Ensure the Chip8Core class is defined here or imported if defined elsewhere
import random

class Chip8Core:
    def __init__(self):
        # 4KB memory
        self.memory = [0] * 4096
        
        # 16 general purpose 8-bit registers: V0 to VF
        self.V = [0] * 16
        
        # 16-bit register (generally used to store memory addresses)
        self.I = 0
        
        # Program counter starts at 0x200 where most Chip-8 ROMs begin
        self.pc = 0x200
        
        # Stack for subroutine calls
        self.stack = []
        
        # Timers (decrement at 60Hz when > 0)
        self.delay_timer = 0
        self.sound_timer = 0
        
        # 64×32 monochrome display (0 or 1 for each pixel)
        self.display = [[0] * 64 for _ in range(32)]
        
        # Keys (0-F)
        self.keys = [0] * 16
        
        # For certain opcodes, need to wait for key press
        self.waiting_for_key = False
        self.waiting_key_register = 0
        
        # Last timer update time
        self.last_timer_update = time.time()

        # Load Chip-8 "fontset" into memory
        self._load_fonts()

    # [Previous methods remain the same until _update_timers]

    def _update_timers(self):
        """Update timers at 60Hz independently of CPU speed."""
        current_time = time.time()
        elapsed = current_time - self.last_timer_update
        
        # Update timers at 60Hz
        if elapsed >= 1/60:
            if self.delay_timer > 0:
                self.delay_timer -= 1
            if self.sound_timer > 0:
                self.sound_timer -= 1
                # Implement sound here if desired (e.g., beep)
            self.last_timer_update = current_time

    # [Rest of Chip8Core methods remain the same]

class Chip8EmulatorUI:
    """
    Chip8EmulatorUI is a class that provides a graphical user interface for a CHIP-8 emulator.
    Attributes:
        root (tk.Tk): The root window of the Tkinter application.
        scale (int): The scale factor for the CHIP-8 display.
        window_width (int): The width of the emulator window.
        window_height (int): The height of the emulator window.
        core (Chip8Core): The core emulation logic for CHIP-8.
        emulation_running (bool): Flag indicating if the emulation is currently running.
        emulation_speed (int): The speed of the emulation in instructions per second.
        last_cycle_time (float): The time of the last emulation cycle.
        emulation_thread (threading.Thread): The thread running the emulation loop.
        speed_var (tk.StringVar): The variable holding the emulation speed for the UI.
        canvas (tk.Canvas): The canvas widget for displaying the CHIP-8 screen.
        rects (list): A 2D list of rectangle objects representing the CHIP-8 display pixels.
    Methods:
        __init__(root): Initializes the Chip8EmulatorUI with the given root window.
        _setup_control_panel(): Sets up the control panel with buttons and speed control.
        _setup_display(): Sets up the display canvas with improved scaling.
        _emulation_loop(): The main emulation loop with improved timing.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("CHIP-8 Emulator")
        
        # Calculate window size based on desired CHIP-8 display scale
        self.scale = 12  # Increased scale for better visibility
        self.window_width = 64 * self.scale + 40  # Add padding
        self.window_height = 32 * self.scale + 100  # Add space for controls
        
        self.root.geometry(f"{self.window_width}x{self.window_height}")
        self.root.resizable(False, False)

        # Initialize Chip8 core
        self.core = Chip8Core()

        # Setup UI components
        self._setup_menu()
        self._setup_display()
        self._setup_status_bar()
        self._setup_control_panel()

        # Setup input handling
        self._setup_input()

        # Emulation control
        self.emulation_running = False
        self.emulation_speed = 700  # Increased to ~700 instructions per second
        self.last_cycle_time = time.time()

        # Start the emulation loop in a separate thread
        self.emulation_thread = threading.Thread(target=self._emulation_loop, daemon=True)
        self.emulation_thread.start()

    def _setup_control_panel(self):
        """Set up the control panel with buttons and speed control."""
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=5)

        # Add speed control
        speed_label = tk.Label(control_frame, text="Speed:")
        speed_label.pack(side=tk.LEFT, padx=5)
        
        self.speed_var = tk.StringVar(value="700")
        speed_entry = tk.Entry(control_frame, textvariable=self.speed_var, width=5)
        speed_entry.pack(side=tk.LEFT, padx=5)
        
        def update_speed(event=None):
            try:
                new_speed = int(self.speed_var.get())
                if 100 <= new_speed <= 2000:
                    self.emulation_speed = new_speed
            except ValueError:
                pass
        
        speed_entry.bind('<Return>', update_speed)

        # Control buttons
        start_button = tk.Button(control_frame, text="Start", command=self.start_emulation)
        start_button.pack(side=tk.LEFT, padx=5)

        stop_button = tk.Button(control_frame, text="Stop", command=self.stop_emulation)
        stop_button.pack(side=tk.LEFT, padx=5)

        step_button = tk.Button(control_frame, text="Step", 
                              command=lambda: [self.core.cycle(), self._update_display()])
        step_button.pack(side=tk.LEFT, padx=5)

    def _setup_display(self):
        """Set up the display canvas with improved scaling."""
        self.canvas = tk.Canvas(
            self.root, 
            width=64 * self.scale, 
            height=32 * self.scale, 
            bg="black"
        )
        self.canvas.pack(pady=10)

        # Initialize a 64x32 grid of rectangles
        self.rects = []
        for y in range(32):
            row = []
            for x in range(64):
                rect = self.canvas.create_rectangle(
                    x * self.scale, 
                    y * self.scale,
                    (x + 1) * self.scale, 
                    (y + 1) * self.scale,
                    fill="black", 
                    outline="dark gray"  # Subtle grid
                )
                row.append(rect)
            self.rects.append(row)

    def _emulation_loop(self):
        """Main emulation loop with improved timing."""
        while True:
            if self.emulation_running:
                current_time = time.time()
                elapsed = current_time - self.last_cycle_time
                
                if elapsed >= 1.0 / self.emulation_speed:
                    try:
                        self.core.cycle()
                        self._update_display()
                        self.last_cycle_time = current_time
                    except Exception as e:
                        self.emulation_running = False
                        self.root.after(0, lambda: messagebox.showerror(
                            "Emulation Error", 
                            f"An error occurred:\n{e}"
                        ))
            
            # Short sleep to prevent excessive CPU usage
            time.sleep(0.001)

    # [Rest of the UI class methods remain the same]

def main():
    root = tk.Tk()
    emulator = Chip8EmulatorUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
    ## [C] Team Flames 20XX 100% ##
