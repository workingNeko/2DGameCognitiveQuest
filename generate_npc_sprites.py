import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def generate_number_character_frame(number, frame_idx, total_frames=8, out_size=64):
    scale = 4
    canvas_size = out_size * scale  # 256x256
    
    palettes = {
        1: {
            "name": "Number 1 Guardian",
            "main": (255, 71, 87),        # Strawberry Coral Red
            "light": (255, 150, 160),     # Highlight
            "dark": (190, 30, 48),        # Shadow
            "outline": (40, 10, 18),      # Crisp dark border
            "shoe": (220, 40, 60),        # Matching shoes
            "blush": (255, 110, 145, 195),
            "font_size": 195,
            "y_offset": 5,
            "eye_offset_y": -12,
            "eye_spacing": 22,
        },
        2: {
            "name": "Number 2 Guardian",
            "main": (255, 159, 26),       # Warm Amber Orange
            "light": (255, 215, 95),      # Highlight
            "dark": (205, 105, 0),        # Shadow
            "outline": (45, 22, 5),       # Crisp dark border
            "shoe": (225, 115, 0),
            "blush": (255, 125, 80, 195),
            "font_size": 190,
            "y_offset": -2,
            "eye_offset_y": -26,
            "eye_spacing": 20,
        },
        3: {
            "name": "Number 3 Guardian",
            "main": (46, 213, 115),       # Emerald Green
            "light": (135, 245, 180),     # Highlight
            "dark": (20, 155, 75),        # Shadow
            "outline": (8, 42, 18),       # Crisp dark border
            "shoe": (25, 160, 75),
            "blush": (255, 140, 160, 195),
            "font_size": 190,
            "y_offset": -2,
            "eye_offset_y": -28,
            "eye_spacing": 19,
        },
        4: {
            "name": "Number 4 Guardian",
            "main": (30, 144, 255),       # Azure Blue
            "light": (130, 200, 255),     # Highlight
            "dark": (10, 95, 200),        # Shadow
            "outline": (6, 28, 55),       # Crisp dark border
            "shoe": (15, 105, 210),
            "blush": (255, 135, 175, 195),
            "font_size": 185,
            "y_offset": 5,
            "eye_offset_y": -12,
            "eye_spacing": 20,
        },
        5: {
            "name": "Number 5 Guardian",
            "main": (168, 85, 247),       # Royal Violet
            "light": (220, 165, 255),     # Highlight
            "dark": (125, 45, 195),       # Shadow
            "outline": (35, 10, 60),      # Crisp dark border
            "shoe": (135, 45, 205),
            "blush": (255, 130, 185, 195),
            "font_size": 190,
            "y_offset": -2,
            "eye_offset_y": -26,
            "eye_spacing": 20,
        }
    }
    
    pal = palettes[number]
    
    # 8-Frame Animation Loop
    t = (frame_idx / total_frames) * 2 * math.pi
    bounce_y = -math.sin(t) * 9   # Bobbing up and down
    squash_x = 1.0 + (0.035 * math.sin(t))
    squash_y = 1.0 - (0.035 * math.sin(t))
    arm_sway = math.sin(t) * 16
    is_blinking = (frame_idx == 4)
    
    img = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    cx = canvas_size // 2
    cy = 126 + int(bounce_y) + pal["y_offset"]
    
    # 1. Ground Drop Shadow
    shadow_w = int(120 * squash_x)
    shadow_h = 24
    shadow_y = 224
    draw.ellipse([cx - shadow_w//2, shadow_y - shadow_h//2, cx + shadow_w//2, shadow_y + shadow_h//2], fill=(0, 0, 0, 75))
    
    # 2. Render Font Glyph (Cooper Black)
    font_path = "C:/Windows/Fonts/COOPBL.TTF"
    if not os.path.exists(font_path):
        font_path = "C:/Windows/Fonts/ariblk.ttf"
    
    font = ImageFont.truetype(font_path, pal["font_size"])
    text = str(number)
    
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    
    glyph_surf = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glyph_surf)
    
    gx = cx - (bbox[0] + bbox[2]) // 2
    gy = cy - (bbox[1] + bbox[3]) // 2
    
    gdraw.text((gx, gy), text, font=font, fill=pal["main"])
    glyph_alpha = glyph_surf.split()[3]
    
    # Find exact contour edges of the glyph at arm height
    arm_target_y = cy + 5
    alpha_np = np.array(glyph_alpha)
    
    safe_arm_y = max(10, min(canvas_size - 10, arm_target_y))
    row_pixels = np.where(alpha_np[safe_arm_y, :] > 50)[0]
    
    if len(row_pixels) > 0:
        left_anchor_x = row_pixels[0]
        right_anchor_x = row_pixels[-1]
    else:
        left_anchor_x = cx - tw // 2
        right_anchor_x = cx + tw // 2
        
    feet_row = max(10, min(canvas_size - 10, cy + th // 2 - 5))
    feet_pixels = np.where(alpha_np[feet_row, :] > 50)[0]
    if len(feet_pixels) > 0:
        left_foot_x = max(cx - 45, feet_pixels[0] + 10)
        right_foot_x = min(cx + 45, feet_pixels[-1] - 10)
    else:
        left_foot_x = cx - 30
        right_foot_x = cx + 30

    # 3. Cute Legs & Shoes
    leg_surf = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    ldraw = ImageDraw.Draw(leg_surf)
    
    foot_bounce = int(bounce_y * 0.35)
    foot_y = 206 + foot_bounce
    
    # Left Leg & Shoe
    lf_x = cx - 34
    ldraw.line([(left_foot_x, cy + th//2 - 12), (lf_x, foot_y - 2)], fill=pal["outline"], width=14)
    ldraw.line([(left_foot_x, cy + th//2 - 12), (lf_x, foot_y - 2)], fill=pal["main"], width=8)
    
    ldraw.ellipse([lf_x - 19, foot_y - 12, lf_x + 19, foot_y + 12], fill=pal["outline"])
    ldraw.ellipse([lf_x - 15, foot_y - 9, lf_x + 15, foot_y + 9], fill=pal["shoe"])
    ldraw.ellipse([lf_x - 10, foot_y - 7, lf_x + 6, foot_y + 3], fill=pal["light"])

    # Right Leg & Shoe
    rf_x = cx + 34
    ldraw.line([(right_foot_x, cy + th//2 - 12), (rf_x, foot_y - 2)], fill=pal["outline"], width=14)
    ldraw.line([(right_foot_x, cy + th//2 - 12), (rf_x, foot_y - 2)], fill=pal["main"], width=8)
    
    ldraw.ellipse([rf_x - 19, foot_y - 12, rf_x + 19, foot_y + 12], fill=pal["outline"])
    ldraw.ellipse([rf_x - 15, foot_y - 9, rf_x + 15, foot_y + 9], fill=pal["shoe"])
    ldraw.ellipse([rf_x - 10, foot_y - 7, rf_x + 6, foot_y + 3], fill=pal["light"])

    # 4. Animated Cartoon Arms with White Gloves & Thumbs
    arm_surf = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    adraw = ImageDraw.Draw(arm_surf)
    
    # Left Arm
    la_angle = math.radians(22 - arm_sway)
    la_len = 36
    lh_x = int(left_anchor_x - la_len * math.cos(la_angle))
    lh_y = int(safe_arm_y - la_len * math.sin(la_angle))
    
    adraw.line([(left_anchor_x, safe_arm_y), (lh_x, lh_y)], fill=pal["outline"], width=16)
    adraw.line([(left_anchor_x, safe_arm_y), (lh_x, lh_y)], fill=pal["main"], width=10)
    
    adraw.ellipse([lh_x - 16, lh_y - 16, lh_x + 16, lh_y + 16], fill=pal["outline"])
    adraw.ellipse([lh_x - 13, lh_y - 13, lh_x + 13, lh_y + 13], fill=(210, 220, 235))
    adraw.ellipse([lh_x - 11, lh_y - 11, lh_x + 11, lh_y + 9], fill=(255, 255, 255))
    thumb_lx = lh_x + 7
    thumb_ly = lh_y - 9
    adraw.ellipse([thumb_lx - 6, thumb_ly - 6, thumb_lx + 6, thumb_ly + 6], fill=pal["outline"])
    adraw.ellipse([thumb_lx - 4, thumb_ly - 4, thumb_lx + 4, thumb_ly + 4], fill=(255, 255, 255))

    # Right Arm
    ra_angle = math.radians(22 + arm_sway)
    ra_len = 36
    rh_x = int(right_anchor_x + ra_len * math.cos(ra_angle))
    rh_y = int(safe_arm_y - ra_len * math.sin(ra_angle))
    
    adraw.line([(right_anchor_x, safe_arm_y), (rh_x, rh_y)], fill=pal["outline"], width=16)
    adraw.line([(right_anchor_x, safe_arm_y), (rh_x, rh_y)], fill=pal["main"], width=10)
    
    adraw.ellipse([rh_x - 16, rh_y - 16, rh_x + 16, rh_y + 16], fill=pal["outline"])
    adraw.ellipse([rh_x - 13, rh_y - 13, rh_x + 13, rh_y + 13], fill=(210, 220, 235))
    adraw.ellipse([rh_x - 11, rh_y - 11, rh_x + 11, rh_y + 9], fill=(255, 255, 255))
    thumb_rx = rh_x - 7
    thumb_ry = rh_y - 9
    adraw.ellipse([thumb_rx - 6, thumb_ry - 6, thumb_rx + 6, thumb_ry + 6], fill=pal["outline"])
    adraw.ellipse([thumb_rx - 4, thumb_ry - 4, thumb_rx + 4, thumb_ry + 4], fill=(255, 255, 255))

    # 5. Generate Thick Cartoon Outline for Number Body
    outline_surf = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    outline_radius = 8
    for ox in range(-outline_radius, outline_radius + 1):
        for oy in range(-outline_radius, outline_radius + 1):
            if ox*ox + oy*oy <= outline_radius*outline_radius:
                outline_surf.paste(Image.new("RGBA", (canvas_size, canvas_size), pal["outline"]), (ox, oy), mask=glyph_alpha)
    
    # 6. Shading & 3D Bevel for Body
    light_surf = Image.new("RGBA", (canvas_size, canvas_size), pal["light"])
    dark_surf = Image.new("RGBA", (canvas_size, canvas_size), pal["dark"])
    main_surf = Image.new("RGBA", (canvas_size, canvas_size), pal["main"])
    
    body_surf = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    body_surf.paste(dark_surf, (0, 6), mask=glyph_alpha)
    body_surf.paste(main_surf, (0, 0), mask=glyph_alpha)
    body_surf.paste(light_surf, (0, -6), mask=glyph_alpha)
    body_surf.paste(main_surf, (0, 0), mask=glyph_alpha.filter(ImageFilter.MinFilter(3)))
    
    gloss_surf = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    gloss_draw = ImageDraw.Draw(gloss_surf)
    gloss_draw.ellipse([cx - 24, cy - 64, cx - 8, cy - 50], fill=(255, 255, 255, 185))
    gloss_draw.ellipse([cx - 30, cy - 44, cx - 20, cy - 34], fill=(255, 255, 255, 130))

    # 7. Cute Chibi Face
    face_surf = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    fdraw = ImageDraw.Draw(face_surf)
    
    fx = cx
    fy = cy + pal["eye_offset_y"]
    eye_spacing = pal["eye_spacing"]
    eye_w, eye_h = 16, 22
    
    if is_blinking:
        fdraw.arc([fx - eye_spacing - eye_w//2, fy - 10, fx - eye_spacing + eye_w//2, fy + 8], start=20, end=160, fill=pal["outline"], width=5)
        fdraw.arc([fx + eye_spacing - eye_w//2, fy - 10, fx + eye_spacing + eye_w//2, fy + 8], start=20, end=160, fill=pal["outline"], width=5)
    else:
        for ex in [fx - eye_spacing, fx + eye_spacing]:
            fdraw.ellipse([ex - eye_w//2, fy - eye_h//2, ex + eye_w//2, fy + eye_h//2], fill=(255, 255, 255))
            fdraw.ellipse([ex - eye_w//2, fy - eye_h//2, ex + eye_w//2, fy + eye_h//2], outline=pal["outline"], width=3)
            fdraw.ellipse([ex - eye_w//2 + 3, fy - eye_h//2 + 4, ex + eye_w//2 - 3, fy + eye_h//2 - 2], fill=(30, 20, 35))
            fdraw.ellipse([ex + 1, fy - 7, ex + 6, fy - 2], fill=(255, 255, 255))
            fdraw.ellipse([ex - 4, fy + 2, ex - 1, fy + 5], fill=(255, 255, 255, 220))
            
    # Rosy Cheeks
    fdraw.ellipse([fx - eye_spacing - 14, fy + 10, fx - eye_spacing + 2, fy + 20], fill=pal["blush"])
    fdraw.ellipse([fx + eye_spacing - 2, fy + 10, fx + eye_spacing + 14, fy + 20], fill=pal["blush"])
    
    # Cute Open Smile
    mouth_y = fy + 14
    fdraw.pieslice([fx - 8, mouth_y - 3, fx + 8, mouth_y + 13], start=0, end=180, fill=(50, 12, 18), outline=pal["outline"], width=2)
    fdraw.pieslice([fx - 5, mouth_y + 3, fx + 5, mouth_y + 12], start=0, end=180, fill=(255, 115, 135))
    
    # Composite Layers
    img.alpha_composite(leg_surf)
    img.alpha_composite(arm_surf)
    img.alpha_composite(outline_surf)
    img.alpha_composite(body_surf)
    img.alpha_composite(gloss_surf)
    img.alpha_composite(face_surf)
    
    final_img = img.resize((out_size, out_size), Image.Resampling.LANCZOS)
    return final_img

def main():
    npc_base_path = os.path.join(BASE_DIR, "assets", "images", "sprites", "objects", "NPC")
    for num in range(1, 6):
        folder_name = f"Number{num}NPC"
        folder_path = os.path.join(npc_base_path, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        
        for frame_idx in range(8):
            filename = f"sprite_number{num}npc{frame_idx:02d}.png"
            filepath = os.path.join(folder_path, filename)
            frame_img = generate_number_character_frame(num, frame_idx, 8, 64)
            frame_img.save(filepath)
            print(f"Generated {folder_name}/{filename}")
            
    print("All Number NPC frames generated successfully!")

if __name__ == "__main__":
    main()
