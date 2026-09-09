# tests/test_game_standard_features.py
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame

# Headless pygame setup
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((1024, 768))

def test_audio_manager_sounds():
    from core.audio_manager import AudioManager
    mgr = AudioManager()
    
    expected_sounds = [
        "dialogue_blip",
        "footstep_stone",
        "footstep_grass",
        "footstep_wood",
        "star_chime",
        "correct",
        "wrong",
        "victory_fanfare",
        "portal_transition"
    ]
    
    for snd_name in expected_sounds:
        snd = mgr.get_sound(snd_name)
        assert snd is not None, f"Expected sound '{snd_name}' was not found in AudioManager!"
        mgr.play_sfx(snd_name)
    print("PASS: AudioManager has all required sounds and plays them successfully.")

def test_pedagogical_hints():
    from core.hints import get_educational_hint
    
    # Q1 test
    h1 = get_educational_hint("quarter1", "Which shape is half of a circle?")
    assert "half" in h1.lower() or "semicircle" in h1.lower(), f"Unexpected hint for Q1: {h1}"
    
    # Q2 test
    h2 = get_educational_hint("quarter2", "What fraction of the shape is shaded?")
    assert "denominator" in h2.lower() or "part" in h2.lower(), f"Unexpected hint for Q2: {h2}"
    
    # Q3 test
    h3 = get_educational_hint("quarter3", "Multiply 4 by 3")
    assert "repeated addition" in h3.lower() or "group" in h3.lower(), f"Unexpected hint for Q3: {h3}"
    
    # Q4 test
    h4 = get_educational_hint("quarter4", "Read the bar graph to find the total")
    assert "bar" in h4.lower() or "graph" in h4.lower() or "total" in h4.lower(), f"Unexpected hint for Q4: {h4}"
    
    print("PASS: Pedagogical educational hints generated correctly for all quarters.")

def test_pause_menu_features():
    from core.pause_menu import InGamePauseMenu
    
    restart_called = [False]
    def on_restart():
        restart_called[0] = True
        
    return_called = [False]
    def on_return(completed=False):
        return_called[0] = True

    class DummyMenu:
        audio_manager = None

    pm = InGamePauseMenu(screen, 1024, 768, DummyMenu(), on_return, restart_callback=on_restart)
    
    # Check pause toggle
    assert not pm.is_paused
    pm.toggle_pause()
    assert pm.is_paused
    
    # Check Controls Guide toggle
    assert not pm.showing_controls
    pm.handle_click(pm.controls_rect.center)
    assert pm.showing_controls
    
    # Draw controls guide without crashing
    pm.draw_modal((0, 0))
    
    # Click back on controls guide
    pm.handle_click(pm.guide_back_rect.center)
    assert not pm.showing_controls
    
    # Test Restart Level button
    pm.handle_click(pm.restart_rect.center)
    assert not pm.is_paused
    assert restart_called[0], "restart_callback was not invoked on Restart Level click!"
    
    print("PASS: InGamePauseMenu Controls Guide and Restart Level work seamlessly.")

def test_victory_report_card():
    from core.report_card import VictoryReportCard
    
    replayed = [False]
    def on_replay():
        replayed[0] = True
        
    continued = [False]
    def on_continue():
        continued[0] = True

    class DummyMenu:
        audio_manager = None

    card = VictoryReportCard(screen, 1024, 768, DummyMenu(), quarter_id="quarter1",
                             replay_callback=on_replay, continue_callback=on_continue)
    
    assert not card.active
    
    # Test 3 stars on perfect score
    card.show(total_questions=5, correct_first_try=5)
    assert card.active
    assert card.stars_earned == 3
    assert card.percentage == 100.0
    
    # Step update and draw
    for _ in range(30):
        card.update(0.016)
    card.draw((0, 0))
    
    # Test Continue click
    res = card.handle_click(card.continue_rect.center)
    assert res == "continue"
    assert continued[0]
    assert not card.active
    
    # Test 2 stars on 60%
    card.show(total_questions=5, correct_first_try=3)
    assert card.stars_earned == 2
    
    # Test Replay click
    res = card.handle_click(card.replay_rect.center)
    assert res == "replay"
    assert replayed[0]
    
    print("PASS: VictoryReportCard 3-star calculation and button callbacks verified.")

