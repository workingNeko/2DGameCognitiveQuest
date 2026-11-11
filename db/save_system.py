import os
import json
import time
import datetime
import copy
import threading
import pygame

_IO_SAVE_LOCK = threading.RLock()
_ASYNC_QUEUE_LOCK = threading.Lock()
_PENDING_ASYNC_SAVES = {}
_ASYNC_WORKER_RUNNING = False

def cleanup_orphaned_tmp_saves():
    """Cleans up stray temporary files left over from ungraceful power cuts."""
    saves_dir = "db/saves"
    if not os.path.exists(saves_dir):
        return
    now = time.time()
    try:
        for fname in os.listdir(saves_dir):
            if ".tmp_" in fname:
                fpath = os.path.join(saves_dir, fname)
                try:
                    if now - os.path.getmtime(fpath) > 10.0:
                        os.remove(fpath)
                except Exception:
                    pass
    except Exception:
        pass

# Clean up any leftover temporary files from previous hard power cuts
cleanup_orphaned_tmp_saves()

def atomic_save_json(path, data):
    """
    Safely writes JSON data atomically:
    Serializes once to compact UTF-8 bytes, writes to a temporary file first and replaces
    the target file, preventing corrupt/empty (0-byte) save files during crashes or interruptions.
    Maintains a verified shadow backup (.bak) for recovery against power failures.
    """
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    payload_bytes = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    with _IO_SAVE_LOCK:
        tmp_path = f"{path}.tmp_{os.getpid()}_{threading.get_ident()}_{int(time.time()*1000)}"
        try:
            with open(tmp_path, "wb") as f:
                f.write(payload_bytes)
                f.flush()
                os.fsync(f.fileno())

            # Attempt atomic replace with retries for Windows file locking
            saved_ok = False
            for attempt in range(5):
                try:
                    os.replace(tmp_path, path)
                    saved_ok = True
                    break
                except (PermissionError, OSError):
                    if attempt < 4:
                        time.sleep(0.03 * (attempt + 1))
                    else:
                        # Fallback to direct write if os.replace is repeatedly locked
                        with open(path, "wb") as target_f:
                            target_f.write(payload_bytes)
                            target_f.flush()
                            os.fsync(target_f.fileno())
                        if os.path.exists(tmp_path):
                            try:
                                os.remove(tmp_path)
                            except Exception:
                                pass
                        saved_ok = True
                        break

            if saved_ok:
                # Maintain a verified shadow backup file (.bak) for power-interruption recovery
                try:
                    bak_path = f"{path}.bak"
                    with open(bak_path, "wb") as bf:
                        bf.write(payload_bytes)
                        bf.flush()
                        os.fsync(bf.fileno())
                except Exception:
                    pass
                invalidate_save_cache()
                return True
        except Exception as e:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            raise e


def _async_save_worker():
    global _ASYNC_WORKER_RUNNING
    while True:
        with _ASYNC_QUEUE_LOCK:
            if not _PENDING_ASYNC_SAVES:
                _ASYNC_WORKER_RUNNING = False
                return
            path, payload = next(iter(_PENDING_ASYNC_SAVES.items()))
            del _PENDING_ASYNC_SAVES[path]
        try:
            atomic_save_json(path, payload)
        except Exception as e:
            print(f"[WARN] Background autosave write failed for {path}: {e}")
        time.sleep(0.002)


def flush_pending_async_saves():
    """Flushes any queued asynchronous autosaves synchronously (called on app exit)."""
    while True:
        with _ASYNC_QUEUE_LOCK:
            if not _PENDING_ASYNC_SAVES:
                break
            pending_items = list(_PENDING_ASYNC_SAVES.items())
            _PENDING_ASYNC_SAVES.clear()
        for path, payload in pending_items:
            try:
                atomic_save_json(path, payload)
            except Exception as e:
                print(f"[WARN] Flush pending save failed for {path}: {e}")

