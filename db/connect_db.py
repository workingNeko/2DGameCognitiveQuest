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
        """Fetch students list from Vercel API."""
        url = f"{BASE_URL}/students"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode('utf-8'))
                # If online, flush any pending offline sync queue
                self.sync_offline_results()
                return data
        except Exception as e:
            print(f"[API ERROR] Failed to fetch students from Vercel: {e}")
            return None

    def get_questions(self, quarter=1):
        """Fetch questions for a specific quarter unit from Vercel API."""
        try:
            # 1. Fetch units to find all matching unit_ids for the quarter
            units_url = f"{BASE_URL}/units"
            req_units = urllib.request.Request(units_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req_units, timeout=8) as resp:
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
            with urllib.request.urlopen(req_qs, timeout=8) as resp:
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
            
            # Print status summary
            if len(filtered) > 0:
                print(f"[API SUCCESS] Found {len(filtered)} active questions matching {q_full_str}")
            else:
                print(f"[API WARNING] No active questions found matching {q_full_str}")
            
            return filtered
        except Exception as e:
            print(f"[API ERROR] Failed to fetch questions from Vercel: {e}")
            return None

    def get_assessment_id(self, quarter=1):
        """Fetch assessments and find one matching the given Quarter."""
        url = f"{BASE_URL}/assessments"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as resp:
                assessments = json.loads(resp.read().decode('utf-8'))
            
            q_str = f"Q{quarter}"
            q_full_str = f"Quarter {quarter}"
            for ass in assessments:
                title = str(ass.get("title", "")).upper()
                if q_str in title or q_full_str.upper() in title:
                    return ass.get("id")
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

    def get_grades(self):
        """Fetch all recorded grades (recent grades) from Vercel API."""
        url = f"{BASE_URL}/grades"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data if isinstance(data, list) else []
        except Exception as e:
            print(f"[API ERROR] Failed to fetch grades from Vercel: {e}")
            return []

    def get_game_results(self):
        """Fetch all recorded game results from Vercel API."""
        url = f"{BASE_URL}/game-results"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data if isinstance(data, list) else []
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
