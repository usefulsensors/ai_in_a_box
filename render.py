import pygame

from fontfile import lang_to_font
from volume_file import get_current_volume, set_current_volume
import pygame_menu


# Maintains a landscape oriented surface to write to. Translates and rotates
# this surface behind the scenes to correctly display on portrait mode display.
class BaseDisplay:

    def __init__(self):
        pygame.display.init()
        pygame.font.init()

        # Override get_init() so that pygame-menu works as expeted without needing to initailize
        # all pygame submodules.
        def get_init():
            return True

        pygame.get_init = get_init
        pygame.mouse.set_visible(0)
        display, width, height = self.get_correct_display()
        self.display = pygame.display.set_mode((height, width),
                                               pygame.FULLSCREEN,
                                               display=display)
        # Rotated 90 degrees to the right
        self.surface = pygame.Surface((1280, 720))
        self.clear()

    def get_correct_display(self):
        resolutions = pygame.display.get_desktop_sizes()
        for idx, res in enumerate(resolutions):
            if res[0] != 720 or res[1] != 1280:
                self.rotate = False
                return idx, 720, 1280
        self.rotate = True
        return 0, 1280, 720

    def clear(self):
        self.surface.fill("black")
        self.flip()

    def flip(self):
        surface = self.surface
        if self.rotate:
            surface = pygame.transform.rotate(surface, -90)
        self.display.blit(surface, (0, 0))
        pygame.display.flip()

    def update(self, rect):
        surface = self.surface
        if self.rotate:
            surface = pygame.transform.rotate(surface, -90)
        self.display.blit(surface, (0, 0))
        pygame.display.update((rect[1], rect[0], rect[3], rect[2]))

    def blit(self, surface, dst):
        self.surface.blit(surface, dst)

    def height(self):
        return self.surface.get_height()

    def width(self):
        return self.surface.get_width()


class TextWindow:

    def __init__(self, display, rect, text_size, text_color, fontfile):
        self.display = display
        self.rect = rect
        self.text_size = text_size
        self.text_color = text_color
        self.fontfile = fontfile
        sample_text = self.render_text("Testing")
        self.text_height = sample_text.get_height()
        self.left, self.top, self.width, self.height = rect
        self.surface = pygame.Surface((self.width, self.height))
        self.n_lines = max(1, int(self.height / self.text_height))
        self.lines = [[] for i in range(int(self.n_lines))]
        self.current_line = 0
        self.x_offset = 0

    def render_text(self, text):
        font = pygame.font.Font(self.fontfile, self.text_size)
        return font.render(text, True, self.text_color)

    def scroll(self):
        print(f' scrolling cur line {self.current_line} n lines {self.n_lines}')
        if self.current_line >= self.n_lines - 1:
            self.surface.scroll(dy=-self.text_height)
        self.current_line = min(self.current_line + 1, self.n_lines - 1)
        clear_top = self.text_height * (self.n_lines - 1)
        pygame.draw.rect(self.surface, (0, 0, 0),
                         (0, clear_top, self.width, self.text_height))

        self.lines.insert(0, [])
        self.lines = self.lines[:self.n_lines]
        self.x_offset = 0

    def addWord(self, word, add_spaces=True, update=True):
        # Catch escape characters for a new line.  LLM may pass others.
        if word == '\n' or word == '\r' or word == '\r\n':
            self.scroll()
            word = ''

        cur = self.lines[0]
        word_to_add = word + ' ' if add_spaces else word
        text = self.render_text(word_to_add)
        if self.x_offset + text.get_width() > self.width:
            self.scroll()

        self.lines[0].append(word_to_add)

        line_offset = min(self.n_lines - 1, self.current_line)
        y_offset = line_offset * self.text_height
        self.surface.blit(text, (self.x_offset, y_offset))
        self.display.blit(self.surface, (self.left, self.top))
        if update:
            rect = [
                self.left + self.x_offset, self.top + y_offset,
                text.get_width(),
                text.get_height()
            ]
            self.display.flip()  #update(rect)
        self.x_offset += text.get_width()

    def addWords(self, words, add_spaces=True, update=True):
        for word in words:
            self.addWord(word, add_spaces=add_spaces, update=update)

    def updateNLines(self, lines_cleared, new_words):
        clear_height = lines_cleared * self.text_height
        self.current_line = self.current_line - lines_cleared + 1 if self.current_line >= lines_cleared else 0
        y_offset = self.current_line * self.text_height
        pygame.draw.rect(self.surface, (0, 0, 0),
                         (0, y_offset, self.width, clear_height))
        self.x_offset = 0
        lines_to_update = self.lines[:lines_cleared]
        line_lengths = [len(line) for line in lines_to_update
                       ]  #[len(line) for line in self.lines[:lines_cleared]]
        words_to_update = sum(line_lengths)

        self.lines = self.lines[lines_cleared:]
        self.lines.insert(0, [])
        for _ in range(lines_cleared - 1):
            self.lines.append([])
        new_words = new_words if words_to_update >= len(
            new_words) else new_words[-words_to_update:]
        self.addWords(new_words, update=False)
        rect = [self.left, self.top + y_offset, self.width, clear_height]
        self.display.update(rect)

    def clear(self):
        pygame.draw.rect(self.surface, (0, 0, 0),
                         (0, 0, self.width, self.height))
        self.x_offset = 0
        self.current_line = 0
        self.display.blit(self.surface, (self.left, self.top))
        self.display.flip()