def get_save_path(student_id):
    os.makedirs("db/saves", exist_ok=True)
    return f"db/saves/{student_id}.json"

def check_save_exists(student_id):
    if not student_id:
        return False
    path = get_save_path(student_id)
    if not os.path.exists(path):
        return False
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Verify actual gameplay progress exists (completed quarters, tutorial, or stage data)
            q = data.get("completed_quarters", {})
            has_completed_q = any(isinstance(v, dict) and v.get("completed") for v in q.values())
            has_tutorial = bool(data.get("tutorial_completed"))
            has_stage = bool(data.get("stage_select"))
            return has_completed_q or has_tutorial or has_stage
    except Exception:
        return False

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

    with _ASYNC_QUEUE_LOCK:
        for tid in target_ids:
            _PENDING_ASYNC_SAVES.pop(get_save_path(tid), None)

    saves_dir = "db/saves"
    with _IO_SAVE_LOCK:
        pass
    if os.path.exists(saves_dir):
        for fname in os.listdir(saves_dir):
            if (fname.endswith(".json") or fname.endswith(".bak")) and fname != "audio_settings.json":
                fpath = os.path.join(saves_dir, fname)
                should_delete = False
                base_name = fname.replace(".json.bak", "").replace(".bak", "").replace(".json", "")
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
                        if os.path.exists(fpath):
                            os.remove(fpath)
                        bak_file = f"{fpath}.bak"
                        if os.path.exists(bak_file):
                            os.remove(bak_file)
                        invalidate_save_cache()
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

    # Write a single canonical clean save file with 0 score and 0% progress (no duplicate numeric/code files)
    sel_obj = getattr(main_menu, 'selected_student', None) or {}
    canonical_sid = (
        student_id
        or (getattr(main_menu, 'student_id', None) if main_menu else None)
        or sel_obj.get("student_id")
        or sel_obj.get("studentId")
        or student_db_id
    )
    if canonical_sid:
        tid_str = str(canonical_sid)
        clean_path = get_save_path(tid_str)
        try:
            first_n = sel_obj.get("first_name") or "Student"
            resolved_pk = (
                int(student_db_id)
                if student_db_id and str(student_db_id).isdigit()
                else (sel_obj.get("id") if sel_obj.get("id") is not None else 9)
            )
            student_clean_data = {
                "student_id": tid_str,
                "selected_student": {
                    "id": resolved_pk,
                    "student_id": tid_str,
                    "first_name": first_n,
                    "last_name": sel_obj.get("last_name") or "",
                    "score": 0,
                    "progress": 0,
                    "level": sel_obj.get("level") or sel_obj.get("gradeLevel") or "Grade 2",
                    "gender": sel_obj.get("gender") or "male",
                    "section": sel_obj.get("section") or "A",
                    "avatarColor": sel_obj.get("avatarColor") or ""
                },
                "current_screen": "menu",
                "tutorial_completed": False,
                "completed_quarters": {},
                "timestamp": time.time()
            }
            atomic_save_json(clean_path, student_clean_data)
            print(f"[CLEAN SAVE] Created initialized fresh save for student {tid_str}")
        except Exception as se:
            print(f"[WARN] Error creating clean save file for {tid_str}: {se}")

    # Reset in-memory session states on main_menu
    if main_menu:
        main_menu.last_stage_select_data = None
        main_menu.tutorial_completed = False
        if hasattr(main_menu, 'completed_quarters'):
            main_menu.completed_quarters = {}
        if getattr(main_menu, 'selected_student', None):
            main_menu.selected_student["score"] = 0
            main_menu.selected_student["progress"] = 0
        if getattr(main_menu, 'student_select', None) and hasattr(main_menu.student_select, 'students'):
            for s in main_menu.student_select.students:
                if str(s.get("student_id")) in target_ids or str(s.get("id")) in target_ids:
                    s["score"] = 0
                    s["progress"] = 0
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
    if not student_id and getattr(main_menu, 'selected_student', None):
        student_id = main_menu.selected_student.get('student_id') or main_menu.selected_student.get('studentId')
    if not student_id:
        return
    save_data = load_student_progress(student_id) or {}
    if "completed_quarters" not in save_data:
        save_data["completed_quarters"] = {}
    
    prev_q = save_data["completed_quarters"].get(quarter_name)
    if isinstance(prev_q, dict) and prev_q.get("completed"):
        best_score = max(int(prev_q.get("score", 0)), int(score))
        best_pct = max(float(prev_q.get("percentage", 0.0)), round(float(percentage), 1))
        best_tot = int(total_questions) if int(score) >= int(prev_q.get("score", 0)) else int(prev_q.get("total_questions", total_questions))
    else:
        best_score = int(score)
        best_pct = round(float(percentage), 1)
        best_tot = int(total_questions)

    now_str = datetime.datetime.now().strftime("%b %d, %Y %I:%M %p")
    save_data["completed_quarters"][quarter_name] = {
        "completed": True,
        "score": best_score,
        "percentage": best_pct,
        "total_questions": best_tot,
        "timestamp": time.time(),
        "recorded_date": now_str,
    }
    save_data["timestamp"] = time.time()
    save_data["last_recorded_date"] = now_str
    
    # Calculate cumulative score and progress percentage across all quarters
    comp_qs = save_data["completed_quarters"]
    cum_score = sum(d.get("score", 0) for d in comp_qs.values() if isinstance(d, dict))
    comp_count = sum(1 for d in comp_qs.values() if isinstance(d, dict) and d.get("completed"))
    cum_prog = int((comp_count / 4.0) * 100)

    # Sync selected_student in save data
    if "selected_student" in save_data and isinstance(save_data["selected_student"], dict):
        save_data["selected_student"]["score"] = cum_score
        save_data["selected_student"]["progress"] = cum_prog
    elif main_menu and getattr(main_menu, 'selected_student', None):
        save_data["selected_student"] = dict(main_menu.selected_student)
        save_data["selected_student"]["score"] = cum_score
        save_data["selected_student"]["progress"] = cum_prog

    # Sync in-memory selected_student on main_menu
    if main_menu and getattr(main_menu, 'selected_student', None):
        main_menu.selected_student["score"] = cum_score
        main_menu.selected_student["progress"] = cum_prog

    # Sync student_select roster if active
    if main_menu and getattr(main_menu, 'student_select', None):
        for s in getattr(main_menu.student_select, 'students', []):
            if str(s.get('student_id')) == str(student_id) or str(s.get('id')) == str(getattr(main_menu, 'student_db_id', None)):
                s["score"] = cum_score
                s["progress"] = cum_prog
    
    path = get_save_path(student_id)
    try:
        atomic_save_json(path, save_data)
        print(f"[STAR] Quarter '{quarter_name}' marked as COMPLETED for student {student_id}! ({score} pts, {percentage:.1f}%) [Total: {cum_score} pts, {cum_prog}%]")
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

