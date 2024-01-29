import os
import time
import threading
import pygame


class ButtonHandler:

    def __init__(self):
        self.enter_gpio = 139
        self.up_gpio = 63
        self.down_gpio = 43
        self.back_gpio = 138
        self.up_button_pressed = False
        self.down_button_pressed = False
        self.enter_button_pressed = False
        self.back_button_pressed = False

        self.up_was_pressed = False
        self.down_was_pressed = False
        self.enter_was_pressed = False
        self.back_was_pressed = False

        gpio_export_file = '/sys/class/gpio/export'
        os.chmod(gpio_export_file, 0o222)
        self._export_gpio(gpio_export_file, self.up_gpio)
        self._export_gpio(gpio_export_file, self.down_gpio)
        self._export_gpio(gpio_export_file, self.enter_gpio)
        self._export_gpio(gpio_export_file, self.back_gpio)

        self.button_thread = threading.Thread(target=self._button_thread)
        self.button_thread.start()

    def _export_gpio(self, gpio_export_file, gpio_num):
        if not os.path.exists(f'/sys/class/gpio/gpio{gpio_num}'):
            with open(gpio_export_file, "w") as f:
                f.write(f'{gpio_num}')

    def _read_gpio_value(self, gpio_num):
        with open(f'/sys/class/gpio/gpio{gpio_num}/value', 'r') as f:
            val = f.read()
            return val

    def _post_pygame_event(self, key):
        newevent = pygame.event.Event(
            pygame.KEYDOWN, key=key,
            mod=pygame.locals.KMOD_NONE)  #create the event
        pygame.event.post(newevent)  #add the event to the queue

    # Records the press and release of buttons on the AI Box. In order to record
    # a button press, the button must be pressed and held for at least 0.1 seconds
    # and then released.
    def _button_thread(self):
        while True:
            up_val = self._read_gpio_value(self.up_gpio)
            down_val = self._read_gpio_value(self.down_gpio)
            enter_val = self._read_gpio_value(self.enter_gpio)
            back_val = self._read_gpio_value(self.back_gpio)

            up_pressed = '0' in up_val
            down_pressed = '0' in down_val
            enter_pressed = '0' in enter_val
            back_pressed = '0' in back_val

            up_released = self.up_was_pressed and not up_pressed
            down_released = self.down_was_pressed and not down_pressed
            enter_released = self.enter_was_pressed and not enter_pressed
            back_released = self.back_was_pressed and not back_pressed

            self.up_was_pressed = up_pressed
            self.down_was_pressed = down_pressed
            self.enter_was_pressed = enter_pressed
            self.back_was_pressed = back_pressed

            if up_released:
                self._post_pygame_event(pygame.locals.K_UP)
            if down_released:
                self._post_pygame_event(pygame.locals.K_DOWN)
            if enter_released:
                self._post_pygame_event(pygame.locals.K_RETURN)
            if back_released:
                self._post_pygame_event(pygame.locals.K_ESCAPE)

            self.up_button_pressed = self.up_button_pressed or up_released
            self.down_button_pressed = self.down_button_pressed or down_released
            self.enter_button_pressed = self.enter_button_pressed or enter_released
            self.back_button_pressed = self.back_button_pressed or back_released
            time.sleep(0.01)

    def up_pressed(self):
        ret = self.up_button_pressed
        self.up_button_pressed = False
        return ret

    def down_pressed(self):
        ret = self.down_button_pressed
        self.down_button_pressed = False
        return ret

    def enter_pressed(self):
        ret = self.enter_button_pressed
        self.enter_button_pressed = False
        return ret

    def back_pressed(self):
        ret = self.back_button_pressed
        self.back_button_pressed = False
        return ret

    def clear(self):
        self.up_button_pressed = False
        self.down_button_pressed = False
        self.enter_button_pressed = False
