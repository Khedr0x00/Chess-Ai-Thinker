# created by khedr0x00
import tkinter as tk
from tkinter import PhotoImage
import json
import os
import glob
import requests
import re
import random

class ChessBoardApp:
    def __init__(self, master, json_file="chess_board.json"):
        # Initialize the main application window.
        self.master = master
        master.title("Chess Board")
        
        self.json_file = json_file
        self.backup_json_file = "backup/chess_board.json" # New backup file path
        self.pieces_data = self.load_data()
        self.images = {}
        self.selected_piece = None
        self.pieces_on_board = {}
        
        # API key variable and file
        self.api_key_file = "api.txt"
        self.api_key = tk.StringVar()
        self.load_api_key()
        
        # Board dimensions
        self.board_size = 640
        self.square_size = self.board_size // 8
        
        # Main frame with tabs
        self.notebook = tk.ttk.Notebook(master)
        self.notebook.pack(pady=10, expand=True)
        
        # Chess board tab
        self.board_frame = tk.Frame(self.notebook)
        self.notebook.add(self.board_frame, text="Board")
        
        # Settings tab
        self.settings_frame = tk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="Settings")
        self.setup_settings_tab()
        
        # Frame for canvas and controls
        self.game_controls_frame = tk.Frame(self.board_frame)
        self.game_controls_frame.pack(padx=10, pady=10)
        
        # Create the canvas for the chessboard
        self.canvas = tk.Canvas(self.game_controls_frame, width=self.board_size, height=self.board_size, bg="white")
        self.canvas.pack()
        
        # Bind mouse events to the canvas for piece interaction
        self.canvas.bind("<Button-1>", self.on_board_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-3>", self.on_right_click) # Bind right-click event

        # AI Think button and New Game button
        button_frame = tk.Frame(self.board_frame)
        button_frame.pack(pady=10)
        
        self.think_button = tk.Button(button_frame, text="Think", command=self.ai_think)
        self.think_button.pack(side=tk.LEFT, padx=5)

        self.new_game_button = tk.Button(button_frame, text="New Game", command=self.reset_game)
        self.new_game_button.pack(side=tk.LEFT, padx=5)

        self.draw_board()
        self.draw_pieces()
        
    def load_api_key(self):
        # Load API key from file
        try:
            with open(self.api_key_file, 'r') as f:
                self.api_key.set(f.read().strip())
        except FileNotFoundError:
            print(f"API key file '{self.api_key_file}' not found. Please enter your key in the Settings tab.")
        
    def save_api_key(self):
        # Save API key to file
        try:
            with open(self.api_key_file, 'w') as f:
                f.write(self.api_key.get())
            print("API key saved successfully.")
        except Exception as e:
            print(f"Error saving API key: {e}")

    def setup_settings_tab(self):
        # Setup for the settings tab
        tk.Label(self.settings_frame, text="Gemini API Key:").pack(pady=5)
        self.api_key_entry = tk.Entry(self.settings_frame, textvariable=self.api_key, width=50)
        self.api_key_entry.pack(pady=5)
        
        self.save_button = tk.Button(self.settings_frame, text="Save API Key", command=self.save_api_key)
        self.save_button.pack(pady=5)
        
    def load_data(self):
        # Load the chess piece data from the JSON file.
        try:
            with open(self.json_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Error: The file '{self.json_file}' was not found.")
            return None
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from '{self.json_file}'.")
            return None

    def save_data(self):
        # Save the updated chess piece data to the JSON file.
        try:
            with open(self.json_file, 'w') as f:
                json.dump(self.pieces_data, f, indent=2)
            print(f"File '{self.json_file}' updated successfully.")
        except Exception as e:
            print(f"Error: Could not save data to '{self.json_file}'. {e}")

    def reset_game(self):
        # Copy the backup JSON file to the main JSON file
        try:
            with open(self.backup_json_file, 'r') as backup_file:
                backup_data = json.load(backup_file)
            with open(self.json_file, 'w') as main_file:
                json.dump(backup_data, main_file, indent=2)
            
            # Reload data and redraw the board
            self.pieces_data = self.load_data()
            self.draw_board()
            self.draw_pieces()
            print("Game reset successfully. A new game has started.")
        except FileNotFoundError:
            print(f"Error: Backup file '{self.backup_json_file}' not found.")
        except Exception as e:
            print(f"Error: Could not reset the game. {e}")

    def draw_board(self):
        # Draw the 8x8 chessboard squares.
        for row in range(8):
            for col in range(8):
                x1 = col * self.square_size
                y1 = row * self.square_size
                x2 = x1 + self.square_size
                y2 = y1 + self.square_size
                
                # Alternate colors for the squares.
                color = "#D18B47" if (row + col) % 2 == 0 else "#FFCE9E"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color)

    def draw_pieces(self):
        # Clear the board before redrawing pieces
        self.canvas.delete("pieces")
        self.pieces_on_board = {}

        if not self.pieces_data:
            return
            
        current_dir = os.path.dirname(os.path.abspath(__file__))

        for player, data in self.pieces_data.items():
            pieces = {k: v for k, v in data.items() if isinstance(v, dict) and v.get("status", "alive") == "alive"}
            
            for piece_name, piece_info in pieces.items():
                position = piece_info["position"]
                image_path = piece_info["image_path"]

                col = ord(position[0]) - ord('a')
                row = 7 - (int(position[1]) - 1)
                
                x_center = col * self.square_size + self.square_size / 2
                y_center = row * self.square_size + self.square_size / 2

                full_image_path = os.path.join(current_dir, image_path.replace('/', os.sep))

                try:
                    if not os.path.exists(full_image_path):
                        print(f"Image not found: {full_image_path}. Displaying text instead.")
                        piece_initial = piece_name[0].upper()
                        self.canvas.create_text(x_center, y_center, text=piece_initial, font=("Arial", 24, "bold"), tags="pieces")
                        continue

                    original_image = tk.PhotoImage(file=full_image_path)
                    
                    image_ref = f"{full_image_path}_{piece_name}"
                    self.images[image_ref] = original_image
                    
                    item_id = self.canvas.create_image(x_center, y_center, image=original_image, tags=("pieces", piece_name, "piece"))
                    
                    self.pieces_on_board[item_id] = {
                        "name": piece_name,
                        "player": player,
                        "info": piece_info,
                        "image": original_image,
                        "item_id": item_id
                    }
                    
                except tk.TclError as e:
                    print(f"Error loading image {full_image_path}: {e}")
                    piece_initial = piece_name[0].upper()
                    self.canvas.create_text(x_center, y_center, text=piece_initial, font=("Arial", 24, "bold"), tags="pieces")
                    
    def on_board_click(self, event):
        item_ids = self.canvas.find_closest(event.x, event.y)
        for item_id in item_ids:
            if "piece" in self.canvas.gettags(item_id):
                self.selected_piece = self.pieces_on_board.get(item_id)
                
                if self.selected_piece:
                    self.canvas.delete("selection_rect")
                    
                    col = ord(self.selected_piece['info']['position'][0]) - ord('a')
                    row = 7 - (int(self.selected_piece['info']['position'][1]) - 1)
                    x1 = col * self.square_size
                    y1 = row * self.square_size
                    x2 = x1 + self.square_size
                    y2 = y1 + self.square_size

                    self.canvas.create_rectangle(x1, y1, x2, y2, outline="red", width=3, tags="selection_rect")
                    self.canvas.tag_raise(item_id)
                    print(f"Selected: {self.selected_piece['name']} at {self.selected_piece['info']['position']}")
                    break
            
    def on_drag(self, event):
        if self.selected_piece:
            self.canvas.coords(self.selected_piece['item_id'], event.x, event.y)

    def on_release(self, event):
        if self.selected_piece:
            # Get the new position
            col = event.x // self.square_size
            row = event.y // self.square_size
            
            # Check if the drop is within the board boundaries
            if 0 <= col < 8 and 0 <= row < 8:
                new_pos = f"{chr(ord('a') + col)}{8 - row}"
                
                # Update position in data structure
                player = self.selected_piece['player']
                piece_name = self.selected_piece['name']
                
                self.pieces_data[player][piece_name]['position'] = new_pos
                
                # Redraw board and pieces
                self.draw_board()
                self.draw_pieces()
                self.save_data()
            
            # Deselect the piece and remove highlight
            self.selected_piece = None
            self.canvas.delete("selection_rect")

    def on_right_click(self, event):
        item_ids = self.canvas.find_closest(event.x, event.y)
        if item_ids:
            item_id = item_ids[0]
            if "piece" in self.canvas.gettags(item_id):
                piece = self.pieces_on_board.get(item_id)
                if piece:
                    player = piece['player']
                    piece_name = piece['name']
                    self.pieces_data[player][piece_name]['status'] = "dead"
                    self.draw_pieces()
                    self.save_data()
                    print(f"{piece_name} is now dead.")

    def ai_think(self):
        # Check if API key is provided
        api_key = self.api_key.get()
        if not api_key:
            print("Please provide a Gemini API Key in the Settings tab and click 'Save API Key'.")
            return

        print("AI is thinking...")
        
        # Prepare the prompt for the AI
        board_state = json.dumps(self.pieces_data, indent=2)
        prompt = f"""
        You are an expert chess bot. Given the current state of a chess board, suggest the best possible move for the White player.
        The board state is provided in JSON format.
        
        Current board state:
        {board_state}
        
        Your response must be a single JSON object containing the piece to move and its new position.
        Example response format:
        {{
            "piece_name": "pawn1",
            "new_position": "e4"
        }}
        """
        
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "contents": [{"parts": [{"text": prompt}]}]
        }
        
        try:
            response = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent?key={api_key}", headers=headers, json=data)
            response.raise_for_status() # Raise an error for bad status codes
            
            ai_move_str = response.json()['candidates'][0]['content']['parts'][0]['text']
            
            # Use regex to extract the JSON object from the response string
            json_match = re.search(r'```json\s*(\{.*\})\s*```', ai_move_str, re.DOTALL)
            
            if json_match:
                ai_move_str_clean = json_match.group(1)
            else:
                ai_move_str_clean = ai_move_str

            # Extract and clean up the JSON part of the response
            try:
                ai_move = json.loads(ai_move_str_clean)
                piece_name = ai_move['piece_name']
                new_position = ai_move['new_position']

                # Update the piece's position in the data and save
                if piece_name in self.pieces_data['player1']:
                    self.pieces_data['player1'][piece_name]['position'] = new_position
                    self.save_data()
                    print(f"AI moved {piece_name} to {new_position}")
                    self.draw_board()
                    self.draw_pieces()
                else:
                    print(f"AI suggested moving a piece not found in player1's pieces: {piece_name}")

            except json.JSONDecodeError as e:
                print(f"AI response was not valid JSON: {e}")
                print(f"AI response: {ai_move_str}")

        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            print("Please check your API key and internet connection.")
            
if __name__ == "__main__":
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
    root = ttk.Window(themename="superhero")
    app = ChessBoardApp(root)
    root.mainloop()