def save_student_progress(main_menu, async_flush=False):
    if not main_menu or not getattr(main_menu, 'selected_student', None):
        return False
    
    student_id = main_menu.student_id
    if not student_id and getattr(main_menu, 'selected_student', None):
        student_id = main_menu.selected_student.get('student_id') or main_menu.selected_student.get('studentId')
    if not student_id:
        return False
        
    existing_save = load_student_progress(student_id) or {}
    completed_quarters = copy.deepcopy(existing_save.get("completed_quarters", {}))

    # Sync cumulative score and progress percentage
    cum_score = sum(d.get("score", 0) for d in completed_quarters.values() if isinstance(d, dict))
    comp_count = sum(1 for d in completed_quarters.values() if isinstance(d, dict) and d.get("completed"))
    cum_prog = int((comp_count / 4.0) * 100)
    
    if getattr(main_menu, 'selected_student', None):
        main_menu.selected_student["score"] = cum_score
        main_menu.selected_student["progress"] = cum_prog

    save_data = {
        "student_id": str(student_id),
        "selected_student": copy.deepcopy(main_menu.selected_student),
        "current_screen": main_menu.current_screen,
        "tutorial_completed": getattr(main_menu, 'tutorial_completed', True if check_save_exists(student_id) else False),
        "completed_quarters": completed_quarters,
        "timestamp": time.time()
    }
    
    # Save Stage Select state if last_stage_select_data is present on main_menu
    # or if main_menu.stage_select is currently active
    ss_data = None
    if getattr(main_menu, 'stage_select', None):
        ss = main_menu.stage_select
        ss_data = {
            "player_x": ss.player_x,
            "player_y": ss.player_y,
            "oldman_dialogue_state": ss.oldman_dialogue_state,
            "knight_dialogue_state": ss.knight_dialogue_state,
            "skeleton_dialogue_state": ss.skeleton_dialogue_state,
            "bromen_dialogue_state": ss.bromen_dialogue_state,
            "player_following_target": ss.player_following_target,
            "barriers_lifted": getattr(ss, 'barriers_lifted', False)
        }
    elif hasattr(main_menu, 'last_stage_select_data') and main_menu.last_stage_select_data:
        ss_data = copy.deepcopy(main_menu.last_stage_select_data)
        
    if ss_data:
        save_data["stage_select"] = ss_data
        
    # Gather active Quarter progress
    q_data = None
    if getattr(main_menu, 'quarter1', None):
        q = main_menu.quarter1
        q_data = gather_quarter_data(q, "quarter1")
    elif getattr(main_menu, 'quarter2', None):
        q = main_menu.quarter2
        q_data = gather_quarter_data(q, "quarter2")
    elif getattr(main_menu, 'quarter3', None):
        q = main_menu.quarter3
        q_data = gather_quarter_data(q, "quarter3")
    elif getattr(main_menu, 'quarter4', None):
        q = main_menu.quarter4
        q_data = gather_quarter_data(q, "quarter4")
        
    if q_data:
        save_data["quarter_data"] = q_data
        if q_data.get("completed"):
            prev_q = save_data["completed_quarters"].get(q_data["quarter_name"], {})
            best_score = max(prev_q.get("score", 0), q_data.get("score", prev_q.get("score", 100)))
            best_pct = max(prev_q.get("percentage", 0.0), q_data.get("percentage", prev_q.get("percentage", 100.0)))
            save_data["completed_quarters"][q_data["quarter_name"]] = {
                "completed": True,
                "score": best_score,
                "percentage": best_pct,
                "timestamp": time.time()
            }
        
    path = get_save_path(student_id)
    if async_flush:
        global _ASYNC_WORKER_RUNNING
        sid_str = str(student_id)
        _SAVE_CACHE[sid_str] = {"mtime": -1.0, "last_check": time.time(), "data": save_data}
        with _ASYNC_QUEUE_LOCK:
            _PENDING_ASYNC_SAVES[path] = save_data
            if not _ASYNC_WORKER_RUNNING:
                _ASYNC_WORKER_RUNNING = True
                threading.Thread(target=_async_save_worker, daemon=True).start()
        if main_menu and hasattr(main_menu, 'autosave_manager') and main_menu.autosave_manager:
            main_menu.autosave_manager.notify_saved()
        return True

    try:
        with _ASYNC_QUEUE_LOCK:
            _PENDING_ASYNC_SAVES.pop(path, None)
        atomic_save_json(path, save_data)
        print(f"[SAVE] Student progress saved successfully to: {path}")
        # Notify autosave manager for on-screen visual confirmation badge
        if main_menu and hasattr(main_menu, 'autosave_manager') and main_menu.autosave_manager:
            main_menu.autosave_manager.notify_saved()
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

    # Collect answered stations / stalls across all quarters
    if hasattr(q, 'answered_stations') and isinstance(q.answered_stations, (set, list)):
        data["answered_stations"] = list(q.answered_stations)

    # Collect cognitive puzzle flags
    for flag in ('addition_puzzle_solved', 'key_puzzle_solved', 'puzzle_solved', 'oldman_riddle_answered', 'raft_unlocked'):
        if hasattr(q, flag):
            data[flag] = bool(getattr(q, flag))

    if hasattr(q, 'raft_state'):
        data["raft_state"] = getattr(q, 'raft_state')
    
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

