# tests/test_quarter2_currency_matching.py
# Automated Unit & Integration Tests for Quarter 2 Philippine Currency Matching Game

import pytest
import pygame
import os
import sys

# Ensure project root is on sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Initialize headless pygame for testing
pygame.init()
pygame.display.set_mode((1280, 720), pygame.HIDDEN)

from core.philippine_currency import (
    PHILIPPINE_CURRENCY,
    get_randomized_quarter2_currency_pool,
    render_banknote_surface,
    render_coin_surface,
    render_currency_token
)
from screens.quarter2 import Quarter2


class DummyAudioManager:
    def play_sfx(self, name):
        pass
    def get_sound(self, name):
        return None


class DummyMainMenu:
    def __init__(self):
        self.audio_manager = DummyAudioManager()
        self.selected_student = {"id": 1, "username": "Juan", "first_name": "Juan", "level": "Grade 2", "gender": "boy"}
        self.student_db_id = 1
        self.student_id = 1
        self.current_screen = "quarter2"
        self.quarter1 = None
        self.quarter2 = None
        self.quarter3 = None
        self.quarter4 = None
        self.stage_select = None
        self.last_stage_select_data = None
        self.is_quarter_completed = lambda q: False


def test_currency_dataset_structure():
    """Verify all 10 Philippine banknotes and coins exist with required metadata (centavos excluded)"""
    assert len(PHILIPPINE_CURRENCY) == 10
    
    # 6 Banknotes (₱20, ₱50, ₱100, ₱200, ₱500, ₱1000)
    banknotes = [c for c in PHILIPPINE_CURRENCY.values() if c["type"] == "banknote"]
    assert len(banknotes) == 6
    banknote_vals = [c["value_peso"] for c in banknotes]
    assert sorted(banknote_vals) == [20.0, 50.0, 100.0, 200.0, 500.0, 1000.0]
    
    # 4 Coins (₱1, ₱5, ₱10, ₱20) - 1c, 5c, 25c excluded
    coins = [c for c in PHILIPPINE_CURRENCY.values() if c["type"] == "coin"]
    assert len(coins) == 4
    coin_vals = [c["value_peso"] for c in coins]
    assert 0.01 not in coin_vals
    assert 0.05 not in coin_vals
    assert 0.25 not in coin_vals
    assert 1.0 in coin_vals
    assert 5.0 in coin_vals
    assert 10.0 in coin_vals
    assert 20.0 in coin_vals


def test_randomized_currency_pools_per_map():
    """Verify that get_randomized_quarter2_currency_pool yields valid random sets for maps"""
    maps = ["map4.txt", "map5.txt", "map6.txt", "map2.txt"]
    for m in maps:
        pool = get_randomized_quarter2_currency_pool(m, num_items=5)
        assert len(pool) == 5
        # Ensure unique IDs in each pool
        ids = [item["id"] for item in pool]
        assert len(ids) == len(set(ids))
        # Ensure both banknotes and coins can be included
        for item in pool:
            assert "name" in item
            assert "value_text" in item
            assert "type" in item
            assert "color_accent" in item


def test_currency_surface_renderers():
    """Verify procedural vector currency renderers return valid Pygame surfaces"""
    for item in PHILIPPINE_CURRENCY.values():
        token = render_currency_token(item, 160, 90)
        assert isinstance(token, pygame.Surface)
        assert token.get_width() == 160
        assert token.get_height() == 90
        
        if item["type"] == "banknote":
            surf = render_banknote_surface(item, 160, 90)
            assert isinstance(surf, pygame.Surface)
        else:
            surf = render_coin_surface(item, 160, 90)
            assert isinstance(surf, pygame.Surface)


def test_knight_guardian_placement_in_quarter2():
    """Verify Knight Guardian is spawned guarding the portal in Quarter 2 maps"""
    screen = pygame.display.get_surface()
    main_menu = DummyMainMenu()
    
    for map_name in ["map4.txt", "map5.txt", "map6.txt"]:
        q2 = Quarter2(screen, main_menu, map_name)
        assert q2.npc_knight_found is True
        assert len(q2.portals) > 0
        exit_p = q2.portals[0]
        p_tx = exit_p.x
        p_ty = exit_p.y
        # Knight is placed adjacent to the portal
        assert abs(q2.npc_knight_tile_x - p_tx) <= 1
        assert abs(q2.npc_knight_tile_y - p_ty) <= 1


