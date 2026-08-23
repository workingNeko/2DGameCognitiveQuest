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
            # 1. Fetch units to find the matching unit_id for the quarter
            units_url = f"{BASE_URL}/units"
            req_units = urllib.request.Request(units_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req_units, timeout=8) as resp:
                units = json.loads(resp.read().decode('utf-8'))
            
            # Find unit matching Quarter (e.g. Q1, Q2, etc.)
            q_str = f"Q{quarter}"
            q_full_str = f"Quarter {quarter}"
            unit_id = None
            for unit in units:
                unit_quarter = unit.get("quarter", "")
                code = str(unit.get("code", "")).upper()
                title = str(unit.get("title", "")).upper()
                # Check new quarter field first, then fallback to code/title search
                if q_full_str.upper() == str(unit_quarter).upper() or q_str in code or q_full_str.upper() in title:
                    unit_id = unit.get("id")
                    print(f"[API INFO] Found Unit ID {unit_id} for {q_full_str}")
                    break
            
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
                    # Check the new quarter column directly
                    if q_quarter and q_full_str.upper() == str(q_quarter).upper():
                        is_match = True
                    # Fallback to unit ID
                    elif unit_id is not None and q_unit_id == unit_id:
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

# Function to create mock database connection instance
def connect_db(*args, **kwargs):
    return Database()

# Default singleton instance for `from db import db`
db = Database()
