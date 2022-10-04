import random
import sys
import time

import picounicorn
from math import ceil

picounicorn.init()


class Led:
    RED = (255, 50, 50)
    GREEN = (50, 255, 50)
    BLUE = (50, 50, 255)
    YELLOW = (255, 255, 50)
    PURPLE = (255, 50, 255)
    ORANGE = (255, 120, 50)
    GREY = (150, 150, 150)

    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color


class UnicornLeds:
    def __init__(self, w, h, speed=16):
        self.speed = speed  # Lower is slower
        self.uni_width = w
        self.uni_height = h
        self.leds = []
        self.leds_map = []
        self.deteriorate_speed = 10  # Lower is slower
        self.led_color_add = True
        for x in range(w):
            row = []
            for y in range(h):
                led = Led(x, y, (0, 0, 0))
                self.leds.append(led)
                row.append(led)
            self.leds_map.append(row)

    # Changes the speed of handling updates, in effect changing the speed with which worms move
    def change_speed(self, adjustment):
        self.speed = max(self.speed - adjustment, 1)

    def set_led_color(self, x, y, color, ignore_add=False):
        if self.led_color_add and not ignore_add:
            led = self.leds_map[x][y]
            new_color = []
            for i in range(3):
                added = led.color[i] + color[i]
                new_color.append(min(added, 255))
            self.leds_map[x][y].color = new_color
        else:
            self.leds_map[x][y].color = color

    def deteriorate(self):
        for led in self.leds:
            r, g, b = [max(color - self.deteriorate_speed, 0) for color in led.color]
            led.color = (r, g, b)

    def update_leds(self):
        for led in self.leds:
            picounicorn.set_pixel(led.x, led.y, *led.color)

    def wait_for_loop(self):
        time.sleep(1 / self.speed)


class Worm:
    EDGE_LEFT = 1
    EDGE_RIGHT = 2
    EDGE_TOP = 3
    EDGE_BOTTOM = 4
    MAX_AGE = 5000
    DYING_BOUNDARY = 1000
    AGE_SLOWDOWN = 6

    def __init__(self, leds: UnicornLeds):
        self.led_manager = leds
        self.x = random.randint(0, unicorn_leds.uni_width - 2)
        self.x_speed = 1
        self.y = random.randint(0, unicorn_leds.uni_height - 1)
        self.y_speed = 0
        self.turn_chance = 0.25
        self.worm_color = Led.BLUE
        self.age = 0
        self.wait_move = 0

    def wait_for_age(self):
        if self.is_dying():
            if self.wait_move == 0:
                inverted_life_left = self.DYING_BOUNDARY - self.life_left()
                quartile = (
                    ceil((inverted_life_left * self.AGE_SLOWDOWN) / self.DYING_BOUNDARY)
                    + 1
                )
                self.wait_move = quartile

            if self.wait_move > 0:
                self.wait_move -= 1

        return self.wait_move > 0

    def move(self):
        # Dying worms move slower

        if not self.wait_for_age():
            self.x = self.x + self.x_speed
            self.y = self.y + self.y_speed

        # Consider turning - this will not move us, only point the worm in another direction
        if self.is_ramming_edge() or self.want_to_turn():
            self.turn()
        self.draw_head(self.get_worm_color())
        if self.age < sys.maxsize - 1:
            self.age += 1

    def get_worm_color(self):
        life_left = self.life_left()
        if life_left < self.DYING_BOUNDARY:
            return self.age_worm_color(self.worm_color)
        else:
            return self.worm_color

    def age_worm_color(self, color):
        new_color = []
        average = sum(color) / len(color)
        invert_life_left = self.DYING_BOUNDARY - self.life_left()

        # Calculate how much to add or substract from each color to
        # make the worm appear to fade out
        fraction = round((average * invert_life_left) / self.DYING_BOUNDARY)
        for i in range(3):
            current_color = color[i]
            if current_color > average:
                # First go to grey. Fade the primary color down
                current_color = max(current_color - (2 * fraction), average)
            else:
                # And fade the secondary colors up
                current_color = min(current_color + fraction, average)
            # Finally, fade the entire color down
            new_color.append(round(max(current_color - fraction, 0)))
        return new_color

    def draw_head(self, color):
        try:
            self.led_manager.set_led_color(self.x, self.y, color)
        except IndexError:
            raise Exception(
                f"{__class__.__name__} out of bounds with X {self.x}, speed {self.x_speed}, Y {self.y}, speed {self.y_speed}"
            )

    def is_touching_edge(self, edge):
        is_touching = False
        if edge == self.EDGE_LEFT:
            is_touching = self.x == 0
        elif edge == self.EDGE_RIGHT:
            is_touching = self.x >= self.led_manager.uni_width - 1
        elif edge == self.EDGE_BOTTOM:
            is_touching = self.y == 0
        elif edge == self.EDGE_TOP:
            is_touching = self.y >= self.led_manager.uni_height - 1
        return is_touching

    def is_touching_any_edge(self):
        is_touching = False
        for is_touching_now in [
            self.EDGE_LEFT,
            self.EDGE_TOP,
            self.EDGE_RIGHT,
            self.EDGE_BOTTOM,
        ]:
            is_touching = is_touching or self.is_touching_edge(is_touching_now)
        return is_touching

    def is_ramming_edge(self):
        return (
            (self.is_touching_edge(self.EDGE_LEFT) and self.x_speed < 0)
            or (self.is_touching_edge(self.EDGE_RIGHT) and self.x_speed > 0)
            or (self.is_touching_edge(self.EDGE_BOTTOM) and self.y_speed < 0)
            or (self.is_touching_edge(self.EDGE_TOP) and self.y_speed > 0)
        )

    def turn(self):
        if self.x_speed != 0:
            self.x_speed = 0
            if self.is_touching_edge(self.EDGE_BOTTOM):
                self.y_speed = 1
            elif self.is_touching_edge(self.EDGE_TOP):
                self.y_speed = -1
            else:
                self.y_speed = self.decide_up_or_down()
        elif self.y_speed != 0:
            self.y_speed = 0
            if self.is_touching_edge(self.EDGE_LEFT):
                self.x_speed = 1
            elif self.is_touching_edge(self.EDGE_RIGHT):
                self.x_speed = -1
            else:
                self.x_speed = self.decide_left_or_right()

    def is_dead(self):
        return self.life_left() <= 0

    def life_left(self):
        return self.MAX_AGE - self.age

    def is_dying(self):
        return self.life_left() < self.DYING_BOUNDARY

    def want_to_turn(self):
        return random.random() < self.turn_chance

    def decide_up_or_down(self):
        return 1 if random.random() > 0.5 else -1

    def decide_left_or_right(self):
        return 1 if random.random() > 0.5 else -1


