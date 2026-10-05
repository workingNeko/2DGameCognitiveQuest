import os
import sys
from unittest.mock import MagicMock, patch

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pygame
pygame.init()
screen = pygame.display.set_mode((1280, 720))

from screens.quarter1 import Quarter1
from screens.quarter2 import Quarter2
from screens.quarter3 import Quarter3
from screens.quarter4 import Quarter4
from screens.tutorial import TutorialScreen


def test_quarter1_complete_objectives_shortcut():
    print("\n=== Testing Quarter 1 Complete Objectives Shortcut ===")
    mock_menu = MagicMock()
    mock_menu.screen = screen
    mock_menu.selected_student = {"first_name": "Hero"}
    mock_menu.audio_manager = MagicMock()

    q1 = Quarter1(screen, mock_menu, map_name="map1.txt")
    assert q1.quiz_station_index == 1
    assert q1.puzzle_solved is False

    # Tier 1: First press of 'O' completes 5 shape stations, builds river bridge, teleports to Old Man, and opens Old Man dialog
    event_o1 = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_o, mod=0)
    res1 = q1.handle_event(event_o1)
    assert res1 == "shortcut_complete"
    assert q1.quiz_station_index == 6
    assert q1.puzzle_solved is False  # Puzzle is primed, player is talking to Old Man
    assert q1.quiz_state == 22        # Old Man conversation active!
    assert all(s["answered"] for s in q1.shape_npcs.values())
    assert "B" in q1.game_map[3] or "B" in q1.game_map[4]  # Bridge built

    # Tier 2: Second press of 'O' while in dialog solves the bridge puzzle & unlocks exit portal
    event_o2 = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_o, mod=0)
    res2 = q1.handle_event(event_o2)
    assert res2 == "shortcut_complete"
    assert q1.puzzle_solved is True
    assert q1.quiz_state == 0
    print("[PASS] Quarter 1 2-tier shortcut successfully primes Old Man dialog (Tier 1) and solves puzzle (Tier 2)!")


def test_quarter2_complete_objectives_shortcut():
    print("\n=== Testing Quarter 2 Complete Objectives Shortcut ===")
    mock_menu = MagicMock()
    mock_menu.screen = screen
    mock_menu.selected_student = {"first_name": "Hero"}
    mock_menu.audio_manager = MagicMock()

    q2 = Quarter2(screen, mock_menu, map_name="map5.txt")
    assert q2.quiz_station_index == 1
    assert q2.currency_puzzle_solved is False

    # Tier 1: First press of 'O' completes 5 stalls, builds Bahay Kubo, teleports to Knight Guardian, and opens trial prompt
    event_o1 = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_o, mod=0)
    res1 = q2.handle_event(event_o1)
    assert res1 == "shortcut_complete"
    assert q2.quiz_station_index == 6
    assert q2.currency_puzzle_solved is False  # Ready to talk/take trial
    assert q2.guardian_knight_state == 2       # Knight Guardian trial prompt active!
    assert q2.kubo_built is True

    # Tier 2: Second press of 'O' solves the Currency puzzle & unlocks Grand Fiesta exit portal
    event_o2 = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_o, mod=0)
    res2 = q2.handle_event(event_o2)
    assert res2 == "shortcut_complete"
    assert q2.currency_puzzle_solved is True
    assert q2.currency_puzzle_all_placed is True
    assert q2.guardian_knight_state == 5
    assert q2.quiz_state == 6
    print("[PASS] Quarter 2 2-tier shortcut successfully primes Knight Guardian trial (Tier 1) and solves puzzle (Tier 2)!")


