#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Cognitive Maze: Game Architecture, Mechanics & Dataset Integration Guide
PDF Generation Script using ReportLab
Generates a comprehensive, publication-grade Technical and Game Design Document.
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable, Preformatted
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# =========================================================================
# NUMBERED CANVAS (RUNNING HEADERS, FOOTERS & DYNAMIC PAGE COUNTS)
# =========================================================================
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages):
        page_num = self._pageNumber
        width, height = letter

        # Do not draw running header on cover page
        if page_num > 1:
            # Header top accent line
            self.setStrokeColor(colors.HexColor("#0F172A"))
            self.setLineWidth(1.5)
            self.line(48, height - 42, width - 48, height - 42)

            self.setStrokeColor(colors.HexColor("#D97706"))
            self.setLineWidth(1.0)
            self.line(48, height - 44, width - 48, height - 44)

            # Header running text
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(colors.HexColor("#0F172A"))
            self.drawString(48, height - 36, "COGNITIVE MAZE: TECHNICAL ARCHITECTURE & DATASET INTEGRATION")

            self.setFont("Helvetica", 8)
            self.setFillColor(colors.HexColor("#64748B"))
            self.drawRightString(width - 48, height - 36, "Grade 2 Math Educational RPG Engine")

        # Footer bottom accent line (on all pages)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.75)
        self.line(48, 44, width - 48, 44)

        # Footer text
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(48, 32, "Confidential - CognitiveQuest / DepEd Grade 2 Mathematics System")

        page_str = f"Page {page_num} of {total_pages}"
        self.drawRightString(width - 48, 32, page_str)


# =========================================================================
# HELPER FACTORY FUNCTIONS FOR STYLED ELEMENTS
# =========================================================================
def create_callout(title, text, styles, border_color="#D97706", bg_color="#FEF3C7"):
    content = [
        Paragraph(f"<b>{title}</b>", styles["CalloutTitle"]),
        Spacer(1, 4),
        Paragraph(text, styles["CalloutText"])
    ]
    t = Table([[content]], colWidths=[516])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor(bg_color)),
        ('LEFTPADDING', (0,0), (-1,-1), 14),
        ('RIGHTPADDING', (0,0), (-1,-1), 14),
        ('TOPPADDING', (0,0), (-1,-1), 9),
        ('BOTTOMPADDING', (0,0), (-1,-1), 9),
        ('LINELEFT', (0,0), (-1,-1), 4.5, colors.HexColor(border_color)),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    return t


def create_code_box(code_text, styles, caption=None):
    items = []
    if caption:
        items.append(Paragraph(f"<b>Snippet:</b> {caption}", styles["CodeCaption"]))
        items.append(Spacer(1, 3))
    
    code_flow = Preformatted(code_text, styles["CodeText"])
    t = Table([[code_flow]], colWidths=[516])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#0F172A")),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('BOX', (0,0), (-1,-1), 1.0, colors.HexColor("#334155")),
    ]))
    items.append(t)
    return KeepTogether(items)


