# core/camera_system.py
"""
League of Legends-inspired Camera Controller for 2D Exploration Games.
Features:
- Smooth exponential damping (lerp) tracking player character.
- Dynamic Cursor Lead (Semi-locked mode): view smoothly leads ahead in the direction of the cursor.
- Edge Scrolling: moving the cursor to screen borders smoothly pans the camera.
- Spacebar Recenter: pressing Spacebar snaps/smoothly returns camera focus to the player.
- Middle-mouse drag panning.
- Strict map boundary clamping to prevent showing empty void.
- Cutscene pan override support (e.g., bridge activation).
"""

import pygame


class LoLCamera:
    def __init__(self, screen_width, screen_height, zoom=1.0):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.zoom = zoom

        # Current camera world coordinates (top-left of viewport in world units)
        self.camera_x = 0.0
        self.camera_y = 0.0

        # Accumulated edge scroll / free pan offset
        self.pan_offset_x = 0.0
        self.pan_offset_y = 0.0

        # Tuning Parameters (League of Legends feel)
        self.smooth_rate = 0.12        # Damping factor per frame
        self.lead_factor = 0.18        # Cursor-forward lookahead multiplier
        self.max_lead_x = 90.0         # Max world pixels cursor can lead horizontally
        self.max_lead_y = 70.0         # Max world pixels cursor can lead vertically
        self.edge_margin = 35          # Pixels from screen border to trigger edge scrolling
        self.edge_scroll_speed = 6.0   # World pixels per frame during edge scroll
        self.max_pan_range = 280.0     # Max free exploration pan distance from player

        # Middle mouse drag
        self.is_middle_dragging = False
        self.last_mouse_pos = (0, 0)

        # Spacebar recenter mode
        self.recentering = False

        # Scripted cutscene pan override
        self.scripted_pan_active = False
        self.scripted_x = 0.0
        self.scripted_y = 0.0

    def set_viewport(self, screen_width, screen_height, zoom=None):
        self.screen_width = screen_width
        self.screen_height = screen_height
        if zoom is not None:
            self.zoom = zoom

    def snap_to(self, player_x, player_y, tile_size=48, map_width=None, map_height=None):
        """Immediately center camera on player without interpolation (e.g. on map load)."""
        self.pan_offset_x = 0.0
        self.pan_offset_y = 0.0
        base_x = player_x + tile_size // 2 - (self.screen_width // 2) / self.zoom
        base_y = player_y + tile_size // 2 - (self.screen_height // 2) / self.zoom
        self.camera_x = base_x
        self.camera_y = base_y
        if map_width is not None and map_height is not None:
            self.clamp_to_bounds(map_width, map_height)

    def recenter(self):
        """Iconic League of Legends Spacebar recenter: snap/ease camera offset back to player."""
        self.recentering = True
        self.pan_offset_x *= 0.4
        self.pan_offset_y *= 0.4
        if abs(self.pan_offset_x) < 2.0 and abs(self.pan_offset_y) < 2.0:
            self.pan_offset_x = 0.0
            self.pan_offset_y = 0.0
            self.recentering = False

    def handle_event(self, event):
        """Handle middle mouse drag and Spacebar recentering."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 2:
            self.is_middle_dragging = True
            self.last_mouse_pos = event.pos
            return True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 2:
            self.is_middle_dragging = False
            return True
        elif event.type == pygame.MOUSEMOTION and self.is_middle_dragging:
            dx = (event.pos[0] - self.last_mouse_pos[0]) / self.zoom
            dy = (event.pos[1] - self.last_mouse_pos[1]) / self.zoom
            self.pan_offset_x -= dx
            self.pan_offset_y -= dy
            self.last_mouse_pos = event.pos
            # Clamp free pan offset
            self.pan_offset_x = max(-self.max_pan_range, min(self.max_pan_range, self.pan_offset_x))
            self.pan_offset_y = max(-self.max_pan_range, min(self.max_pan_range, self.pan_offset_y))
            return True
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.recenter()
            return False  # Let game also handle space if needed (e.g. dialogue)

        return False

    def update(self, player_x, player_y, cursor_pos=(0, 0), map_width=1000, map_height=1000, tile_size=48, enable_edge_scroll=True):
        """
        Update camera position following player with LoL-style cursor leading and edge panning.
        """
        # If a scripted cutscene is active, use explicit coords
        if self.scripted_pan_active:
            self.camera_x = self.scripted_x
            self.camera_y = self.scripted_y
            self.clamp_to_bounds(map_width, map_height)
            return

        # Handle recenter easing
        if self.recentering:
            self.recenter()

        # 1. Base Target (Player Center)
        player_center_world_x = player_x + tile_size // 2
        player_center_world_y = player_y + tile_size // 2

        base_cam_x = player_center_world_x - (self.screen_width // 2) / self.zoom
        base_cam_y = player_center_world_y - (self.screen_height // 2) / self.zoom

        # 2. Dynamic Cursor Lead (Semi-Locked Forward Vision)
        lead_x = 0.0
        lead_y = 0.0
        if cursor_pos:
            screen_mid_x = self.screen_width / 2.0
            screen_mid_y = self.screen_height / 2.0
            cur_offset_x = (cursor_pos[0] - screen_mid_x) / self.zoom
            cur_offset_y = (cursor_pos[1] - screen_mid_y) / self.zoom

            # Scale and clamp cursor lead
            raw_lead_x = cur_offset_x * self.lead_factor
            raw_lead_y = cur_offset_y * self.lead_factor
            lead_x = max(-self.max_lead_x, min(self.max_lead_x, raw_lead_x))
            lead_y = max(-self.max_lead_y, min(self.max_lead_y, raw_lead_y))

        # 3. Edge Scrolling (Screen Border Pan)
        if enable_edge_scroll and not self.is_middle_dragging and cursor_pos:
            cx, cy = cursor_pos
            if cx < self.edge_margin:
                self.pan_offset_x -= self.edge_scroll_speed
            elif cx > self.screen_width - self.edge_margin:
                self.pan_offset_x += self.edge_scroll_speed

            if cy < self.edge_margin:
                self.pan_offset_y -= self.edge_scroll_speed
            elif cy > self.screen_height - self.edge_margin:
                self.pan_offset_y += self.edge_scroll_speed

            # Clamp accumulated edge pan range
            self.pan_offset_x = max(-self.max_pan_range, min(self.max_pan_range, self.pan_offset_x))
            self.pan_offset_y = max(-self.max_pan_range, min(self.max_pan_range, self.pan_offset_y))

        # 4. Final Desired Target Position
        target_x = base_cam_x + lead_x + self.pan_offset_x
        target_y = base_cam_y + lead_y + self.pan_offset_y

        # 5. Smooth Exponential Damping (Lerp)
        self.camera_x += (target_x - self.camera_x) * self.smooth_rate
        self.camera_y += (target_y - self.camera_y) * self.smooth_rate

        # 6. Map Boundary Clamping
        self.clamp_to_bounds(map_width, map_height)

    def clamp_to_bounds(self, map_width, map_height):
        """Ensure viewport never reveals out-of-bounds void."""
        max_cam_x = max(0.0, map_width - self.screen_width / self.zoom)
        max_cam_y = max(0.0, map_height - self.screen_height / self.zoom)
        self.camera_x = max(0.0, min(self.camera_x, max_cam_x))
        self.camera_y = max(0.0, min(self.camera_y, max_cam_y))

    def world_to_screen(self, world_x, world_y):
        """Utility to project world coordinate to on-screen pixel coordinate."""
        sx = (world_x - self.camera_x) * self.zoom
        sy = (world_y - self.camera_y) * self.zoom
        return sx, sy

    def screen_to_world(self, screen_x, screen_y):
        """Utility to project screen pixel coordinate to world coordinate."""
        wx = (screen_x / self.zoom) + self.camera_x
        wy = (screen_y / self.zoom) + self.camera_y
        return wx, wy