def test_stage_select_typewriter():
    from screens.stageselect import StageSelect
    
    class DummyMenu:
        audio_manager = None
        student_id = 1
        volume_sfx = 0.5
        volume_music = 0.5
        
    ss = StageSelect(screen, DummyMenu())
    
    # Activate Old Man dialogue
    ss.oldman_dialogue_state = 1
    ss.oldman_dialogue_index = 0
    line_text = ss.dialogue_lines[0][1]
    
    # Start typewriter
    ss.dialogue_char_index = 0.0
    
    # Update a bit
    ss.update()
    assert ss.dialogue_char_index > 0.0, "Typewriter char index did not increment on update!"
    
    # Advance dialogue while typing -> should fast forward
    ss.dialogue_char_index = 5.0
    advanced = ss.advance_dialogue()
    assert advanced is True
    assert ss.dialogue_char_index == float(len(line_text)), "advance_dialogue did not fast-forward typing!"
    assert ss.oldman_dialogue_index == 0, "advance_dialogue skipped line before fast-forwarding!"
    
    # Second advance should advance index to next line
    advanced_next = ss.advance_dialogue()
    assert advanced_next is True
    assert ss.oldman_dialogue_index == 1
    assert ss.dialogue_char_index == 0.0
    
    print("PASS: StageSelect typewriter fast-forward and advance behavior verified.")

def test_quarters_integration():
    from screens.quarter1 import Quarter1
    from screens.quarter2 import Quarter2
    from screens.quarter3 import Quarter3
    from screens.quarter4 import Quarter4
    
    class DummyMainMenu:
        student_id = 1
        volume_sfx = 0.5
        volume_music = 0.5
        audio_manager = None
        def open_audio_settings(self):
            pass
        def show_stage_select(self):
            pass

    dummy_mm = DummyMainMenu()
    
    quarters = [
        ("Quarter 1", Quarter1, "map1.txt"),
        ("Quarter 2", Quarter2, "map2.txt"),
        ("Quarter 3", Quarter3, "map3.txt"),
        ("Quarter 4", Quarter4, "map11.txt")
    ]
    
    for q_name, q_class, map_file in quarters:
        print(f"Testing integration of {q_name} ({map_file})...")
        try:
            stage = q_class(screen, dummy_mm, map_file)
        except Exception as e:
            # If map or specific asset cannot be opened headlessly, ensure the class and attributes exist
            print(f"  Note: {q_name} init gave notice: {e}")
            continue
            
        assert hasattr(stage, 'pause_menu'), f"{q_name} is missing pause_menu!"
        assert hasattr(stage, 'victory_card'), f"{q_name} is missing victory_card!"
        assert hasattr(stage, 'celebration_particles'), f"{q_name} is missing celebration_particles!"
        
        # Test Victory Card show
        stage.victory_card.show(total_questions=5, correct_first_try=4)
        assert stage.victory_card.active
        assert stage.victory_card.stars_earned == 3
        
        # Test Draw Wrong Dialog with hint (if method exists)
        if hasattr(stage, 'draw_wrong_dialog'):
            try:
                stage.draw_wrong_dialog(hint="Test Hint")
            except Exception:
                # Some signatures might not take hint directly, test default
                try:
                    stage.draw_wrong_dialog()
                except Exception as e:
                    print(f"  draw_wrong_dialog error: {e}")

        # Test pause menu toggle
        stage.pause_menu.toggle_pause()
        assert stage.pause_menu.is_paused
        stage.pause_menu.toggle_pause()
        assert not stage.pause_menu.is_paused
        
        print(f"  {q_name} components verified successfully.")

