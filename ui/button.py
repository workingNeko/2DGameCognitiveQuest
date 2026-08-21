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

        # Load image if provided
        if image_path:
            self.image = pygame.image.load(image_path).convert_alpha()
            # Scale image to height of button (square icon)
            self.image = pygame.transform.scale(self.image, (self.rect.height, self.rect.height))

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

        # Draw image (if exists) on left side of button
        text_offset_x = 0
        if self.image:
            img_y = self.rect.y + (self.rect.height - self.image.get_height()) // 2
            screen.blit(self.image, (self.rect.x + 10, img_y))  # 10px padding
            text_offset_x = self.image.get_width() + 20  # space between image and text

        # Draw text (centered vertically, shifted right if image exists)
        if self.text and self.font:
            text_surf = self.font.render(self.text, True, self.text_color)
            text_rect = text_surf.get_rect()
            text_rect.centery = self.rect.y + self.rect.height // 2
            text_rect.x = self.rect.x + text_offset_x
            screen.blit(text_surf, text_rect)
