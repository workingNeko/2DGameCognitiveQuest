import os
import json
import time
import pygame

def get_save_path(student_id):
    os.makedirs("db/saves", exist_ok=True)
    return f"db/saves/{student_id}.json"

def check_save_exists(student_id):
    if not student_id:
        return False
    return os.path.exists(get_save_path(student_id))

def delete_student_progress(student_id):
    if not student_id:
        return
    path = get_save_path(student_id)
    if os.path.exists(path):
        try:
            os.remove(path)
            print(f"🗑️ Deleted save file: {path}")
        except Exception as e:
            print(f"⚠️ Error deleting save file: {e}")

def save_student_progress(main_menu):
    if not main_menu or not getattr(main_menu, 'selected_student', None):
        return False
    
    student_id = main_menu.student_id
    if not student_id:
        return False
        
    save_data = {
        "student_id": student_id,
        "selected_student": main_menu.selected_student,
        "current_screen": main_menu.current_screen,
        "timestamp": time.time()
    }
    
    # Save Stage Select state if last_stage_select_data is present on main_menu
    # or if main_menu.stage_select is currently active
    ss_data = None
    if main_menu.stage_select:
        ss = main_menu.stage_select
        ss_data = {
            "player_x": ss.player_x,
            "player_y": ss.player_y,
            "oldman_dialogue_state": ss.oldman_dialogue_state,
            "knight_dialogue_state": ss.knight_dialogue_state,
            "skeleton_dialogue_state": ss.skeleton_dialogue_state,
            "bromen_dialogue_state": ss.bromen_dialogue_state,
            "player_following_target": ss.player_following_target
        }
    elif hasattr(main_menu, 'last_stage_select_data') and main_menu.last_stage_select_data:
        ss_data = main_menu.last_stage_select_data
        
    if ss_data:
        save_data["stage_select"] = ss_data
        
    # Gather active Quarter progress
    q_data = None
    if main_menu.quarter1:
        q = main_menu.quarter1
        q_data = gather_quarter_data(q, "quarter1")
    elif main_menu.quarter2:
        q = main_menu.quarter2
        q_data = gather_quarter_data(q, "quarter2")
    elif main_menu.quarter3:
        q = main_menu.quarter3
        q_data = gather_quarter_data(q, "quarter3")
    elif main_menu.quarter4:
        q = main_menu.quarter4
        q_data = gather_quarter_data(q, "quarter4")
        
    if q_data:
        save_data["quarter_data"] = q_data
        
    path = get_save_path(student_id)
    try:
        with open(path, "w") as f:
            json.dump(save_data, f, indent=4)
        print(f"💾 Student progress saved successfully to: {path}")
        return True
    except Exception as e:
        print(f"⚠️ Error writing save file: {e}")
        return False

def gather_quarter_data(q, quarter_name):
    # Base progress data
    data = {
        "quarter_name": quarter_name,
        "map_name": getattr(q, 'current_map_name', getattr(q, 'map_name', 'map1.txt')),
        "player_x": q.player_x,
        "player_y": q.player_y,
        "player_dir": getattr(q, 'player_dir', 'down'),
        "quiz_state": getattr(q, 'quiz_state', 0),
        "quiz_station_index": getattr(q, 'quiz_station_index', 1),
        "current_question_index": getattr(q, 'current_question_index', 0),
        "completed": getattr(q, 'completed', False)
    }
    
    # Store first attempt correctness tracker (handles all quarters)
    if hasattr(q, 'first_attempt_correct') and q.first_attempt_correct:
        # JSON keys must be string
        data["first_attempt_correct"] = {str(k): v for k, v in q.first_attempt_correct.items()}
        
    # Store attempt counts per station
    if hasattr(q, 'station_attempts') and q.station_attempts:
        data["station_attempts"] = {str(k): v for k, v in q.station_attempts.items()}
    elif hasattr(q, 'question_attempts') and q.question_attempts:
        data["station_attempts"] = {str(k): v for k, v in q.question_attempts.items()}
        
    # Quarter 1 specific Shape NPCs answered state
    if hasattr(q, 'shape_npcs') and q.shape_npcs:
        shape_data = {}
        for k, v in q.shape_npcs.items():
            shape_data[str(k)] = {"answered": v.get("answered", False)}
        data["shape_npcs"] = shape_data
        
    return data

