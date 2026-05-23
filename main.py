# main.py
import pygame
import sys
from screens.main_menu import MainMenu


def main():
    # Initialize Pygame
    pygame.init()

    # Get display info for fullscreen
    display_info = pygame.display.Info()
    screen_width = display_info.current_w
    screen_height = display_info.current_h

    # Set up fullscreen display
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
    pygame.display.set_caption("Cognitive Play - Educational Games")

    # Set up clock for FPS
    clock = pygame.time.Clock()

    # Create the main menu
    main_menu = MainMenu(screen)

    # Game loop
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:  # Press ESC to exit
                    running = False
                elif event.key == pygame.K_f:  # Press F to toggle fullscreen
                    pygame.display.toggle_fullscreen()
            else:
                main_menu.handle_event(event)

        # Update
        main_menu.update()

        # Draw
        main_menu.draw()

        # Update display
        pygame.display.flip()

        # Control frame rate
        clock.tick(60)  # 60 FPS

    # Quit the game
    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()