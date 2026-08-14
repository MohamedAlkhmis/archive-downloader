import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, IS_DEVICE, get_bg_download_enabled


def main():
    if IS_DEVICE:
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

    pygame.init()
    pygame.joystick.init()

    try:
        pygame.mouse.set_visible(not IS_DEVICE)
    except pygame.error:
        pass

    flags = 0
    if IS_DEVICE:
        flags = pygame.FULLSCREEN

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
    pygame.display.set_caption("Archive Downloader")

    from ui import App
    app = App(screen)
    app.download_manager.load_queue()
    app.run()

    if app.download_manager.has_active() and get_bg_download_enabled():
        app.download_manager.spawn_background()

    pygame.quit()


if __name__ == "__main__":
    main()