def test_currency_puzzle_initialization_and_reset():
    """Verify the currency matching puzzle initializes and resets properly"""
    screen = pygame.display.get_surface()
    main_menu = DummyMainMenu()
    q2 = Quarter2(screen, main_menu, "map4.txt")
    
    q2.init_currency_matching_puzzle()
    assert len(q2.currency_puzzle_slots) == 5
    assert len(q2.currency_puzzle_pieces) == 5
    assert q2.currency_puzzle_solved is False
    assert q2.currency_puzzle_all_placed is False
    
    # Simulate matching slot 0
    slot0 = q2.currency_puzzle_slots[0]
    matching_piece = next(p for p in q2.currency_puzzle_pieces if p["id"] == slot0["id"])
    
    q2.dragged_currency_piece = matching_piece
    # Move dragged piece center onto slot0
    matching_piece["x"] = slot0["rect"].centerx - matching_piece["w"] // 2
    matching_piece["y"] = slot0["rect"].centery - matching_piece["h"] // 2
    
    q2.release_dragged_currency_piece()
    assert slot0["matched"] is True
    assert matching_piece["is_placed"] is True
    
    # Test reset
    q2.reset_currency_matching_puzzle()
    assert slot0["matched"] is False
    assert matching_piece["is_placed"] is False
    assert q2.currency_puzzle_all_placed is False


def test_full_quarter2_progression_to_guardian_and_portal_unlock():
    """Verify complete flow: stations 1-5 -> Knight Guardian -> Currency Matching -> Portal Unlocked"""
    screen = pygame.display.get_surface()
    main_menu = DummyMainMenu()
    q2 = Quarter2(screen, main_menu, "map4.txt")
    if getattr(q2, 'instruction_modal', None):
        q2.instruction_modal.hide()
    
    # Step 1: Simulate completing stations 1 to 4
    for st in range(1, 5):
        q2.quiz_station_index = st
        q2.quiz_state = 3
        # Click correct button to advance
        q2.trigger_click((q2.width // 2, q2.height // 2))
        assert q2.quiz_station_index == st + 1
    
    # Step 2: Complete Station 5
    q2.quiz_station_index = 5
    q2.quiz_state = 3
    q2.trigger_click((q2.width // 2, q2.height // 2))
    
    # Now all 5 stations are cleared; station index is 6 and Knight Guardian is active
    assert q2.quiz_station_index == 6
    assert q2.guardian_knight_state == 1
    assert q2.currency_puzzle_solved is False
    assert q2.quiz_state == 0
    
    # Step 3: Player moves near Knight Guardian
    q2.player_x = q2.npc_knight_x
    q2.player_y = q2.npc_knight_y
    q2.update()
    
    # Guardian greeting / challenge prompt modal opens
    assert q2.guardian_knight_state == 2
    assert q2.currency_trial_start_btn_rect is not None
    
    # Step 4: Click 'Begin Currency Trial'
    q2.trigger_click(q2.currency_trial_start_btn_rect.center)
    assert q2.guardian_knight_state == 3
    assert q2.currency_puzzle_active is True
    assert len(q2.currency_puzzle_slots) == 5
    
    # Step 5: Solve the currency matching puzzle (match all 5 pieces)
    for slot in q2.currency_puzzle_slots:
        piece = next(p for p in q2.currency_puzzle_pieces if p["id"] == slot["id"])
        q2.dragged_currency_piece = piece
        piece["x"] = slot["rect"].centerx - piece["w"] // 2
        piece["y"] = slot["rect"].centery - piece["h"] // 2
        q2.release_dragged_currency_piece()
        assert slot["matched"] is True
    
    assert q2.currency_puzzle_all_placed is True
    assert q2.currency_puzzle_continue_btn_rect is not None
    
    # Step 6: Click 'Unlock Portal >>' on the puzzle board
    q2.trigger_click(q2.currency_puzzle_continue_btn_rect.center)
    assert q2.currency_puzzle_active is False
    assert q2.currency_puzzle_solved is True
    assert q2.guardian_knight_state == 4
    assert q2.quiz_state == 5  # Final victory speech from Knight
    
    # Step 7: Click 'Enter Portal >>' in victory speech (quiz_state = 5)
    assert q2.victory_btn_rect is not None
    q2.trigger_click(q2.victory_btn_rect.center)
    
    # Portal is unlocked!
    assert q2.quiz_state == 6
    assert q2.guardian_knight_state == 5