def test_quarter3_complete_objectives_shortcut():
    print("\n=== Testing Quarter 3 Complete Objectives Shortcut ===")
    mock_menu = MagicMock()
    mock_menu.screen = screen
    mock_menu.selected_student = {"first_name": "Hero"}
    mock_menu.audio_manager = MagicMock()

    q3 = Quarter3(screen, mock_menu, map_name="map8.txt")
    assert q3.quiz_station_index == 1
    assert q3.solar_array_puzzle_solved is False

    # Tier 1: First press of 'O' completes 5 stations, builds aqueduct, teleports to Skeleton Guardian, and opens prompt
    event_o1 = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_o, mod=0)
    res1 = q3.handle_event(event_o1)
    assert res1 == "shortcut_complete"
    assert q3.quiz_station_index == 6
    assert q3.solar_array_puzzle_solved is False  # Ready to talk/take trial
    assert q3.guardian_skeleton_state == 2        # Skeleton Guardian trial prompt active!

    # Tier 2: Second press of 'O' solves the Solar Array puzzle & unlocks Desert Sun exit portal
    event_o2 = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_o, mod=0)
    res2 = q3.handle_event(event_o2)
    assert res2 == "shortcut_complete"
    assert q3.solar_array_puzzle_solved is True
    assert q3.solar_array_puzzle_all_placed is True
    assert q3.guardian_skeleton_state == 5
    assert q3.quiz_state == 6
    print("[PASS] Quarter 3 2-tier shortcut successfully primes Skeleton Guardian trial (Tier 1) and solves puzzle (Tier 2)!")


def test_quarter4_complete_objectives_shortcut():
    print("\n=== Testing Quarter 4 Complete Objectives Shortcut ===")
    mock_menu = MagicMock()
    mock_menu.screen = screen
    mock_menu.selected_student = {"first_name": "Hero"}
    mock_menu.audio_manager = MagicMock()

    q4 = Quarter4(screen, mock_menu, map_name="map12.txt")
    assert len(q4.answered_stations) == 0
    assert q4.key_puzzle_solved is False

    # Tier 1: First press of Ctrl+C collects all 6 keys, readies Lotus Raft, teleports to Bromen, and opens dialog
    event_ctrl_c = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_c, mod=pygame.KMOD_CTRL)
    res1 = q4.handle_event(event_ctrl_c)
    assert res1 == "shortcut_complete"
    assert len(q4.answered_stations) >= 6
    assert q4.key_puzzle_solved is False  # Ready to talk/take trial
    assert q4.bromen_dialogue_state == 2  # Bromen dialogue active!
    assert q4.raft_state == "ready_to_sail"

    # Tier 2: Second press of Ctrl+C solves the Key Lock puzzle & unlocks Exit Portal
    event_ctrl_c2 = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_c, mod=pygame.KMOD_CTRL)
    res2 = q4.handle_event(event_ctrl_c2)
    assert res2 == "shortcut_complete"
    assert q4.key_puzzle_solved is True
    assert q4.emblem_puzzle_solved is True
    assert q4.bromen_dialogue_state == 3
    assert q4.quiz_state == 6
    print("[PASS] Quarter 4 2-tier shortcut successfully primes Bromen dialogue (Tier 1) and solves puzzle (Tier 2)!")


def test_tutorial_complete_objectives_shortcut():
    print("\n=== Testing Tutorial Complete Objectives Shortcut ===")
    mock_menu = MagicMock()
    mock_menu.screen = screen
    mock_menu.audio_manager = MagicMock()

    tut = TutorialScreen(screen, mock_menu)
    assert tut.phase == 1

    # Trigger shortcut via 'F10' key
    event_f10 = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F10, mod=0)
    res = tut.handle_event(event_f10)
    assert res == "shortcut_complete"
    assert tut.phase == 4
    assert tut.quiz_state == 0
    print("[PASS] Tutorial shortcut successfully unlocks exit portal and completes tutorial phase!")


if __name__ == "__main__":
    test_quarter1_complete_objectives_shortcut()
    test_quarter2_complete_objectives_shortcut()
    test_quarter3_complete_objectives_shortcut()
    test_quarter4_complete_objectives_shortcut()
    test_tutorial_complete_objectives_shortcut()
    print("\nALL OBJECTIVE SHORTCUT TESTS PASSED SUCCESSFULLY!")
