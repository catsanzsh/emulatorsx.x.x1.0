import tkinter as tk
import time
import random

class Chip8Emulator:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("CHIP-8 Emulator")
        self.window.geometry("640x320")
        self.canvas = tk.Canvas(self.window, width=640, height=320, bg="black")
        self.canvas.pack()

        # CHIP-8 specs
        self.memory = [0] * 4096  # 4 KB memory
        self.registers = [0] * 16  # 16 general-purpose registers
        self.index_register = 0
        self.pc = 0x200  # Program counter starts at 0x200
        self.stack = []
        self.delay_timer = 0
        self.sound_timer = 0
        self.display = [[0] * 64 for _ in range(32)]  # 64x32 display
        self.keys = [0] * 16  # Input keys
        self.running = True

        # Key mapping
        self.key_map = {
            '1': 0x1, '2': 0x2, '3': 0x3, '4': 0xC,
            'q': 0x4, 'w': 0x5, 'e': 0x6, 'r': 0xD,
            'a': 0x7, 's': 0x8, 'd': 0x9, 'f': 0xE,
            'z': 0xA, 'x': 0x0, 'c': 0xB, 'v': 0xF
        }
        self.setup_input()

    def setup_input(self):
        self.window.bind("<KeyPress>", self.key_press)
        self.window.bind("<KeyRelease>", self.key_release)

    def key_press(self, event):
        if event.char in self.key_map:
            self.keys[self.key_map[event.char]] = 1

    def key_release(self, event):
        if event.char in self.key_map:
            self.keys[self.key_map[event.char]] = 0

    def load_rom(self, file_path):
        with open(file_path, 'rb') as file:
            rom_data = file.read()
        for i, byte in enumerate(rom_data):
            self.memory[0x200 + i] = byte

    def emulate_cycle(self):
        opcode = self.memory[self.pc] << 8 | self.memory[self.pc + 1]  # Fetch opcode
        self.pc += 2
        self.execute_opcode(opcode)
        self.update_timers()

    def execute_opcode(self, opcode):
        # Example: Decode and execute opcodes
        if opcode == 0x00E0:  # Clear the display
            self.display = [[0] * 64 for _ in range(32)]
        elif opcode == 0x00EE:  # Return from subroutine
            self.pc = self.stack.pop()
        elif opcode & 0xF000 == 0x1000:  # Jump to address
            self.pc = opcode & 0x0FFF
        elif opcode & 0xF000 == 0x6000:  # Set register VX
            x = (opcode & 0x0F00) >> 8
            self.registers[x] = opcode & 0x00FF
        elif opcode & 0xF000 == 0xA000:  # Set index register
            self.index_register = opcode & 0x0FFF
        elif opcode & 0xF000 == 0xD000:  # Draw sprite
            x = self.registers[(opcode & 0x0F00) >> 8]
            y = self.registers[(opcode & 0x00F0) >> 4]
            height = opcode & 0x000F
            self.registers[0xF] = 0
            for row in range(height):
                sprite_byte = self.memory[self.index_register + row]
                for col in range(8):
                    if sprite_byte & (0x80 >> col):
                        pixel_x = (x + col) % 64
                        pixel_y = (y + row) % 32
                        if self.display[pixel_y][pixel_x] == 1:
                            self.registers[0xF] = 1  # Collision detected
                        self.display[pixel_y][pixel_x] ^= 1

    def update_timers(self):
        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.sound_timer > 0:
            self.sound_timer -= 1

    def render_graphics(self):
        self.canvas.delete("all")
        for y in range(32):
            for x in range(64):
                if self.display[y][x]:
                    self.canvas.create_rectangle(
                        x * 10, y * 10, x * 10 + 10, y * 10 + 10, fill="white"
                    )

    def run(self):
        while self.running:
            self.emulate_cycle()
            self.render_graphics()
            self.window.update()
            time.sleep(1 / 60)  # 60 Hz refresh rate


if __name__ == "__main__":
    emulator = Chip8Emulator()
    emulator.load_rom("path_to_rom.ch8")  # Replace with the path to your CHIP-8 ROM
    emulator.run()