def load_student_progress(student_id):
    if not student_id:
        return None
    path = get_save_path(student_id)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Error reading save file {path}: {e}")
        return None

def apply_student_progress(main_menu, save_data):
    if not save_data:
        return
        
    current_screen = save_data.get("current_screen")
    main_menu.current_screen = current_screen
    
    # Restore Stage Select data reference
    if "stage_select" in save_data:
        main_menu.last_stage_select_data = save_data["stage_select"]
        
    # Re-instantiate appropriate screen
    if current_screen == "stage_select":
        from screens.stageselect import StageSelect
        ss = StageSelect(main_menu.screen, main_menu)
        main_menu.stage_select = ss
        
        # Apply StageSelect coordinates and dialogue states
        ss_data = save_data["stage_select"]
        ss.player_x = ss_data.get("player_x", ss.player_x)
        ss.player_y = ss_data.get("player_y", ss.player_y)
        ss.oldman_dialogue_state = ss_data.get("oldman_dialogue_state", 0)
        ss.knight_dialogue_state = ss_data.get("knight_dialogue_state", 0)
        ss.skeleton_dialogue_state = ss_data.get("skeleton_dialogue_state", 0)
        ss.bromen_dialogue_state = ss_data.get("bromen_dialogue_state", 0)
        ss.player_following_target = ss_data.get("player_following_target", None)
        
        # Re-center Camera to player position
        ss.camera_x = ss.player_x + 16 - (ss.width // 2) / 1.50
        ss.camera_y = ss.player_y + 16 - (ss.height // 2) / 1.50
        
        print("🗺️ Stage Select screen state resumed.")
        
    elif current_screen in ["quarter1", "quarter2", "quarter3", "quarter4"]:
        q_data = save_data.get("quarter_data", {})
        map_name = q_data.get("map_name", "map1.txt")
        
        q = None
        if current_screen == "quarter1":
            from screens.quarter1 import Quarter1
            q = Quarter1(main_menu.screen, main_menu, map_name)
            main_menu.quarter1 = q
        elif current_screen == "quarter2":
            from screens.quarter2 import Quarter2
            q = Quarter2(main_menu.screen, main_menu, map_name)
            main_menu.quarter2 = q
        elif current_screen == "quarter3":
            from screens.quarter3 import Quarter3
            q = Quarter3(main_menu.screen, main_menu, map_name)
            main_menu.quarter3 = q
        elif current_screen == "quarter4":
            from screens.quarter4 import Quarter4
            q = Quarter4(main_menu.screen, main_menu, map_name)
            main_menu.quarter4 = q
            
        if q:
            # Apply Quarter coordinate states
            q.player_x = q_data.get("player_x", q.player_x)
            q.player_y = q_data.get("player_y", q.player_y)
            q.player_dir = q_data.get("player_dir", "down")
            
            # Apply Quiz progression variables
            q.quiz_state = q_data.get("quiz_state", 0)
            q.quiz_station_index = q_data.get("quiz_station_index", 1)
            q.current_question_index = q_data.get("current_question_index", 0)
            q.completed = q_data.get("completed", False)
            
            # Restore first attempt correct tracking (all quarters)
            if "first_attempt_correct" in q_data and hasattr(q, 'first_attempt_correct'):
                correct_dict = q_data["first_attempt_correct"]
                q.first_attempt_correct = {int(k): v for k, v in correct_dict.items()}
                
            # Restore station/question attempts tracking
            if "station_attempts" in q_data:
                att_dict = q_data["station_attempts"]
                if hasattr(q, 'station_attempts'):
                    q.station_attempts = {int(k): v for k, v in att_dict.items()}
                if hasattr(q, 'question_attempts'):
                    q.question_attempts = {int(k): v for k, v in att_dict.items()}
                
            # Quarter 1 specific Shape NPC answered states
            if current_screen == "quarter1" and "shape_npcs" in q_data and hasattr(q, 'shape_npcs'):
                shape_npcs_save = q_data["shape_npcs"]
                for k, v in shape_npcs_save.items():
                    k_int = int(k)
                    if k_int in q.shape_npcs:
                        q.shape_npcs[k_int]["answered"] = v.get("answered", False)
                        
            # Reposition companion/NPC pathfinding coordinates based on quiz_station_index
            if current_screen == "quarter2":
                if q.quiz_station_index in q.quiz_stations:
                    q.npc_knight_tile_x, q.npc_knight_tile_y = q.quiz_stations[q.quiz_station_index]
                    q.npc_knight_x = q.npc_knight_tile_x * 32
                    q.npc_knight_y = q.npc_knight_tile_y * 32
            elif current_screen == "quarter3":
                if q.quiz_station_index in q.quiz_stations:
                    q.npc_skeleton_tile_x, q.npc_skeleton_tile_y = q.quiz_stations[q.quiz_station_index]
                    q.npc_skeleton_x = q.npc_skeleton_tile_x * 32
                    q.npc_skeleton_y = q.npc_skeleton_tile_y * 32
            elif current_screen == "quarter4":
                if q.quiz_station_index in q.quiz_stations:
                    q.npc_bromen_tile_x, q.npc_bromen_tile_y = q.quiz_stations[q.quiz_station_index]
                    q.npc_bromen_x = q.npc_bromen_tile_x * 32
                    q.npc_bromen_y = q.npc_bromen_tile_y * 32
            
            # Re-center Camera to player position
            ZOOM_FACTOR = 1.50
            q.camera_x = q.player_x + 16 - (q.width // 2) / ZOOM_FACTOR
            q.camera_y = q.player_y + 16 - (q.height // 2) / ZOOM_FACTOR
            
            print(f"🎮 Resumed {current_screen} state at Question {q.current_question_index + 1}.")

def show_saving_and_exit(main_menu, target_screen="menu"):
    # Intercept return to Main Menu
    screen = main_menu.screen
    font = main_menu.small_font if hasattr(main_menu, 'small_font') else pygame.font.SysFont("Comic Sans MS", 22)
    
    # Renders centered card on screen
    def render_popup(msg):
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        
        # Center message text
        txt_surf = font.render(msg, True, (255, 255, 255))
        rect = txt_surf.get_rect(center=(screen.get_width() // 2, screen.get_height() // 2))
        
        # Beautiful slate card
        card_rect = rect.inflate(120, 50)
        pygame.draw.rect(screen, (30, 41, 59), card_rect, border_radius=12)
        pygame.draw.rect(screen, (255, 215, 0), card_rect, 3, border_radius=12)
        screen.blit(txt_surf, rect)
        
        pygame.display.flip()

    # Step 1: Show "Saving Progress..."
    print("Saving student progress...")
    render_popup("Saving Progress...")
    pygame.time.delay(600)
    
    # Step 2: Do write
    save_student_progress(main_menu)
    
    # Step 3: Show "Progress Saved!"
    render_popup("Progress Saved!")
    pygame.time.delay(600)
    
    # Step 4: Perform cleanup and state change
    # Safely clear screen objects in main_menu
    if main_menu.quarter1 and hasattr(main_menu.quarter1, 'cleanup'):
        main_menu.quarter1.cleanup()
    main_menu.quarter1 = None
    if main_menu.quarter2 and hasattr(main_menu.quarter2, 'cleanup'):
        main_menu.quarter2.cleanup()
    main_menu.quarter2 = None
    if main_menu.quarter3 and hasattr(main_menu.quarter3, 'cleanup'):
        main_menu.quarter3.cleanup()
    main_menu.quarter3 = None
    if main_menu.quarter4 and hasattr(main_menu.quarter4, 'cleanup'):
        main_menu.quarter4.cleanup()
    main_menu.quarter4 = None
    if main_menu.stage_select and hasattr(main_menu.stage_select, 'cleanup'):
        main_menu.stage_select.cleanup()
    main_menu.stage_select = None
    
    # Reset states
    main_menu.current_screen = target_screen
    main_menu.popup_state = None
    
    # Refresh buttons to reflect save state (e.g. if they exited back to menu, check if we need to show Continue Activity)
    if hasattr(main_menu, 'setup_buttons'):
        main_menu.setup_buttons()
        
    print("🚪 Returned to menu screen.")