class TurnyWorm(Worm):
    def __init__(self, leds):
        super(TurnyWorm, self).__init__(leds)
        self.turn_chance = 0.6
        self.worm_color = Led.RED


class StraightWorm(Worm):
    def __init__(self, leds):
        super(StraightWorm, self).__init__(leds)
        self.turn_chance = 0.2
        self.worm_color = Led.BLUE


class WallWorm(Worm):
    def __init__(self, leds):
        super(WallWorm, self).__init__(leds)
        self.small_turn_chance = 0.1
        self.turn_chance = 0.6
        self.worm_color = Led.GREEN

    def want_to_turn(self):
        if self.is_touching_any_edge():
            return random.random() < self.small_turn_chance
        else:
            return random.random() < self.turn_chance


class RainbowWorm(Worm):
    RAINBOW_COLORS = [Led.RED, Led.ORANGE, Led.YELLOW, Led.GREEN, Led.BLUE, Led.PURPLE]

    def __init__(self, leds):
        super(RainbowWorm, self).__init__(leds)
        self.turn_chance = 0.3
        self.rainbow_index = 0

    def get_worm_color(self):
        color = self.RAINBOW_COLORS[self.rainbow_index]
        color = [max(rgb - 50, 0) for rgb in color]
        self.rainbow_index += 1
        self.rainbow_index %= len(self.RAINBOW_COLORS)
        color = self.age_worm_color(color)
        return color


class SlowWorm(Worm):
    def __init__(self, leds):
        super(SlowWorm, self).__init__(leds)
        self.turn_chance = 0.6
        self.worm_color = Led.PURPLE
        self.move_this_turn = True

    def move(self):
        if self.move_this_turn:
            self.move_this_turn = False
            super(SlowWorm, self).move()
        else:
            self.move_this_turn = True
            self.draw_head(self.get_worm_color())


class RedHeadWorm(Worm):
    def __init__(self, leds):
        super(RedHeadWorm, self).__init__(leds)
        self.worm_body_color = Led.GREY
        self.worm_color = Led.RED
        self.last_x = self.x
        self.last_y = self.y

    def move(self):
        # This worm jots down it's last position. We have the superclass draw our new led,
        # then we draw a grey led in our old position
        self.last_x = self.x
        self.last_y = self.y
        super(RedHeadWorm, self).move()
        self.led_manager.set_led_color(
            self.last_x, self.last_y, self.worm_body_color, ignore_add=True
        )


class ButtonPresses:
    def __init__(self):
        self.button_map = {
            picounicorn.BUTTON_A: False,
            picounicorn.BUTTON_B: False,
            picounicorn.BUTTON_X: False,
            picounicorn.BUTTON_Y: False,
        }

    def is_pressed(self, uni_button):
        result = False
        if picounicorn.is_pressed(uni_button) and not self.button_map[uni_button]:
            self.button_map[uni_button] = True
            result = True
        elif not picounicorn.is_pressed(uni_button):
            self.button_map[uni_button] = False
        return result

    def handle_buttons(self):
        # Button A adds a new worm
        if self.is_pressed(picounicorn.BUTTON_A):
            worm = random.choice(worm_collection)
            worms.append(worm(unicorn_leds))
        # Button B deletes the last added worm
        if self.is_pressed(picounicorn.BUTTON_B):
            if len(worms) > 0:
                worms.pop()
        # Button X slows everything down
        if self.is_pressed(picounicorn.BUTTON_X):
            unicorn_leds.change_speed(2)
        # And finally, button y speeds it up again
        if self.is_pressed(picounicorn.BUTTON_Y):
            unicorn_leds.change_speed(-2)


def clean_up_dead_worms():
    for worm in worms:
        if worm.is_dead():
            worms.remove(worm)
            worm = random.choice(worm_collection)
            worms.append(worm(unicorn_leds))


# Unicorn leds managed a matrix of virtual leds and manages the merging
# of colors. Changes are made there, before calling the update method that
# actually updates the screen.
unicorn_leds = UnicornLeds(picounicorn.get_width(), picounicorn.get_height())
worm_collection = [
    TurnyWorm,
    StraightWorm,
    WallWorm,
    SlowWorm,
    RainbowWorm,
    RedHeadWorm,
]

worms = [worm(unicorn_leds) for worm in worm_collection]
buttons = ButtonPresses()
while True:
    buttons.handle_buttons()

    dead_worms = []
    for worm in worms:
        # This moves the worm and tells unicorn_leds what to light up
        worm.move()
    clean_up_dead_worms()

    # Here we darken all leds a little
    unicorn_leds.deteriorate()

    # And this function finally sends the leds to the screen
    unicorn_leds.update_leds()

    unicorn_leds.wait_for_loop()
