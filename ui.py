import pygame
import time
from config import *


def draw_rounded_rect(surface, color, rect, radius=8):
    x, y, w, h = rect
    r = min(radius, h // 2, w // 2)
    pygame.draw.rect(surface, color, (x + r, y, w - 2 * r, h))
    pygame.draw.rect(surface, color, (x, y + r, w, h - 2 * r))
    pygame.draw.circle(surface, color, (x + r, y + r), r)
    pygame.draw.circle(surface, color, (x + w - r, y + r), r)
    pygame.draw.circle(surface, color, (x + r, y + h - r), r)
    pygame.draw.circle(surface, color, (x + w - r, y + h - r), r)


class InputEvent:
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    CONFIRM = "confirm"
    BACK = "back"
    PAGE_UP = "page_up"
    PAGE_DOWN = "page_down"
    START = "start"
    QUIT = "quit"


class InputHandler:
    def __init__(self):
        self.joystick = None
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
        self._repeat_delay = 400
        self._repeat_interval = 80
        self._held_keys = {}
        self._events = []

    def update(self, pygame_events):
        self._events = []
        now = pygame.time.get_ticks()

        for event in pygame_events:
            if event.type == pygame.KEYDOWN:
                action = self._key_to_action(event.key)
                if action:
                    self._events.append(action)
                    self._held_keys[event.key] = (now, False)
            elif event.type == pygame.KEYUP:
                self._held_keys.pop(event.key, None)
            elif event.type == pygame.JOYHATMOTION:
                hx, hy = event.value
                if hy == 1:
                    self._events.append(InputEvent.UP)
                elif hy == -1:
                    self._events.append(InputEvent.DOWN)
                if hx == -1:
                    self._events.append(InputEvent.LEFT)
                elif hx == 1:
                    self._events.append(InputEvent.RIGHT)
            elif event.type == pygame.JOYBUTTONDOWN:
                if self.joystick and event.button in GAMEPAD_START:
                    select_held = any(self.joystick.get_button(b) for b in GAMEPAD_SELECT)
                    if select_held:
                        self._events.append(InputEvent.QUIT)
                        continue
                elif self.joystick and event.button in GAMEPAD_SELECT:
                    start_held = any(self.joystick.get_button(b) for b in GAMEPAD_START)
                    if start_held:
                        self._events.append(InputEvent.QUIT)
                        continue
                if event.button in GAMEPAD_CONFIRM:
                    self._events.append(InputEvent.CONFIRM)
                elif event.button in GAMEPAD_BACK:
                    self._events.append(InputEvent.BACK)
                elif event.button in GAMEPAD_L:
                    self._events.append(InputEvent.PAGE_UP)
                elif event.button in GAMEPAD_R:
                    self._events.append(InputEvent.PAGE_DOWN)
                elif event.button in GAMEPAD_START:
                    self._events.append(InputEvent.START)

        for key, (start_time, repeating) in list(self._held_keys.items()):
            action = self._key_to_action(key)
            if not action:
                continue
            if not repeating and now - start_time > self._repeat_delay:
                self._events.append(action)
                self._held_keys[key] = (now, True)
            elif repeating and now - start_time > self._repeat_interval:
                self._events.append(action)
                self._held_keys[key] = (now, True)

    def get_events(self):
        return self._events

    def _key_to_action(self, key):
        mapping = {
            pygame.K_UP: InputEvent.UP,
            pygame.K_DOWN: InputEvent.DOWN,
            pygame.K_LEFT: InputEvent.LEFT,
            pygame.K_RIGHT: InputEvent.RIGHT,
            pygame.K_RETURN: InputEvent.CONFIRM,
            pygame.K_SPACE: InputEvent.CONFIRM,
            pygame.K_ESCAPE: InputEvent.BACK,
            pygame.K_BACKSPACE: InputEvent.BACK,
            pygame.K_PAGEUP: InputEvent.PAGE_UP,
            pygame.K_PAGEDOWN: InputEvent.PAGE_DOWN,
            pygame.K_TAB: InputEvent.START,
        }
        return mapping.get(key)


class FontCache:
    def __init__(self):
        self._fonts = {}
        self._preferred = None
        for name in ["DejaVu Sans", "Liberation Sans", "FreeSans", "Arial", "Helvetica"]:
            if name.lower().replace(" ", "") in [f.lower().replace(" ", "") for f in pygame.font.get_fonts()]:
                self._preferred = name
                break

    def get(self, size, bold=False):
        key = (size, bold)
        if key not in self._fonts:
            if self._preferred:
                self._fonts[key] = pygame.font.SysFont(self._preferred, size, bold=bold)
            else:
                self._fonts[key] = pygame.font.Font(None, size)
        return self._fonts[key]


fonts = None


def init_fonts():
    global fonts
    fonts = FontCache()


def draw_text(surface, text, pos, color=None, size=FONT_SIZE_BODY, bold=False, max_width=None):
    if color is None:
        color = COLORS["text"]
    font = fonts.get(size, bold)
    if max_width:
        while len(text) > 3 and font.size(text)[0] > max_width:
            text = text[:-4] + "..."
    rendered = font.render(text, True, color)
    surface.blit(rendered, pos)
    return rendered.get_rect(topleft=pos)


def draw_header(surface, title, show_back=True):
    pygame.draw.rect(surface, COLORS["header"], (0, 0, SCREEN_WIDTH, HEADER_HEIGHT))
    pygame.draw.line(surface, COLORS["divider"], (0, HEADER_HEIGHT - 1), (SCREEN_WIDTH, HEADER_HEIGHT - 1))
    if show_back:
        draw_text(surface, "<", (12, 10), COLORS["accent"], FONT_SIZE_TITLE, bold=True)
    draw_text(surface, title, (40 if show_back else 16, 11), COLORS["text"], FONT_SIZE_TITLE, bold=True)


def draw_footer(surface, hints):
    y = SCREEN_HEIGHT - FOOTER_HEIGHT
    pygame.draw.rect(surface, COLORS["header"], (0, y, SCREEN_WIDTH, FOOTER_HEIGHT))
    pygame.draw.line(surface, COLORS["divider"], (0, y), (SCREEN_WIDTH, y))
    x = 16
    for label, action in hints:
        btn_w = fonts.get(FONT_SIZE_HINT, bold=True).size(action)[0] + 10
        draw_rounded_rect(surface, COLORS["bg_lighter"], (x, y + 8, btn_w, 20), 4)
        draw_text(surface, action, (x + 5, y + 10), COLORS["accent"], FONT_SIZE_HINT, bold=True)
        x += btn_w + 4
        draw_text(surface, label, (x, y + 10), COLORS["text_dim"], FONT_SIZE_HINT)
        x += fonts.get(FONT_SIZE_HINT).size(label)[0] + 16


def draw_loading(surface, message="Loading..."):
    t = int(time.time() * 3) % 3
    dots = "." * (t + 1)
    text = message.rstrip(".") + dots
    font = fonts.get(FONT_SIZE_BODY)
    tw, th = font.size(text)
    x = (SCREEN_WIDTH - tw) // 2
    y = CONTENT_Y + CONTENT_HEIGHT // 2 - th // 2
    draw_text(surface, text, (x, y), COLORS["text_dim"])


def draw_message(surface, text, color=None):
    if color is None:
        color = COLORS["text_dim"]
    font = fonts.get(FONT_SIZE_BODY)
    tw, th = font.size(text)
    x = (SCREEN_WIDTH - tw) // 2
    y = CONTENT_Y + CONTENT_HEIGHT // 2 - th // 2
    draw_text(surface, text, (x, y), color)


def draw_progress_bar(surface, rect, progress, color=None):
    if color is None:
        color = COLORS["accent"]
    x, y, w, h = rect
    draw_rounded_rect(surface, COLORS["bg_lighter"], rect, h // 2)
    if progress > 0:
        fill_w = max(h, int(w * min(progress, 1.0)))
        draw_rounded_rect(surface, color, (x, y, fill_w, h), h // 2)


class ListView:
    def __init__(self, item_height=40, visible_area_y=CONTENT_Y, visible_area_h=CONTENT_HEIGHT):
        self.items = []
        self.selected = 0
        self.scroll_offset = 0
        self.item_height = item_height
        self.area_y = visible_area_y
        self.area_h = visible_area_h
        self.visible_count = self.area_h // self.item_height

    def set_items(self, items):
        self.items = items
        self.selected = min(self.selected, max(0, len(items) - 1))
        self._clamp_scroll()

    def handle_input(self, events):
        for event in events:
            if event == InputEvent.UP:
                self.selected = max(0, self.selected - 1)
            elif event == InputEvent.DOWN:
                self.selected = min(len(self.items) - 1, self.selected + 1)
            elif event == InputEvent.PAGE_UP:
                self.selected = max(0, self.selected - self.visible_count)
            elif event == InputEvent.PAGE_DOWN:
                self.selected = min(len(self.items) - 1, self.selected + self.visible_count)
        self._clamp_scroll()

    def _clamp_scroll(self):
        if self.selected < self.scroll_offset:
            self.scroll_offset = self.selected
        elif self.selected >= self.scroll_offset + self.visible_count:
            self.scroll_offset = self.selected - self.visible_count + 1

    def draw(self, surface, render_item_fn):
        clip = pygame.Rect(0, self.area_y, SCREEN_WIDTH, self.area_h)
        surface.set_clip(clip)

        for i in range(self.scroll_offset, min(self.scroll_offset + self.visible_count + 1, len(self.items))):
            y = self.area_y + (i - self.scroll_offset) * self.item_height
            is_selected = i == self.selected
            if is_selected:
                draw_rounded_rect(surface, COLORS["accent_dark"], (8, y + 2, SCREEN_WIDTH - 16, self.item_height - 4), 6)
            render_item_fn(surface, self.items[i], i, y, is_selected)

        if len(self.items) > self.visible_count:
            sb_h = self.area_h
            thumb_h = max(20, int(sb_h * self.visible_count / len(self.items)))
            thumb_y = self.area_y + int((sb_h - thumb_h) * self.scroll_offset / max(1, len(self.items) - self.visible_count))
            pygame.draw.rect(surface, COLORS["scrollbar"], (SCREEN_WIDTH - 4, self.area_y, 4, sb_h))
            draw_rounded_rect(surface, COLORS["scrollbar_thumb"], (SCREEN_WIDTH - 4, thumb_y, 4, thumb_h), 2)

        surface.set_clip(None)

    def get_selected(self):
        if 0 <= self.selected < len(self.items):
            return self.items[self.selected]
        return None


OSK_PAGES = [
    [
        list("1234567890"),
        list("QWERTYUIOP"),
        list("ASDFGHJKL_"),
        list("ZXCVBNM.:-"),
        ["SPC", "DEL", "#+=", "OK"],
    ],
    [
        list("@#$%&*+-=^"),
        list("(){}[]<>|/"),
        list('!?~`"' + "';,\\"),
        list("._:-@#$%&*"),
        ["SPC", "DEL", "ABC", "OK"],
    ],
]  # clean up row 4


class OnScreenKeyboard:
    def __init__(self):
        self.text = ""
        self.cursor_row = 0
        self.cursor_col = 0
        self.page = 0
        self.active = True
        self.confirmed = False

    @property
    def rows(self):
        return OSK_PAGES[self.page]

    def handle_input(self, events):
        for event in events:
            row = self.rows[self.cursor_row]
            if event == InputEvent.UP:
                self.cursor_row = max(0, self.cursor_row - 1)
                self.cursor_col = min(self.cursor_col, len(self.rows[self.cursor_row]) - 1)
            elif event == InputEvent.DOWN:
                self.cursor_row = min(len(self.rows) - 1, self.cursor_row + 1)
                self.cursor_col = min(self.cursor_col, len(self.rows[self.cursor_row]) - 1)
            elif event == InputEvent.LEFT:
                self.cursor_col = max(0, self.cursor_col - 1)
            elif event == InputEvent.RIGHT:
                self.cursor_col = min(len(row) - 1, self.cursor_col + 1)
            elif event == InputEvent.CONFIRM:
                key = self.rows[self.cursor_row][self.cursor_col]
                if key == "SPC":
                    self.text += " "
                elif key == "DEL":
                    self.text = self.text[:-1]
                elif key == "OK":
                    self.confirmed = True
                elif key in ("#+=", "ABC"):
                    self.page = 1 - self.page
                    self.cursor_col = min(self.cursor_col, len(self.rows[self.cursor_row]) - 1)
                else:
                    self.text += key.lower() if key.isalpha() else key

    def draw(self, surface, y_offset):
        text_box_y = y_offset
        draw_rounded_rect(surface, COLORS["bg_lighter"], (16, text_box_y, SCREEN_WIDTH - 32, 32), 6)
        display = self.text if self.text else "Type to search..."
        color = COLORS["text"] if self.text else COLORS["text_hint"]
        draw_text(surface, display, (24, text_box_y + 7), color, FONT_SIZE_BODY, max_width=SCREEN_WIDTH - 56)
        cursor_x = 24 + fonts.get(FONT_SIZE_BODY).size(self.text)[0]
        if int(time.time() * 2) % 2 == 0 and self.text:
            pygame.draw.rect(surface, COLORS["accent"], (min(cursor_x, SCREEN_WIDTH - 40), text_box_y + 6, 2, 20))

        key_start_y = text_box_y + 44
        key_w = 42
        key_h = 34
        gap = 4

        for ri, row in enumerate(self.rows):
            if ri == len(self.rows) - 1:
                total_w = sum(120 if k == "SPC" else 80 for k in row) + gap * (len(row) - 1)
            else:
                total_w = len(row) * (key_w + gap) - gap
            start_x = (SCREEN_WIDTH - total_w) // 2
            ky = key_start_y + ri * (key_h + gap)
            kx = start_x

            for ci, key in enumerate(row):
                if ri == len(self.rows) - 1:
                    w = 120 if key == "SPC" else 80
                else:
                    w = key_w
                is_sel = ri == self.cursor_row and ci == self.cursor_col
                bg = COLORS["accent"] if is_sel else COLORS["bg_light"]
                text_color = COLORS["bg"] if is_sel else COLORS["text"]
                draw_rounded_rect(surface, bg, (kx, ky, w, key_h), 5)
                label_font = fonts.get(FONT_SIZE_SMALL, bold=is_sel)
                lw, lh = label_font.size(key)
                draw_text(surface, key, (kx + (w - lw) // 2, ky + (key_h - lh) // 2), text_color, FONT_SIZE_SMALL, bold=is_sel)
                kx += w + gap

    def get_height(self):
        return 32 + 12 + len(self.rows) * 38 + 8


class Screen:
    def __init__(self, app):
        self.app = app

    def on_enter(self):
        pass

    def handle_input(self, events):
        pass

    def update(self):
        pass

    def draw(self, surface):
        pass


class MainMenuScreen(Screen):
    ITEMS = [
        {"label": "Browse by System", "icon": "SYS", "desc": "Browse curated console collections"},
        {"label": "Search Archive.org", "icon": "SRC", "desc": "Search for any content on archive.org"},
        {"label": "Downloads", "icon": "DWN", "desc": "View active and completed downloads"},
        {"label": "Settings", "icon": "SET", "desc": "Configure paths and button mapping"},
        {"label": "Exit", "icon": "END", "desc": "Close the application"},
    ]

    def __init__(self, app):
        super().__init__(app)
        self.list = ListView(item_height=56)
        self.list.set_items(self.ITEMS)

    def handle_input(self, events):
        self.list.handle_input(events)
        for event in events:
            if event == InputEvent.CONFIRM:
                sel = self.list.selected
                if sel == 0:
                    self.app.push_screen(BrowseSystemScreen(self.app))
                elif sel == 1:
                    self.app.push_screen(SearchScreen(self.app))
                elif sel == 2:
                    self.app.push_screen(DownloadQueueScreen(self.app))
                elif sel == 3:
                    self.app.push_screen(SettingsScreen(self.app))
                elif sel == 4:
                    self.app.quit()

    def draw(self, surface):
        draw_header(surface, "Archive Downloader", show_back=False)

        def render_item(surf, item, idx, y, selected):
            tag_bg = COLORS["accent"] if selected else COLORS["bg_lighter"]
            draw_rounded_rect(surf, tag_bg, (20, y + 10, 44, 36), 6)
            tag_font = fonts.get(FONT_SIZE_HINT, bold=True)
            tw, th = tag_font.size(item["icon"])
            draw_text(surf, item["icon"], (20 + (44 - tw) // 2, y + 10 + (36 - th) // 2),
                       COLORS["bg"] if selected else COLORS["text_dim"], FONT_SIZE_HINT, bold=True)
            draw_text(surf, item["label"], (76, y + 8), COLORS["text"], FONT_SIZE_BODY, bold=selected)
            draw_text(surf, item["desc"], (76, y + 30), COLORS["text_dim"], FONT_SIZE_SMALL)

        self.list.draw(surface, render_item)
        draw_footer(surface, [("Select", "A"), ("Exit", "B")])


class BrowseSystemScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.list = ListView(item_height=40)
        self.list.set_items(get_enabled_systems())

    def handle_input(self, events):
        self.list.handle_input(events)
        for event in events:
            if event == InputEvent.CONFIRM:
                system = self.list.get_selected()
                if system:
                    self.app.push_screen(SearchResultsScreen(self.app, system["query"], system["name"], system["dir"]))
            elif event == InputEvent.BACK:
                self.app.pop_screen()

    def draw(self, surface):
        draw_header(surface, "Browse by System")

        def render_item(surf, item, idx, y, selected):
            tag_bg = COLORS["accent"] if selected else COLORS["bg_lighter"]
            draw_rounded_rect(surf, tag_bg, (20, y + 6, 40, 28), 5)
            tag_font = fonts.get(FONT_SIZE_HINT, bold=True)
            tw, th = tag_font.size(item["tag"])
            draw_text(surf, item["tag"], (20 + (40 - tw) // 2, y + 6 + (28 - th) // 2),
                       COLORS["bg"] if selected else COLORS["text_dim"], FONT_SIZE_HINT, bold=True)
            draw_text(surf, item["name"], (72, y + 10), COLORS["text"], FONT_SIZE_BODY, bold=selected)

        self.list.draw(surface, render_item)
        draw_footer(surface, [("Select", "A"), ("Back", "B"), ("Page", "L/R")])


class SearchScreen(Screen):
    def __init__(self, app, initial_query=""):
        super().__init__(app)
        self.keyboard = OnScreenKeyboard()
        self.keyboard.text = initial_query

    def handle_input(self, events):
        for event in events:
            if event == InputEvent.BACK:
                self.app.pop_screen()
                return
        self.keyboard.handle_input(events)
        if self.keyboard.confirmed:
            query = self.keyboard.text.strip()
            if query:
                self.app.push_screen(SearchResultsScreen(self.app, query, f'"{query}"'))
            self.keyboard.confirmed = False

    def draw(self, surface):
        draw_header(surface, "Search Archive.org")
        self.keyboard.draw(surface, CONTENT_Y + 12)
        draw_footer(surface, [("Type", "A"), ("Back", "B")])


LOAD_MORE_SENTINEL = {"_load_more": True}
RESULTS_PER_PAGE = 10


class SearchResultsScreen(Screen):
    def __init__(self, app, query, title, system_dir=None):
        super().__init__(app)
        self.query = query
        self.title = title
        self.system_dir = system_dir
        self.list = ListView(item_height=48)
        self.task = None
        self.loading = True
        self.loading_more = False
        self.error = None
        self.results = []
        self.page = 1
        self.total = 0

    def on_enter(self):
        self._fetch_page(1)

    def _fetch_page(self, page):
        from archive_api import AsyncTask, ArchiveAPI
        api = ArchiveAPI()
        self.task = AsyncTask(api.search, self.query, page, RESULTS_PER_PAGE)
        self.page = page

    def _rebuild_list(self):
        items = list(self.results)
        if len(self.results) < self.total:
            items.append(LOAD_MORE_SENTINEL)
        self.list.set_items(items)

    def handle_input(self, events):
        if self.loading or self.loading_more:
            for event in events:
                if event == InputEvent.BACK:
                    self.app.pop_screen()
            return
        self.list.handle_input(events)
        for event in events:
            if event == InputEvent.CONFIRM:
                item = self.list.get_selected()
                if item and item.get("_load_more"):
                    self.loading_more = True
                    self._fetch_page(self.page + 1)
                elif item:
                    self.app.push_screen(FileListScreen(self.app, item["identifier"], item.get("title", item["identifier"]), self.system_dir))
            elif event == InputEvent.BACK:
                self.app.pop_screen()

    def update(self):
        if self.task and self.task.done:
            if self.task.error:
                if self.loading:
                    self.error = self.task.error
                else:
                    self.app.toast("Failed to load more", COLORS["error"])
                self.loading = False
                self.loading_more = False
            elif self.task.result:
                result = self.task.result
                if result.get("error"):
                    if self.loading:
                        self.error = result["error"]
                    else:
                        self.app.toast(result["error"], COLORS["error"])
                else:
                    new_items = result.get("items", [])
                    self.total = result.get("total", 0)
                    self.results.extend(new_items)
                    if not self.results:
                        self.error = "No results found"
                    else:
                        old_sel = self.list.selected
                        self._rebuild_list()
                        self.list.selected = old_sel
                        self.list._clamp_scroll()
                self.loading = False
                self.loading_more = False
            self.task = None

    def draw(self, surface):
        draw_header(surface, self.title)
        if self.loading:
            draw_loading(surface, "Searching archive.org")
        elif self.error:
            draw_message(surface, self.error, COLORS["error"])
        else:
            count_text = f"{len(self.results)} of {self.total}"
            draw_text(surface, count_text,
                      (SCREEN_WIDTH - fonts.get(FONT_SIZE_SMALL).size(count_text)[0] - 12, CONTENT_Y + 2),
                      COLORS["text_dim"], FONT_SIZE_SMALL)

            def render_item(surf, item, idx, y, selected):
                if item.get("_load_more"):
                    label = "Loading..." if self.loading_more else f"Load More Results ({self.total - len(self.results)} remaining)"
                    color = COLORS["text_dim"] if self.loading_more else COLORS["accent"]
                    draw_text(surf, label, (20, y + 14), color, FONT_SIZE_BODY, bold=selected, max_width=SCREEN_WIDTH - 50)
                    return
                title = item.get("title", item.get("identifier", "Unknown"))
                draw_text(surf, title, (20, y + 6), COLORS["text"], FONT_SIZE_BODY, bold=selected, max_width=SCREEN_WIDTH - 50)
                desc = item.get("identifier", "")
                downloads = item.get("downloads", 0)
                sub = f"{desc}"
                if downloads:
                    sub += f"  |  {downloads:,} downloads"
                draw_text(surf, sub, (20, y + 28), COLORS["text_dim"], FONT_SIZE_SMALL, max_width=SCREEN_WIDTH - 50)

            self.list.draw(surface, render_item)
        draw_footer(surface, [("Open", "A"), ("Back", "B"), ("Page", "L/R")])


class FileListScreen(Screen):
    def __init__(self, app, identifier, title, system_dir=None):
        super().__init__(app)
        self.identifier = identifier
        self.title = title
        self.system_dir = system_dir
        self.list = ListView(item_height=40)
        self.task = None
        self.loading = True
        self.error = None
        self.all_files = []
        self.show_all = False
        self.login_required = False

    def on_enter(self):
        from archive_api import AsyncTask, ArchiveAPI
        api = ArchiveAPI()
        self.task = AsyncTask(api.get_files, self.identifier, ROM_EXTENSIONS)

    def handle_input(self, events):
        if self.loading:
            for event in events:
                if event == InputEvent.BACK:
                    self.app.pop_screen()
            return
        self.list.handle_input(events)
        for event in events:
            if event == InputEvent.CONFIRM:
                f = self.list.get_selected()
                if f:
                    if self.login_required:
                        self.app.toast("Login required - may fail", COLORS["warning"])
                    detected = detect_system_dir(f["name"], self.system_dir)
                    dest = get_rom_path(detected) if detected else get_rom_path("downloads")
                    self.app.download_manager.add(f["url"], dest, f["name"])
                    self.app.toast("Download started: " + f["name"], COLORS["success"])
            elif event == InputEvent.BACK:
                self.app.pop_screen()
            elif event == InputEvent.START:
                self.show_all = not self.show_all
                if self.show_all:
                    self.list.set_items(self.all_files)
                else:
                    self.list.set_items([f for f in self.all_files if any(f["name"].lower().endswith(e) for e in ROM_EXTENSIONS)])

    def update(self):
        if self.task and self.task.done:
            self.loading = False
            if self.task.error:
                self.error = self.task.error
            elif self.task.result:
                result = self.task.result
                if result.get("error"):
                    self.error = result["error"]
                else:
                    self.all_files = result.get("files", [])
                    self.login_required = result.get("login_required", False)
                    self.list.set_items(self.all_files)
                    if not self.all_files:
                        self.error = "No ROM files found in this item"
            self.task = None

    def draw(self, surface):
        title = self.title
        if len(title) > 35:
            title = title[:32] + "..."
        draw_header(surface, title)
        if self.loading:
            draw_loading(surface, "Fetching file list")
        elif self.error:
            draw_message(surface, self.error, COLORS["warning"])
        else:
            banner_h = 0
            if self.login_required:
                banner_h = 22
                draw_rounded_rect(surface, (80, 40, 20), (8, CONTENT_Y + 2, SCREEN_WIDTH - 16, 18), 4)
                draw_text(surface, "Requires archive.org login - downloads may fail", (14, CONTENT_Y + 4), COLORS["warning"], FONT_SIZE_HINT)

            count = len(self.list.items)
            info = f"{count} file{'s' if count != 1 else ''}"
            draw_text(surface, info, (SCREEN_WIDTH - fonts.get(FONT_SIZE_SMALL).size(info)[0] - 12, CONTENT_Y + banner_h + 2), COLORS["text_dim"], FONT_SIZE_SMALL)
            file_list = ListView(item_height=38, visible_area_y=CONTENT_Y + banner_h + 20, visible_area_h=CONTENT_HEIGHT - banner_h - 20)
            file_list.items = self.list.items
            file_list.selected = self.list.selected
            file_list.scroll_offset = self.list.scroll_offset
            file_list.visible_count = file_list.area_h // file_list.item_height

            def render_item(surf, item, idx, y, selected):
                name = item["name"].rsplit("/", 1)[-1] if "/" in item["name"] else item["name"]
                draw_text(surf, name, (20, y + 4), COLORS["text"], FONT_SIZE_SMALL, bold=selected, max_width=SCREEN_WIDTH - 120)
                size_str = format_size(item["size"])
                sw = fonts.get(FONT_SIZE_HINT).size(size_str)[0]
                draw_text(surf, size_str, (SCREEN_WIDTH - sw - 20, y + 6), COLORS["text_dim"], FONT_SIZE_HINT)
                ext = name.rsplit(".", 1)[-1].upper() if "." in name else ""
                draw_text(surf, ext, (20, y + 22), COLORS["text_hint"], FONT_SIZE_HINT)

            file_list.draw(surface, render_item)

        draw_footer(surface, [("Download", "A"), ("Back", "B"), ("Page", "L/R")])


class DownloadQueueScreen(Screen):
    TAB_ACTIVE = 0
    TAB_HISTORY = 1
    TAB_HEIGHT = 32

    def __init__(self, app):
        super().__init__(app)
        self.tab = self.TAB_ACTIVE
        content_y = CONTENT_Y + self.TAB_HEIGHT
        content_h = CONTENT_HEIGHT - self.TAB_HEIGHT
        self.active_list = ListView(item_height=52, visible_area_y=content_y, visible_area_h=content_h)
        self.history_list = ListView(item_height=44, visible_area_y=content_y, visible_area_h=content_h)

    def handle_input(self, events):
        consumed_lr = False
        for event in events:
            if event == InputEvent.PAGE_UP and self.tab != self.TAB_ACTIVE:
                self.tab = self.TAB_ACTIVE
                consumed_lr = True
            elif event == InputEvent.PAGE_DOWN and self.tab != self.TAB_HISTORY:
                self.tab = self.TAB_HISTORY
                self._refresh_history()
                consumed_lr = True
            elif event == InputEvent.BACK:
                self.app.pop_screen()
                return

        filtered = [e for e in events if not consumed_lr or e not in (InputEvent.PAGE_UP, InputEvent.PAGE_DOWN)]

        if self.tab == self.TAB_ACTIVE:
            self._handle_active(filtered)
        else:
            self._handle_history(filtered)

    def _handle_active(self, events):
        downloads = self.app.download_manager.get_all()
        self.active_list.set_items(downloads)
        self.active_list.handle_input(events)
        dl = self.active_list.get_selected()
        for event in events:
            if event == InputEvent.CONFIRM and dl:
                if dl.status in ("downloading", "pending"):
                    self.app.download_manager.cancel(dl)
                    self.app.toast("Cancelled", COLORS["warning"])
                elif dl.status in ("error", "cancelled"):
                    self.app.download_manager.retry(dl)
                    self.app.toast("Retrying...", COLORS["accent"])
            elif event == InputEvent.START:
                self.app.download_manager.remove_completed()

    def _handle_history(self, events):
        self.history_list.handle_input(events)
        entry = self.history_list.get_selected()
        for event in events:
            if event == InputEvent.CONFIRM and entry:
                if not self.app.history.is_on_disk(entry):
                    self.app.download_manager.add(entry["url"], entry["dest_path"], entry["filename"])
                    self.app.toast("Redownloading: " + entry["filename"], COLORS["accent"])
                else:
                    self.app.toast("File already on disk", COLORS["success"])
            elif event == InputEvent.START:
                self.app.history.clear()
                self.history_list.set_items([])
                self.app.toast("History cleared", COLORS["text_dim"])

    def _refresh_history(self):
        self.history_list.set_items(self.app.history.get_all())

    def update(self):
        if self.tab == self.TAB_ACTIVE:
            self.active_list.set_items(self.app.download_manager.get_all())

    def _draw_tabs(self, surface):
        tab_y = CONTENT_Y
        tab_w = SCREEN_WIDTH // 2
        labels = ["Active", "History"]
        for i, label in enumerate(labels):
            x = i * tab_w
            is_active = i == self.tab
            bg = COLORS["bg_light"] if is_active else COLORS["bg"]
            pygame.draw.rect(surface, bg, (x, tab_y, tab_w, self.TAB_HEIGHT))
            lw = fonts.get(FONT_SIZE_BODY, bold=is_active).size(label)[0]
            color = COLORS["accent"] if is_active else COLORS["text_dim"]
            draw_text(surface, label, (x + (tab_w - lw) // 2, tab_y + 7), color, FONT_SIZE_BODY, bold=is_active)
            if is_active:
                pygame.draw.rect(surface, COLORS["accent"], (x + 4, tab_y + self.TAB_HEIGHT - 3, tab_w - 8, 3))
        pygame.draw.line(surface, COLORS["divider"], (0, tab_y + self.TAB_HEIGHT - 1), (SCREEN_WIDTH, tab_y + self.TAB_HEIGHT - 1))

    def draw(self, surface):
        draw_header(surface, "Downloads")
        self._draw_tabs(surface)

        if self.tab == self.TAB_ACTIVE:
            self._draw_active(surface)
        else:
            self._draw_history(surface)

    def _draw_active(self, surface):
        downloads = self.active_list.items
        if not downloads:
            y = CONTENT_Y + self.TAB_HEIGHT + (CONTENT_HEIGHT - self.TAB_HEIGHT) // 2
            font = fonts.get(FONT_SIZE_BODY)
            tw = font.size("No downloads yet")[0]
            draw_text(surface, "No downloads yet", ((SCREEN_WIDTH - tw) // 2, y), COLORS["text_dim"])
        else:
            def render_item(surf, dl, idx, y, selected):
                name = dl.filename
                draw_text(surf, name, (20, y + 4), COLORS["text"], FONT_SIZE_SMALL, bold=selected, max_width=SCREEN_WIDTH - 40)

                status_colors = {
                    "pending": COLORS["text_dim"],
                    "downloading": COLORS["accent"],
                    "extracting": COLORS["warning"],
                    "done": COLORS["success"],
                    "error": COLORS["error"],
                    "cancelled": COLORS["warning"],
                }
                status_color = status_colors.get(dl.status, COLORS["text_dim"])

                if dl.status == "downloading":
                    draw_progress_bar(surf, (20, y + 24, SCREEN_WIDTH - 140, 10), dl.progress)
                    pct = f"{int(dl.progress * 100)}%"
                    speed = format_size(int(dl.speed)) + "/s" if dl.speed > 0 else ""
                    info = f"{pct}  {speed}"
                    draw_text(surf, info, (SCREEN_WIDTH - 110, y + 20), COLORS["accent"], FONT_SIZE_HINT)
                elif dl.status == "extracting":
                    draw_progress_bar(surf, (20, y + 24, SCREEN_WIDTH - 140, 10), 1.0, COLORS["warning"])
                    draw_text(surf, "Extracting ZIP...", (SCREEN_WIDTH - 110, y + 20), COLORS["warning"], FONT_SIZE_HINT)
                else:
                    status_text = dl.status.upper()
                    if dl.status == "error" and dl.error:
                        status_text += f": {dl.error[:40]}"
                    elif dl.status == "done" and dl.error:
                        status_text += f" ({dl.error[:30]})"
                    draw_text(surf, status_text, (20, y + 26), status_color, FONT_SIZE_HINT)
                    if dl.status == "done" and not dl.error:
                        size_str = format_size(dl.downloaded_bytes)
                        draw_text(surf, size_str, (SCREEN_WIDTH - fonts.get(FONT_SIZE_HINT).size(size_str)[0] - 20, y + 26), COLORS["text_dim"], FONT_SIZE_HINT)

                if selected:
                    action = ""
                    if dl.status in ("downloading", "pending"):
                        action = "[A] Cancel"
                    elif dl.status in ("error", "cancelled"):
                        action = "[A] Retry"
                    if action:
                        aw = fonts.get(FONT_SIZE_HINT).size(action)[0]
                        draw_text(surf, action, (SCREEN_WIDTH - aw - 20, y + 4), COLORS["accent"], FONT_SIZE_HINT)

            self.active_list.draw(surface, render_item)

        dl = self.active_list.get_selected()
        hints = [("Back", "B")]
        if dl:
            if dl.status in ("downloading", "pending"):
                hints.insert(0, ("Cancel", "A"))
            elif dl.status in ("error", "cancelled"):
                hints.insert(0, ("Retry", "A"))
        hints.append(("Clear All", "START"))
        hints.append(("History", "R"))
        draw_footer(surface, hints)

    def _draw_history(self, surface):
        entries = self.history_list.items
        if not entries:
            y = CONTENT_Y + self.TAB_HEIGHT + (CONTENT_HEIGHT - self.TAB_HEIGHT) // 2
            font = fonts.get(FONT_SIZE_BODY)
            tw = font.size("No download history")[0]
            draw_text(surface, "No download history", ((SCREEN_WIDTH - tw) // 2, y), COLORS["text_dim"])
        else:
            def render_item(surf, entry, idx, y, selected):
                name = entry["filename"]
                on_disk = self.app.history.is_on_disk(entry)
                icon = "OK" if on_disk else "DL"
                icon_bg = COLORS["success"] if on_disk else COLORS["bg_lighter"]
                draw_rounded_rect(surf, icon_bg, (14, y + 8, 30, 28), 5)
                iw = fonts.get(FONT_SIZE_HINT, bold=True).size(icon)[0]
                draw_text(surf, icon, (14 + (30 - iw) // 2, y + 14), COLORS["bg"] if on_disk else COLORS["text_dim"], FONT_SIZE_HINT, bold=True)
                draw_text(surf, name, (52, y + 6), COLORS["text"], FONT_SIZE_SMALL, bold=selected, max_width=SCREEN_WIDTH - 70)
                size_str = format_size(entry.get("size", 0))
                status = "On device" if on_disk else "Not found - A to redownload"
                status_color = COLORS["success"] if on_disk else COLORS["text_dim"]
                draw_text(surf, f"{size_str}  {status}", (52, y + 26), status_color, FONT_SIZE_HINT)

            self.history_list.draw(surface, render_item)

        hints = [("Back", "B"), ("Redownload", "A"), ("Clear", "START"), ("Active", "L")]
        draw_footer(surface, hints)


class SettingsScreen(Screen):
    def __init__(self, app):
        super().__init__(app)
        self.list = ListView(item_height=50)
        self._refresh_items()

    def _refresh_items(self):
        from archive_api import load_credentials
        creds = load_credentials()
        if creds:
            login_icon = "ON"
            login_value = creds.get("email", "Logged in")
            login_label = "Archive.org Account"
        else:
            login_icon = "OFF"
            login_value = "Not logged in"
            login_label = "Archive.org Account"

        enabled_count = len(get_enabled_systems())
        total_count = len(ALL_SYSTEMS)

        custom_count = len(get_custom_paths())
        paths_value = f"{custom_count} custom path{'s' if custom_count != 1 else ''}" if custom_count else "All default"

        self.items = [
            {"label": login_label, "value": login_value, "key": "login", "icon": login_icon,
             "icon_color": COLORS["success"] if creds else COLORS["text_dim"]},
            {"label": "Manage Systems", "value": f"{enabled_count} of {total_count} systems enabled", "key": "systems", "icon": "SYS",
             "icon_color": COLORS["accent"]},
            {"label": "System Paths", "value": paths_value, "key": "paths", "icon": "DIR",
             "icon_color": COLORS["warning"] if custom_count else COLORS["text_dim"]},
            {"label": "Device Info", "value": f"{'Device' if IS_DEVICE else 'PC'} | {'Gamepad' if pygame.joystick.get_count() > 0 else 'Keyboard'} | {SCREEN_WIDTH}x{SCREEN_HEIGHT}", "key": "info", "icon": "INF",
             "icon_color": COLORS["text_dim"]},
        ]
        self.list.set_items(self.items)

    def handle_input(self, events):
        self.list.handle_input(events)
        for event in events:
            if event == InputEvent.BACK:
                self.app.pop_screen()
            elif event == InputEvent.CONFIRM:
                item = self.list.get_selected()
                if not item:
                    continue
                if item["key"] == "login":
                    from archive_api import load_credentials
                    creds = load_credentials()
                    if creds:
                        self.app.push_screen(LogoutConfirmScreen(self.app, self))
                    else:
                        self.app.push_screen(LoginEmailScreen(self.app, self))
                elif item["key"] == "systems":
                    self.app.push_screen(ManageSystemsScreen(self.app, self))
                elif item["key"] == "paths":
                    self.app.push_screen(SystemPathsScreen(self.app, self))

    def draw(self, surface):
        draw_header(surface, "Settings")

        def render_item(surf, item, idx, y, selected):
            icon_bg = item.get("icon_color", COLORS["bg_lighter"])
            draw_rounded_rect(surf, icon_bg, (16, y + 9, 36, 32), 6)
            icon = item.get("icon", "?")
            iw = fonts.get(FONT_SIZE_HINT, bold=True).size(icon)[0]
            draw_text(surf, icon, (16 + (36 - iw) // 2, y + 16), COLORS["bg"], FONT_SIZE_HINT, bold=True)
            draw_text(surf, item["label"], (62, y + 6), COLORS["text"], FONT_SIZE_BODY, bold=selected)
            draw_text(surf, item["value"], (62, y + 28), COLORS["text_dim"], FONT_SIZE_SMALL, max_width=SCREEN_WIDTH - 80)

        self.list.draw(surface, render_item)
        draw_footer(surface, [("Select", "A"), ("Back", "B")])


class ManageSystemsScreen(Screen):
    def __init__(self, app, settings_screen):
        super().__init__(app)
        self.settings_screen = settings_screen
        self.list = ListView(item_height=40)
        enabled = get_enabled_systems()
        self.enabled_dirs = set(s["dir"] for s in enabled)
        self.list.set_items(list(ALL_SYSTEMS))

    def handle_input(self, events):
        self.list.handle_input(events)
        for event in events:
            if event == InputEvent.BACK:
                set_enabled_systems(list(self.enabled_dirs))
                self.settings_screen._refresh_items()
                self.app.pop_screen()
            elif event == InputEvent.CONFIRM:
                item = self.list.get_selected()
                if item:
                    d = item["dir"]
                    if d in self.enabled_dirs:
                        self.enabled_dirs.discard(d)
                    else:
                        self.enabled_dirs.add(d)
            elif event == InputEvent.START:
                if len(self.enabled_dirs) == len(ALL_SYSTEMS):
                    self.enabled_dirs = set()
                else:
                    self.enabled_dirs = set(s["dir"] for s in ALL_SYSTEMS)

    def draw(self, surface):
        draw_header(surface, "Manage Systems")
        count = len(self.enabled_dirs)
        info = f"{count} enabled"
        draw_text(surface, info, (SCREEN_WIDTH - fonts.get(FONT_SIZE_SMALL).size(info)[0] - 12, CONTENT_Y + 4), COLORS["text_dim"], FONT_SIZE_SMALL)

        enabled_dirs = self.enabled_dirs

        def render_item(surf, item, idx, y, selected):
            on = item["dir"] in enabled_dirs
            box_color = COLORS["accent"] if on else COLORS["bg_lighter"]
            draw_rounded_rect(surf, box_color, (16, y + 8, 24, 24), 4)
            if on:
                draw_text(surf, "OK", (18, y + 12), COLORS["bg"], FONT_SIZE_HINT, bold=True)
            tag_bg = COLORS["bg_lighter"]
            draw_rounded_rect(surf, tag_bg, (48, y + 8, 36, 24), 4)
            tw = fonts.get(FONT_SIZE_HINT, bold=True).size(item["tag"])[0]
            draw_text(surf, item["tag"], (48 + (36 - tw) // 2, y + 12), COLORS["text_dim"], FONT_SIZE_HINT, bold=True)
            draw_text(surf, item["name"], (92, y + 10), COLORS["text"] if on else COLORS["text_dim"], FONT_SIZE_BODY, bold=selected)

        self.list.draw(surface, render_item)
        draw_footer(surface, [("Toggle", "A"), ("Back", "B"), ("All/None", "START")])


class SystemPathsScreen(Screen):
    def __init__(self, app, settings_screen):
        super().__init__(app)
        self.settings_screen = settings_screen
        self.list = ListView(item_height=44)
        self._refresh()

    def _refresh(self):
        custom = get_custom_paths()
        items = []
        for s in ALL_SYSTEMS:
            is_custom = s["dir"] in custom
            path = custom[s["dir"]] if is_custom else get_default_rom_path(s["dir"])
            items.append({
                "system": s,
                "path": path,
                "custom": is_custom,
            })
        self.list.set_items(items)

    def handle_input(self, events):
        self.list.handle_input(events)
        for event in events:
            if event == InputEvent.BACK:
                self.settings_screen._refresh_items()
                self.app.pop_screen()
            elif event == InputEvent.CONFIRM:
                item = self.list.get_selected()
                if item:
                    self.app.push_screen(EditPathScreen(self.app, item["system"], self))
            elif event == InputEvent.START:
                reset_all_paths()
                self._refresh()
                self.app.toast("All paths reset to default", COLORS["success"])

    def draw(self, surface):
        draw_header(surface, "System Paths")

        def render_item(surf, item, idx, y, selected):
            s = item["system"]
            tag_bg = COLORS["warning"] if item["custom"] else COLORS["bg_lighter"]
            draw_rounded_rect(surf, tag_bg, (14, y + 8, 36, 28), 5)
            tw = fonts.get(FONT_SIZE_HINT, bold=True).size(s["tag"])[0]
            draw_text(surf, s["tag"], (14 + (36 - tw) // 2, y + 13),
                       COLORS["bg"] if item["custom"] else COLORS["text_dim"], FONT_SIZE_HINT, bold=True)
            draw_text(surf, s["name"], (58, y + 4), COLORS["text"], FONT_SIZE_SMALL, bold=selected)
            path_color = COLORS["warning"] if item["custom"] else COLORS["text_dim"]
            draw_text(surf, item["path"], (58, y + 24), path_color, FONT_SIZE_HINT, max_width=SCREEN_WIDTH - 75)

        self.list.draw(surface, render_item)
        draw_footer(surface, [("Edit", "A"), ("Back", "B"), ("Reset All", "START")])


class EditPathScreen(Screen):
    def __init__(self, app, system, paths_screen):
        super().__init__(app)
        self.system = system
        self.paths_screen = paths_screen
        self.keyboard = OnScreenKeyboard()
        custom = get_custom_paths()
        if system["dir"] in custom:
            self.keyboard.text = custom[system["dir"]]
        else:
            self.keyboard.text = get_default_rom_path(system["dir"])
        self.selected_action = 0

    def handle_input(self, events):
        for event in events:
            if event == InputEvent.BACK:
                self.app.pop_screen()
                return
            if event == InputEvent.START:
                reset_custom_path(self.system["dir"])
                self.paths_screen._refresh()
                self.app.toast(f"Reset {self.system['name']} to default", COLORS["success"])
                self.app.pop_screen()
                return
        self.keyboard.handle_input(events)
        if self.keyboard.confirmed:
            path = self.keyboard.text.strip()
            if path:
                default = get_default_rom_path(self.system["dir"])
                if path == default:
                    reset_custom_path(self.system["dir"])
                else:
                    set_custom_path(self.system["dir"], path)
                self.paths_screen._refresh()
                self.app.toast(f"Path saved for {self.system['name']}", COLORS["success"])
                self.app.pop_screen()
            else:
                self.app.toast("Path cannot be empty", COLORS["error"])
            self.keyboard.confirmed = False

    def draw(self, surface):
        draw_header(surface, f"{self.system['name']} Path")
        default = get_default_rom_path(self.system["dir"])
        draw_text(surface, f"Default: {default}", (16, CONTENT_Y + 4), COLORS["text_dim"], FONT_SIZE_HINT)
        self.keyboard.draw(surface, CONTENT_Y + 22)
        draw_footer(surface, [("Type", "A"), ("Back", "B"), ("Reset", "START")])


class LoginEmailScreen(Screen):
    def __init__(self, app, settings_screen):
        super().__init__(app)
        self.settings_screen = settings_screen
        self.keyboard = OnScreenKeyboard()
        self.email = ""

    def handle_input(self, events):
        for event in events:
            if event == InputEvent.BACK:
                self.app.pop_screen()
                return
        self.keyboard.handle_input(events)
        if self.keyboard.confirmed:
            self.email = self.keyboard.text.strip()
            if self.email and "@" in self.email:
                self.app.push_screen(LoginPasswordScreen(self.app, self.email, self.settings_screen))
            else:
                self.app.toast("Enter a valid email", COLORS["error"])
            self.keyboard.confirmed = False

    def draw(self, surface):
        draw_header(surface, "Login - Email")
        draw_text(surface, "Enter your archive.org email:", (16, CONTENT_Y + 4), COLORS["text_dim"], FONT_SIZE_SMALL)
        self.keyboard.draw(surface, CONTENT_Y + 24)
        draw_footer(surface, [("Type", "A"), ("Back", "B")])


class LoginPasswordScreen(Screen):
    def __init__(self, app, email, settings_screen):
        super().__init__(app)
        self.email = email
        self.settings_screen = settings_screen
        self.keyboard = OnScreenKeyboard()
        self.task = None
        self.logging_in = False

    def handle_input(self, events):
        if self.logging_in:
            for event in events:
                if event == InputEvent.BACK:
                    self.app.pop_screen()
            return
        for event in events:
            if event == InputEvent.BACK:
                self.app.pop_screen()
                return
        self.keyboard.handle_input(events)
        if self.keyboard.confirmed:
            password = self.keyboard.text.strip()
            if password:
                self.logging_in = True
                from archive_api import AsyncTask, login
                self.task = AsyncTask(login, self.email, password)
            else:
                self.app.toast("Enter your password", COLORS["error"])
            self.keyboard.confirmed = False

    def update(self):
        if self.task and self.task.done:
            self.logging_in = False
            if self.task.error:
                self.app.toast(f"Error: {self.task.error}", COLORS["error"])
            elif self.task.result:
                result = self.task.result
                if result.get("success"):
                    self.app.toast("Logged in successfully!", COLORS["success"])
                    self.settings_screen._refresh_items()
                    self.app.pop_screen()
                    self.app.pop_screen()
                else:
                    self.app.toast(result.get("error", "Login failed"), COLORS["error"])
            self.task = None

    def draw(self, surface):
        draw_header(surface, "Login - Password")
        draw_text(surface, f"Email: {self.email}", (16, CONTENT_Y + 4), COLORS["text_dim"], FONT_SIZE_SMALL)
        if self.logging_in:
            draw_loading(surface, "Logging in")
        else:
            masked = "*" * len(self.keyboard.text) if self.keyboard.text else ""
            draw_text(surface, "Enter your password:", (16, CONTENT_Y + 22), COLORS["text_dim"], FONT_SIZE_SMALL)
            self.keyboard.draw(surface, CONTENT_Y + 40)
        draw_footer(surface, [("Type", "A"), ("Back", "B")])


class LogoutConfirmScreen(Screen):
    def __init__(self, app, settings_screen):
        super().__init__(app)
        self.settings_screen = settings_screen
        self.selected = 0

    def handle_input(self, events):
        for event in events:
            if event == InputEvent.UP or event == InputEvent.DOWN:
                self.selected = 1 - self.selected
            elif event == InputEvent.CONFIRM:
                if self.selected == 0:
                    from archive_api import clear_credentials
                    clear_credentials()
                    self.app.toast("Logged out", COLORS["text_dim"])
                    self.settings_screen._refresh_items()
                    self.app.pop_screen()
                else:
                    self.app.pop_screen()
            elif event == InputEvent.BACK:
                self.app.pop_screen()

    def draw(self, surface):
        draw_header(surface, "Logout")
        draw_text(surface, "Are you sure you want to log out?", (20, CONTENT_Y + 40), COLORS["text"], FONT_SIZE_BODY)
        from archive_api import load_credentials
        creds = load_credentials()
        if creds:
            draw_text(surface, f"Signed in as: {creds.get('email', '?')}", (20, CONTENT_Y + 70), COLORS["text_dim"], FONT_SIZE_SMALL)

        for i, label in enumerate(["Yes, log out", "Cancel"]):
            y = CONTENT_Y + 110 + i * 44
            if i == self.selected:
                draw_rounded_rect(surface, COLORS["accent_dark"], (16, y, SCREEN_WIDTH - 32, 38), 6)
            color = COLORS["error"] if i == 0 and self.selected == 0 else COLORS["text"]
            draw_text(surface, label, (30, y + 10), color, FONT_SIZE_BODY, bold=(i == self.selected))

        draw_footer(surface, [("Select", "A"), ("Back", "B")])


class App:
    def __init__(self, screen_surface):
        self.surface = screen_surface
        self.clock = pygame.time.Clock()
        self.input = InputHandler()
        self.running = True
        self.screen_stack = []
        self._toast_text = None
        self._toast_color = COLORS["text"]
        self._toast_time = 0

        from archive_api import DownloadManager, DownloadHistory
        self.history = DownloadHistory()
        self.download_manager = DownloadManager(history=self.history)

        init_fonts()
        self.push_screen(MainMenuScreen(self))

    def push_screen(self, screen):
        self.screen_stack.append(screen)
        screen.on_enter()

    def pop_screen(self):
        if len(self.screen_stack) > 1:
            self.screen_stack.pop()

    def toast(self, text, color=None):
        self._toast_text = text
        self._toast_color = color or COLORS["text"]
        self._toast_time = time.time()

    def quit(self):
        self.running = False

    def run(self):
        while self.running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
                    return

            self.input.update(events)
            input_events = self.input.get_events()

            if InputEvent.QUIT in input_events:
                self.running = False
                return

            current_screen = self.screen_stack[-1] if self.screen_stack else None
            if current_screen:
                current_screen.handle_input(input_events)
                current_screen.update()

            self.surface.fill(COLORS["bg"])
            if current_screen:
                current_screen.draw(self.surface)

            if self._toast_text and time.time() - self._toast_time < 2.5:
                self._draw_toast()
            elif self._toast_text:
                self._toast_text = None

            pygame.display.flip()
            self.clock.tick(FPS)

    def _draw_toast(self):
        alpha = 1.0
        elapsed = time.time() - self._toast_time
        if elapsed > 2.0:
            alpha = 1.0 - (elapsed - 2.0) / 0.5

        font = fonts.get(FONT_SIZE_BODY)
        tw, th = font.size(self._toast_text)
        padding = 16
        w = tw + padding * 2
        h = th + 12
        x = (SCREEN_WIDTH - w) // 2
        y = SCREEN_HEIGHT - FOOTER_HEIGHT - h - 10

        toast_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        bg_color = (*COLORS["bg_lighter"], int(220 * alpha))
        draw_rounded_rect(toast_surf, bg_color, (0, 0, w, h), 8)
        text_color = (*self._toast_color[:3], int(255 * alpha))
        rendered = font.render(self._toast_text, True, text_color)
        toast_surf.blit(rendered, (padding, 6))
        self.surface.blit(toast_surf, (x, y))
