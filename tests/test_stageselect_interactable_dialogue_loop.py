import os
import sys
import unittest
import math

# Headless display
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["MPLBACKEND"] = "Agg"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pygame
pygame.init()
screen = pygame.display.set_mode((1280, 720))

from screens.stageselect import StageSelect, TILE_SIZE

class MockAudioManager:
    def __init__(self):
        self.played = []
    def play_sfx(self, name):
        self.played.append(name)
    def play_bgm(self, *args, **kwargs):
        pass

class MockMainMenu:
    def __init__(self):
        self.screen = screen
        self.audio_manager = MockAudioManager()
        self.selected_student = {"id": 999999, "name": "Tester", "gender": "male"}
        self.student_id = 999999
        self.current_screen = "stage_select"
        self.stage_select = None

class TestStageSelectInteractableDialogueLoop(unittest.TestCase):
    def setUp(self):
        self.menu = MockMainMenu()
        self.stage = StageSelect(self.menu.screen, self.menu)

    def test_interactable_no_loop_on_dialogue_completion(self):
        """Verify that completing dialogue at any of the 4 quadrangle bonus objects does NOT loop."""
        for obj in self.stage.interactables:
            obj_id = obj["id"]
            # Position player at the object
            self.stage.player_x = obj["world_x"]
            self.stage.player_y = obj["world_y"] + 20
            self.stage.update(0.016)
            self.assertEqual(self.stage.nearby_interactable, obj, f"Player should be near {obj_id}")

            # Trigger interactable
            self.stage.trigger_interactable(obj)
            self.assertEqual(self.stage.interactable_dialogue_state, 1)
            self.assertTrue(self.stage.is_dialogue_active())

            # Advance all lines of dialogue to completion
            lines = obj.get("dialogue", [])
            for _ in range(len(lines) + 1):
                self.stage.advance_dialogue()
                self.stage.advance_dialogue()

            # Dialogue should now be closed and inactive
            self.assertFalse(self.stage.is_dialogue_active(), f"Dialogue for {obj_id} should be closed")
            self.assertEqual(self.stage.interactable_dialogue_state, 0)
            self.assertIsNone(self.stage.active_interactable)
            self.assertEqual(self.stage.interactable_standoff, obj_id)

            # Frame updates with fist closed (gesture active) while standing in place must NOT restart dialogue
            self.stage.fist_closed = True
            for _ in range(10):
                self.stage.update(0.016)
            self.assertFalse(self.stage.is_dialogue_active(), f"Dialogue for {obj_id} looped on gesture update!")

            # Pressing Space/Enter while standing in place must NOT restart dialogue
            event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
            res = self.stage.handle_event(event)
            self.assertNotEqual(res, "interactable_triggered", f"Space key re-triggered {obj_id} without stepping away")
            self.assertFalse(self.stage.is_dialogue_active())

            # Clicking near the object while standing in place must NOT restart dialogue
            screen_ox = (obj["world_x"] - self.stage.camera_x + obj["width"] / 2) * 1.5
            screen_oy = (obj["world_y"] - self.stage.camera_y + obj["height"] / 2) * 1.5
            self.stage.trigger_click((int(screen_ox), int(screen_oy)))
            self.assertFalse(self.stage.is_dialogue_active(), f"Click re-triggered {obj_id} without stepping away")

            # Player walks away (distance >= 3.5 tiles)
            self.stage.player_x += int(TILE_SIZE * 4.0)
            self.stage.update(0.016)
            self.assertIsNone(self.stage.interactable_standoff, "Standoff should reset once player walks away")

            # Player walks back and triggers interaction again cleanly
            self.stage.player_x = obj["world_x"]
            self.stage.player_y = obj["world_y"] + 20
            self.stage.update(0.016)
            self.stage.trigger_interactable(obj)
            self.assertTrue(self.stage.is_dialogue_active(), f"Should be able to re-trigger {obj_id} after returning")

            # Close it for the next loop
            while self.stage.interactable_dialogue_state == 1:
                self.stage.advance_dialogue()
                self.stage.advance_dialogue()

if __name__ == "__main__":
    unittest.main()
