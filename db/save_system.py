import os
import json
import time
import pygame

def atomic_save_json(path, data):
    """
    Safely writes JSON data atomically:
    Writes to a temporary file first and replaces the target file,
    preventing corrupt/empty (0-byte) save files during crashes or interruptions.
    """
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    tmp_path = f"{path}.tmp_{os.getpid()}_{int(time.time()*1000)}"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
        return True
    except Exception as e:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        raise e

def get_save_path(student_id):
    os.makedirs("db/saves", exist_ok=True)
    return f"db/saves/{student_id}.json"

def check_save_exists(student_id):
    if not student_id:
        return False
    return os.path.exists(get_save_path(student_id))

def is_tutorial_completed(student_id):
    """Check if the given student has completed the controls/gameplay tutorial"""
    if not student_id:
        return False
    save_data = load_student_progress(student_id)
    if not save_data:
        return False
    return bool(save_data.get("tutorial_completed", False))

def set_tutorial_completed(main_menu, student_id, completed=True):
    """Marks tutorial as completed and saves the status to student's profile"""
    if not student_id:
        return
    if hasattr(main_menu, 'tutorial_completed'):
        main_menu.tutorial_completed = completed
    save_data = load_student_progress(student_id) or {}
    save_data["student_id"] = student_id
    if main_menu and getattr(main_menu, 'selected_student', None):
        save_data["selected_student"] = main_menu.selected_student
    save_data["tutorial_completed"] = completed
    save_data["timestamp"] = time.time()
    
    path = get_save_path(student_id)
    try:
        atomic_save_json(path, save_data)
        print(f"[TUTORIAL] Tutorial completed status saved for student {student_id}: {completed}")
    except Exception as e:
        print(f"[WARN] Error saving tutorial status: {e}")

def delete_student_progress(student_id, student_db_id=None, main_menu=None):
    """
    Deletes past progress in both the game and the database when starting a New Game:
    1. Removes all local save files for this student from db/saves/
    2. Deletes past grade records from the live Vercel database via DELETE /api/grades
    3. Cleans up pending offline sync entries in db/pending_sync.json
    4. Sets student reset timestamp in db/reset_records.json
    5. Cleans in-memory stage and quarter states on main_menu
    """
    if not student_id and not student_db_id and not main_menu:
        return

    target_ids = set()
    if student_id:
        target_ids.add(str(student_id))
    if student_db_id:
        target_ids.add(str(student_db_id))
    if main_menu:
        if getattr(main_menu, 'student_id', None):
            target_ids.add(str(main_menu.student_id))
        if getattr(main_menu, 'student_db_id', None):
            target_ids.add(str(main_menu.student_db_id))
        if getattr(main_menu, 'selected_student', None):
            sel = main_menu.selected_student
            if sel.get("id"): target_ids.add(str(sel.get("id")))
            if sel.get("student_id"): target_ids.add(str(sel.get("student_id")))
            if sel.get("studentId"): target_ids.add(str(sel.get("studentId")))

    saves_dir = "db/saves"
    if os.path.exists(saves_dir):
        for fname in os.listdir(saves_dir):
            if fname.endswith(".json") and fname != "audio_settings.json":
                fpath = os.path.join(saves_dir, fname)
                should_delete = False
                base_name = fname[:-5]
                if base_name in target_ids:
                    should_delete = True
                else:
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            sid = str(data.get("student_id") or "")
                            sel_id = str(data.get("selected_student", {}).get("id") or "")
                            sel_sid = str(data.get("selected_student", {}).get("student_id") or "")
                            if sid in target_ids or sel_id in target_ids or sel_sid in target_ids:
                                should_delete = True
                    except Exception:
                        pass
                if should_delete:
                    try:
                        os.remove(fpath)
                        print(f"[DELETE] Deleted local save file: {fpath}")
                    except Exception as e:
                        print(f"[WARN] Error deleting save file {fpath}: {e}")

    # Purge past records in the live database via db.connect_db
    try:
        from db.connect_db import db
        effective_sid = student_id or (getattr(main_menu, 'student_id', None) if main_menu else None)
        effective_db_id = student_db_id or (getattr(main_menu, 'student_db_id', None) if main_menu else None)
        deleted_count = db.delete_student_records(
            student_id=effective_sid,
            student_db_id=effective_db_id
        )
        print(f"[DB RESET] Purged past database records ({deleted_count} deleted) for student {target_ids}")
    except Exception as e:
        print(f"[WARN] Could not purge database records: {e}")

    # Reset in-memory session states on main_menu
    if main_menu:
        main_menu.last_stage_select_data = None
        main_menu.tutorial_completed = False
        if hasattr(main_menu, 'completed_quarters'):
            main_menu.completed_quarters = {}
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
        if hasattr(main_menu, 'setup_buttons'):
            main_menu.setup_buttons()

