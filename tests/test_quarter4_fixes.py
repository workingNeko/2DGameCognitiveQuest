# tests/test_quarter4_fixes.py
import os
import sys
import unittest
import pygame

# Use headless video driver for testing
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

pygame.init()
screen = pygame.display.set_mode((1280, 720))

from screens.main_menu import MainMenu
from screens.quarter4 import Quarter4
from core.npc_scripts import get_map_instructions, get_station_script, get_mentor_script

class TestQuarter4Fixes(unittest.TestCase):
    def setUp(self):
        self.screen = screen
        self.mm = MainMenu(self.screen)
        self.mm.selected_student = {"id": 1, "student_id": "1001", "first_name": "HeroTester"}

    def test_default_map_is_map10(self):
        """Verify Quarter 4 defaults to map10.txt (Stage 1 of Quarter 4) when no map is passed."""
        q4 = Quarter4(self.screen, self.mm, None)
        self.assertEqual(q4.map_name, "map10.txt")

    def test_map10_single_station_3(self):
        """Verify map10.txt has no duplicate station 3 tile and Station 3 is at (20, 9)."""
        q4 = Quarter4(self.screen, self.mm, "map10.txt")
        self.assertIn(3, q4.quiz_stations)
        self.assertEqual(q4.quiz_stations[3], (20, 9))
        # Verify line 10 in map10 has only one '3'
        map_path = os.path.join("assets", "map", "Quarter4Maps", "map10.txt")
        with open(map_path, "r") as f:
            lines = f.readlines()
        self.assertEqual(lines[9].count("3"), 1)

    def test_quarter4_instructions_and_scripts(self):
        """Verify customized instructions and mentor scripts for maps 10, 11, and 12."""
        # Map 10
        instr10 = get_map_instructions("map10.txt", "HeroTester")
        self.assertIn("THE TEMPLE AQUEDUCT", instr10["title"])
        self.assertIn("HeroTester", instr10["subtitle"])

        # Map 11
        instr11 = get_map_instructions("map11.txt", "HeroTester")
        self.assertEqual(instr11["title"], "THE SUBMERGED KEY VAULT")

        # Map 12
        instr12 = get_map_instructions("map12.txt", "HeroTester")
        self.assertEqual(instr12["title"], "THE LOTUS RAFT & FINAL SANCTUM")

        # Mentor scripts
        mentor_q4 = get_mentor_script("map10.txt", "HeroTester")
        self.assertEqual(mentor_q4["name"], "Temple Elder")

    def test_feedback_dialog_rendering_and_hitboxes(self):
        """Verify all feedback dialogs render without crash and button hitboxes are valid."""
        q4 = Quarter4(self.screen, self.mm, "map10.txt")
        q4.instruction_modal.hide()

        # Wrong dialog
        q4.quiz_state = 2
        q4.draw_wrong_dialog()
        self.assertTrue(hasattr(q4, "wrong_btn_rect"))
        self.assertTrue(isinstance(q4.wrong_btn_rect, pygame.Rect))

        # Out of tries dialog
        q4.quiz_state = 4
        q4.draw_out_of_tries_dialog()
        self.assertTrue(hasattr(q4, "reveal_btn_rect"))
        self.assertTrue(isinstance(q4.reveal_btn_rect, pygame.Rect))

        # Correct dialog
        q4.quiz_state = 3
        q4.draw_correct_dialog()
        self.assertTrue(hasattr(q4, "correct_btn_rect"))
        self.assertTrue(isinstance(q4.correct_btn_rect, pygame.Rect))

        # Final dialog
        q4.quiz_state = 5
        q4.draw_final_dialog()
        self.assertTrue(hasattr(q4, "final_btn_rect"))
        self.assertTrue(isinstance(q4.final_btn_rect, pygame.Rect))

        # Bromen dialog (state 1 and state 2)
        q4.bromen_dialogue_state = 1
        q4.draw_bromen_dialog()
        self.assertTrue(hasattr(q4, "bromen_btn_rect"))

        q4.bromen_dialogue_state = 2
        q4.draw_bromen_dialog()
        self.assertTrue(hasattr(q4, "bromen_btn_rect"))

    def test_map10_full_playthrough(self):
        """Simulate complete playthrough on Map 10: all stations -> elder -> key puzzle -> portal."""
        q4 = Quarter4(self.screen, self.mm, "map10.txt")
        q4.instruction_modal.hide()

        for st in range(1, len(q4.quiz_stations) + 1):
            q4.answered_stations.add(st)
        self.assertEqual(len(q4.answered_stations), len(q4.quiz_stations))

        # Walk to Elder
        q4.player_x = q4.npc_bromen_x
        q4.player_y = q4.npc_bromen_y
        q4.update()
        self.assertEqual(q4.bromen_dialogue_state, 2)

        # Open Key Puzzle
        q4.draw_bromen_dialog()
        q4.trigger_click(q4.bromen_btn_rect.center)
        self.assertTrue(q4.key_puzzle_active)

        # Solve Key Puzzle
        for piece in q4.key_puzzle_pieces:
            piece["is_placed"] = True
            piece["inserting"] = False
            piece["turning"] = False
        q4.update_key_puzzle()
        q4.draw()
        self.assertTrue(q4.key_puzzle_all_placed)

        # Click Continue on Key Puzzle
        q4.trigger_click(q4.key_puzzle_continue_btn_rect.center)
        self.assertEqual(q4.quiz_state, 5)

        # Final Speech Continue
        q4.final_dialog_open_time = 0
        q4.draw_final_dialog()
        q4.trigger_click(q4.final_btn_rect.center)
        self.assertEqual(q4.quiz_state, 6)

        # Walk to portal
        port = q4.portals[0]
        q4.player_x = port.get_world_x()
        q4.player_y = port.get_world_y()
        teleported = q4.check_portal_teleport_on_hold()
        self.assertTrue(teleported)
        self.assertTrue(q4.warp_out_active)

    def test_map11_full_playthrough(self):
        """Simulate complete playthrough on Map 11: verifies door opening and portal transition."""
        q4 = Quarter4(self.screen, self.mm, "map11.txt")
        q4.instruction_modal.hide()

        for st in range(1, len(q4.quiz_stations) + 1):
            q4.answered_stations.add(st)

        # Trigger Elder interaction
        q4.player_x = q4.npc_bromen_x
        q4.player_y = q4.npc_bromen_y
        q4.update()
        self.assertEqual(q4.bromen_dialogue_state, 2)

        q4.draw_bromen_dialog()
        q4.trigger_click(q4.bromen_btn_rect.center)
        self.assertTrue(q4.key_puzzle_active)

        # Solve Key Puzzle
        for piece in q4.key_puzzle_pieces:
            piece["is_placed"] = True
            piece["inserting"] = False
            piece["turning"] = False
        q4.update_key_puzzle()
        q4.draw()
        self.assertTrue(q4.key_puzzle_all_placed)

        # Check doors open
        q4.trigger_click(q4.key_puzzle_continue_btn_rect.center)
        self.assertTrue(q4.key_puzzle_solved)
        self.assertIn("{", q4.WALKABLE_TILES)

        q4.final_dialog_open_time = 0
        q4.draw_final_dialog()
        q4.trigger_click(q4.final_btn_rect.center)
        self.assertEqual(q4.quiz_state, 6)

        port = q4.portals[0]
        q4.player_x = port.get_world_x()
        q4.player_y = port.get_world_y()
        teleported = q4.check_portal_teleport_on_hold()
        self.assertTrue(teleported)

    def test_map12_full_playthrough_and_addition_puzzle(self):
        """Simulate Map 12: Addition puzzle, Lotus Raft cruise, and no KeyError: None."""
        q4 = Quarter4(self.screen, self.mm, "map12.txt")
        q4.instruction_modal.hide()

        for st in range(1, len(q4.quiz_stations) + 1):
            q4.answered_stations.add(st)

        q4.init_addition_puzzle()
        q4.key_puzzle_active = True

        # Test drawing before pieces placed does NOT raise KeyError: None
        q4.addition_is_correct = True
        try:
            q4.draw_addition_puzzle()
        except Exception as e:
            self.fail(f"draw_addition_puzzle crashed with exception: {e}")

        # Place pieces correctly into slots
        for i in range(5):
            q4.addition_slots[i]["placed_piece_id"] = i
            q4.addition_pieces[i]["slot_id"] = i
            q4.addition_pieces[i]["is_placed"] = True

        q4.update_addition_puzzle()
        q4.draw_addition_puzzle()
        self.assertTrue(q4.addition_is_correct)
        self.assertIsNotNone(q4.addition_continue_btn_rect)

        # Click continue on addition puzzle
        q4.trigger_click(q4.addition_continue_btn_rect.center)
        self.assertEqual(q4.quiz_state, 5)
        self.assertEqual(q4.raft_state, "ready_to_sail")

        # Click final speech
        q4.final_dialog_open_time = 0
        q4.draw_final_dialog()
        q4.trigger_click(q4.final_btn_rect.center)
        self.assertEqual(q4.quiz_state, 0)
        self.assertEqual(q4.raft_state, "ready_to_sail")

        # Step near raft
        q4.player_x = q4.raft_x
        q4.player_y = q4.raft_y
        q4.update()
        self.assertEqual(q4.raft_state, "sailing")
        self.assertTrue(q4.raft_passenger)

        # Simulate sailing arrival at East Pier
        q4.raft_x = q4.raft_target_x
        q4.update()
        self.assertEqual(q4.raft_state, "docked_east")
        self.assertFalse(q4.raft_passenger)
        self.assertEqual(q4.quiz_state, 6)

        # Check goal portal warp
        port = q4.portals[0]
        q4.player_x = port.get_world_x()
        q4.player_y = port.get_world_y()
        teleported = q4.check_portal_teleport_on_hold()
        self.assertTrue(teleported)

    def test_greeting_dialog_click_and_eliminated_choices(self):
        """Verify greeting dialog click initializes quiz question without eliminated_choices AttributeError."""
        q4 = Quarter4(self.screen, self.mm, "map10.txt")
        q4.instruction_modal.hide()

        # Step next to Station 1 NPC
        st1_pos = q4.quiz_stations[1]
        q4.player_x = st1_pos[0] * 32
        q4.player_y = st1_pos[1] * 32
        q4.update()

        # Greeting dialog is now visible
        self.assertTrue(q4.greeting_dialog.is_visible)

        # Click greeting action button -> transitions to quiz question
        btn_rect = q4.greeting_dialog.btn_rect
        q4.trigger_click(btn_rect.center)

        self.assertFalse(q4.greeting_dialog.is_visible)
        self.assertEqual(q4.quiz_state, 1)
        self.assertTrue(hasattr(q4, "eliminated_choices"))
        self.assertEqual(len(q4.eliminated_choices), 0)

        # Answer incorrectly (choice that is not correct)
        q_data = q4.quiz_questions[0]
        wrong_choice_idx = (q_data["correct"] + 1) % len(q_data["choices"])
        wrong_rect = q4.quiz_dialog.get_button_rect(wrong_choice_idx)
        q4.trigger_click(wrong_rect.center)

        # State 2 (Wrong try again) and choice added to eliminated_choices
        self.assertEqual(q4.quiz_state, 2)
        self.assertIn(wrong_choice_idx, q4.eliminated_choices)

        # Click Try Again button
        q4.draw_wrong_dialog()
        q4.trigger_click(q4.wrong_btn_rect.center)
        self.assertEqual(q4.quiz_state, 1)

        # Draw quiz dialog with eliminated choice
        q4.draw_quiz_dialog()

        # Now answer correctly
        correct_rect = q4.quiz_dialog.get_button_rect(q_data["correct"])
        q4.trigger_click(correct_rect.center)
        self.assertEqual(q4.quiz_state, 3)
        self.assertEqual(len(q4.eliminated_choices), 0)

    def test_portal_dimensions_and_no_wall_overlap(self):
        """Verify portal uses large corridor dimensions (2x3 or 3x2) and all covered tiles have zero wall overlap."""
        from screens.quarter4 import PORTAL_SIZES
        for map_file in ["map10.txt", "map11.txt", "map12.txt"]:
            q4 = Quarter4(self.screen, self.mm, map_file)
            self.assertEqual(len(q4.portals), 1)
            port = q4.portals[0]
            expected_size = PORTAL_SIZES[port.direction]
            self.assertEqual(port.width_tiles, expected_size[0])
            self.assertEqual(port.height_tiles, expected_size[1])

            # Ensure ALL tiles covered by the portal are pure floor ('G' or non-wall) and within bounds
            for py in range(port.tile_y, port.tile_y + port.height_tiles):
                for px in range(port.tile_x, port.tile_x + port.width_tiles):
                    tile_char = q4.map_loader.get_map_tile(py, px)
                    self.assertNotEqual(tile_char, "T", f"Wall overlap detected at ({px}, {py}) in {map_file}")
                    self.assertGreaterEqual(px, 0)
                    self.assertLess(px, q4.map_loader.cols)
                    self.assertGreaterEqual(py, 0)
                    self.assertLess(py, q4.map_loader.rows)

    def test_map12_walk_and_click_platform_boarding(self):
        """Verify Map 12 Lotus Platform can be boarded via walking to dock or direct click after answering stations."""
        q4 = Quarter4(self.screen, self.mm, "map12.txt")
        q4.instruction_modal.hide()

        # 1. Answer all 6 stations
        for st in range(1, len(q4.quiz_stations) + 1):
            q4.answered_stations.add(st)
        q4.quiz_state = 0

        # Updating automatically sets raft to ready_to_sail
        q4.update()
        self.assertEqual(q4.raft_state, "ready_to_sail")

        # 2. Test walkability of dock bank (col 28, 29, 30) - can_move should allow walking onto embarkation tiles
        self.assertTrue(q4.can_move(28 * 32, 9 * 32))
        self.assertTrue(q4.can_move(29 * 32, 9 * 32))
        self.assertTrue(q4.can_move(30 * 32, 9 * 32))

        # 3. Test walking near west dock triggers sailing cruise
        q4.player_x = 28 * 32
        q4.player_y = 9 * 32
        q4.update()
        self.assertEqual(q4.raft_state, "sailing")
        self.assertTrue(q4.raft_passenger)

        # 4. Finish cruise across water canal
        q4.raft_x = q4.raft_target_x
        q4.update()
        self.assertEqual(q4.raft_state, "docked_east")
        self.assertFalse(q4.raft_passenger)
        self.assertAlmostEqual(q4.player_x, 37 * 32, delta=8)
        self.assertEqual(q4.quiz_state, 6)

        # 5. Verify East Pier dock walkability and path to portal at (48, 8)
        self.assertTrue(q4.can_move(37 * 32, 9 * 32))
        self.assertTrue(q4.can_move(38 * 32, 9 * 32))
        self.assertTrue(q4.can_move(38 * 32, 8 * 32))

        # 6. Test direct click on raft to return or board
        rx = (q4.raft_x - q4.camera_x) * 1.5
        ry = (q4.raft_y - q4.camera_y) * 1.5
        q4.trigger_click((int(rx + 10), int(ry + 10)))
        self.assertEqual(q4.raft_state, "sailing_west")
        self.assertTrue(q4.raft_passenger)

if __name__ == "__main__":
    unittest.main()

