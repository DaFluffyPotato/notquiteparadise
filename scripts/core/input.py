import pygame

from scripts.core.constants import GameStates, TILE_SIZE, MessageEventTypes
from scripts.core.global_data import entity_manager, game_manager, ui_manager, world_manager, debug_manager
from scripts.events.entity_events import UseSkillEvent, MoveEvent
from scripts.events.game_events import ExitEvent, ChangeGameStateEvent
from scripts.events.message_events import MessageEvent


def get_input():
    """
    Get the pygame event, update the input_values dictionary and return input_values.

    Returns:
        Dict[] : `input_values` containing True for all appropriate inputs, and Tuple[int,int] for the `mouse_xy`.

    """
    # gets mouse and key input as list of events
    input_events = pygame.event.get()

    # init input values
    input_values = {
        "left_click": False,
        "right_click": False,
        "middle_click": False,
        "mouse_xy": (0, 0),
        "up": False,
        "down": False,
        "left": False,
        "right": False,
        "up_right": False,
        "up_left": False,
        "down_right": False,
        "down_left": False,
        "wait": False,
        "interact": False,
        "inventory": False,
        "drop": False,
        "character": False,
        "fullscreen": False,
        "cancel": False,
        "new_game": False,
        "load_game": False,
        "debug_toggle": False,
        "first_skill": False

    }

    # check all input events
    for input in input_events:

        # update MOUSE input values based on input
        # TODO: move each set of event typ eto its own function
        if input.type == pygame.MOUSEBUTTONDOWN:
            check_mouse_input(input_values)

        # is a key pressed?
        if input.type == pygame.KEYDOWN:

            # update OTHER input values based on input
            if input.key == pygame.K_UP or input.key == pygame.K_KP8 or input.key == pygame.K_k:
                input_values["up"] = True
            elif input.key == pygame.K_DOWN or input.key == pygame.K_KP2 or input.key == pygame.K_j:
                input_values["down"] = True
            elif input.key == pygame.K_LEFT or input.key == pygame.K_KP4 or input.key == pygame.K_h:
                input_values["left"] = True
            elif input.key == pygame.K_RIGHT or input.key == pygame.K_KP6 or input.key == pygame.K_l:
                input_values["right"] = True
            elif input.key == pygame.K_KP7 or input.key == pygame.K_y:
                input_values["up_left"] = True
            elif input.key == pygame.K_KP9 or input.key == pygame.K_u:
                input_values["up_right"] = True
            elif input.key == pygame.K_KP1 or input.key == pygame.K_b:
                input_values["down_left"] = True
            elif input.key == pygame.K_KP3 or input.key == pygame.K_n:
                input_values["down_right"] = True
            elif input.key == pygame.K_z or input.key == pygame.K_KP5:
                input_values["wait"] = True
            elif input.key == pygame.K_i:
                input_values["inventory"] = True
            elif input.key == pygame.K_d:
                input_values["drop"] = True
            elif input.key == pygame.K_RETURN:
                input_values["interact"] = True
            elif input.key == pygame.K_c:
                input_values["character"] = True
            elif input.key == pygame.K_RETURN and pygame.K_LALT:
                # Alt+Enter: toggle full screen
                input_values["fullscreen"] = True
            elif input.key == pygame.K_ESCAPE:
                input_values["cancel"] = True
            elif input.key == pygame.K_a:
                # TODO remove this legacy when menu's can use kb+m
                input_values["new_game"] = True
            elif input.key == pygame.K_b:
                # TODO remove this legacy when menu's can use kb+m
                input_values["load_game"] = True
            elif input.key == pygame.K_TAB:
                input_values["debug_toggle"] = True
            elif input.key == pygame.K_1:
                input_values["first_skill"] = True

    return input_values


