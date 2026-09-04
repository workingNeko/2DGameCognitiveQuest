import urllib.request
import urllib.parse
import json

# =====================================================
# VERCEL WEB API CONFIGURATION
# =====================================================
BASE_URL = "https://gamified-math-grading-system.vercel.app/api"

# For backwards compatibility with db/__init__.py imports
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "cognitive_quest"
DB_PORT = 3306

class Database:
    """HTTP API Client class for Vercel Integration."""
    def __init__(self, *args, **kwargs):
        self.connection = None
        self.cursor = None
        self._assessment_cache = {}
        print(f"[API SUCCESS] Web API Client initialized targeting: {BASE_URL}")

    def connect(self):
        """Mock method for backwards compatibility."""
        return True

    def is_connected(self):
        """Mock method for backwards compatibility."""
        return True

    def close(self):
        """Mock method for backwards compatibility."""
        pass

    def get_students(self):
        """Fetch students list from Vercel API, with automatic local cache fallback."""
        import os
        url = f"{BASE_URL}/students"
        cache_dir = os.path.join("db", "cache")
        cache_file = os.path.join(cache_dir, "students_cache.json")
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                if isinstance(data, list) and len(data) > 0:
                    try:
                        os.makedirs(cache_dir, exist_ok=True)
                        with open(cache_file, "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=4)
                    except Exception:
                        pass
                # If online, flush any pending offline sync queue
                self.sync_offline_results()
                return data
        except Exception as e:
            print(f"[API ERROR] Failed to fetch students from Vercel: {e}")
            # Offline fallback: read from local cache
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        cached = json.load(f)
                    if isinstance(cached, list) and len(cached) > 0:
                        print(f"[OFFLINE CACHE] Loaded {len(cached)} student(s) from local cache!")
                        return cached
                except Exception:
                    pass
            return None

    def get_questions(self, quarter=1):
        """Fetch questions for a specific quarter unit from Vercel API, with local cache fallback."""
        import os
        cache_dir = os.path.join("db", "cache")
        cache_file = os.path.join(cache_dir, f"questions_q{quarter}.json")
        try:
            # 1. Fetch units to find all matching unit_ids for the quarter
            units_url = f"{BASE_URL}/units"
            req_units = urllib.request.Request(units_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req_units, timeout=5) as resp:
                units = json.loads(resp.read().decode('utf-8'))
            
            # Find all units matching Quarter (e.g. Q1, Q2, etc.)
            q_str = f"Q{quarter}"
            q_full_str = f"Quarter {quarter}"
            matching_unit_ids = set()
            for unit in units:
                unit_quarter = unit.get("quarter", "")
                code = str(unit.get("code", "")).upper()
                title = str(unit.get("title", "")).upper()
                # Check quarter field first, then fallback to code/title search
                if q_full_str.upper() == str(unit_quarter).upper() or q_str in code or q_full_str.upper() in title:
                    matching_unit_ids.add(unit.get("id"))
            
            print(f"[API INFO] Matching Unit IDs for {q_full_str}: {list(matching_unit_ids)}")
            
            # 2. Fetch all questions and filter by unit_id or quarter field
            questions_url = f"{BASE_URL}/questions"
            req_qs = urllib.request.Request(questions_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req_qs, timeout=5) as resp:
                all_questions = json.loads(resp.read().decode('utf-8'))
            
            # Filter active questions matching unit_id or quarter field
            filtered = []
            for q in all_questions:
                q_unit_id = q.get("unitId") or q.get("unit_id")
                q_quarter = q.get("quarter")
                q_active = q.get("isActive") if q.get("isActive") is not None else q.get("is_active", True)
                
                is_match = False
                if q_active:
                    # Check the quarter column directly
                    if q_quarter and q_full_str.upper() == str(q_quarter).upper():
                        is_match = True
                    # Match against any of the unit IDs associated with this Quarter
                    elif q_unit_id in matching_unit_ids:
                        is_match = True
                
                if is_match:
                    filtered.append(q)
            
            # Print status summary and cache if questions found
            if len(filtered) > 0:
                print(f"[API SUCCESS] Found {len(filtered)} active questions matching {q_full_str}")
                try:
                    os.makedirs(cache_dir, exist_ok=True)
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(filtered, f, indent=4)
                except Exception:
                    pass
                return filtered
            else:
                print(f"[API WARNING] No active questions found matching {q_full_str}")
            
        except Exception as e:
            print(f"[API ERROR] Failed to fetch questions from Vercel: {e}")

        # Offline fallback: read from local cache if available
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_qs = json.load(f)
                if isinstance(cached_qs, list) and len(cached_qs) > 0:
                    print(f"[OFFLINE CACHE] Loaded {len(cached_qs)} dynamic question(s) for Quarter {quarter} from local cache!")
                    return cached_qs
            except Exception:
                pass

        return None

    def get_assessment_id(self, quarter=1):
        """Fetch assessments and find one matching the given Quarter, with session cache."""
        if quarter in self._assessment_cache:
            return self._assessment_cache[quarter]

        url = f"{BASE_URL}/assessments"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as resp:
                assessments = json.loads(resp.read().decode('utf-8'))
            
            q_str = f"Q{quarter}"
            q_full_str = f"Quarter {quarter}"
            for ass in assessments:
                title = str(ass.get("title", "")).upper()
                if q_str in title or q_full_str.upper() in title:
                    ass_id = ass.get("id")
                    self._assessment_cache[quarter] = ass_id
                    return ass_id
            return None
        except Exception as e:
            print(f"[API ERROR] Failed to fetch assessment_id: {e}")
            return None

    def queue_offline_result(self, payload):
        """Save un-synced game result to local persistent queue for automatic retry."""
        import os
        os.makedirs("db", exist_ok=True)
        q_path = os.path.join("db", "pending_sync.json")
        pending = []
        if os.path.exists(q_path):
            try:
                with open(q_path, "r", encoding="utf-8") as f:
                    pending = json.load(f)
            except Exception:
                pending = []
        pending.append(payload)
        try:
            with open(q_path, "w", encoding="utf-8") as f:
                json.dump(pending, f, indent=4)
            print(f"[OFFLINE QUEUE] Saved game result to local offline queue (pending sync count: {len(pending)})")
        except Exception as e:
            print(f"[OFFLINE QUEUE ERROR] Failed to write offline queue: {e}")

    def sync_offline_results(self):
        """Flush any pending offline game results to the live Vercel database."""
        import os
        q_path = os.path.join("db", "pending_sync.json")
        if not os.path.exists(q_path):
            return 0
        try:
            with open(q_path, "r", encoding="utf-8") as f:
                pending = json.load(f)
        except Exception:
            return 0

        if not pending or not isinstance(pending, list):
            return 0

        remaining = []
        synced_count = 0
        for item in pending:
            try:
                url = f"{BASE_URL}/game-results"
                data = json.dumps(item).encode('utf-8')
                req = urllib.request.Request(
                    url,
                    data=data,
                    headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'},
                    method='POST'
                )
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status in [200, 201]:
                        synced_count += 1
                        print(f"[SYNC SUCCESS] Flushed offline evaluation for student #{item.get('studentId')}")
                    else:
                        remaining.append(item)
            except Exception:
                # Network still offline / failed -> keep for next retry
                remaining.append(item)

        if remaining:
            try:
                with open(q_path, "w", encoding="utf-8") as f:
                    json.dump(remaining, f, indent=4)
            except Exception:
                pass
        else:
            try:
                os.remove(q_path)
                print("[SYNC COMPLETE] All offline records successfully synced to live database!")
            except Exception:
                pass

        return synced_count

    def save_game_result(self, student_id, score, total_questions, correct_answers, percentage, feedback, grade_level, assessment_id=None):
        """Post game result to Vercel API, or automatically queue for offline sync if disconnected."""
        url = f"{BASE_URL}/game-results"
        # Convert student_id to integer if possible for relational foreign key in DB
        numeric_student_id = student_id
        if isinstance(student_id, str) and student_id.isdigit():
            numeric_student_id = int(student_id)

        # Ensure valid assessment ID (fallback to 1 if None)
        ass_id = assessment_id if assessment_id is not None else 1

        payload = {
            "studentId": numeric_student_id,
            "student_id": numeric_student_id,
            "assessmentId": ass_id,
            "assessment_id": ass_id,
            "gradeLevel": grade_level,
            "grade_level": grade_level,
            "score": score,
            "totalQuestions": total_questions,
            "total_questions": total_questions,
            "correctAnswers": correct_answers,
            "correct_answers": correct_answers,
            "percentage": percentage,
            "feedback": feedback
        }

        try:
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                url, 
                data=data, 
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'Mozilla/5.0'
                },
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=8) as response:
                res_body = response.read().decode('utf-8')
                print(f"[API SUCCESS] Game result saved to Vercel. Response: {res_body}")
                # Try flushing any other previously pending results as well
                self.sync_offline_results()
                return True
        except Exception as e:
            print(f"[API ERROR / OFFLINE] Network unavailable ({e}). Queuing result offline...")
            self.queue_offline_result(payload)
            return False

    def _get_student_reset_timestamp(self, student_id):
        """Read recorded reset timestamp for a student from db/reset_records.json."""
        if not student_id:
            return None
        import os
        reset_file = os.path.join("db", "reset_records.json")
        if os.path.exists(reset_file):
            try:
                with open(reset_file, "r", encoding="utf-8") as f:
                    records = json.load(f)
                    val = records.get(str(student_id))
                    if val is not None:
                        return float(val)
            except Exception:
                pass
        return None

    def delete_student_records(self, student_id=None, student_db_id=None):
        """
        Purge all past progress and grade records from the live Vercel database for a student:
        1. Deletes all past grade rows for this student via DELETE /api/grades
        2. Clears any pending offline synchronization results in db/pending_sync.json
        3. Records a persistent reset timestamp in db/reset_records.json so historical game results
           prior to starting this new game are excluded from leaderboards and rankings.
        """
        import os
        import time
        from datetime import datetime, timezone

        target_ids = set()
        if student_id is not None:
            target_ids.add(str(student_id))
            if str(student_id).isdigit():
                target_ids.add(int(student_id))
        if student_db_id is not None:
            target_ids.add(str(student_db_id))
            if str(student_db_id).isdigit():
                target_ids.add(int(student_db_id))

        if not target_ids:
            return 0

        print(f"[DB RESET] Purging past database records for student IDs: {target_ids}...")

        # 1. Delete matching grades from live Vercel database (/api/grades)
        deleted_count = 0
        try:
            all_grades = self.get_grades(filter_reset=False)
            for g in all_grades:
                g_sid = g.get("studentId")
                if g_sid in target_ids or str(g_sid) in target_ids:
                    gid = g.get("id")
                    if gid is not None:
                        del_url = f"{BASE_URL}/grades"
                        del_data = json.dumps({"id": gid}).encode("utf-8")
                        req = urllib.request.Request(
                            del_url,
                            data=del_data,
                            headers={"User-Agent": "Mozilla/5.0", "Content-Type": "application/json"},
                            method="DELETE"
                        )
                        try:
                            with urllib.request.urlopen(req, timeout=5) as resp:
                                if resp.status == 200:
                                    deleted_count += 1
                        except Exception as de:
                            print(f"[DB RESET WARN] Failed to delete grade ID {gid}: {de}")
            print(f"[DB RESET SUCCESS] Deleted {deleted_count} past grade record(s) from Vercel database.")
        except Exception as e:
            print(f"[DB RESET ERROR] Error querying/deleting grades from Vercel: {e}")

        # 2. Clear matching pending offline sync results
        try:
            q_path = os.path.join("db", "pending_sync.json")
            if os.path.exists(q_path):
                with open(q_path, "r", encoding="utf-8") as f:
                    pending = json.load(f)
                if isinstance(pending, list):
                    filtered_pending = [
                        item for item in pending
                        if item.get("studentId") not in target_ids
                        and str(item.get("studentId")) not in target_ids
                        and str(item.get("student_id")) not in target_ids
                    ]
                    if len(filtered_pending) != len(pending):
                        with open(q_path, "w", encoding="utf-8") as f:
                            json.dump(filtered_pending, f, indent=4)
                        print(f"[DB RESET] Removed {len(pending) - len(filtered_pending)} item(s) from offline sync queue.")
        except Exception as e:
            print(f"[DB RESET WARN] Error cleaning offline sync queue: {e}")

        # 3. Store reset timestamp in db/reset_records.json
        try:
            os.makedirs("db", exist_ok=True)
            reset_file = os.path.join("db", "reset_records.json")
            records = {}
            if os.path.exists(reset_file):
                try:
                    with open(reset_file, "r", encoding="utf-8") as f:
                        records = json.load(f)
                except Exception:
                    records = {}
            now_ts = datetime.now(timezone.utc).timestamp()
            for tid in target_ids:
                records[str(tid)] = now_ts
            with open(reset_file, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=4)
            print(f"[DB RESET] Stored reset timestamp {now_ts} for student {target_ids}")
        except Exception as e:
            print(f"[DB RESET WARN] Error writing reset timestamp: {e}")

        return deleted_count

    def get_grades(self, filter_reset=True):
        """Fetch all recorded grades (recent grades) from Vercel API, filtering out reset past records."""
        url = f"{BASE_URL}/grades"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode('utf-8'))
                if not isinstance(data, list):
                    return []
                if not filter_reset:
                    return data
                
                # Filter out grades created before student's reset timestamp
                from datetime import datetime, timezone
                filtered = []
                for g in data:
                    sid = g.get("studentId")
                    reset_ts = self._get_student_reset_timestamp(sid)
                    if reset_ts and g.get("createdAt"):
                        try:
                            g_time = datetime.fromisoformat(g["createdAt"].replace('Z', '+00:00')).timestamp()
                            if g_time < reset_ts:
                                continue
                        except Exception:
                            pass
                    filtered.append(g)
                return filtered
        except Exception as e:
            print(f"[API ERROR] Failed to fetch grades from Vercel: {e}")
            return []

    def get_game_results(self, filter_reset=True):
        """Fetch all recorded game results from Vercel API, filtering out reset past records."""
        url = f"{BASE_URL}/game-results"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode('utf-8'))
                if not isinstance(data, list):
                    return []
                if not filter_reset:
                    return data

                # Filter out results created before student's reset timestamp
                from datetime import datetime, timezone
                filtered = []
                for gr in data:
                    sid = gr.get("studentId")
                    reset_ts = self._get_student_reset_timestamp(sid)
                    if reset_ts and gr.get("createdAt"):
                        try:
                            gr_time = datetime.fromisoformat(gr["createdAt"].replace('Z', '+00:00')).timestamp()
                            if gr_time < reset_ts:
                                continue
                        except Exception:
                            pass
                    filtered.append(gr)
                return filtered
        except Exception as e:
            print(f"[API ERROR] Failed to fetch game results from Vercel: {e}")
            return []

    def get_highest_grade_student(self):
        """
        Identify the student with the highest grade based on the database
        'recent grades' and evaluation records.
        """
        import os

        students = self.get_students() or []
        grades = self.get_grades()
        game_results = self.get_game_results()

        student_names = {}
        student_details = {}
        for s in students:
            db_id = s.get("id")
            c_id = str(s.get("studentId") or "")
            name = s.get("fullName") or f"{s.get('first_name', '')} {s.get('last_name', '')}".strip()
            if db_id is not None:
                student_names[db_id] = name
                student_details[db_id] = s
            if c_id:
                student_names[c_id] = name
                student_details[c_id] = s

        highest = None
        max_score = -1.0

        # 1. Process Live Grades table ("recent grades")
        for g in grades:
            s_id = g.get("studentId")
            s_name = g.get("studentName") or student_names.get(s_id) or student_names.get(str(s_id)) or f"Student #{s_id}"
            score = float(g.get("score") or g.get("pointsEarned") or 0.0)
            ass_title = g.get("assessmentTitle") or "Math Assessment"
            created = g.get("createdAt", "")
            
            details = student_details.get(s_id) or student_details.get(str(s_id)) or {}
            grade_lvl = details.get("gradeLevel") or "Grade 2"
            section = details.get("section") or "A"
            av_col = details.get("avatarColor") or "#6366f1"

            if score > max_score:
                max_score = score
                highest = {
                    "name": s_name,
                    "student_id": s_id,
                    "score": score,
                    "percentage": score,
                    "assessment_title": ass_title,
                    "grade_level": grade_lvl,
                    "section": section,
                    "avatar_color": av_col,
                    "created_at": created
                }

        # 2. Check Game Results if higher score or no grades
        for gr in game_results:
            s_id = gr.get("studentId")
            s_name = gr.get("studentName") or student_names.get(s_id) or student_names.get(str(s_id)) or f"Student #{s_id}"
            pct = float(gr.get("percentage") or gr.get("score") or 0.0)
            fb = gr.get("feedback") or "Quarter Quiz"
            created = gr.get("createdAt", "")

            details = student_details.get(s_id) or student_details.get(str(s_id)) or {}
            grade_lvl = gr.get("gradeLevel") or details.get("gradeLevel") or "Grade 2"
            section = details.get("section") or "A"
            av_col = details.get("avatarColor") or "#6366f1"

            if pct > max_score:
                max_score = pct
                highest = {
                    "name": s_name,
                    "student_id": s_id,
                    "score": pct,
                    "percentage": pct,
                    "assessment_title": fb,
                    "grade_level": grade_lvl,
                    "section": section,
                    "avatar_color": av_col,
                    "created_at": created
                }

        # 3. Offline/Local fallback
        if not highest:
            saves_dir = os.path.join("db", "saves")
            if os.path.exists(saves_dir):
                for fname in os.listdir(saves_dir):
                    if fname.endswith(".json"):
                        try:
                            with open(os.path.join(saves_dir, fname), "r", encoding="utf-8") as f:
                                sdata = json.load(f)
                                sel = sdata.get("selected_student") or {}
                                s_name = sel.get("fullName") or f"{sel.get('first_name', '')} {sel.get('last_name', '')}".strip() or "Student"
                                qd = sdata.get("quarter_data") or {}
                                correct = sum(1 for v in qd.get("first_attempt_correct", {}).values() if v)
                                total = len(qd.get("first_attempt_correct", {})) or 5
                                pct = (correct / total * 100) if total > 0 else 0
                                if pct > max_score:
                                    max_score = pct
                                    highest = {
                                        "name": s_name,
                                        "student_id": sel.get("id") or sdata.get("student_id"),
                                        "score": pct,
                                        "percentage": pct,
                                        "assessment_title": f"{qd.get('quarter_name', 'Stage').upper()} Quiz",
                                        "grade_level": sel.get("level") or "Grade 2",
                                        "section": "A",
                                        "avatar_color": "#38bdf8",
                                        "created_at": ""
                                    }
                        except Exception:
                            pass

        return highest

    def get_leaderboard_data(self):
        """
        Aggregate and rank student performance across all Quarters
        combining live Vercel API data (students, grades, game results) and local progress saves.
        Strictly restricts the roster to registered students in the live database.
        """
        import os

        # 1. Fetch Students from Live API
        students_api = self.get_students()
        student_map = {}
        alias_map = {}

        if students_api:
            for s in students_api:
                s_db_id = str(s.get("id") or "")
                s_custom_id = str(s.get("studentId") or "")
                
                primary_key = s_db_id if s_db_id else s_custom_id
                if not primary_key:
                    continue
                    
                student_entry = {
                    "id": s.get("id", primary_key),
                    "student_id": s_custom_id or primary_key,
                    "name": s.get("fullName") or f"{s.get('first_name', '')} {s.get('last_name', '')}".strip() or f"Student #{primary_key}",
                    "grade_level": s.get("gradeLevel") or s.get("grade_level") or "Grade 2",
                    "section": s.get("section") or "A",
                    "avatar_color": s.get("avatarColor") or "#6366f1",
                    "quarters": {1: None, 2: None, 3: None, 4: None},
                    "total_score": 0,
                    "total_correct": 0,
                    "total_questions": 0,
                    "quarters_completed": 0,
                    "average_percentage": 0.0
                }
                student_map[primary_key] = student_entry
                if s_db_id:
                    alias_map[s_db_id] = primary_key
                if s_custom_id:
                    alias_map[s_custom_id] = primary_key
        else:
            # Fallback ONLY if API is completely offline / unreachable
            saves_dir = os.path.join("db", "saves")
            if os.path.exists(saves_dir):
                for fname in os.listdir(saves_dir):
                    if fname.endswith(".json"):
                        try:
                            with open(os.path.join(saves_dir, fname), "r", encoding="utf-8") as f:
                                sdata = json.load(f)
                                raw_id = str(sdata.get("student_id") or fname[:-5])
                                sel = sdata.get("selected_student") or {}
                                s_name = sel.get("fullName") or f"{sel.get('first_name', '')} {sel.get('last_name', '')}".strip() or f"Student #{raw_id}"
                                student_map[raw_id] = {
                                    "id": sel.get("id", raw_id),
                                    "student_id": raw_id,
                                    "name": s_name,
                                    "grade_level": sel.get("grade_level") or sel.get("level") or "Grade 2",
                                    "section": sel.get("section") or "A",
                                    "avatar_color": "#38bdf8",
                                    "quarters": {1: None, 2: None, 3: None, 4: None},
                                    "total_score": 0,
                                    "total_correct": 0,
                                    "total_questions": 0,
                                    "quarters_completed": 0,
                                    "average_percentage": 0.0
                                }
                                alias_map[raw_id] = raw_id
                        except Exception:
                            pass

        # 2. Check local saves for quarter progress of registered students
        saves_dir = os.path.join("db", "saves")
        if os.path.exists(saves_dir):
            for fname in os.listdir(saves_dir):
                if fname.endswith(".json"):
                    fpath = os.path.join(saves_dir, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            sdata = json.load(f)
                            raw_id = str(sdata.get("student_id") or fname[:-5])
                            sel = sdata.get("selected_student") or {}
                            s_id = alias_map.get(raw_id) or alias_map.get(str(sel.get("id", ""))) or alias_map.get(str(sel.get("studentId", "")))
                            
                            if s_id and s_id in student_map:
                                # Parse local quarter completion
                                q_data = sdata.get("quarter_data") or {}
                                q_name = q_data.get("quarter_name") or ""
                                if q_name:
                                    q_num = 1
                                    if "2" in q_name: q_num = 2
                                    elif "3" in q_name: q_num = 3
                                    elif "4" in q_name: q_num = 4
                                    
                                    correct_dict = q_data.get("first_attempt_correct", {})
                                    correct = sum(1 for v in correct_dict.values() if v)
                                    total = len(correct_dict) if len(correct_dict) > 0 else 5
                                    pct = (correct / total * 100) if total > 0 else 0
                                    score = correct * 20  # 20 pts per question -> 100 max
                                    
                                    student_map[s_id]["quarters"][q_num] = {
                                        "score": score,
                                        "correct": correct,
                                        "total": total,
                                        "percentage": pct,
                                        "completed": bool(q_data.get("completed", False) or correct > 0)
                                    }
                    except Exception as e:
                        print(f"[SAVE ERROR] Error reading local save {fname}: {e}")

        # 3. Fetch Live Grades and Game Results from Vercel API
        api_grades = self.get_grades()
        for g in api_grades:
            raw_id = str(g.get("studentId") or g.get("student_id") or "")
            if not raw_id:
                continue
            st_id = alias_map.get(raw_id)
            if not st_id or st_id not in student_map:
                continue

            # Map assessment title to quarter
            q_num = 1
            title = str(g.get("assessmentTitle", "")).upper()
            if "UNIT 2" in title or "Q2" in title or "QUARTER 2" in title: q_num = 2
            elif "UNIT 3" in title or "Q3" in title or "QUARTER 3" in title: q_num = 3
            elif "UNIT 4" in title or "Q4" in title or "QUARTER 4" in title: q_num = 4

            score = int(g.get("pointsEarned") or g.get("score") or 0)
            pct = float(g.get("score") or 100.0)

            existing = student_map[st_id]["quarters"][q_num]
            if not existing or score > existing.get("score", 0):
                student_map[st_id]["quarters"][q_num] = {
                    "score": score,
                    "correct": int(score // 20) if score <= 100 else 5,
                    "total": 5,
                    "percentage": pct,
                    "completed": True
                }

        api_results = self.get_game_results()
        for res in api_results:
            raw_id = str(res.get("studentId") or res.get("student_id") or "")
            if not raw_id:
                continue
            st_id = alias_map.get(raw_id)
            if not st_id or st_id not in student_map:
                continue

            q_num = 1
            fb = str(res.get("feedback", "")).upper()
            if "QUARTER 2" in fb or "Q2" in fb: q_num = 2
            elif "QUARTER 3" in fb or "Q3" in fb: q_num = 3
            elif "QUARTER 4" in fb or "Q4" in fb: q_num = 4

            raw_score = int(res.get("score") or 0)
            correct = int(res.get("correctAnswers") or res.get("correct_answers") or raw_score)
            total = int(res.get("totalQuestions") or res.get("total_questions") or 5)
            pct = float(res.get("percentage") or ((correct / total * 100) if total > 0 else 0))

            # Normalize score: if raw_score was stored as raw question count (<= 5), scale to standard 100-point stage score
            score = raw_score
            if total > 0 and score <= total and score <= 5:
                score = int(correct * (100 // total))

            existing = student_map[st_id]["quarters"][q_num]
            if not existing or score > existing.get("score", 0):
                student_map[st_id]["quarters"][q_num] = {
                    "score": score,
                    "correct": correct,
                    "total": total,
                    "percentage": pct,
                    "completed": True
                }

        # 4. Calculate aggregate totals
        leaderboard_list = []
        for s_id, s_info in student_map.items():
            tot_score = 0
            tot_correct = 0
            tot_questions = 0
            q_completed = 0
            pcts = []

            for qn in range(1, 5):
                qd = s_info["quarters"][qn]
                if qd:
                    tot_score += qd.get("score", 0)
                    tot_correct += qd.get("correct", 0)
                    tot_questions += qd.get("total", 0)
                    if qd.get("completed", False) or qd.get("score", 0) > 0:
                        q_completed += 1
                    pcts.append(qd.get("percentage", 0))

            s_info["total_score"] = tot_score
            s_info["total_correct"] = tot_correct
            s_info["total_questions"] = tot_questions
            s_info["quarters_completed"] = q_completed
            s_info["average_percentage"] = (sum(pcts) / len(pcts)) if pcts else 0.0
            leaderboard_list.append(s_info)

        # 5. Sort by Total Score descending -> Quarters Completed -> Average Percentage
        leaderboard_list.sort(
            key=lambda x: (x["total_score"], x["quarters_completed"], x["average_percentage"]),
            reverse=True
        )

        # Assign Ranks
        for idx, entry in enumerate(leaderboard_list):
            entry["rank"] = idx + 1

        return leaderboard_list

# Function to create mock database connection instance
def connect_db(*args, **kwargs):
    return Database()

# Default singleton instance for `from db import db`
db = Database()
