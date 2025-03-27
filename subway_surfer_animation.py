"""
MIT License

Copyright (c) 2025 Anton Zimin

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import tkinter as tk
from tkinter import ttk
import random
import time

class SubwaySurferAnimation:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Searching...")
        self.window.geometry("400x300")
        self.window.transient(parent)
        self.window.grab_set()
        
        # Create canvas
        self.canvas = tk.Canvas(self.window, width=400, height=300, bg='#87CEEB')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Animation parameters
        self.character_x = 100
        self.character_y = 200
        self.character_jumping = False
        self.jump_velocity = 0
        self.gravity = 0.8
        self.jump_power = -15
        self.ground_y = 250
        self.coins = []
        self.trains = []
        self.score = 0
        
        # Create initial elements
        self.create_ground()
        self.create_character()
        self.create_initial_coins()
        self.create_initial_trains()
        
        # Start animation
        self.animate()
        
    def create_ground(self):
        # Draw ground
        self.canvas.create_rectangle(0, self.ground_y, 400, 300, fill='#8B4513')
        # Draw train tracks
        for i in range(0, 400, 30):
            self.canvas.create_line(i, self.ground_y, i+20, self.ground_y, fill='#808080', width=2)
            
    def create_character(self):
        # Body
        self.character = self.canvas.create_rectangle(
            self.character_x, self.character_y,
            self.character_x + 20, self.character_y + 40,
            fill='#FFD700'
        )
        # Head
        self.canvas.create_oval(
            self.character_x + 5, self.character_y - 10,
            self.character_x + 15, self.character_y,
            fill='#FFD700'
        )
        
    def create_initial_coins(self):
        for i in range(3):
            x = 300 + i * 100
            y = self.ground_y - 30
            coin = self.canvas.create_oval(
                x, y, x + 20, y + 20,
                fill='#FFD700', outline='#DAA520'
            )
            self.coins.append({'id': coin, 'x': x, 'y': y})
            
    def create_initial_trains(self):
        for i in range(2):
            x = 250 + i * 150
            y = self.ground_y - 60
            train = self.canvas.create_rectangle(
                x, y, x + 40, y + 30,
                fill='#FF0000'
            )
            self.trains.append({'id': train, 'x': x, 'y': y})
            
    def jump(self):
        if not self.character_jumping:
            self.character_jumping = True
            self.jump_velocity = self.jump_power
            
    def update_character(self):
        if self.character_jumping:
            self.character_y += self.jump_velocity
            self.jump_velocity += self.gravity
            
            # Update character position
            self.canvas.coords(
                self.character,
                self.character_x, self.character_y,
                self.character_x + 20, self.character_y + 40
            )
            
            # Check for landing
            if self.character_y >= self.ground_y - 40:
                self.character_y = self.ground_y - 40
                self.character_jumping = False
                self.jump_velocity = 0
                
    def update_coins(self):
        for coin in self.coins:
            coin['x'] -= 2
            if coin['x'] < -20:
                coin['x'] = 400
                coin['y'] = self.ground_y - 30
            self.canvas.coords(
                coin['id'],
                coin['x'], coin['y'],
                coin['x'] + 20, coin['y'] + 20
            )
            
    def update_trains(self):
        for train in self.trains:
            train['x'] -= 3
            if train['x'] < -40:
                train['x'] = 400
                train['y'] = self.ground_y - 60
            self.canvas.coords(
                train['id'],
                train['x'], train['y'],
                train['x'] + 40, train['y'] + 30
            )
            
    def check_collisions(self):
        # Check coin collisions
        for coin in self.coins:
            if (self.character_x < coin['x'] + 20 and
                self.character_x + 20 > coin['x'] and
                self.character_y < coin['y'] + 20 and
                self.character_y + 40 > coin['y']):
                self.score += 1
                coin['x'] = 400
                coin['y'] = self.ground_y - 30
                
        # Check train collisions
        for train in self.trains:
            if (self.character_x < train['x'] + 40 and
                self.character_x + 20 > train['x'] and
                self.character_y < train['y'] + 30 and
                self.character_y + 40 > train['y']):
                self.jump()
                
    def animate(self):
        self.update_character()
        self.update_coins()
        self.update_trains()
        self.check_collisions()
        
        # Randomly trigger jumps
        if not self.character_jumping and random.random() < 0.02:
            self.jump()
            
        self.window.after(16, self.animate)  # ~60 FPS
        
    def close(self):
        self.window.destroy() 