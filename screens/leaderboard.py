# screens/leaderboard.py - Leaderboard and Hall of Fame Screen
import pygame
import os
import time
import math
from db.connect_db import db


class LeaderboardScreen:
    def __init__(self, screen, main_menu):
        self.screen = screen
        self.main_menu = main_menu
        self.width, self.height = screen.get_size()

        # Gesture and Cursor Tracking
        self.cursor_pos = (self.width // 2, self.height // 2)
        self.current_gesture = "NO HAND"
        self.fist_start_time = 0
        self.CLICK_HOLD_TIME = 0.9

        # Background Image or Gradient
        bg_path = os.path.join("assets", "images", "menu_background.png")
        if os.path.exists(bg_path):
            self.bg_image = pygame.image.load(bg_path).convert()
            self.bg_image = pygame.transform.scale(self.bg_image, (self.width, self.height))
        else:
            self.bg_image = None

        # Fonts
        self.title_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Comic Sans MS", "Arial"], 34, bold=True)
        self.subtitle_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Calibri", "Arial"], 15)
        self.spotlight_title_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Calibri", "Arial"], 13, bold=True)
        self.spotlight_name_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Calibri", "Arial"], 18, bold=True)
        self.spotlight_meta_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Calibri", "Arial"], 14)
        self.tab_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Calibri", "Arial"], 15, bold=True)
        self.header_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Calibri", "Arial"], 14, bold=True)
        self.row_name_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Calibri", "Arial"], 16, bold=True)
        self.row_meta_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Calibri", "Arial"], 14)
        self.score_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Calibri", "Arial"], 17, bold=True)
        self.badge_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Calibri", "Arial"], 13, bold=True)
        self.btn_font = pygame.font.SysFont(["Segoe UI", "Tahoma", "Calibri", "Arial"], 15, bold=True)

        # Tab Selection: 0 = OVERALL, 1 = Q1, 2 = Q2, 3 = Q3, 4 = Q4
        self.active_tab = 0
        self.tabs = [
            {"id": 0, "label": "OVERALL RANKINGS", "quarter": None},
            {"id": 1, "label": "QUARTER 1 (Shapes)", "quarter": 1},
            {"id": 2, "label": "QUARTER 2 (Division)", "quarter": 2},
            {"id": 3, "label": "QUARTER 3 (Fractions)", "quarter": 3},
            {"id": 4, "label": "QUARTER 4 (Time & Angles)", "quarter": 4}
        ]

        # Top Action Buttons
        self.back_btn_rect = pygame.Rect(30, 18, 124, 42)
        self.refresh_btn_rect = pygame.Rect(self.width - 154, 18, 124, 42)

        # Scroll & Data State
        self.scroll_offset = 0
        self.row_height = 58
        self.max_visible_rows = 6
        self.leaderboard_data = []
        self.filtered_data = []
        self.highest_student = None
        self.is_loading = False
        self.status_message = "Syncing with live database..."
        self.status_timer = time.time() + 2.0

        # Load initial leaderboard data from live database
        self.refresh_data()

    def update_gesture(self, cursor_pos, fist_start_time, click_hold_time, current_gesture):
        """Update cursor and gesture tracking from MainMenu."""
        self.cursor_pos = cursor_pos
        self.fist_start_time = fist_start_time
        self.CLICK_HOLD_TIME = click_hold_time
        self.current_gesture = current_gesture

    def refresh_data(self):
        """Fetch and filter leaderboard and highest recent grade data from live database."""
        self.is_loading = True
        try:
            # Query live database for rankings and highest grade
            self.leaderboard_data = db.get_leaderboard_data()
            self.highest_student = db.get_highest_grade_student()
            self.apply_filter()
            
            top_name = self.highest_student.get("name", "Student") if self.highest_student else "None"
            top_score = self.highest_student.get("score", 0) if self.highest_student else 0
            self.status_message = f"Live DB Synced: Top Grade - {top_name} ({top_score:.0f}%)"
            self.status_timer = time.time() + 3.0
            print(f"[LEADERBOARD] Leaderboard updated from live database! Highest Grade: {top_name} ({top_score}%)")
        except Exception as e:
            print(f"[LEADERBOARD ERROR] Leaderboard data fetch error: {e}")
            self.status_message = "Loaded offline save data"
            self.status_timer = time.time() + 2.5
        finally:
            self.is_loading = False

    def apply_filter(self):
        """Filter and sort leaderboard based on selected tab."""
        target_q = self.tabs[self.active_tab]["quarter"]
        
        if target_q is None:
            # Overall: already sorted by total_score -> quarters_completed -> average_percentage
            self.filtered_data = list(self.leaderboard_data)
            for idx, entry in enumerate(self.filtered_data):
                entry["display_rank"] = idx + 1
                entry["display_score"] = entry.get("total_score", 0)
                entry["display_acc"] = entry.get("average_percentage", 0.0)
        else:
            # Filter and sort by specific Quarter
            q_list = []
            for entry in self.leaderboard_data:
                qd = entry.get("quarters", {}).get(target_q)
                score = qd.get("score", 0) if qd else 0
                pct = qd.get("percentage", 0.0) if qd else 0.0
                completed = qd.get("completed", False) if qd else False
                
                clone = dict(entry)
                clone["display_score"] = score
                clone["display_acc"] = pct
                clone["quarter_completed"] = completed
                q_list.append(clone)

            q_list.sort(
                key=lambda x: (x["display_score"], x["display_acc"]),
                reverse=True
            )
            for idx, entry in enumerate(q_list):
                entry["display_rank"] = idx + 1
            self.filtered_data = q_list

        self.scroll_offset = 0

    def trigger_click(self, pos):
        """Handle click actions from gesture fist or mouse."""
        # 1. Back button
        if self.back_btn_rect.collidepoint(pos):
            self.main_menu.current_screen = "menu"
            self.main_menu.leaderboard = None
            self.main_menu.setup_buttons()
            return

        # 2. Refresh button
        if self.refresh_btn_rect.collidepoint(pos):
            self.refresh_data()
            return

        # 3. Tab buttons
        tab_start_x = (self.width - (len(self.tabs) * 190 + (len(self.tabs) - 1) * 10)) // 2
        tab_y = 142
        tab_w = 190
        tab_h = 36
        
        for i, tab in enumerate(self.tabs):
            t_rect = pygame.Rect(tab_start_x + i * (tab_w + 10), tab_y, tab_w, tab_h)
            if t_rect.collidepoint(pos):
                if self.active_tab != i:
                    self.active_tab = i
                    self.apply_filter()
                return

        # 4. Scroll buttons
        table_w = min(1080, self.width - 80)
        table_x = (self.width - table_w) // 2
        table_y = 186
        table_h = self.height - table_y - 25

        up_btn = pygame.Rect(table_x + table_w - 44, table_y + 12, 36, 36)
        down_btn = pygame.Rect(table_x + table_w - 44, table_y + table_h - 48, 36, 36)

        max_scroll = max(0, len(self.filtered_data) - self.max_visible_rows)
        if up_btn.collidepoint(pos):
            self.scroll_offset = max(0, self.scroll_offset - 1)
        elif down_btn.collidepoint(pos):
            self.scroll_offset = min(max_scroll, self.scroll_offset + 1)

    def handle_event(self, event):
        """Handle keyboard or mouse events."""
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_BACKSPACE]:
                return "back"
            elif event.key == pygame.K_UP:
                self.scroll_offset = max(0, self.scroll_offset - 1)
            elif event.key == pygame.K_DOWN:
                max_scroll = max(0, len(self.filtered_data) - self.max_visible_rows)
                self.scroll_offset = min(max_scroll, self.scroll_offset + 1)
            elif event.key == pygame.K_r:
                self.refresh_data()
        elif event.type == pygame.MOUSEWHEEL:
            max_scroll = max(0, len(self.filtered_data) - self.max_visible_rows)
            if event.y > 0:
                self.scroll_offset = max(0, self.scroll_offset - 1)
            elif event.y < 0:
                self.scroll_offset = min(max_scroll, self.scroll_offset + 1)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.cursor_pos = event.pos
            self.trigger_click(event.pos)
        return None

    def update(self):
        """Update animations and states."""
        pass

    def draw(self):
        """Render the complete Hall of Fame & Leaderboard screen with live top student highlight."""
        now = pygame.time.get_ticks()

        # 1. Background
        if self.bg_image:
            self.screen.blit(self.bg_image, (0, 0))
        else:
            self.screen.fill((15, 23, 42))

        # Dark translucent overlay
        dim = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        dim.fill((10, 15, 29, 215))
        self.screen.blit(dim, (0, 0))

        # 2. Header & Title
        title_surf = self.title_font.render("COGNITIVE QUEST - HALL OF FAME", True, (255, 215, 0))
        self.screen.blit(title_surf, title_surf.get_rect(center=(self.width // 2, 28)))

        subtitle_surf = self.subtitle_font.render("DepEd MATATAG Grade 2 Mathematics Official Student Rankings", True, (203, 213, 225))
        self.screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(self.width // 2, 54)))

        # 3. Top Action Buttons
        # Back Button
        b_hov = self.back_btn_rect.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (220, 38, 38) if b_hov else (30, 41, 59), self.back_btn_rect, border_radius=10)
        pygame.draw.rect(self.screen, (248, 113, 113), self.back_btn_rect, 2, border_radius=10)
        b_txt = self.btn_font.render("<< BACK", True, (255, 255, 255))
        self.screen.blit(b_txt, b_txt.get_rect(center=self.back_btn_rect.center))

        # Refresh Button
        r_hov = self.refresh_btn_rect.collidepoint(self.cursor_pos)
        pygame.draw.rect(self.screen, (37, 99, 235) if r_hov else (30, 41, 59), self.refresh_btn_rect, border_radius=10)
        pygame.draw.rect(self.screen, (96, 165, 250), self.refresh_btn_rect, 2, border_radius=10)
        r_txt = self.btn_font.render("REFRESH", True, (255, 255, 255))
        self.screen.blit(r_txt, r_txt.get_rect(center=self.refresh_btn_rect.center))

        # Status toast
        if time.time() < self.status_timer:
            stat_surf = self.subtitle_font.render(self.status_message, True, (74, 222, 128))
            self.screen.blit(stat_surf, (self.width - stat_surf.get_width() - 170, 28))

        # 4. HIGHEST GRADE STUDENT SPOTLIGHT BANNER ("Recent Grades" from Database)
        spotlight_w = min(1080, self.width - 80)
        spotlight_x = (self.width - spotlight_w) // 2
        spotlight_y = 74
        spotlight_h = 56

        # Card container
        spotlight_surf = pygame.Surface((spotlight_w, spotlight_h), pygame.SRCALPHA)
        spotlight_surf.fill((20, 29, 50, 240))
        self.screen.blit(spotlight_surf, (spotlight_x, spotlight_y))
        
        # Subtle pulsing gold border
        pulse = (math.sin(now * 0.005) + 1) / 2
        border_col = (int(245 * (0.8 + 0.2 * pulse)), int(158 * (0.8 + 0.2 * pulse)), 11)
        pygame.draw.rect(self.screen, border_col, (spotlight_x, spotlight_y, spotlight_w, spotlight_h), 2, border_radius=12)

        if self.highest_student:
            top_name = self.highest_student.get("name", "Student")
            top_score = self.highest_student.get("score", 100.0)
            top_ass = self.highest_student.get("assessment_title", "Recent Assessment")
            top_grade_lvl = self.highest_student.get("grade_level", "Grade 2")
            top_section = self.highest_student.get("section", "A")
            top_avatar_col = self.highest_student.get("avatar_color", "#6366f1")

            # Crown / Star Ribbon Badge (Left)
            crown_badge_rect = pygame.Rect(spotlight_x + 14, spotlight_y + 11, 210, 34)
            pygame.draw.rect(self.screen, (245, 158, 11), crown_badge_rect, border_radius=8)
            crown_txt = self.spotlight_title_font.render("HIGHEST RECENT GRADE", True, (15, 23, 42))
            self.screen.blit(crown_txt, crown_txt.get_rect(center=crown_badge_rect.center))

            # Avatar Circle
            try:
                av_rgb = pygame.Color(top_avatar_col)
            except Exception:
                av_rgb = (99, 102, 241)
            av_center = (spotlight_x + 252, spotlight_y + 28)
            pygame.draw.circle(self.screen, av_rgb, av_center, 18)
            pygame.draw.circle(self.screen, (255, 215, 0), av_center, 18, 2)
            
            top_initial = top_name[0].upper() if top_name else "S"
            top_ini_surf = self.badge_font.render(top_initial, True, (255, 255, 255))
            self.screen.blit(top_ini_surf, top_ini_surf.get_rect(center=av_center))

            # Student Name
            name_surf = self.spotlight_name_font.render(top_name, True, (255, 255, 255))
            self.screen.blit(name_surf, (spotlight_x + 280, spotlight_y + 11))

            # Grade & Section
            meta_txt = f"{top_grade_lvl} - Section {top_section}"
            meta_surf = self.spotlight_meta_font.render(meta_txt, True, (148, 163, 184))
            self.screen.blit(meta_surf, (spotlight_x + 280, spotlight_y + 32))

            # Assessment & Score Tag (Right)
            score_badge_rect = pygame.Rect(spotlight_x + spotlight_w - 240, spotlight_y + 11, 226, 34)
            pygame.draw.rect(self.screen, (30, 58, 138), score_badge_rect, border_radius=8)
            pygame.draw.rect(self.screen, (56, 189, 248), score_badge_rect, 1, border_radius=8)
            
            score_tag_surf = self.score_font.render(f"{top_score:.1f}% Score", True, (74, 222, 128))
            self.screen.blit(score_tag_surf, (score_badge_rect.x + 12, score_badge_rect.y + 6))

            # Assessment title tag
            ass_txt = top_ass if len(top_ass) <= 30 else top_ass[:28] + "..."
            ass_surf = self.spotlight_meta_font.render(ass_txt, True, (203, 213, 225))
            self.screen.blit(ass_surf, (spotlight_x + spotlight_w - 250 - ass_surf.get_width(), spotlight_y + 18))
        else:
            no_rec_surf = self.row_meta_font.render("Awaiting evaluation and recent grades from live database...", True, (148, 163, 184))
            self.screen.blit(no_rec_surf, no_rec_surf.get_rect(center=(spotlight_x + spotlight_w // 2, spotlight_y + spotlight_h // 2)))

        # 5. Tab Bar
        tab_start_x = (self.width - (len(self.tabs) * 190 + (len(self.tabs) - 1) * 10)) // 2
        tab_y = 140
        tab_w = 190
        tab_h = 36

        for i, tab in enumerate(self.tabs):
            is_active = (self.active_tab == i)
            t_rect = pygame.Rect(tab_start_x + i * (tab_w + 10), tab_y, tab_w, tab_h)
            is_hov = t_rect.collidepoint(self.cursor_pos)

            if is_active:
                pygame.draw.rect(self.screen, (245, 158, 11), t_rect, border_radius=8)
                txt_col = (15, 23, 42)
            else:
                bg = (51, 65, 85) if is_hov else (30, 41, 59)
                pygame.draw.rect(self.screen, bg, t_rect, border_radius=8)
                pygame.draw.rect(self.screen, (100, 116, 139), t_rect, 1, border_radius=8)
                txt_col = (255, 255, 255) if is_hov else (203, 213, 225)

            t_surf = self.tab_font.render(tab["label"], True, txt_col)
            self.screen.blit(t_surf, t_surf.get_rect(center=t_rect.center))

        # 6. Main Leaderboard Card Box
        table_w = min(1080, self.width - 80)
        table_x = (self.width - table_w) // 2
        table_y = 186
        table_h = self.height - table_y - 25

        # Card Background
        card_surf = pygame.Surface((table_w, table_h), pygame.SRCALPHA)
        card_surf.fill((15, 23, 42, 235))
        self.screen.blit(card_surf, (table_x, table_y))
        pygame.draw.rect(self.screen, (51, 65, 85), (table_x, table_y, table_w, table_h), 2, border_radius=14)

        # Table Column Positions
        col_rank_x = table_x + 24
        col_name_x = table_x + 90
        col_grade_x = table_x + 360
        col_prog_x = table_x + 540
        col_acc_x = table_x + 750
        col_score_x = table_x + table_w - 140

        # Table Header Bar
        hdr_rect = pygame.Rect(table_x + 4, table_y + 4, table_w - 8, 38)
        pygame.draw.rect(self.screen, (30, 41, 59), hdr_rect, border_radius=10)

        self.screen.blit(self.header_font.render("RANK", True, (251, 191, 36)), (col_rank_x, table_y + 14))
        self.screen.blit(self.header_font.render("STUDENT NAME", True, (148, 163, 184)), (col_name_x, table_y + 14))
        self.screen.blit(self.header_font.render("GRADE & SECTION", True, (148, 163, 184)), (col_grade_x, table_y + 14))
        self.screen.blit(self.header_font.render("PROGRESS", True, (148, 163, 184)), (col_prog_x, table_y + 14))
        self.screen.blit(self.header_font.render("ACCURACY", True, (148, 163, 184)), (col_acc_x, table_y + 14))
        self.screen.blit(self.header_font.render("TOTAL POINTS", True, (251, 191, 36)), (col_score_x, table_y + 14))

        # 7. Render Student Rows
        active_student_id = str(getattr(self.main_menu, 'student_id', '') or '')
        content_y_start = table_y + 48

        # Calculate visible rows
        available_height = table_h - 60
        self.max_visible_rows = max(1, available_height // self.row_height)
        visible_entries = self.filtered_data[self.scroll_offset : self.scroll_offset + self.max_visible_rows]

        if not visible_entries:
            empty_txt = self.row_name_font.render("No student evaluation records found yet in database.", True, (148, 163, 184))
            self.screen.blit(empty_txt, empty_txt.get_rect(center=(table_x + table_w // 2, table_y + table_h // 2)))
        else:
            for r_idx, entry in enumerate(visible_entries):
                row_y = content_y_start + r_idx * self.row_height
                row_rect = pygame.Rect(table_x + 10, row_y, table_w - 60, self.row_height - 6)

                # Check if this row is the currently selected student
                is_current_player = (active_student_id and str(entry.get("student_id", "")) == active_student_id)
                row_hov = row_rect.collidepoint(self.cursor_pos)

                # Row background
                if is_current_player:
                    pygame.draw.rect(self.screen, (30, 58, 138), row_rect, border_radius=10)
                    row_pulse = (math.sin(now * 0.006) + 1) / 2
                    p_col = (255, 215, 0) if row_pulse > 0.4 else (56, 189, 248)
                    pygame.draw.rect(self.screen, p_col, row_rect, 2, border_radius=10)
                elif row_hov:
                    pygame.draw.rect(self.screen, (51, 65, 85), row_rect, border_radius=10)
                elif r_idx % 2 == 1:
                    pygame.draw.rect(self.screen, (23, 33, 53), row_rect, border_radius=10)

                # Rank Badge
                rank = entry.get("display_rank", 1)
                badge_rect = pygame.Rect(col_rank_x, row_y + 8, 38, 38)
                if rank == 1:
                    pygame.draw.rect(self.screen, (245, 158, 11), badge_rect, border_radius=8)
                    r_txt = self.badge_font.render("1st", True, (15, 23, 42))
                elif rank == 2:
                    pygame.draw.rect(self.screen, (148, 163, 184), badge_rect, border_radius=8)
                    r_txt = self.badge_font.render("2nd", True, (15, 23, 42))
                elif rank == 3:
                    pygame.draw.rect(self.screen, (180, 83, 9), badge_rect, border_radius=8)
                    r_txt = self.badge_font.render("3rd", True, (255, 255, 255))
                else:
                    pygame.draw.rect(self.screen, (30, 41, 59), badge_rect, border_radius=8)
                    pygame.draw.rect(self.screen, (71, 85, 105), badge_rect, 1, border_radius=8)
                    r_txt = self.badge_font.render(f"#{rank}", True, (203, 213, 225))
                self.screen.blit(r_txt, r_txt.get_rect(center=badge_rect.center))

                # Student Name & Avatar
                av_col_hex = entry.get("avatar_color", "#6366f1")
                try:
                    av_rgb = pygame.Color(av_col_hex)
                except Exception:
                    av_rgb = (99, 102, 241)
                pygame.draw.circle(self.screen, av_rgb, (col_name_x + 14, row_y + 26), 16)
                
                # Initial letter
                s_name = entry.get("name", "Student")
                initial = s_name[0].upper() if s_name else "S"
                ini_surf = self.badge_font.render(initial, True, (255, 255, 255))
                self.screen.blit(ini_surf, ini_surf.get_rect(center=(col_name_x + 14, row_y + 26)))

                name_txt = s_name
                if is_current_player:
                    name_txt += " (YOU)"
                name_surf = self.row_name_font.render(name_txt, True, (255, 215, 0) if is_current_player else (255, 255, 255))
                self.screen.blit(name_surf, (col_name_x + 40, row_y + 15))

                # Grade & Section
                gr_txt = f"{entry.get('grade_level', 'Grade 2')} - {entry.get('section', 'A')}"
                gr_surf = self.row_meta_font.render(gr_txt, True, (148, 163, 184))
                self.screen.blit(gr_surf, (col_grade_x, row_y + 17))

                # Progress Pills (Q1, Q2, Q3, Q4)
                for qn in range(1, 5):
                    q_box = pygame.Rect(col_prog_x + (qn - 1) * 44, row_y + 13, 38, 26)
                    qd = entry.get("quarters", {}).get(qn)
                    q_done = qd and (qd.get("completed", False) or qd.get("score", 0) > 0)

                    if q_done:
                        pygame.draw.rect(self.screen, (22, 101, 52), q_box, border_radius=6)
                        pygame.draw.rect(self.screen, (74, 222, 128), q_box, 1, border_radius=6)
                        q_txt_col = (255, 255, 255)
                    else:
                        pygame.draw.rect(self.screen, (30, 41, 59), q_box, border_radius=6)
                        pygame.draw.rect(self.screen, (71, 85, 105), q_box, 1, border_radius=6)
                        q_txt_col = (100, 116, 139)

                    qp_surf = self.badge_font.render(f"Q{qn}", True, q_txt_col)
                    self.screen.blit(qp_surf, qp_surf.get_rect(center=q_box.center))

                # Accuracy Percentage
                acc_val = entry.get("display_acc", 0.0)
                acc_txt = f"{acc_val:.1f}%" if acc_val > 0 else "0.0%"
                acc_col = (74, 222, 128) if acc_val >= 80 else ((251, 191, 36) if acc_val >= 60 else (248, 113, 113))
                acc_surf = self.score_font.render(acc_txt, True, acc_col)
                self.screen.blit(acc_surf, (col_acc_x, row_y + 15))

                # Total Score Badge
                pts_val = entry.get("display_score", 0)
                pts_box = pygame.Rect(col_score_x, row_y + 9, 100, 34)
                pygame.draw.rect(self.screen, (30, 41, 59), pts_box, border_radius=8)
                pygame.draw.rect(self.screen, (245, 158, 11), pts_box, 1, border_radius=8)

                pts_surf = self.score_font.render(f"{pts_val} pts", True, (255, 215, 0))
                self.screen.blit(pts_surf, pts_surf.get_rect(center=pts_box.center))

        # 8. Scroll Buttons
        max_scroll = max(0, len(self.filtered_data) - self.max_visible_rows)
        if max_scroll > 0:
            up_btn = pygame.Rect(table_x + table_w - 42, table_y + 48, 34, 34)
            down_btn = pygame.Rect(table_x + table_w - 42, table_y + table_h - 48, 34, 34)

            up_hov = up_btn.collidepoint(self.cursor_pos)
            down_hov = down_btn.collidepoint(self.cursor_pos)

            # Up button
            pygame.draw.rect(self.screen, (51, 65, 85) if up_hov else (30, 41, 59), up_btn, border_radius=8)
            pygame.draw.rect(self.screen, (148, 163, 184), up_btn, 1, border_radius=8)
            up_txt = self.btn_font.render("^", True, (255, 255, 255))
            self.screen.blit(up_txt, up_txt.get_rect(center=up_btn.center))

            # Down button
            pygame.draw.rect(self.screen, (51, 65, 85) if down_hov else (30, 41, 59), down_btn, border_radius=8)
            pygame.draw.rect(self.screen, (148, 163, 184), down_btn, 1, border_radius=8)
            down_txt = self.btn_font.render("v", True, (255, 255, 255))
            self.screen.blit(down_txt, down_txt.get_rect(center=down_btn.center))

    def cleanup(self):
        """Cleanup resources on exit."""
        pass