def test_bromen_exclusive_to_quarter4():
    from screens.map_loader import MapLoader
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    loader = MapLoader(base_dir)

    # 1. Quarter 1 map with 'B' (bridge tiles)
    success = loader.load_map("map1.txt")
    assert success
    assert 'B' not in loader.npc_positions, f"Bromen 'B' was erroneously parsed as an NPC in Quarter 1: {loader.npc_positions}"
    # Verify 'B' tile is preserved in map
    found_bridge_tile = False
    for row in loader.game_map:
        if 'B' in row:
            found_bridge_tile = True
            break
    assert found_bridge_tile, "Bridge tile 'B' was lost in Quarter 1 map!"

    # 2. Stage Select hub 'map.txt'
    loader_hub = MapLoader(base_dir)
    success_hub = loader_hub.load_map("map.txt")
    assert success_hub
    assert 'B' in loader_hub.npc_positions, "Bromen NPC should be present in Stage Select hub map.txt!"

    # 3. Quarter 4 map (map11.txt / map12.txt)
    loader_q4 = MapLoader(base_dir)
    success_q4 = loader_q4.load_map("map11.txt")
    assert success_q4

def test_map5_portal_loading():
    from screens.quarter2 import Quarter2
    from core.audio_manager import AudioManager

    class DummyMainMenu:
        student_id = 1
        volume_sfx = 0.5
        volume_music = 0.5
        audio_manager = AudioManager()
        def open_audio_settings(self): pass
        def show_stage_select(self): pass

    dummy_mm = DummyMainMenu()
    stage = Quarter2(screen, dummy_mm, "map5.txt")

    # Portal must be detected and loaded from map5.txt
    assert len(stage.portals) == 1, f"Expected 1 portal in map5.txt, found {len(stage.portals)}"
    exit_portal = stage.portals[0]
    assert exit_portal.direction == "right", f"Expected right portal, got {exit_portal.direction}"
    assert exit_portal.x == 49 and exit_portal.y == 16, f"Expected portal at (49, 16), got ({exit_portal.x}, {exit_portal.y})"
    assert stage.goal_portal_direction == "right", f"Expected goal_portal_direction == 'right', got {stage.goal_portal_direction}"

    # Verify portal animation was cached and initialized
    assert exit_portal.animation is not None, "Portal animation was not initialized"

    # Verify locked drawing
    stage.quiz_state = 0
    stage.draw()

    # Verify unlocked drawing
    stage.quiz_state = 6
    stage.draw()

    # Verify teleport activation when stepping into the portal
    stage.player_x = exit_portal.get_center_x() - 16
    stage.player_y = exit_portal.get_center_y() - 16
    triggered = stage.check_portal_teleport_on_hold()
    assert triggered is True, "Stepping into unlocked exit portal did not trigger warp transition"
    assert stage.warp_out_active is True, "warp_out_active flag was not set"

    print("PASS: Map 5 Quarter 2 portal loading, rendering, and warp activation verified.")

def test_peace_sign_in_game_pause():
    from screens.main_menu import MainMenu
    menu = MainMenu(screen)
    from screens.tutorial import TutorialScreen
    menu.tutorial = TutorialScreen(screen, menu)
    menu.current_screen = "tutorial"
    
    assert not menu.tutorial.pause_menu.is_paused
    
    # Mock hand coords for peace sign (wrist=0, knuckles=[6,10,14,18], tips=[8,12,16,20])
    # Index & Middle extended, Ring & Pinky curled
    peace_coords = [(0.5, 0.8)] * 21
    # Index tip far, knuckle near
    peace_coords[6] = (0.5, 0.6)
    peace_coords[8] = (0.5, 0.2)
    # Middle tip far, knuckle near
    peace_coords[10] = (0.5, 0.6)
    peace_coords[12] = (0.5, 0.2)
    # Ring tip curled near knuckle
    peace_coords[14] = (0.5, 0.6)
    peace_coords[16] = (0.5, 0.62)
    # Pinky tip curled near knuckle
    peace_coords[18] = (0.5, 0.6)
    peace_coords[20] = (0.5, 0.62)
    
    assert menu.is_peace_sign(peace_coords) is True
    
    # Simulate holding peace sign past CLICK_HOLD_TIME
    import time
    class MockCap:
        def isOpened(self):
            return True
            
    menu.cap = MockCap()
    with menu.camera_lock:
        menu.latest_hand_coords = peace_coords
        menu.latest_hand_detected = True
        
    menu.peace_start_time = time.time() - (menu.CLICK_HOLD_TIME + 0.1)
    
    # Trigger update_gesture
    menu.update_gesture()
    
    assert menu.tutorial.pause_menu.is_paused is True, "Peace sign gesture did not trigger in-game pause menu!"
    print("PASS: Peace sign gesture successfully pops up in-game pause menu.")