class SingleScreenRenderer:

    def __init__(self, display):
        self.display = display
        self.window = TextWindow(display,
                                 rect=(50, 50, 1180, 620),
                                 text_color=(255, 255, 255),
                                 fontfile=lang_to_font('english'),
                                 text_size=70)

    def clear(self):
        self.display.clear()
        self.window.clear()

    def addWord(self, word, add_spaces=True):
        self.window.addWord(word, add_spaces=add_spaces)

    def scroll(self):
        self.window.scroll()

    def addWords(self, words):
        self.window.addWords(words)

    def updateNLines(self, n_lines, new_words):
        self.window.updateNLines(n_lines, new_words)

    def update(self):
        self.display.flip()


class SplitScreenRenderer:

    def __init__(self, base_display):
        self.display = base_display
        self.src_lang = None
        self.tgt_lang = None

    def setLanguages(self, src_lang, tgt_lang, draw=True):
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang
        if draw:
            self.update()

    def update(self):
        src_lang = self.src_lang
        tgt_lang = self.tgt_lang
        self.top_title_window = TextWindow(self.display,
                                           rect=(50, 10, 1180, 100),
                                           text_size=70,
                                           text_color=(220, 100, 100),
                                           fontfile=lang_to_font('english'))
        self.bottom_title_window = TextWindow(self.display,
                                              rect=(50, 360, 1180, 100),
                                              text_size=70,
                                              text_color=(220, 100, 100),
                                              fontfile=lang_to_font('english'))
        self.top_window = TextWindow(self.display,
                                     rect=(50, 110, 1180, 250),
                                     text_size=70,
                                     text_color=(255, 255, 255),
                                     fontfile=lang_to_font(src_lang))
        self.bottom_window = TextWindow(self.display,
                                        rect=(50, 460, 1180, 250),
                                        text_size=70,
                                        text_color=(100, 255, 100),
                                        fontfile=lang_to_font(tgt_lang))

        src_lang = src_lang[0].upper() + src_lang[1:]
        tgt_lang = tgt_lang[0].upper() + tgt_lang[1:]
        self.top_title_window.addWord(src_lang)
        self.bottom_title_window.addWord(tgt_lang)

    def is_cjk(self, character):
        return any([
            start <= ord(character) <= end
            for start, end in [(4352, 4607), (11904, 42191), (
                43072,
                43135), (44032,
                         55215), (63744,
                                  64255), (65072,
                                           65103), (65381,
                                                    65500), (131072, 196607)]
        ])

    def addTextTop(self, text):
        is_cjk = self.is_cjk(text[0])
        words = text if is_cjk else text.split()
        self.top_window.addWords(words, add_spaces=not is_cjk)

    def addTextBottom(self, text, add_spaces=True):
        is_cjk = self.is_cjk(text[0])
        words = text if is_cjk else text.split()
        self.bottom_window.addWords(words, add_spaces=not is_cjk)

    def clear(self):
        self.display.clear()
        self.top_title_window.clear()
        self.top_window.clear()
        self.bottom_title_window.clear()
        self.bottom_window.clear()

    def clearTop(self):
        self.top_window.clear()

    def clearBottom(self):
        self.bottom_window.clear()


