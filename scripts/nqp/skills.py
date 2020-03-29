from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Type

from snecs.typedefs import EntityID

from scripts.engine import world, utility, act, existence
from scripts.engine.component import Position, Resources, HasCombatStats
from scripts.engine.core.constants import Direction, BASE_ACCURACY, PrimaryStat, Shape, TargetTag, BASE_DAMAGE, \
    DamageType, DirectionType, ProjectileSpeed, TravelMethod, TerrainCollision, ProjectileExpiry, ResourceType, \
    Resource, TargetingMethodType, TargetTagType, TargetingMethod, ShapeType, PrimaryStatType, DamageTypeType
from scripts.engine.core.definitions import EffectData, DamageEffectData, ProjectileData, MoveActorEffectData
from scripts.engine.effect import DamageEffect
from scripts.engine.library import library
from scripts.engine.world_objects.tile import Tile

if TYPE_CHECKING:
    from typing import Union, Optional, Any, Tuple, Dict, List


# TODO - current problem:
#  wants target_entity on init but we need other values earlier
#  need to give entity an instance and change the relevant methods to take the entity at the moment we have a target


class Skill(ABC):
    """
    A subclass of Skill represents a skill and holds all the data that is
    not dependent on the individual cast - stuff like shape, base accuracy,
    etc etc.

    An instance of Skill represents an individual use of that skill,
    and holds only the data that is tied to the individual use - stuff like
    the user and target.
    """

    def __init__(self, user: EntityID, target_tile: Tile, description: str, icon_path: str,
            required_tags: List[TargetTagType], resource_type: ResourceType, resource_cost: int, time_cost: int,
            max_cooldown: int, targeting_method: TargetingMethodType, target_directions: List[DirectionType],
            shape: ShapeType, shape_size: int):

        # state
        self.cooldown = 0

        # to be provided by instance
        self.user = user
        self.target_tile = target_tile

        # to be overwritten in subclass
        self.description: str = description
        self.icon_path: str = icon_path
        self.required_tags: List[TargetTagType] = required_tags
        self.resource_type: ResourceType = resource_type
        self.resource_cost: int = resource_cost
        self.time_cost: int = time_cost
        self.max_cooldown: int = max_cooldown
        self.targeting_method: TargetingMethodType = targeting_method
        self.target_directions: List[DirectionType] = target_directions
        self.shape: ShapeType = shape
        self.shape_size: int = shape_size

    def get_affected_entities(self):
        """
        Return a list of entities that this particular cast affects.

        Note that these aren't necessarily only entities that got hit - hit calculation should be done in build_effects
        """
        affected_entities = []
        affected_positions = []
        target_x = self.target_tile.x
        target_y = self.target_tile.y

        # get affected tiles
        coords = utility.get_coords_from_shape(self.shape, self.shape_size)
        for coord in coords:
            affected_positions.append((coord[0] + target_x, coord[1] + target_y))

        # get relevant entities in target area
        for entity, (position, *others) in existence.get_components([Position, Resources, HasCombatStats]):
            if (position.x, position.y) in affected_positions:
                affected_entities.append(entity)

        return affected_entities

    def apply(self):
        """
        An iterator over pairs of (affected entity, [effects])
        """
        for entity in self.get_affected_entities():
            yield entity, self.build_effects(entity)

    @abstractmethod
    def build_effects(self, entity):
        """
        Build the effects of this skill applying to a single entity.
        """
        pass


