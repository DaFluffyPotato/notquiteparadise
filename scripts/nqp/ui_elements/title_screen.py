from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pygame
import pygame_gui
from pygame import Rect
from pygame_gui.core import ObjectID
from pygame_gui.elements import UIButton

from scripts.engine.internal.constant import RenderLayer
from scripts.engine.internal.event import event_hub, ExitGameEvent, LoadGameEvent, NewGameEvent
from scripts.engine.widgets.panel import Panel

if TYPE_CHECKING:
    from typing import List

    from pygame_gui import UIManager

__all__ = ["TitleScreen"]


class TitleScreen(Panel):
    """
    Initial screen menu
    """

    def __init__(self, rect: Rect, manager: UIManager):

        self.button_events = {
            "new_game": NewGameEvent(),
            "load_game": LoadGameEvent(),
            "exit_game": ExitGameEvent(),
        }

        self.buttons: List[UIButton] = []

        # complete base class init
        super().__init__(rect, RenderLayer.BOTTOM, manager, object_id=ObjectID("#title_screen", "@menu_screen"))

        self._init_buttons()

        # confirm init complete
        logging.debug(f"TitleScreen initialised.")

    def process_event(self, event):
        super().process_event(event)

        # only progress for user events
        if event.type != pygame.USEREVENT:
            return

        if event.user_type == pygame_gui.UI_BUTTON_PRESSED:

            # Find out which button we are clicking
            button = event.ui_element

            # post the new event
            if button in self.buttons:
                # get the id
                ids = event.ui_object_id.split(".")
                button_id = ids[-1]  # get last element
                new_event = self.button_events[button_id]
                event_hub.post(new_event)

                logging.debug(f"TitleScreen button '{button_id}' pressed.")

    def _init_buttons(self):
        """
        Init the buttons for the menu
        """
        info = self.button_events
        manager = self.ui_manager

        # set button dimensions
        max_width = self.rect.width
        max_height = self.rect.height
        height = int(max_height / 8)
        width = int(max_width / 4)
        x = int((max_width / 2) - (width / 2))
        start_y = int(max_height / 4)
        gap = int(((max_height - start_y) / len(info)) - height)

        count = 0
        for name in info.keys():
            y = start_y + ((height + gap) * count)
            friendly_name = name.replace("_", " ")

            button = UIButton(
                relative_rect=Rect((x, y), (width, height)),
                text=friendly_name.title(),
                manager=manager,
                container=self,
                object_id=f"{name}",
            )

            self.buttons.append(button)

            count += 1
