# map_loader.py - Handles loading and managing multiple maps

import os
import random


class MapLoader:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.maps_dir = os.path.join(base_dir, "assets", "map")
        self.quarter_maps_dir = os.path.join(self.maps_dir, "Quarter1Maps")

        # Map data
        self.current_map = None
        self.current_map_name = None
        self.game_map = []
        self.rows = 0
        self.cols = 0

        # NPC positions
        self.npc_positions = {}  # {'B': [(x,y)], 'O': [(x,y)], etc.}
        self.player_start = None

    def load_map(self, map_filename):
        """Load a map file and parse it"""
        # Try multiple paths
        possible_paths = [
            os.path.join(self.maps_dir, map_filename),
            os.path.join(self.quarter_maps_dir, map_filename),
        ]

        map_path = None
        for path in possible_paths:
            if os.path.exists(path):
                map_path = path
                break

        if map_path is None:
            print(f"❌ Map not found: {map_filename}")
            return False

        try:
            with open(map_path, "r", encoding="utf-8") as f:
                lines = [line.rstrip("\n\r") for line in f if line.rstrip("\n\r")]

            if not lines:
                print(f"❌ Map file is empty: {map_path}")
                return False

            self.game_map = lines
            self.rows = len(lines)
            self.cols = max(len(row) for row in lines)
            self.current_map_name = os.path.basename(map_path)

            # Parse NPC positions and player start
            self._parse_map_data()

            print(f"✅ Loaded map: {self.current_map_name} ({self.rows}x{self.cols})")
            print(f"   Player start: {self.player_start}")
            print(f"   NPCs found: {len(self.npc_positions)}")
            return True

        except Exception as e:
            print(f"❌ Error loading map {map_filename}: {e}")
            return False

    def _parse_map_data(self):
        """Parse the map for NPC positions and player start"""
        self.npc_positions = {}
        self.player_start = None

        # NPC markers to look for - using 'O' for oldman as in stage select
        npc_markers = ['B', 'O', 'S', 'K']

        for y, row in enumerate(self.game_map):
            for x, char in enumerate(row):
                if char == 'P':
                    self.player_start = (x, y)
                elif char == 'N':
                    # Treat N as O (Oldman NPC)
                    if 'O' not in self.npc_positions:
                        self.npc_positions['O'] = []
                    self.npc_positions['O'].append((x, y))
                elif char in npc_markers:
                    if char not in self.npc_positions:
                        self.npc_positions[char] = []
                    self.npc_positions[char].append((x, y))

    def get_random_map(self):
        """Get a random map from Quarter1Maps folder"""
        if not os.path.exists(self.quarter_maps_dir):
            print(f"❌ Quarter1Maps directory not found: {self.quarter_maps_dir}")
            return None

        try:
            map_files = [f for f in os.listdir(self.quarter_maps_dir)
                         if f.endswith('.txt')]
            if not map_files:
                print(f"❌ No map files found in {self.quarter_maps_dir}")
                return None

            selected = random.choice(map_files)
            print(f"🎲 Randomly selected map: {selected}")
            return selected

        except Exception as e:
            print(f"❌ Error getting random map: {e}")
            return None

    def get_map_tile(self, row, col):
        """Get tile character at position"""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            if row < len(self.game_map) and col < len(self.game_map[row]):
                return self.game_map[row][col]
        return None

    def replace_npc_markers_with_walkable_tiles(self):
        """Replace NPC markers with walkable tiles for rendering"""
        modified_map = []
        for y, row in enumerate(self.game_map):
            row_list = list(row)
            modified = False
            for x, char in enumerate(row_list):
                if char == 'N' or char in self.npc_positions:
                    # Replace with walkable tile (6 or 7)
                    if char in ['B', 'K']:
                        row_list[x] = '7'
                    elif char in ['O', 'S', 'N']:
                        row_list[x] = 'G'
                    modified = True
            modified_map.append(''.join(row_list))
        return modified_map