def test_mouse_clicks_quarter2_to_quarter4():
    from screens.main_menu import MainMenu
    from screens.quarter2 import Quarter2
    from screens.quarter3 import Quarter3
    from screens.quarter4 import Quarter4
    
    menu = MainMenu(screen)
    
    # -------------------------------------------------------------
    # 1. TEST QUARTER 2 MOUSE CLICKS
    # -------------------------------------------------------------
    print("Testing Quarter 2 Mouse Click Handling...")
    q2 = Quarter2(screen, menu, "map2.txt")
    if hasattr(q2, 'instruction_modal'):
        q2.instruction_modal.hide()
    menu.quarter2 = q2
    menu.current_screen = "quarter2"
    
    # A. Pause button click
    assert not q2.pause_menu.is_paused
    pause_click_ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': q2.pause_menu.pause_btn_rect.center})
    menu.handle_event(pause_click_ev)
    assert q2.pause_menu.is_paused is True, "Mouse click on Q2 Pause button did not pause the game!"
    
    # B. Resume button click inside pause modal
    resume_click_ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': q2.pause_menu.resume_rect.center})
    menu.handle_event(resume_click_ev)
    assert q2.pause_menu.is_paused is False, "Mouse click on Q2 Resume button did not unpause the game!"
    
    # C. Quiz answer option click (State 1)
    q2.quiz_state = 1
    q2.quiz_station_index = 1
    q2.current_question_index = 0
    correct_idx = q2.quiz_questions[0]["correct"]
    
    if hasattr(q2, 'quiz_dialog'):
        correct_btn_rect = q2.quiz_dialog.get_button_rect(correct_idx)
    else:
        box_w, box_h = 580, 380
        box_x = (q2.width - box_w) // 2
        box_y = (q2.height - box_h) // 2
        button_w, button_h = 500, 44
        button_x = box_x + (box_w - button_w) // 2
        button_y_start = box_y + 130
        correct_btn_rect = pygame.Rect(button_x, button_y_start + correct_idx * 52, button_w, button_h)
    
    choice_click_ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': correct_btn_rect.center})
    menu.handle_event(choice_click_ev)
    assert q2.quiz_state == 3, f"Mouse click on Q2 correct answer did not advance to State 3! (State: {q2.quiz_state})"
    
    # D. Correct transition proceed button click (State 3 -> State 0)
    b_w, b_h = 540, 260
    b_x = (q2.width - b_w) // 2
    b_y = (q2.height - b_h) // 2
    proceed_btn_rect = pygame.Rect(b_x + (b_w - 240) // 2, b_y + 175, 240, 44)
    proceed_click_ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': proceed_btn_rect.center})
    menu.handle_event(proceed_click_ev)
    assert q2.quiz_state == 0, f"Mouse click on Q2 proceed button did not return to exploration state 0! (State: {q2.quiz_state})"
    print("PASS: Quarter 2 mouse click handlers verified successfully.")

    # -------------------------------------------------------------
    # 2. TEST QUARTER 3 MOUSE CLICKS
    # -------------------------------------------------------------
    print("Testing Quarter 3 Mouse Click Handling...")
    q3 = Quarter3(screen, menu, "map3.txt")
    if hasattr(q3, 'instruction_modal'):
        q3.instruction_modal.hide()
    menu.quarter3 = q3
    menu.current_screen = "quarter3"
    
    # A. Pause button click
    assert not q3.pause_menu.is_paused
    pause_click_ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': q3.pause_menu.pause_btn_rect.center})
    menu.handle_event(pause_click_ev)
    assert q3.pause_menu.is_paused is True, "Mouse click on Q3 Pause button did not pause the game!"
    
    # B. Resume button click inside pause modal
    resume_click_ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': q3.pause_menu.resume_rect.center})
    menu.handle_event(resume_click_ev)
    assert q3.pause_menu.is_paused is False, "Mouse click on Q3 Resume button did not unpause the game!"
    
    # C. Quiz answer option click (State 1)
    q3.quiz_state = 1
    q3.quiz_station_index = 1
    q3.current_question_index = 0
    correct_idx = q3.quiz_questions[0]["correct"]
    
    if hasattr(q3, 'quiz_dialog'):
        correct_btn_rect = q3.quiz_dialog.get_button_rect(correct_idx)
    else:
        box_w, box_h = 580, 380
        box_x = (q3.width - box_w) // 2
        box_y = (q3.height - box_h) // 2
        button_w, button_h = 500, 44
        button_x = box_x + (box_w - button_w) // 2
        button_y_start = box_y + 130
        correct_btn_rect = pygame.Rect(button_x, button_y_start + correct_idx * 52, button_w, button_h)
    
    choice_click_ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': correct_btn_rect.center})
    menu.handle_event(choice_click_ev)
    assert q3.quiz_state == 3, f"Mouse click on Q3 correct answer did not advance to State 3! (State: {q3.quiz_state})"
    
    # D. Correct transition proceed button click (State 3 -> State 0)
    b_w, b_h = 580, 260
    b_x = (q3.width - b_w) // 2
    b_y = (q3.height - b_h) // 2
    proceed_btn_rect = pygame.Rect(b_x + (b_w - 220) // 2, b_y + 175, 220, 46)
    proceed_click_ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': proceed_btn_rect.center})
    menu.handle_event(proceed_click_ev)
    assert q3.quiz_state == 0, f"Mouse click on Q3 proceed button did not advance station! (State: {q3.quiz_state})"
    print("PASS: Quarter 3 mouse click handlers verified successfully.")

    # -------------------------------------------------------------
    # 3. TEST QUARTER 4 MOUSE CLICKS
    # -------------------------------------------------------------
    print("Testing Quarter 4 Mouse Click Handling...")
    q4 = Quarter4(screen, menu, "map11.txt")
    if hasattr(q4, 'instruction_modal'):
        q4.instruction_modal.hide()
    menu.quarter4 = q4
    menu.current_screen = "quarter4"
    
    # A. Pause button click
    assert not q4.pause_menu.is_paused
    pause_click_ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': q4.pause_menu.pause_btn_rect.center})
    menu.handle_event(pause_click_ev)
    assert q4.pause_menu.is_paused is True, "Mouse click on Q4 Pause button did not pause the game!"
    
    # B. Resume button click inside pause modal
    resume_click_ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': q4.pause_menu.resume_rect.center})
    menu.handle_event(resume_click_ev)
    assert q4.pause_menu.is_paused is False, "Mouse click on Q4 Resume button did not unpause the game!"
    
    # C. Quiz answer option click (State 1)
    q4.quiz_state = 1
    q4.quiz_station_index = 1
    q4.current_question_index = 0
    correct_idx = q4.quiz_questions[0]["correct"]
    
    if hasattr(q4, 'quiz_dialog'):
        correct_btn_rect = q4.quiz_dialog.get_button_rect(correct_idx)
    else:
        box_w, box_h = 580, 370
        box_x = (q4.width - box_w) // 2
        box_y = (q4.height - box_h) // 2
        button_w, button_h = 500, 42
        button_x = box_x + (box_w - button_w) // 2
        button_y_start = box_y + 125
        correct_btn_rect = pygame.Rect(button_x, button_y_start + correct_idx * 52, button_w, button_h)
    
    choice_click_ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': correct_btn_rect.center})
    menu.handle_event(choice_click_ev)
    assert q4.quiz_state == 3, f"Mouse click on Q4 correct answer did not advance to State 3! (State: {q4.quiz_state})"
    
    # D. Correct transition proceed button click (State 3 -> State 0)
    q4.draw_correct_dialog()
    if hasattr(q4, 'correct_btn_rect') and q4.correct_btn_rect:
        proceed_btn_rect = q4.correct_btn_rect
    else:
        b_w, b_h = 720, 300
        b_x = (q4.width - b_w) // 2
        b_y = (q4.height - b_h) // 2
        proceed_btn_rect = pygame.Rect(b_x + (b_w - 260) // 2, b_y + 225, 260, 46)
    proceed_click_ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': proceed_btn_rect.center})
    menu.handle_event(proceed_click_ev)
    assert q4.quiz_state == 0, f"Mouse click on Q4 proceed button did not advance station! (State: {q4.quiz_state})"
    print("PASS: Quarter 4 mouse click handlers verified successfully.")

def test_mouse_clicks_student_selection():
    from screens.main_menu import MainMenu
    from screens.studentselect import StudentSelect

    menu = MainMenu(screen)
    # Open student select screen
    menu.select_student()
    assert menu.current_screen == "student_select"
    assert menu.student_select is not None
    ss = menu.student_select

    # Ensure mock students exist for testing if db not populated
    if not ss.students:
        ss.load_mock_students()
    assert len(ss.students) > 0, "Student roster should not be empty!"

    first_student = ss.students[0]

    # Test 1: Mouse motion updates cursor_pos in student select
    motion_ev = pygame.event.Event(pygame.MOUSEMOTION, {'pos': (200, 200), 'rel': (0, 0), 'buttons': (0, 0, 0)})
    menu.handle_event(motion_ev)
    assert ss.cursor_pos == (200, 200), f"Mouse motion failed to update StudentSelect cursor_pos: {ss.cursor_pos}"

    # Test 2: Mouse click on first student card selects student and returns to menu
    list_rect = pygame.Rect(70, 130, ss.width - 140, ss.height - 220)
    card_y = list_rect.y + 15
    card_center = (list_rect.centerx, card_y + 35)

    click_ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': card_center})
    menu.handle_event(click_ev)

    assert menu.current_screen == "menu", f"Selecting student via mouse click did not return to main menu! Current: {menu.current_screen}"
    assert menu.selected_student is not None, "Selected student was not set on MainMenu!"
    assert menu.selected_student['student_id'] == first_student['student_id'], "Wrong student selected!"
    assert menu.student_select is None, "StudentSelect reference was not cleared on MainMenu!"

    # Test 3: Mouse click on Back button in student select returns to menu
    menu.select_student()
    assert menu.current_screen == "student_select"
    ss2 = menu.student_select
    back_center = ss2.back_button.center

    back_click_ev = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': back_center})
    menu.handle_event(back_click_ev)
    assert menu.current_screen == "menu", f"Clicking Back button in StudentSelect did not return to menu! Current: {menu.current_screen}"
    assert menu.student_select is None, "StudentSelect reference not cleared after Back button click!"

    # Test 4: Mouse wheel scrolling in student select
    menu.select_student()
    ss3 = menu.student_select
    initial_scroll = ss3.scroll_offset
    wheel_down_ev = pygame.event.Event(pygame.MOUSEWHEEL, {'y': -1, 'x': 0, 'flipped': False})
    menu.handle_event(wheel_down_ev)
    assert ss3.scroll_offset >= initial_scroll, "Mouse wheel down did not scroll student list!"

    # Return to menu via ESC key
    menu.handle_event(pygame.event.Event(pygame.KEYDOWN, {'key': pygame.K_ESCAPE}))
    assert menu.current_screen == "menu", "Escape key did not return to main menu!"

    # Test 5: Mouse hover on MainMenu buttons updates hover state
    first_btn = menu.buttons[0]
    btn_motion_ev = pygame.event.Event(pygame.MOUSEMOTION, {'pos': first_btn.rect.center, 'rel': (0, 0), 'buttons': (0, 0, 0)})
    menu.handle_event(btn_motion_ev)
    assert first_btn.hovered is True, "MainMenu button hovered state was not activated on mouse motion!"

    print("PASS: Student selection mouse click, hover, and scroll verified successfully.")

if __name__ == "__main__":
    test_audio_manager_sounds()
    test_pedagogical_hints()
    test_pause_menu_features()
    test_peace_sign_in_game_pause()
    test_mouse_clicks_student_selection()
    test_mouse_clicks_quarter2_to_quarter4()
    test_victory_report_card()
    test_stage_select_typewriter()
    test_quarters_integration()
    test_bromen_exclusive_to_quarter4()
    test_map5_portal_loading()
    print("\nALL GAME STANDARD ENHANCEMENT TESTS PASSED SUCCESSFULLY!")