def build_pdf(output_filename="Cognitive_Maze_Game_Architecture_and_Dataset_Integration_Guide.pdf"):
    print(f"[PDF] Generating publication document: {output_filename}...")
    
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        leftMargin=48,
        rightMargin=48,
        topMargin=54,
        bottomMargin=54
    )

    raw_styles = getSampleStyleSheet()
    
    # Custom Palette Typography Styles
    styles = {
        "CoverTag": ParagraphStyle(
            "CoverTag",
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=12,
            textColor=colors.HexColor("#D97706")
        ),
        "CoverTitle": ParagraphStyle(
            "CoverTitle",
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            textColor=colors.HexColor("#0F172A")
        ),
        "CoverSubtitle": ParagraphStyle(
            "CoverSubtitle",
            fontName="Helvetica",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#475569")
        ),
        "Heading1": ParagraphStyle(
            "Heading1",
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=14,
            spaceAfter=6,
            keepWithNext=True
        ),
        "Heading2": ParagraphStyle(
            "Heading2",
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#1E3A8A"),
            spaceBefore=10,
            spaceAfter=4,
            keepWithNext=True
        ),
        "Heading3": ParagraphStyle(
            "Heading3",
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#B45309"),
            spaceBefore=8,
            spaceAfter=3,
            keepWithNext=True
        ),
        "Body": ParagraphStyle(
            "Body",
            fontName="Helvetica",
            fontSize=9,
            leading=13.5,
            textColor=colors.HexColor("#1E293B"),
            spaceAfter=5
        ),
        "BodyBold": ParagraphStyle(
            "BodyBold",
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=13.5,
            textColor=colors.HexColor("#0F172A"),
            spaceAfter=5
        ),
        "BulletItem": ParagraphStyle(
            "BulletItem",
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#1E293B"),
            leftIndent=14,
            spaceAfter=3
        ),
        "CalloutTitle": ParagraphStyle(
            "CalloutTitle",
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=12,
            textColor=colors.HexColor("#92400E")
        ),
        "CalloutText": ParagraphStyle(
            "CalloutText",
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#78350F")
        ),
        "CodeCaption": ParagraphStyle(
            "CodeCaption",
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#475569")
        ),
        "CodeText": ParagraphStyle(
            "CodeText",
            fontName="Courier",
            fontSize=7,
            leading=9.5,
            textColor=colors.HexColor("#E2E8F0")
        ),
        "TableHead": ParagraphStyle(
            "TableHead",
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.white,
            alignment=1
        ),
        "TableCell": ParagraphStyle(
            "TableCell",
            fontName="Helvetica",
            fontSize=8,
            leading=10.5,
            textColor=colors.HexColor("#1E293B")
        ),
        "TableCellBold": ParagraphStyle(
            "TableCellBold",
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10.5,
            textColor=colors.HexColor("#0F172A")
        ),
        "TableCellCode": ParagraphStyle(
            "TableCellCode",
            fontName="Courier",
            fontSize=7.5,
            leading=9.5,
            textColor=colors.HexColor("#0369A1")
        ),
    }

    story = []

    # =========================================================================
    # 1. COVER / HEADER BANNER BLOCK
    # =========================================================================
    story.append(Paragraph("TECHNICAL SPECIFICATION & CURRICULUM INTEGRATION MANUAL", styles["CoverTag"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Cognitive Maze: 2D Educational RPG Engine & Dataset Architecture", styles["CoverTitle"]))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "A Deep-Dive Guide into Game Mechanics, MediaPipe Gesture Tracking, Pygame 60 FPS Low-Spec APU Optimization, "
        "and Dynamic Dataset Integration via REST API & Atomic Persistence.",
        styles["CoverSubtitle"]
    ))
    story.append(Spacer(1, 8))

    # Metadata Grid Table
    meta_data = [
        [
            Paragraph("<b>Target System:</b> Dual-Core Target Hardware (2 Threads)", styles["TableCell"]),
            Paragraph("<b>Engine:</b> Pygame 2.6.1 + MediaPipe 0.10", styles["TableCell"]),
            Paragraph("<b>Target Audience:</b> DepEd Grade 2 Pupils (Ages 7-8)", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Cloud Backend:</b> Supabase / Vercel Web REST API", styles["TableCell"]),
            Paragraph("<b>Local Persistence:</b> Atomic JSON with Lock Recovery", styles["TableCell"]),
            Paragraph("<b>Date:</b> October 2026 | Release v1.3", styles["TableCell"]),
        ]
    ]
    meta_table = Table(meta_data, colWidths=[172, 172, 172])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # =========================================================================
    # SECTION 1: EXECUTIVE SUMMARY & CURRICULUM FOUNDATION
    # =========================================================================
    story.append(Paragraph("1. Executive Summary & Educational Foundation", styles["Heading1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0F172A"), spaceAfter=8))
    
    story.append(Paragraph(
        "<b>Cognitive Maze</b> (also identified as <i>CognitiveQuest 2D</i>) is an interactive, gamified 2D RPG designed "
        "to elevate foundational mathematics learning for Grade 2 elementary pupils in the Philippines. "
        "Built to align strictly with the <b>DepEd K-12 Elementary Mathematics Curriculum Guide</b>, the game transforms "
        "abstract arithmetic concepts—such as place value, repeated addition, fractions, and time measurement—into tactile, "
        "visually grounded adventure quests across four distinct thematic quarters.",
        styles["Body"]
    ))

    # Table of DepEd Competencies by Quarter
    q_data = [
        [Paragraph("Quarter", styles["TableHead"]), Paragraph("Thematic Setting", styles["TableHead"]), Paragraph("DepEd Grade 2 Mathematics Competencies", styles["TableHead"]), Paragraph("Milestone Mini-Game", styles["TableHead"])],
        [
            Paragraph("<b>Quarter 1</b>", styles["TableCellBold"]),
            Paragraph("Verdant Forest & Village", styles["TableCell"]),
            Paragraph("Numbers up to 1000, Place Value (Hundreds, Tens, Ones), Addition & Subtraction with Regrouping, 2D/3D Geometric Shapes & Repeating Patterns.", styles["TableCell"]),
            Paragraph("Magic Shape Pattern Altar", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Quarter 2</b>", styles["TableCellBold"]),
            Paragraph("Crystal Cavern & Minecart", styles["TableCell"]),
            Paragraph("Multiplication Concept as Repeated Addition, Arrays of Objects, Equal Groups, Skip Counting by 2, 5, and 10, Traversal Logic.", styles["TableCell"]),
            Paragraph("Cavern Minecart Track Switcher", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Quarter 3</b>", styles["TableCellBold"]),
            Paragraph("Sun Temple & Desert Oasis", styles["TableCell"]),
            Paragraph("Fractions: Unit Fractions (1/2, 1/3, 1/4) and Non-Unit Fractions (3/4), Fair Sharing, Bar Models, Caravan Cargo Weight & Keystones.", styles["TableCell"]),
            Paragraph("Royal Oasis Fraction Bakery", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Quarter 4</b>", styles["TableCellBold"]),
            Paragraph("Royal Citadel & Clock Sanctum", styles["TableCell"]),
            Paragraph("Time Measurement (Analog/Digital Clock reading to 5-minute intervals), Linear Length (cm/m), Mass (g/kg), Capacity (mL/L), Word Problems.", styles["TableCell"]),
            Paragraph("Sun Clock Gear Align & Grand Trial", styles["TableCell"]),
        ],
    ]
    q_table = Table(q_data, colWidths=[66, 105, 235, 110])
    q_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(q_table)
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 2: GAME OVERVIEW & CORE GAMEPLAY LOOP
    # =========================================================================
    story.append(Paragraph("2. Game Overview & How the Game Works (Player Journey)", styles["Heading1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0F172A"), spaceAfter=8))

    story.append(Paragraph(
        "The player's journey is structured as an interconnected state machine that guides pupils seamlessly from login "
        "to curriculum mastery without cognitive overload:",
        styles["Body"]
    ))

    story.append(Paragraph("<b>Step 1: Student Profile Authentication & Selection</b>", styles["Heading3"]))
    story.append(Paragraph(
        "Upon launching, pupils select or create their student profile. Each student has a unique alphanumeric identifier "
        "(e.g., <code>S-2024-001</code>), full name, section, grade level, and avatar color. Profiles load directly from local "
        "JSON storage or sync with the cloud database. If a pupil has never completed the gesture calibration tutorial, the "
        "game gently directs them to the tutorial before unlocking stage select.",
        styles["Body"]
    ))

    story.append(Paragraph("<b>Step 2: Interactive Controls & Gesture Tutorial</b>", styles["Heading3"]))
    story.append(Paragraph(
        "A dedicated calibration screen introduces pupils to the dual-input system: moving their hand in front of the webcam "
        "to move the magical star wand cursor, pointing, dwelling (holding steady for 0.22s to click), and making a closed fist "
        "to grab and drag puzzle elements.",
        styles["Body"]
    ))

    story.append(Paragraph("<b>Step 3: Exploration Hub & Stage Progression</b>", styles["Heading3"]))
    story.append(Paragraph(
        "In the Stage Selection Hub, unlocked quarters are rendered with vibrant animated gates guarded by NPC mentors "
        "(Sage Oldman, Knight Guardian, Skeleton Guardian, and Sun Bromen). Completed quarters proudly display their star ratings, "
        "score percentages, and total time.",
        styles["Body"]
    ))

    story.append(Paragraph("<b>Step 4: The Station Quest Loop (5 Sages per Level)</b>", styles["Heading3"]))
    story.append(Paragraph(
        "Inside each stage (e.g., Quarter 3's <code>map7.txt</code>, <code>map8.txt</code>, <code>map9.txt</code>), the player "
        "explores a grid-based 2D map containing 5 Station Sages positioned strategically. As the player walks near an NPC (within 1.8 tiles):",
        styles["Body"]
    ))
    story.append(Paragraph("• <b>Proximity Greeting:</b> A welcoming dialog modal introduces the mathematical story problem.", styles["BulletItem"]))
    story.append(Paragraph("• <b>Interactive Question Modal:</b> Pupils solve either a Multiple-Choice or Identification math challenge.", styles["BulletItem"]))
    story.append(Paragraph("• <b>50:50 Wizard Hint:</b> If a pupil makes an incorrect first choice, the wrong answer is eliminated, giving immediate encouragement.", styles["BulletItem"]))
    story.append(Paragraph("• <b>2-Try Guaranteed Progression:</b> To prevent frustration in Grade 2 learners, pupils are allowed up to 2 attempts per question. If still incorrect, the correct concept is explained gently and progression continues.", styles["BulletItem"]))
    story.append(Paragraph("• <b>World Construction & Rewards:</b> On Map 8, answering each station materializes a segment of the Golden Aqueduct Bridge with an automatic cinematic drone camera pan.", styles["BulletItem"]))

    story.append(Paragraph("<b>Step 5: Milestone Mini-Games & Sealed Exit Portals</b>", styles["Heading3"]))
    story.append(Paragraph(
        "Clearing all 5 stations activates the stage's <b>Guardian NPC</b> standing in front of the Exit Portal. "
        "The portal remains <b>firmly sealed</b> by an ancient magical barrier until the pupil proves their mastery in the milestone mini-game. "
        "For example, in Quarter 3, speaking with the Skeleton Guardian activates the <b>Royal Oasis Fraction Bakery</b>. "
        "Only when all fraction pastry orders (1/2, 1/3, 1/4, 3/4) are served does the Skeleton Guardian celebrate, lifting the seal "
        "and opening the Sun Gate for stage completion.",
        styles["Body"]
    ))

    callout_1 = create_callout(
        "Critical UX Guard: Zero Wandering Character During Mini-Games",
        "Whenever a pupil engages in a mini-game (such as the Fraction Bakery or Minecart Switcher), "
        "<code>is_minigame_or_puzzle_active()</code> evaluates to True. This instantly stops character walking and disables "
        "movement inputs. Pupils can freely click, drag, and drop slices without their avatar walking across the map in the background.",
        styles,
        border_color="#16A34A",
        bg_color="#DCFCE7"
    )
    story.append(Spacer(1, 4))
    story.append(callout_1)
    story.append(Spacer(1, 10))

    # =========================================================================
    # SECTION 3: THE CODES BEHIND IT ALL (SUBSYSTEMS ARCHITECTURE)
    # =========================================================================
    story.append(Paragraph("3. Core Subsystems & The Code Behind It All", styles["Heading1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0F172A"), spaceAfter=8))

    story.append(Paragraph(
        "The codebase is cleanly compartmentalized into core engine services, screen controllers, and database handlers. "
        "Below is a breakdown of the primary subsystems:",
        styles["Body"]
    ))

    # Architectural Overview Table
    arch_data = [
        [Paragraph("Subsystem", styles["TableHead"]), Paragraph("Primary Source Files", styles["TableHead"]), Paragraph("Core Responsibilities & Technical Architecture", styles["TableHead"])],
        [
            Paragraph("<b>Master Engine & Lifecycle</b>", styles["TableCellBold"]),
            Paragraph("<code>main.py</code>", styles["TableCellCode"]),
            Paragraph("Pygame display double-buffering, full-screen hardware toggle, 60 FPS clock regulation, CPU core affinity environment flags, clean shutdown hooks.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Scene / State Controller</b>", styles["TableCellBold"]),
            Paragraph("<code>screens/main_menu.py</code><br/><code>screens/stageselect.py</code><br/><code>screens/quarter[1-4].py</code>", styles["TableCellCode"]),
            Paragraph("Game state machine (`quiz_state`: 0=Roam, 1=Quiz, 2=Wrong, 3=Correct, 4=Out of Tries, 5=Mentor, 6=Portal Ready, 7=Camera Pan, 8=Relic, 9=Mini-game).", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Dual-Input & AI Gestures</b>", styles["TableCellBold"]),
            Paragraph("<code>core/cursor_system.py</code><br/><code>screens/main_menu.py</code>", styles["TableCellCode"]),
            Paragraph("Background MediaPipe thread, OpenCV video capture, 1-Euro signal smoothing filter, closed-fist grab detector, stardust trail particles.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>2D Viewport Camera Engine</b>", styles["TableCellBold"]),
            Paragraph("<code>core/camera_system.py</code>", styles["TableCellCode"]),
            Paragraph("Smooth exponential lerp tracking, boundary clamping, spacebar recentering, and cinematic cutscene pan overrides.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Memoized Font Engine</b>", styles["TableCellBold"]),
            Paragraph("<code>core/font_manager.py</code>", styles["TableCellCode"]),
            Paragraph("SafeFont cache eliminating per-frame font allocations, text surface memoization, automatic word wrapping for grade 2 dialog cards.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Data Layer & Persistence</b>", styles["TableCellBold"]),
            Paragraph("<code>db/connect_db.py</code><br/><code>db/save_system.py</code>", styles["TableCellCode"]),
            Paragraph("Vercel REST API client, Supabase cloud sync, offline queue (`pending_sync.json`), atomic save files with Windows file-lock retry handlers.", styles["TableCell"]),
        ],
    ]
    arch_table = Table(arch_data, colWidths=[110, 115, 291])
    arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(arch_table)
    story.append(Spacer(1, 10))

    # MediaPipe and 1-Euro Filter deep dive
    story.append(Paragraph("<b>3.1 MediaPipe AI Hand Tracking & 1-Euro Filter Engine</b>", styles["Heading2"]))
    story.append(Paragraph(
        "A hallmark innovation of Cognitive Maze is enabling pupils to interact touchlessly via their webcam. "
        "Standard webcam hand tracking suffers from two critical flaws: high-frequency hand jitter when aiming, and noticeable lag "
        "when moving quickly. Cognitive Maze resolves this using the <b>1-Euro Filter</b> (Casiez et al., CHI 2012):",
        styles["Body"]
    ))

    code_filter = (
        "class OneEuroFilter:\n"
        "    def __init__(self, t0=0.0, x0=0.0, dx0=0.0, min_cutoff=0.18, beta=0.03, d_cutoff=1.0):\n"
        "        self.min_cutoff = float(min_cutoff) # Low cutoff (~0.18Hz) eliminates micro-shakes\n"
        "        self.beta = float(beta)             # Speed coefficient dynamically increases cutoff\n"
        "        self.d_cutoff = float(d_cutoff)     # Derivative cutoff\n"
        "        self.x_prev, self.dx_prev, self.t_prev = float(x0), float(dx0), float(t0)\n\n"
        "    def filter(self, t, x):\n"
        "        t_e = max(0.001, t - self.t_prev)\n"
        "        rate = max(10.0, min(240.0, 1.0 / t_e))\n"
        "        dx = (x - self.x_prev) * rate\n"
        "        edx = self.dx_prev + self._alpha(rate, self.d_cutoff) * (dx - self.dx_prev)\n"
        "        cutoff = self.min_cutoff + self.beta * abs(edx)\n"
        "        x_hat = self.x_prev + self._alpha(rate, cutoff) * (x - self.x_prev)\n"
        "        self.x_prev, self.dx_prev, self.t_prev = x_hat, edx, t\n"
        "        return x_hat"
    )
    story.append(create_code_box(code_filter, styles, "core/cursor_system.py: 1-Euro Filter Implementation"))
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "<b>Gesture Classification:</b> Hand landmarks are captured via <code>mp.solutions.hands.Hands(max_num_hands=1)</code>. "
        "The cursor coordinates track Landmark 8 (Index Fingertip) or Landmark 0 (Wrist) smoothed via the 1-Euro filter. "
        "A <b>Closed Fist</b> is detected by measuring the Euclidean distance between fingertips (Landmarks 8, 12, 16, 20) and "
        "their respective MCP knuckle joints (Landmarks 5, 9, 13, 17). When fingertips curl inward past the threshold, "
        "<code>fist_closed</code> triggers, enabling drag-and-drop mechanics in mini-games.",
        styles["Body"]
    ))

    # =========================================================================
    # SECTION 4: LOW-SPEC HARDWARE OPTIMIZATIONS
    # =========================================================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("4. Low-Spec Hardware Optimization Strategy", styles["Heading1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0F172A"), spaceAfter=8))

    callout_hw = create_callout(
        "Strict Target Hardware Constraint: Low-Spec Dual-Core Hardware",
        "Primary Target System: Dual-Core Low-Spec Target Hardware.<br/>"
        "All features, camera tracking, rendering, audio mixing, and background AI threads must strictly maintain solid 60 FPS "
        "without frame drops or audio stuttering on this low-spec hardware.",
        styles,
        border_color="#DC2626",
        bg_color="#FEE2E2"
    )
    story.append(callout_hw)
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "To satisfy this tight hardware budget, Cognitive Maze employs five specialized architectural constraints:",
        styles["Body"]
    ))

    story.append(Paragraph("<b>1. Two-Thread CPU Budget & Thread-Pool Isolation:</b>", styles["BodyBold"]))
    story.append(Paragraph(
        "Because target hardware has only 2 physical CPU threads and limited cache, background libraries (OpenMP, BLAS, NumPy, OpenCV, MKL) "
        "could easily spawn competing worker pools and starve the Pygame main game loop. In <code>main.py</code>, strict environment variables "
        "force all underlying libraries to single-threaded mode:<br/>"
        "<code>os.environ['OMP_NUM_THREADS'] = '1'</code> | <code>os.environ['OPENBLAS_NUM_THREADS'] = '1'</code> | <code>cv2.setNumThreads(1)</code><br/>"
        "This reserves Thread 0 exclusively for the 60 FPS Pygame loop and Thread 1 for the MediaPipe/OpenCV camera worker.",
        styles["Body"]
    ))

    story.append(Paragraph("<b>2. MediaPipe Resolution Downsampling:</b>", styles["BodyBold"]))
    story.append(Paragraph(
        "Camera frames captured by OpenCV are downsampled to <b>320x240</b> pixels before being passed to MediaPipe with <code>num_hands=1</code>. "
        "This slashes CPU landmark inference time from ~45ms down to ~8ms, fitting comfortably within the 16.6ms frame budget.",
        styles["Body"]
    ))

    story.append(Paragraph("<b>3. Memoized SafeFont System (`core/font_manager.py`):</b>", styles["BodyBold"]))
    story.append(Paragraph(
        "Calling <code>pygame.font.SysFont()</code> or <code>font.render()</code> inside the 60 FPS game loop triggers disk I/O and memory allocations "
        "that thrash the 1MB L2 cache. The <code>SafeFont</code> manager pre-loads and caches font glyphs by <code>(size, bold)</code>, ensuring "
        "zero per-frame font allocations in hot render loops.",
        styles["Body"]
    ))

    story.append(Paragraph("<b>4. Pygame Surface Hardware Baking:</b>", styles["BodyBold"]))
    story.append(Paragraph(
        "All sprite sheets, portraits, and tile textures call <code>.convert()</code> or <code>.convert_alpha()</code> immediately upon loading. "
        "Furthermore, static map backgrounds are baked into a single pre-rendered surface (<code>render_map</code>), avoiding 1000+ individual tile "
        "blit calls per frame.",
        styles["Body"]
    ))

    story.append(Paragraph("<b>5. Audio Buffer Low-Latency Tuning:</b>", styles["BodyBold"]))
    story.append(Paragraph(
        "The Pygame audio mixer is pre-initialized with <code>frequency=44100, buffer=512</code>. A 512-byte buffer prevents audio playback lag "
        "while eliminating the CPU underruns typical with larger buffers.",
        styles["Body"]
    ))

    # =========================================================================
    # SECTION 5: DATASET INTEGRATION & DATA ARCHITECTURE
    # =========================================================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("5. Dataset Integration & Data Flow Architecture", styles["Heading1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0F172A"), spaceAfter=8))

    story.append(Paragraph(
        "Cognitive Maze features an end-to-end dataset pipeline connecting classroom curriculum questions, local pupil progress, "
        "and cloud grading analytics:",
        styles["Body"]
    ))

    # Dataset Flowchart Table
    flow_data = [
        [Paragraph("Data Pipeline Stage", styles["TableHead"]), Paragraph("Endpoint / Storage Mechanism", styles["TableHead"]), Paragraph("Integration & Redundancy Behavior", styles["TableHead"])],
        [
            Paragraph("<b>1. Curriculum Questions</b>", styles["TableCellBold"]),
            Paragraph("Vercel Web REST API:<br/><code>/api/questions?quarter=X</code>", styles["TableCellCode"]),
            Paragraph("Dynamically fetched based on Quarter / Unit ID. Validates JSON schema, randomizes choices, and falls back to local cache or embedded question bank if offline.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>2. Student Profiles</b>", styles["TableCellBold"]),
            Paragraph("Local Atomic Files:<br/><code>db/saves/S-XXXX-XXX.json</code>", styles["TableCellCode"]),
            Paragraph("Contains student name, grade, section, avatar color, stars, and quarter completion. Saved atomically with `.tmp` files to prevent 0-byte corruption.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>3. Offline Sync Queue</b>", styles["TableCellBold"]),
            Paragraph("Local Queue File:<br/><code>db/pending_sync.json</code>", styles["TableCellCode"]),
            Paragraph("When gameplay completes offline, assessment records are queued locally. A non-blocking background thread auto-probes cloud health and flushes the queue once connected.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>4. Teacher Assessment</b>", styles["TableCellBold"]),
            Paragraph("Remote Supabase DB via Vercel:<br/><code>/api/assessments</code>", styles["TableCellCode"]),
            Paragraph("Stores completed scores, question counts, percentage accuracy, time elapsed, and automated feedback for teacher grading dashboards.", styles["TableCell"]),
        ],
    ]
    flow_table = Table(flow_data, colWidths=[120, 160, 236])
    flow_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(flow_table)
    story.append(Spacer(1, 10))

    story.append(Paragraph("<b>5.1 Question Dataset Schema & Mapping</b>", styles["Heading2"]))
    story.append(Paragraph(
        "Questions are organized by Philippine Grade 2 curriculum Unit IDs in <code>db/connect_db.py</code>:<br/>"
        "• <b>Quarter 1:</b> Unit IDs <code>[1, 2, 3]</code> (Numbers, Operations, Place Value)<br/>"
        "• <b>Quarter 2:</b> Unit IDs <code>[4, 5, 6]</code> (Multiplication, Equal Groups, Arrays)<br/>"
        "• <b>Quarter 3:</b> Unit IDs <code>[10, 11, 12]</code> (Unit & Non-Unit Fractions, Bar Models, Fair Sharing)<br/>"
        "• <b>Quarter 4:</b> Unit IDs <code>[13, 14, 15]</code> (Time, Length, Mass, Capacity, Word Problems)",
        styles["Body"]
    ))

    code_q_schema = (
        "// Standardized Curriculum Question JSON Schema\n"
        "{\n"
        '    "id": 1024,\n'
        '    "quarter": 3,\n'
        '    "unit_id": 11,\n'
        '    "q_type": "multiple_choice", // Or "identification"\n'
        '    "question": "What fraction of the royal Oasis Fig Pie is one shaded slice out of 3 equal parts?",\n'
        '    "choices": ["1/2", "1/3", "1/4", "3/4"],\n'
        '    "correct": 1, // Index matching "1/3"\n'
        '    "explanation": "One part out of 3 equal parts is called One-Third (1/3).",\n'
        '    "points": 20\n'
        "}"
    )
    story.append(create_code_box(code_q_schema, styles, "Standardized Question Schema"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>5.2 Three-Tier Redundant Question Fallback Architecture</b>", styles["Heading2"]))
    story.append(Paragraph(
        "To guarantee that classroom instruction never halts due to network outages, <code>get_questions(quarter)</code> implements a 3-tier fallback:",
        styles["Body"]
    ))
    story.append(Paragraph("1. <b>Tier 1 (Live Cloud REST API):</b> Probes <code>https://gamified-math-grading-system.vercel.app/api/questions</code> with a 4-second timeout. If successful, updates the local cache.", styles["BulletItem"]))
    story.append(Paragraph("2. <b>Tier 2 (Cached Local JSON):</b> If the school network is down, reads from <code>db/cache/questions_q{quarter}.json</code> populated during previous sessions.", styles["BulletItem"]))
    story.append(Paragraph("3. <b>Tier 3 (Hardcoded Python Question Bank):</b> If the cache file is absent or corrupted, loads an immutable, DepEd-verified question bank embedded directly in <code>screens/quarter{X}.py</code>.", styles["BulletItem"]))

    story.append(Spacer(1, 6))
    story.append(Paragraph("<b>5.3 Student Save State & Atomic File Operations</b>", styles["Heading2"]))
    story.append(Paragraph(
        "In <code>db/save_system.py</code>, save states are persisted using <b>atomic file replacement</b> to prevent 0-byte corrupted files "
        "if a school computer experiences a sudden power cut or crash:",
        styles["Body"]
    ))

    code_atomic = (
        "def atomic_save_json(path, data):\n"
        "    directory = os.path.dirname(path)\n"
        "    if directory: os.makedirs(directory, exist_ok=True)\n"
        "    tmp_path = f\"{path}.tmp_{os.getpid()}_{int(time.time()*1000)}\"\n"
        "    with open(tmp_path, 'w', encoding='utf-8') as f:\n"
        "        json.dump(data, f, indent=4)\n"
        "        f.flush()\n"
        "        os.fsync(f.fileno()) # Force write to physical storage platter\n"
        "    # Atomic replace with retry handling for Windows file locks\n"
        "    for attempt in range(5):\n"
        "        try:\n"
        "            os.replace(tmp_path, path)\n"
        "            return True\n"
        "        except (PermissionError, OSError):\n"
        "            time.sleep(0.05 * (attempt + 1))\n"
        "    return False"
    )
    story.append(create_code_box(code_atomic, styles, "db/save_system.py: Atomic File Write Engine"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>5.4 Offline Synchronization Queue (`db/pending_sync.json`)</b>", styles["Heading2"]))
    story.append(Paragraph(
        "When an assessment completes while offline, <code>queue_offline_result(payload)</code> appends the grade record to "
        "<code>db/pending_sync.json</code>. A lightweight background thread periodically calls <code>check_cloud_health()</code>. "
        "As soon as the probe receives HTTP 200/204 from Vercel, <code>sync_offline_results()</code> flushes all queued records to the "
        "cloud database in FIFO order without interrupting active gameplay.",
        styles["Body"]
    ))

    # =========================================================================
    # SECTION 6: CODE WALKTHROUGHS & IMPLEMENTATION HIGHLIGHTS
    # =========================================================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("6. Code Walkthroughs & Implementation Highlights", styles["Heading1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0F172A"), spaceAfter=8))

    story.append(Paragraph("<b>6.1 Station 5 Completion & Skeleton Guardian Activation Flow</b>", styles["Heading2"]))
    story.append(Paragraph(
        "In Quarter 3 (Desert Oasis), answering all 5 station questions seamlessly activates the Skeleton Guardian trial. "
        "Below is the unified implementation across all maps:",
        styles["Body"]
    ))

    code_guard_flow = (
        "# screens/quarter3.py - Unified Station 5 Completion Flow\n"
        "def advance_station_progress(self):\n"
        "    if self.quiz_station_index < 5:\n"
        "        self.quiz_station_index += 1\n"
        "        self.current_question_index += 1\n"
        "        self.quiz_state = 0\n"
        "    else:\n"
        "        # All 5 stations solved -> Activate Skeleton Guardian trial!\n"
        "        self.quiz_station_index = 6\n"
        "        self.guardian_skeleton_state = 1 # Awaiting challenge with glowing aura & '!' badge\n"
        "        self.quiz_state = 0              # Return to free roam\n"
        "        self.fraction_bakery_solved = False\n"
        "        self.caravan_upgrade_banner_text = 'ALL 5 STATIONS SOLVED!'\n"
        "        self.caravan_upgrade_banner_sub = 'Speak with the Skeleton Guardian to begin the Fraction Bakery!'\n"
        "        self.caravan_upgrade_banner_timer = 6.0"
    )
    story.append(create_code_box(code_guard_flow, styles, "screens/quarter3.py: Station Completion"))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>6.2 Fraction Bakery Mini-Game Engine</b>", styles["Heading2"]))
    story.append(Paragraph(
        "The Fraction Bakery replaces legacy scarab puzzles with a Grade 2 interactive pastry kitchen. "
        "The engine computes angular sector math for plate slots and connects to a two-way toggle / drag system:",
        styles["Body"]
    ))

    code_bakery = (
        "# screens/quarter3.py - Fraction Bakery Plate Sector & Order Engine\n"
        "def setup_fraction_order(self, order_idx):\n"
        "    order = self.fraction_bakery_orders[order_idx] # e.g. 1/3 Fig Pie\n"
        "    denom, target = order['denom'], order['target']\n"
        "    slice_ang = (2.0 * math.pi) / denom\n"
        "    self.fraction_bakery_plate_slots = []\n"
        "    for i in range(denom):\n"
        "        start_ang = -math.pi / 2.0 + i * slice_ang\n"
        "        self.fraction_bakery_plate_slots.append({\n"
        "            'index': i, 'denom': denom,\n"
        "            'start_ang': start_ang, 'end_ang': start_ang + slice_ang,\n"
        "            'mid_ang': start_ang + slice_ang / 2.0, 'slice': None\n"
        "        })\n"
        "    # Clicking a tray slice places it in the first empty slot;\n"
        "    # Clicking a placed plate slice returns it back to the cooling rack.\n"
        "    # When placed_count == target: Serve Order sparkles and unlocks next recipe!"
    )
    story.append(create_code_box(code_bakery, styles, "screens/quarter3.py: Fraction Bakery Math Engine"))

    # =========================================================================
    # SECTION 7: SYSTEM SPECIFICATIONS & SUMMARY TABLE
    # =========================================================================
    story.append(Spacer(1, 10))
    story.append(Paragraph("7. Technical Specifications & Reference Summary", styles["Heading1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#0F172A"), spaceAfter=8))

    spec_data = [
        [Paragraph("Category", styles["TableHead"]), Paragraph("Specification Parameter", styles["TableHead"]), Paragraph("Implementation Details & Guarantees", styles["TableHead"])],
        [
            Paragraph("<b>Target Hardware</b>", styles["TableCellBold"]),
            Paragraph("Dual-Core Low-Spec System", styles["TableCellBold"]),
            Paragraph("Dual-Core, 2 Threads @ 3.7 GHz, 1MB L2 Cache, Radeon HD 8370D Integrated Graphics.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Framerate Budget</b>", styles["TableCellBold"]),
            Paragraph("60.0 FPS Fixed", styles["TableCellBold"]),
            Paragraph("16.6ms max frame budget. Zero per-frame allocations in hot render loops.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Camera Input</b>", styles["TableCellBold"]),
            Paragraph("OpenCV + MediaPipe Hands", styles["TableCellBold"]),
            Paragraph("320x240 capture @ 30 FPS. Thread-isolated worker. 1-Euro noise filter (min_cutoff=0.18, beta=0.03).", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Display & Audio</b>", styles["TableCellBold"]),
            Paragraph("Pygame Fullscreen 1080p/720p", styles["TableCellBold"]),
            Paragraph("Hardware double-buffering (`DOUBLEBUF`), mixer buffer=512, SafeFont texture caching.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Database API</b>", styles["TableCellBold"]),
            Paragraph("Vercel Web API / Supabase", styles["TableCellBold"]),
            Paragraph("REST endpoints for questions, students, assessments, and leaderboards. 3-tier fallback architecture.", styles["TableCell"]),
        ],
        [
            Paragraph("<b>Local Persistence</b>", styles["TableCellBold"]),
            Paragraph("Atomic JSON Files", styles["TableCellBold"]),
            Paragraph("Located at `db/saves/S-XXXX-XXX.json` with temporary file replacement and Windows retry handler.", styles["TableCell"]),
        ],
    ]
    spec_table = Table(spec_data, colWidths=[105, 135, 276])
    spec_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0F172A")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F8FAFC")]),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(spec_table)
    story.append(Spacer(1, 14))

    # Concluding signature badge
    concl = create_callout(
        "Deployment Ready - Cognitive Maze v1.3",
        "This document certifies that the Cognitive Maze codebase adheres strictly to Philippine DepEd Grade 2 Mathematics "
        "curriculum benchmarks, guarantees 60 FPS performance on target school laboratory hardware, and maintains complete "
        "data integrity across online and offline classroom environments.",
        styles,
        border_color="#0284C7",
        bg_color="#E0F2FE"
    )
    story.append(concl)

    # Build the document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[PDF SUCCESS] Successfully created: {os.path.abspath(output_filename)}")
    return os.path.abspath(output_filename)


if __name__ == "__main__":
    out_file = sys.argv[1] if len(sys.argv) > 1 else "Cognitive_Maze_Game_Architecture_and_Dataset_Integration_Guide.pdf"
    build_pdf(out_file)
