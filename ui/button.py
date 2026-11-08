import os
import sys
import pygame

class Button:
    def __init__(self, rect, text=None, font=None, bg_color=None, text_color=(0,0,0), action=None, image_path=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.bg_color = bg_color
        self.text_color = text_color
        self.action = action
        self.hovered = False
        self.image = None

        # Load image if provided with robust resolution and safe fallback
        if image_path:
            resolved_path = image_path
            if not os.path.exists(resolved_path):
                candidates = []
                if getattr(sys, "frozen", False):
                    base_dir = getattr(sys, "_MEIPASS", "")
                    if base_dir:
                        candidates.append(os.path.join(base_dir, image_path))
                    exe_dir = os.path.dirname(os.path.abspath(sys.executable))
                    candidates.append(os.path.join(exe_dir, image_path))
                    candidates.append(os.path.join(exe_dir, "_internal", image_path))
                else:
                    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    candidates.append(os.path.join(here, image_path))

                for cand in candidates:
                    if os.path.exists(cand):
                        resolved_path = cand
                        break

            try:
                if os.path.exists(resolved_path):
                    self.image = pygame.image.load(resolved_path).convert_alpha()
                    # Scale image to height of button (square icon)
                    scaled_img = pygame.transform.scale(self.image, (self.rect.height, self.rect.height))
                    if pygame.display.get_surface() is not None:
                        try:
                            scaled_img = scaled_img.convert_alpha()
                        except Exception:
                            pass
                    self.image = scaled_img
                else:
                    print(f"[WARN] Button image not found at '{image_path}', falling back gracefully.")
                    self.image = None
            except Exception as e:
                print(f"[WARN] Failed to load button image '{image_path}': {e}")
                self.image = None

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                if self.action:
                    self.action()

    def update(self):
        self.hovered = self.rect.collidepoint(pygame.mouse.get_pos())

    def draw(self, screen):
        # Draw background rectangle if color is set
        if self.bg_color:
            color = (
                min(self.bg_color[0] + 30, 255),
                min(self.bg_color[1] + 30, 255),
                min(self.bg_color[2] + 30, 255),
            ) if self.hovered else self.bg_color
            pygame.draw.rect(screen, color, self.rect, border_radius=12)
            pygame.draw.rect(screen, (0,0,0), self.rect, 3, border_radius=12)
        elif not self.image:
            # Fallback styling if image failed to load and no bg_color specified
            fallback_bg = (239, 68, 68) if self.hovered else (185, 28, 28)
            pygame.draw.rect(screen, fallback_bg, self.rect, border_radius=12)
            pygame.draw.rect(screen, (255, 255, 255), self.rect, 2, border_radius=12)

        # Draw image (if exists) on left side of button
        text_offset_x = 0
        if self.image:
            img_y = self.rect.y + (self.rect.height - self.image.get_height()) // 2
            screen.blit(self.image, (self.rect.x + 10, img_y))  # 10px padding
            text_offset_x = self.image.get_width() + 20  # space between image and text

        # Draw text (centered horizontally and vertically, adjusted if image exists)
        display_text = self.text
        if not display_text and not self.image:
            display_text = "EXIT" if "exit" in str(getattr(self, 'action', '')).lower() else "SELECT"

        if display_text:
            font = self.font or pygame.font.SysFont("Arial", 16, bold=True)
            text_surf = font.render(display_text, True, self.text_color if self.text_color else (255, 255, 255))
            text_rect = text_surf.get_rect()
            text_rect.centery = self.rect.y + self.rect.height // 2
            if self.image:
                text_rect.centerx = self.rect.x + text_offset_x + (self.rect.width - text_offset_x) // 2
            else:
                text_rect.centerx = self.rect.centerx
            screen.blit(text_surf, text_rect)
