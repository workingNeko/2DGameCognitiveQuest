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

    def save_game_result(self, student_id, score, total_questions, correct_answers, percentage, feedback, grade_level, assessment_id=None):
        """Post game result to Vercel API."""
        url = f"{BASE_URL}/game-results"
        try:
            # We send both camelCase (Next.js/Drizzle standard) and snake_case fields to be safe
            payload = {
                "studentId": student_id,
                "student_id": student_id,
                "assessmentId": assessment_id,
                "assessment_id": assessment_id,
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
                return True
        except Exception as e:
            print(f"[API ERROR] Failed to save game result to Vercel: {e}")
            return False

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

    def get_leaderboard_data(self):
        """
        Aggregate and rank student performance across all Quarters
        combining live Vercel API data and local progress saves.
        """
        import os

        # 1. Fetch Students
        students_api = self.get_students() or []
        student_map = {}
        alias_map = {}

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

        # 2. Check local saves for any offline/local student profiles
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
                            s_id = alias_map.get(raw_id) or alias_map.get(str(sel.get("id", ""))) or alias_map.get(str(sel.get("studentId", ""))) or raw_id
                            
                            if s_id not in student_map:
                                name = sel.get("fullName") or f"{sel.get('first_name', '')} {sel.get('last_name', '')}".strip() or f"Student #{s_id}"
                                student_map[s_id] = {
                                    "id": sel.get("id", s_id),
                                    "student_id": s_id,
                                    "name": name,
                                    "grade_level": sel.get("grade_level") or sel.get("gradeLevel") or "Grade 2",
                                    "section": sel.get("section") or "A",
                                    "avatar_color": sel.get("avatarColor") or "#38bdf8",
                                    "quarters": {1: None, 2: None, 3: None, 4: None},
                                    "total_score": 0,
                                    "total_correct": 0,
                                    "total_questions": 0,
                                    "quarters_completed": 0,
                                    "average_percentage": 0.0
                                }
                                alias_map[raw_id] = s_id
                            
                            # Parse local quarter completion
                            q_data = sdata.get("quarter_data") or {}
                            q_type = q_data.get("quarter_type")
                            if q_type:
                                q_num = 1
                                if "2" in q_type: q_num = 2
                                elif "3" in q_type: q_num = 3
                                elif "4" in q_type: q_num = 4
                                
                                score = q_data.get("score", 0)
                                correct = q_data.get("correct_answers", 0)
                                total = q_data.get("total_questions", 5)
                                pct = (correct / total * 100) if total > 0 else 0
                                student_map[s_id]["quarters"][q_num] = {
                                    "score": score,
                                    "correct": correct,
                                    "total": total,
                                    "percentage": pct,
                                    "completed": bool(q_data.get("completed", False))
                                }
                    except Exception as e:
                        print(f"⚠️ Error reading local save {fname}: {e}")

        # 3. Fetch Game Results from Vercel API and overlay/aggregate
        api_results = self.get_game_results()
        for res in api_results:
            raw_id = str(res.get("studentId") or res.get("student_id") or "")
            if not raw_id:
                continue
            st_id = alias_map.get(raw_id, raw_id)
            if st_id not in student_map:
                student_map[st_id] = {
                    "id": st_id,
                    "student_id": st_id,
                    "name": f"Student #{st_id}",
                    "grade_level": res.get("gradeLevel") or "Grade 2",
                    "section": "A",
                    "avatar_color": "#6366f1",
                    "quarters": {1: None, 2: None, 3: None, 4: None},
                    "total_score": 0,
                    "total_correct": 0,
                    "total_questions": 0,
                    "quarters_completed": 0,
                    "average_percentage": 0.0
                }

            # Determine Quarter from assessmentId, feedback, or title
            q_num = 1
            fb = str(res.get("feedback", "")).upper()
            if "QUARTER 2" in fb or "Q2" in fb: q_num = 2
            elif "QUARTER 3" in fb or "Q3" in fb: q_num = 3
            elif "QUARTER 4" in fb or "Q4" in fb: q_num = 4

            score = int(res.get("score") or 0)
            correct = int(res.get("correctAnswers") or res.get("correct_answers") or score)
            total = int(res.get("totalQuestions") or res.get("total_questions") or 5)
            pct = float(res.get("percentage") or ((correct / total * 100) if total > 0 else 0))

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
