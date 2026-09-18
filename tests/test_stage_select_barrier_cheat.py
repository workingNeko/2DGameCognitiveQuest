import os
import sys
from unittest.mock import MagicMock, patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pygame
pygame.init()
screen = pygame.display.set_mode((1280, 720))

from screens.stageselect import StageSelect


def test_stage_select_ctrl_shift_b_barrier_cheat():
    print("\n=== Testing Stage Select Ctrl+Shift+B Barrier Cheat ===")
    
    mock_menu = MagicMock()
    mock_menu.screen = screen
    mock_menu.student_id = "test_student"
    mock_menu.selected_student = {"first_name": "Hero"}
    mock_menu.audio_manager = MagicMock()
    
    with patch("db.save_system.get_completed_quarters", return_value={}):
        ss = StageSelect(screen, mock_menu)
        
        # 1. Verify default state - quarters 2, 3, 4 locked
        assert ss.barriers_lifted is False, "Barriers should not be lifted by default"
        assert ss.is_quarter_unlocked("quarter1") is True, "Quarter 1 is unlocked by default"
        assert ss.is_quarter_unlocked("quarter2") is False, "Quarter 2 should be locked"
        assert ss.is_quarter_unlocked("quarter3") is False, "Quarter 3 should be locked"
        assert ss.is_quarter_unlocked("quarter4") is False, "Quarter 4 should be locked"
        
        # Verify corridor collisions block player
        # South corridor (Q2): col 26, row 17 (pixel x: 26*32, y: 17*32)
        assert ss.can_move(26 * 32, 17 * 32) is False, "South corridor to Q2 must be blocked"
        # East corridor (Q3): col 29, row 13 (pixel x: 29*32, y: 13*32)
        assert ss.can_move(29 * 32, 13 * 32) is False, "East corridor to Q3 must be blocked"
        # North corridor (Q4): col 26, row 10 (pixel x: 26*32, y: 10*32)
        assert ss.can_move(26 * 32, 10 * 32) is False, "North corridor to Q4 must be blocked"
        print("[PASS] Initial state: Q2, Q3, Q4 are locked and corridors blocked.")
        
        # 2. Simulate Ctrl + Shift + B press
        cheat_event = pygame.event.Event(
            pygame.KEYDOWN,
            key=pygame.K_b,
            mod=pygame.KMOD_CTRL | pygame.KMOD_SHIFT
        )
        res = ss.handle_event(cheat_event)
        
        assert res == "barriers_toggled", f"Expected 'barriers_toggled', got {res}"
        assert ss.barriers_lifted is True, "barriers_lifted must be True after Ctrl+Shift+B"
        assert ss.is_quarter_unlocked("quarter2") is True, "Quarter 2 must be unlocked"
        assert ss.is_quarter_unlocked("quarter3") is True, "Quarter 3 must be unlocked"
        assert ss.is_quarter_unlocked("quarter4") is True, "Quarter 4 must be unlocked"
        
        # Verify corridor collisions are now lifted (walkable floor tiles)
        assert ss.can_move(26 * 32, 17 * 32) is True, "South corridor to Q2 must be walkable"
        assert ss.can_move(29 * 32, 13 * 32) is True, "East corridor to Q3 must be walkable"
        assert ss.can_move(26 * 32, 10 * 32) is True, "North corridor to Q4 must be walkable"
        
        # Verify audio feedback and banner message
        mock_menu.audio_manager.play_sfx.assert_called_with("success")
        assert "Lifted" in ss.locked_portal_banner_msg
        assert ss.locked_portal_banner_timer > 0
        print("[PASS] Ctrl+Shift+B activates barrier lifting across all quarters!")

        # 3. Verify state save
        ss.save_ss_state()
        assert mock_menu.last_stage_select_data["barriers_lifted"] is True, "barriers_lifted must be saved"

        # 4. Simulate pressing Ctrl + Shift + B again (toggle off)
        res2 = ss.handle_event(cheat_event)
        assert res2 == "barriers_toggled"
        assert ss.barriers_lifted is False, "barriers_lifted must be False after second press"
        assert ss.is_quarter_unlocked("quarter2") is False, "Quarter 2 must be locked again"
        assert ss.can_move(26 * 32, 17 * 32) is False, "South corridor must be blocked again"
        assert "Restored" in ss.locked_portal_banner_msg
        print("[PASS] Pressing Ctrl+Shift+B again successfully toggles barriers back on!")


if __name__ == "__main__":
    test_stage_select_ctrl_shift_b_barrier_cheat()