class BasicAttack(Skill):
    def __init__(self, user, target_tile):
        description = "this is the basic attack."
        icon_path = "assets/skills/placeholder/basic_attack.png"
        required_tags = [TargetTag.OTHER_ENTITY]
        resource_type = Resource.STAMINA
        resource_cost = 5
        time_cost = 30
        cooldown = 1
        targeting_method = TargetingMethod.TARGET
        target_directions = [
            Direction.UP_LEFT,
            Direction.UP,
            Direction.UP_RIGHT,
            Direction.LEFT,
            Direction.CENTRE,
            Direction.RIGHT,
            Direction.DOWN_LEFT,
            Direction.DOWN,
            Direction.DOWN_RIGHT
        ]
        shape = Shape.TARGET
        shape_size = 1

        super().__init__(user, target_tile, description, icon_path, required_tags, resource_type, resource_cost,
                         time_cost, cooldown, targeting_method, target_directions, shape, shape_size)

    def build_effects(self, entity):
        """
        Build the effects of this skill applying to a single entity.
        """
        damage_effect = DamageEffect(
            origin=self.user,
            victim=entity,
            stat_to_target=PrimaryStat.VIGOUR,
            accuracy=BASE_ACCURACY,
            damage=BASE_DAMAGE,
            damage_type=DamageType.MUNDANE,
            mod_stat=PrimaryStat.CLOUT,
            mod_amount=0.1,
            success_effects=[],
            failure_effects=[]
        )

        return [damage_effect]














            ################# EXAMPLES ################################
########## "use" a projectile ###########################
#         _name = self.name + "s projectile"
#         _desc = existence.get_name(self.entity) + self.name + "s projectile"
#         proj_data = ProjectileData(
#             creators_name=self.entity,
#             skill_name=self.name,
#             name=_name,
#             description=_desc,
#             sprite="skills/placeholder/icon_01.png",
#             required_tags=[TargetTag.OTHER_ENTITY],
#             speed=ProjectileSpeed.SLOW,
#             travel_type=TravelMethod.STANDARD,
#             range=3,
#             terrain_collision=TerrainCollision.FIZZLE,
#             expiry_type=ProjectileExpiry.FIZZLE
#         )
#
#         for tile, direction in use_tiles_and_directions:
#             proj_data.direction = direction
#             existence.create_projectile(self.entity, tile.x, tile.y, proj_data)
#
############### "use" without projectile ###############
#         tiles = []
#         for tile, direction in use_tiles_and_directions:
#             tiles.append(tile)
#         self.activate(tiles)
#########################################################


class BaseSkill(ABC):
    def __init__(self, name: str, owning_entity: EntityID):
        self.name = name
        self.entity = owning_entity
        self.cooldown = 0

    def get_use_tiles_and_directions(self, start_position: Tuple[int, int],
            target_position: Tuple[int, int]) -> List[Optional[Tuple[Tile, DirectionType]]]:
        """
        Get the target tiles and relative directions
        """
        target_tiles = []
        data = library.get_skill_data(self.name)
        tags = data.use_required_tags

        # target centre of target pos
        tiles = world.get_tiles(target_position[0], target_position[1], [(0, 0)])

        for tile in tiles:
            if world.tile_has_tags(tile, tags, self.entity):
                direction = world.get_direction(start_position, (tile.x, tile.y))
                target_tiles.append((tile, direction))

        return target_tiles

    @abstractmethod
    def use(self, use_tiles_and_directions: List[Tuple[Tile, DirectionType]]):
        """
        Trigger any use effects. e.g. create projectile. If no projectile call activate directly.
        """
        pass

    @abstractmethod
    def create_effects(self) -> List[EffectData]:
        """
        Create the skills effects.
        """
        pass

    @abstractmethod
    def activate(self, target_tiles: List[Tile]):
        """
        Trigger the effects on the given tiles.
        """
        pass

    @staticmethod
    def _process_result(result: bool, effect: EffectData) -> List[Optional[EffectData]]:
        """
        Get the success/fail effect, if there is one
        """
        if result and effect.success_effects:
            return effect.success_effects
        elif not result and effect.fail_effects:
            return effect.fail_effects

        return []