_SAVE_CACHE = {}

def invalidate_save_cache(student_id=None):
    """Invalidates the in-memory save cache."""
    global _SAVE_CACHE
    if student_id is not None:
        _SAVE_CACHE.pop(str(student_id), None)
    else:
        _SAVE_CACHE.clear()

def load_student_progress(student_id):
    if not student_id:
        return None
    path = get_save_path(student_id)
    with _ASYNC_QUEUE_LOCK:
        pending = _PENDING_ASYNC_SAVES.get(path)
    if pending is not None:
        return copy.deepcopy(pending)
    bak_path = f"{path}.bak"
    if not os.path.exists(path) and not os.path.exists(bak_path):
        _SAVE_CACHE.pop(str(student_id), None)
        return None
    try:
        now = time.time()
        sid_str = str(student_id)
        cached = _SAVE_CACHE.get(sid_str)
        if cached is not None and (now - cached.get("last_check", 0) < 0.2):
            return cached.get("data")

        if os.path.exists(path):
            mtime = os.path.getmtime(path)
            if cached is not None and cached.get("mtime") == mtime:
                cached["last_check"] = now
                return cached.get("data")

            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, dict) or not data:
                    raise ValueError("Save file empty or malformed")
                _SAVE_CACHE[sid_str] = {"mtime": mtime, "last_check": now, "data": data}
                return data
        else:
            raise FileNotFoundError(f"{path} missing, falling back to backup")
    except Exception as e:
        print(f"[WARN] Error reading save file {path}: {e}")
        # Power-interruption recovery: attempt to load from verified shadow backup
        if os.path.exists(bak_path):
            try:
                with open(bak_path, "r", encoding="utf-8") as bf:
                    bak_data = json.load(bf)
                if isinstance(bak_data, dict) and bak_data:
                    print(f"[AUTOSAVE RECOVERY] Restored save data from power-safe backup: {bak_path}")
                    atomic_save_json(path, bak_data)
                    return bak_data
            except Exception as be:
                print(f"[WARN] Backup recovery also failed: {be}")
        return None

