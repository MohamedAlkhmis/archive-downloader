import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, IS_DEVICE


def main():
    if IS_DEVICE:
        os.environ.setdefault("SDL_VIDEODRIVER", "kmsdrm")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

    pygame.init()
    pygame.joystick.init()
    pygame.mouse.set_visible(not IS_DEVICE)

    flags = 0
    if IS_DEVICE:
        flags = pygame.FULLSCREEN

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
    pygame.display.set_caption("Archive Downloader")

    from ui import App
    app = App(screen)
    app.run()

    pygame.quit()


if __name__ == "__main__":
    main()