class BasicAttack(BaseSkill):
    """
    Purpose: To provide a simple damaging effect as the fall back option for entities. Also for use with bump attacks.
    """
    def __init__(self, owning_entity):
        super().__init__("basic_attack", owning_entity)

    def use(self, use_tiles_and_directions: List[Tuple[Tile, DirectionType]]):
        # no projectile so call activate directly
        tiles = []
        for tile, direction in use_tiles_and_directions:
            tiles.append(tile)
        self.activate(tiles)

    def activate(self, target_tiles: List[Tile]):
        effects = self.create_effects()
        entity = self.entity

        # process all effects on all tiles
        while effects:
            effect = effects.pop()  # FIFO
            for tile in target_tiles:
                coords = utility.get_coords_from_shape(effect.shape, effect.shape_size)
                effected_tiles = world.get_tiles(tile.x, tile.y, coords)
                result = act.process_effect(effect, effected_tiles, entity)
                result_effect = self._process_result(result, effect)
                if result_effect:
                    effects.append(result_effect)

    def create_effects(self) -> List[EffectData]:
        effects = []

        effect_dict = {
            "originator": self.entity,
            "creators_name": self.name,
            "accuracy": BASE_ACCURACY + 5,
            "stat_to_target": PrimaryStat.VIGOUR,
            "shape": Shape.TARGET,
            "shape_size": 1,
            "required_tags": [
                TargetTag.OTHER_ENTITY
            ],
            "damage": BASE_DAMAGE + 20,
            "damage_type": DamageType.MUNDANE,
            "mod_amount": 0.1,
            "mod_stat": PrimaryStat.CLOUT,
        }
        effects.append(DamageEffectData(**effect_dict))

        return effects


class Lunge(BaseSkill):
    """
    Purpose: To provide a simple damaging effect as the fall back option for entities. Also for use with bump attacks.
    """
    def __init__(self, owning_entity):
        super().__init__("lunge", owning_entity)

    def use(self, use_tiles_and_directions: List[Tuple[Tile, DirectionType]]):
        # no projectile so call activate directly
        tiles = []
        for tile, direction in use_tiles_and_directions:
            tiles.append(tile)
        self.activate(tiles)

    def activate(self, target_tiles: List[Tile]):
        effects = self.create_effects()
        entity = self.entity

        # process all effects on all tiles
        while effects:
            effect = effects.pop()  # FIFO
            for tile in target_tiles:
                coords = utility.get_coords_from_shape(effect.shape, effect.shape_size)
                effected_tiles = world.get_tiles(tile.x, tile.y, coords)
                result = act.process_effect(effect, effected_tiles, entity)
                result_effects = self._process_result(result, effect)

                # if we have any success or fail actions add them to the list to activate
                if result_effects:
                    for result_effect in result_effects:
                        effects.append(result_effect)

    def create_effects(self) -> List[EffectData]:
        effects = []

        damage_dict = {
            "originator": self.entity,
            "creators_name": self.name,
            "accuracy": BASE_ACCURACY + 5,
            "stat_to_target": PrimaryStat.VIGOUR,
            "shape": Shape.TARGET,
            "shape_size": 1,
            "required_tags": [
                TargetTag.OTHER_ENTITY
            ],
            "damage": BASE_DAMAGE + 20,
            "damage_type": DamageType.MUNDANE,
            "mod_amount": 0.1,
            "mod_stat": PrimaryStat.CLOUT,
        }
        damage_effect = DamageEffectData(**damage_dict)

        move_dict = {
            "originator": self.entity,
            "creators_name": self.name,
            "accuracy": BASE_ACCURACY + 5,
            "stat_to_target": PrimaryStat.VIGOUR,
            "shape": Shape.TARGET,
            "shape_size": 1,
            "required_tags": [
                TargetTag.SELF
            ],
            "move_direction": Direction.DOWN,
            "move_amount": 1,
            "move_target": self.entity,
            "allow_bump_attack": False,
            "move_time_cost": 0
        }
        move_effect = MoveActorEffectData(**move_dict)

        effects.append(move_effect)
        effects.append(damage_effect)

        return effects