def sync_student_with_cloud(student_id, student_db_id=None, main_menu=None, force_cloud_refresh=False):
    """
    Authoritative inbound synchronization from Vercel Web App to local game:
    - If student records/grades/game results were deleted on the web app,
      automatically purges or removes those completed stages from the local save file.
    - If cloud data has higher/updated stage scores, hydrates them locally.
    - If all records for the student were wiped on the web app (and no pending offline queue),
      resets local save so student starts fresh with 'START ACTIVITY' and 0 score.
    Returns:
        dict with {'synced': bool, 'action': str, ...}
    """
    if not student_id and not student_db_id:
        return {"synced": False}

    try:
        from db.connect_db import db
    except ImportError:
        return {"synced": False}

    if not db or db._is_offline_fast_fail():
        return {"synced": False}

    try:
        # Flush pending offline sync items first so cloud has latest data before we compare
        if db._count_pending_sync() > 0:
            db.sync_offline_results()

        cloud_results = db.get_game_results(filter_reset=True, force_refresh=force_cloud_refresh)
        if cloud_results is None or db._is_offline_fast_fail():
            return {"synced": False}

        sid_str = str(student_id or "")
        db_id = student_db_id
        if not db_id and sid_str:
            st_list = db.get_students() or []
            for s in st_list:
                if str(s.get("studentId") or s.get("student_id") or "") == sid_str:
                    db_id = s.get("id")
                    break

        ass_to_q = db._build_assessment_to_quarter_lookup() if hasattr(db, "_build_assessment_to_quarter_lookup") else {}
        cloud_stages = {}
        for r in cloud_results:
            r_sid = r.get("studentId") if r.get("studentId") is not None else r.get("student_id")
            match = False
            if db_id is not None and db._same_student_id(r_sid, db_id):
                match = True
            elif sid_str and db._same_student_id(r_sid, sid_str):
                match = True
            elif sid_str and str(r.get("studentCode") or "") == sid_str:
                match = True

            if match:
                q_num = db._resolve_record_quarter(r, ass_to_q) if hasattr(db, "_resolve_record_quarter") else 1
                if q_num in (1, 2, 3, 4):
                    prev = cloud_stages.get(q_num)
                    score = int(r.get("score") or 0)
                    pct = float(r.get("percentage") if r.get("percentage") is not None else score)
                    tot = int(r.get("totalQuestions") or r.get("total_questions") or 5)
                    if prev is None or score >= int(prev.get("score", -1)):
                        cloud_date = r.get("createdAt") or r.get("created_at") or r.get("updatedAt")
                        cloud_stages[q_num] = {
                            "completed": True,
                            "score": score,
                            "percentage": round(pct, 1),
                            "total_questions": tot,
                            "timestamp": time.time(),
                            "recorded_date": cloud_date or datetime.datetime.now().strftime("%b %d, %Y %I:%M %p"),
                        }

        target_sid = sid_str or str(db_id)
        save_path = get_save_path(target_sid)
        local_save = load_student_progress(target_sid)

        # Cloud has data, but local save is missing -> hydrate local save from cloud!
        if not local_save and cloud_stages:
            sel_obj = getattr(main_menu, 'selected_student', None) or {}
            first_n = sel_obj.get("first_name") or "Student"
            cum_s = sum(c["score"] for c in cloud_stages.values())
            cum_p = int((len(cloud_stages) / 4.0) * 100)
            local_save = {
                "student_id": target_sid,
                "selected_student": {
                    "id": db_id,
                    "student_id": target_sid,
                    "first_name": first_n,
                    "last_name": sel_obj.get("last_name") or "",
                    "score": cum_s,
                    "progress": cum_p,
                    "level": sel_obj.get("level") or "Grade 2",
                    "gender": sel_obj.get("gender") or "male",
                    "section": sel_obj.get("section") or "A",
                    "avatarColor": sel_obj.get("avatarColor") or ""
                },
                "current_screen": "menu",
                "tutorial_completed": True,
                "completed_quarters": {f"quarter{qn}": dict(info) for qn, info in cloud_stages.items()},
                "timestamp": time.time()
            }
            atomic_save_json(save_path, local_save)
            invalidate_save_cache(target_sid)
            return {"synced": True, "action": "hydrated", "stages": list(cloud_stages.keys())}

        if not local_save:
            return {"synced": True, "action": "none"}

        comp_dict = local_save.get("completed_quarters", {})
        local_q_nums = set()
        for k, v in comp_dict.items():
            if isinstance(v, dict) and v.get("completed"):
                qn = db.normalize_quarter_number(k) or db.infer_quarter_from_text(k) or 1
                local_q_nums.add(qn)

        cloud_q_nums = set(cloud_stages.keys())
        deleted_q_nums = local_q_nums - cloud_q_nums

        # CASE 1: Cloud has ZERO records for this student, but local has completed stages
        # -> Student's progress was wiped / deleted on the webapp!
        if len(cloud_q_nums) == 0 and len(local_q_nums) > 0:
            if os.path.exists(save_path):
                try:
                    os.remove(save_path)
                except Exception:
                    pass
            bak = f"{save_path}.bak"
            if os.path.exists(bak):
                try:
                    os.remove(bak)
                except Exception:
                    pass
            invalidate_save_cache(target_sid)

            if main_menu:
                if getattr(main_menu, 'selected_student', None):
                    main_menu.selected_student["score"] = 0
                    main_menu.selected_student["progress"] = 0
                if hasattr(main_menu, 'completed_quarters'):
                    main_menu.completed_quarters = {}
                if hasattr(main_menu, 'create_buttons'):
                    main_menu.create_buttons()

            print(f"[CLOUD SYNC] Web app deleted all data for student {target_sid}. Local save reset to 0.")
            return {"synced": True, "action": "reset_all", "deleted_stages": list(local_q_nums)}

        # CASE 2: Specific stage(s) deleted on webapp, or higher scores present on cloud
        updated = False
        deleted_keys = []
        if deleted_q_nums:
            for qn in deleted_q_nums:
                k = f"quarter{qn}"
                if k in comp_dict:
                    comp_dict.pop(k, None)
                    deleted_keys.append(k)
            updated = True

        for qn, qinfo in cloud_stages.items():
            k = f"quarter{qn}"
            prev = comp_dict.get(k)
            if not isinstance(prev, dict) or not prev.get("completed") or int(qinfo["score"]) != int(prev.get("score", -1)):
                comp_dict[k] = dict(qinfo)
                updated = True

        if updated:
            new_score = sum(int(d.get("score", 0)) for d in comp_dict.values() if isinstance(d, dict))
            new_prog = int((len([d for d in comp_dict.values() if isinstance(d, dict) and d.get("completed")]) / 4.0) * 100)
            local_save["completed_quarters"] = comp_dict
            local_save["timestamp"] = time.time()
            if isinstance(local_save.get("selected_student"), dict):
                local_save["selected_student"]["score"] = new_score
                local_save["selected_student"]["progress"] = new_prog
            atomic_save_json(save_path, local_save)
            invalidate_save_cache(target_sid)

            if main_menu:
                if getattr(main_menu, 'selected_student', None):
                    main_menu.selected_student["score"] = new_score
                    main_menu.selected_student["progress"] = new_prog
                if hasattr(main_menu, 'create_buttons'):
                    main_menu.create_buttons()

            print(f"[CLOUD SYNC] Synced student {target_sid} with web app: {len(deleted_keys)} deleted stage(s), score={new_score}, progress={new_prog}%.")
            return {"synced": True, "action": "updated", "deleted_stages": deleted_keys, "total_score": new_score, "progress": new_prog}

        return {"synced": True, "action": "in_sync"}
    except Exception as e:
        print(f"[CLOUD SYNC ERROR] {e}")
        return {"synced": False, "error": str(e)}