class MainMenu:

    def __init__(self, display, src_langs, tgt_langs):
        self.language_menu = LanguageMenu(display, src_langs, tgt_langs)
        self.volume_menu = VolumeMenu(display)
        self.main_menu = pygame_menu.Menu(
            height=620,
            theme=pygame_menu.themes.THEME_BLUE,
            title='Main Menu',
            width=350,
            position=(100, 8, True),
        )

        self.main_menu.add.button('Set Volume', self.set_volume)
        self.main_menu.add.button('Select Languages', self.select_languages)
        self.main_menu.add.button('Back', self.back)

        self.volume = 50
        self.src_lang = None
        self.tgt_lang = None
        self.display = display

    def set_volume(self):
        self.volume = self.volume_menu.open_menu()

    def select_languages(self):
        self.src_lang, self.tgt_lang = self.language_menu.open_menu()

    def back(self):
        self.should_close = True

    def open_menu(self):
        events = pygame.event.clear()
        clock = pygame.time.Clock()
        self.should_close = False
        while not self.should_close:
            clock.tick(60)
            events = pygame.event.get()
            if self.main_menu.is_enabled():
                self.main_menu.update(events)
                self.main_menu.draw(self.display.surface)
                self.display.flip()

            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.locals.K_UP:
                        self.main_menu._down()
                    elif event.key == pygame.locals.K_DOWN:
                        self.main_menu._up()
                    elif event.key == pygame.locals.K_ESCAPE:
                        self.should_close = True
        return self.volume, self.src_lang, self.tgt_lang


class VolumeMenu:

    def __init__(self, display):
        self.display = display
        self.volume = get_current_volume()

    def open_menu(self):
        menu = pygame_menu.Menu(height=620,
                                theme=pygame_menu.themes.THEME_BLUE,
                                title='Volume (%)',
                                width=350,
                                position=(100, 8, True))

        for vol in [100, 75, 50, 25, 0]:
            menu.add.button(vol, self.select_volume, vol)

        events = pygame.event.clear()
        clock = pygame.time.Clock()
        while True:
            clock.tick(60)
            events = pygame.event.get()
            if menu.is_enabled():
                menu.update(events)
                menu.draw(self.display.surface)
                self.display.flip()

            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.locals.K_UP:
                        menu._down()
                    elif event.key == pygame.locals.K_DOWN:
                        menu._up()
                    elif event.key == pygame.locals.K_RETURN:
                        return self.volume
                    elif event.key == pygame.locals.K_ESCAPE:
                        return None

    def select_volume(self, volume):
        self.volume = volume
        volume_map = {100: 100, 75: 25, 50: 8, 25: 2, 0: 0}
        adjusted_volume = volume_map[volume]
        set_current_volume(adjusted_volume)


class LanguageMenu:

    def __init__(self, display, src_langs, tgt_langs):
        self.display = display
        self.src_langs = src_langs
        self.tgt_langs = tgt_langs
        self.selected_item = None

    def menu_loop(self, menu):
        events = pygame.event.clear()
        clock = pygame.time.Clock()
        while True:
            clock.tick(60)
            events = pygame.event.get()
            if menu.is_enabled():
                menu.update(events)
                menu.draw(self.display.surface)
                self.display.flip()

            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.locals.K_UP:
                        menu._down()
                    elif event.key == pygame.locals.K_DOWN:
                        menu._up()
                    elif event.key == pygame.locals.K_RETURN:
                        return self.selected_item
                    elif event.key == pygame.locals.K_ESCAPE:
                        return None

    def open_menu(self):
        src_lang_menu = pygame_menu.Menu(
            height=620,
            theme=pygame_menu.themes.THEME_BLUE,
            title='Source Language',
            width=350,
            position=(100, 8, True),
        )

        tgt_lang_menu = pygame_menu.Menu(height=620,
                                         theme=pygame_menu.themes.THEME_BLUE,
                                         title='Target Language',
                                         width=350,
                                         position=(100, 8, True))

        for lang in self.src_langs:
            src_lang_menu.add.button(lang, self.select_item, lang)

        for lang in self.tgt_langs:
            tgt_lang_menu.add.button(lang, self.select_item, lang)

        source_lang = self.menu_loop(src_lang_menu)
        target_lang = self.menu_loop(tgt_lang_menu)
        if source_lang and target_lang:
            return source_lang, target_lang
        else:
            return None, None

    def select_item(self, item):
        self.selected_item = item