def handle_input(values):
    """
    Process the user input into game action by interpreting the value in relation to the `GameState`.

    Args:
        values (Dict[]): User input events.

    """
    game_state = game_manager.game_state
    player = entity_manager.player

    # game state agnostic
    if game_state:
        if values["debug_toggle"]:
            if debug_manager.visible:
                debug_manager.set_visibility(False)
            else:
                debug_manager.set_visibility(True)

    if game_state == GameStates.PLAYER_TURN:
        handle_player_turn_input(values)

    if game_state == GameStates.TARGETING_MODE:
        handle_targeting_mode_input(values)

    if game_state == GameStates.PLAYER_DEAD:
        if values["inventory"]:
            return {"show_inventory": True}
        elif values["fullscreen"]:
            return {"fullscreen": True}
        elif values["cancel"]:
            return {"exit": True}


def check_mouse_input(input_values):
    """

    Args:
        input_values:
    """

    if pygame.mouse.get_pressed()[0]:
        input_values["left_click"] = True
    elif pygame.mouse.get_pressed()[1]:
        input_values["middle_click"] = True
    elif pygame.mouse.get_pressed()[2]:
        input_values["right_click"] = True

    input_values["mouse_xy"] = ui_manager.get_scaled_mouse_pos()


def handle_player_turn_input(input_values):
    """

    Args:
        input_values:

    """
    values = input_values
    player = entity_manager.player

    if values["right_click"]:
        pos = values["mouse_xy"]
        for key, rect in ui_manager.visible_panels.items():
            if rect.collidepoint(pos):
                clicked_rect = key

        # right clicked on the map so give the selected tile to the ui manager to display info
        if clicked_rect == "game_map":
            tile_pos = ui_manager.get_relative_scaled_mouse_pos(clicked_rect)
            tile_x = tile_pos[0] // TILE_SIZE
            tile_y = tile_pos[1] // TILE_SIZE
            entity = entity_manager.query.get_entity_in_fov_at_tile(tile_x, tile_y)

            if entity:
                ui_manager.entity_info.set_selected_entity(entity)

    direction_x = 0
    direction_y = 0

    if values["up"]:
        direction_x = 0
        direction_y = -1
    elif values["down"]:
        direction_x = 0
        direction_y = 1
    elif values["left"]:
        direction_x = -1
        direction_y = 0
    elif values["right"]:
        direction_x = 1
        direction_y = 0
    elif values["up_left"]:
        direction_x = -1
        direction_y = -1
    elif values["up_right"]:
        direction_x = 1
        direction_y = -1
    elif values["down_left"]:
        direction_x = -1
        direction_y = 1
    elif values["down_right"]:
        direction_x = 1
        direction_y = 1

    # if destination isn't 0 then we need to move player
    if direction_x != 0 or direction_y != 0:
        target_x, target_y = direction_x + player.x, direction_y + player.y

        # is there something in the way?
        in_bounds = world_manager.game_map.is_tile_in_bounds(target_x, target_y)
        tile_blocking_movement = world_manager.game_map.is_tile_blocking_movement(target_x, target_y)
        entity_blocking_movement = entity_manager.query.get_blocking_entity_at_location(target_x, target_y)

        if in_bounds and not tile_blocking_movement:
            if not entity_blocking_movement:
                # nothing in the way, time to move!
                game_manager.create_event(MoveEvent(player, (target_x, target_y)))
            else:
                game_manager.create_event((UseSkillEvent(player, (target_x, target_y), "basic_attack")))
        else:
            msg = f"You can't do that there!"
            game_manager.create_event(MessageEvent(MessageEventTypes.BASIC, msg))

    if values["first_skill"]:
        mouse_x, mouse_y = ui_manager.get_relative_scaled_mouse_pos("game_map")
        target_x, target_y = world_manager.convert_xy_to_tile(mouse_x, mouse_y)

        # if no entity on spot then pass empty target to skill
        if entity_manager.query.get_blocking_entity_at_location(target_x, target_y) is None:
            target_x, target_y = 0, 0

        game_manager.create_event((UseSkillEvent(player, (target_x, target_y), "basic_attack")))
        # TODO - update  to skill slot use, not specify basic skill

    if values["wait"]:
        # TODO - add wait
        pass

    elif values["cancel"]:
        game_manager.create_event(ExitEvent())


def handle_targeting_mode_input(input_values):
    """

    Args:
        input_values:
    """
    values = input_values

    if values["cancel"]:
        previous_state = game_manager.previous_game_state
        game_manager.create_event(ChangeGameStateEvent(previous_state))