def mark_quarter_completed(main_menu, quarter_name, score=100, percentage=100.0, total_questions=5):
    """Marks a specific quarter as completed in the student's persistent save data."""
    student_id = getattr(main_menu, 'student_id', None)
    if not student_id:
        return
    save_data = load_student_progress(student_id) or {}
    if "completed_quarters" not in save_data:
        save_data["completed_quarters"] = {}
    
    save_data["completed_quarters"][quarter_name] = {
        "completed": True,
        "score": score,
        "percentage": round(percentage, 1),
        "total_questions": total_questions,
        "timestamp": time.time()
    }
    save_data["timestamp"] = time.time()
    
    path = get_save_path(student_id)
    try:
        atomic_save_json(path, save_data)
        print(f"[STAR] Quarter '{quarter_name}' marked as COMPLETED for student {student_id}! ({score} pts, {percentage:.1f}%)")
    except Exception as e:
        print(f"[WARN] Error marking quarter completed: {e}")

def get_completed_quarters(student_id):
    """Returns dict of completed quarters for given student."""
    if not student_id:
        return {}
    save_data = load_student_progress(student_id)
    if not save_data:
        return {}
    return save_data.get("completed_quarters", {})

def is_game_completed(student_id):
    """Returns True if all 4 Quarters (quarter1, quarter2, quarter3, quarter4) are completed."""
    completed = get_completed_quarters(student_id)
    req = ["quarter1", "quarter2", "quarter3", "quarter4"]
    return all(completed.get(q, {}).get("completed", False) for q in req)

def save_student_progress(main_menu):
    if not main_menu or not getattr(main_menu, 'selected_student', None):
        return False
    
    student_id = main_menu.student_id
    if not student_id:
        return False
        
    existing_save = load_student_progress(student_id) or {}
    completed_quarters = existing_save.get("completed_quarters", {})

    save_data = {
        "student_id": student_id,
        "selected_student": main_menu.selected_student,
        "current_screen": main_menu.current_screen,
        "tutorial_completed": getattr(main_menu, 'tutorial_completed', True if check_save_exists(student_id) else False),
        "completed_quarters": completed_quarters,
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
        if q_data.get("completed"):
            save_data["completed_quarters"][q_data["quarter_name"]] = {
                "completed": True,
                "score": q_data.get("score", 100),
                "percentage": q_data.get("percentage", 100.0),
                "timestamp": time.time()
            }
        
    path = get_save_path(student_id)
    try:
        atomic_save_json(path, save_data)
        print(f"[SAVE] Student progress saved successfully to: {path}")
        return True
    except Exception as e:
        print(f"[WARN] Error writing save file: {e}")
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
        "stage_time_remaining": getattr(q, 'stage_time_remaining', 600.0),
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
        print(f"[WARN] Error reading save file {path}: {e}")
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
        
        print("[MAP] Stage Select screen state resumed.")
        
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
            q.stage_time_remaining = q_data.get("stage_time_remaining", 600.0)
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
            
            print(f"[GAME] Resumed {current_screen} state at Question {q.current_question_index + 1}.")

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
        
    print("[DOOR] Returned to menu screen.")