def apply_student_progress(main_menu, save_data):
    if not save_data:
        return

    # Restore student identifiers and object references
    if save_data.get("student_id"):
        main_menu.student_id = str(save_data["student_id"])
    if save_data.get("selected_student"):
        main_menu.selected_student = save_data["selected_student"]
        if save_data["selected_student"].get("id"):
            main_menu.student_db_id = save_data["selected_student"]["id"]

    # Reconcile student_db_id with true database primary key if available
    try:
        from db.connect_db import db
        if db:
            cached_students = db.get_students() or []
            target_code = str(main_menu.student_id or (main_menu.selected_student and (main_menu.selected_student.get("student_id") or main_menu.selected_student.get("studentId"))))
            for s in cached_students:
                s_code = str(s.get("studentId") or s.get("student_id") or "")
                if s_code == target_code and s.get("id"):
                    main_menu.student_db_id = s.get("id")
                    if isinstance(main_menu.selected_student, dict):
                        main_menu.selected_student["id"] = s.get("id")
                    break
    except Exception:
        pass
        
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
        ss_data = save_data.get("stage_select", {})
        ss.player_x = ss_data.get("player_x", ss.player_x)
        ss.player_y = ss_data.get("player_y", ss.player_y)
        ss.oldman_dialogue_state = ss_data.get("oldman_dialogue_state", 0)
        ss.knight_dialogue_state = ss_data.get("knight_dialogue_state", 0)
        ss.skeleton_dialogue_state = ss_data.get("skeleton_dialogue_state", 0)
        ss.bromen_dialogue_state = ss_data.get("bromen_dialogue_state", 0)
        ss.player_following_target = ss_data.get("player_following_target", None)
        ss.barriers_lifted = ss_data.get("barriers_lifted", False)
        
        # Re-center Camera to player position
        ss.camera_x = ss.player_x + 16 - (ss.width // 2) / 1.50
        ss.camera_y = ss.player_y + 16 - (ss.height // 2) / 1.50
        
        print("[MAP] Stage Select screen state resumed.")
        
    elif current_screen in ["quarter1", "quarter2", "quarter3", "quarter4"]:
        comp_qs = save_data.get("completed_quarters", {})
        q_data = save_data.get("quarter_data", {})
        if comp_qs.get(current_screen, {}).get("completed", False) or q_data.get("completed", False):
            # Quarter was already completed - resume in Stage Select hub instead of completed quarter
            from screens.stageselect import StageSelect
            main_menu.current_screen = "stage_select"
            ss = StageSelect(main_menu.screen, main_menu)
            main_menu.stage_select = ss
            ss_data = save_data.get("stage_select", {})
            if ss_data:
                ss.player_x = ss_data.get("player_x", ss.player_x)
                ss.player_y = ss_data.get("player_y", ss.player_y)
                ss.oldman_dialogue_state = ss_data.get("oldman_dialogue_state", 0)
                ss.knight_dialogue_state = ss_data.get("knight_dialogue_state", 0)
                ss.skeleton_dialogue_state = ss_data.get("skeleton_dialogue_state", 0)
                ss.bromen_dialogue_state = ss_data.get("bromen_dialogue_state", 0)
                ss.player_following_target = ss_data.get("player_following_target", None)
                ss.barriers_lifted = ss_data.get("barriers_lifted", False)
                ss.camera_x = ss.player_x + 16 - (ss.width // 2) / 1.50
                ss.camera_y = ss.player_y + 16 - (ss.height // 2) / 1.50
            print(f"[GAME] {current_screen} already completed. Resumed activity in Stage Select hub.")
            return
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

            # Restore answered stations across Quarters (Quarter 4, Quarter 3, etc.)
            if "answered_stations" in q_data and hasattr(q, 'answered_stations'):
                q.answered_stations = set(q_data["answered_stations"])

            # Restore cognitive puzzle completion flags
            for flag in ('addition_puzzle_solved', 'key_puzzle_solved', 'puzzle_solved', 'oldman_riddle_answered', 'raft_unlocked'):
                if flag in q_data and hasattr(q, flag):
                    setattr(q, flag, q_data[flag])

            if "raft_state" in q_data and hasattr(q, 'raft_state'):
                q.raft_state = q_data["raft_state"]
                        
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
    else:
        # Fallback: When saved screen is 'menu' or anything else, continuing activity enters Stage Select hub!
        from screens.stageselect import StageSelect
        main_menu.current_screen = "stage_select"
        ss = StageSelect(main_menu.screen, main_menu)
        main_menu.stage_select = ss
        
        ss_data = save_data.get("stage_select", {})
        if ss_data:
            ss.player_x = ss_data.get("player_x", ss.player_x)
            ss.player_y = ss_data.get("player_y", ss.player_y)
            ss.oldman_dialogue_state = ss_data.get("oldman_dialogue_state", 0)
            ss.knight_dialogue_state = ss_data.get("knight_dialogue_state", 0)
            ss.skeleton_dialogue_state = ss_data.get("skeleton_dialogue_state", 0)
            ss.bromen_dialogue_state = ss_data.get("bromen_dialogue_state", 0)
            ss.player_following_target = ss_data.get("player_following_target", None)
            
            ss.camera_x = ss.player_x + 16 - (ss.width // 2) / 1.50
            ss.camera_y = ss.player_y + 16 - (ss.height // 2) / 1.50
        print("[MAP] Continued activity into Stage Select screen.")

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
