import gamelib
import random
import math
import warnings
from sys import maxsize
import json


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))
        

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        self.starter_strategy(game_state)

        game_state.submit_turn()


    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """
        # First, place basic defenses
        self.build_defences(game_state)
        # TODO hoard or attack
        self.attack(game_state)

    def build_defences(self, game_state):
        # how to use the first 12 SP
        starting_turrets = [[3, 12], [8, 12], [13, 12], [18, 12], [24, 12]]
        starting_walls = [[2, 13], [3, 13], [24, 13], [25, 13], [26, 13], [27, 13]]
        starting_supports = [[13,2]]

        # urgent defenses
        urgent_supports = [[13, 2], [14, 2]]
        urgent_turrets = [[3, 12], [8, 12], [13, 12], [18, 12], [24, 12], [6, 10], [10, 10], [16, 10], [21, 10]]
        urgent_walls = [[2, 13], [3, 13], [4, 13], [7, 13], [8, 13], [9, 13], [12, 13], [13, 13], [14, 13], [17, 13], [18, 13], [19, 13], [23, 13], [24, 13], [25, 13], [26, 13], [27, 13]]

        # high defenses
        high_supports = [[5, 10], [6, 9], [7, 8], [8, 7], [9, 6], [10, 5], [11, 4], [12, 3], [15, 3], [16, 3], [13, 2], [14, 2]]
        high_turrets = [[3, 12], [4, 12], [8, 12], [13, 12], [18, 12], [21, 12], [24, 12], [25, 12], [4, 11], [6, 10], [10, 10], [16, 10], [21, 10], [12, 8]]
        high_walls = [[2, 13], [3, 13], [4, 13], [5, 13], [6, 13], [7, 13], [8, 13], [9, 13], [12, 13], [13, 13], [14, 13], [17, 13], [18, 13], [19, 13], [20, 13], [21, 13], [22, 13], [23, 13], [24, 13], [25, 13], [26, 13], [27, 13], [16, 11]]
        
        # normal defenses
        normal_supports = [[5, 10], [6, 9], [7, 9], [7, 8], [8, 8], [8, 7], [9, 7], [9, 6], [10, 6], [10, 5], [11, 5], [11, 4], [12, 4], [12, 3], [13, 3], [14, 3], [15, 3], [16, 3], [13, 2], [14, 2],[5,11],[4, 11]]
        normal_turrets = [[3, 12], [4, 12], [5, 12], [8, 12], [10, 12], [12, 12], [13, 12], [18, 12], [21, 12], [22, 12], [24, 12], [25, 12], [17, 11], [6, 10], [11, 10], [16, 10], [21, 10], [16, 9], [12, 8], [14, 6]]
        normal_walls = [[2, 13], [3, 13], [4, 13], [5, 13], [6, 13], [7, 13], [8, 13], [9, 13], [10, 13], [11, 13], [12, 13], [13, 13], [14, 13], [17, 13], [18, 13], [19, 13], [20, 13], [21, 13], [22, 13], [23, 13], [24, 13], [25, 13], [26, 13], [27, 13], [14, 12], [17, 12], [12, 11], [13, 11], [16, 11], [15, 10], [15, 9]]

        # low defenses
        low_supports = [[5, 10], [6, 9], [7, 9], [7, 8], [8, 8], [8, 7], [9, 7], [9, 6], [10, 6], [10, 5], [11, 5], [11, 4], [12, 4], [12, 3], [13, 3], [14, 3], [15, 3], [16, 3], [13, 2], [14, 2],[13,4],[12,5],[11,6],[10,7],[9,8],[8,9],[7,10],[6,11]]
        low_turrets = [[3, 12], [4, 12], [5, 12], [8, 12], [10, 12], [12, 12], [13, 12], [18, 12], [21, 12], [22, 12], [24, 12], [25, 12], [4, 11], [17, 11], [6, 10], [11, 10], [16, 10], [21, 10], [16, 9], [12, 8], [14, 6], [18,8],[19,12], [20,12],[23,12],[6,12],[7,12]]
        low_walls = [[2, 13], [3, 13], [4, 13], [5, 13], [6, 13], [7, 13], [8, 13], [9, 13], [10, 13], [11, 13], [12, 13], [13, 13], [14, 13], [17, 13], [18, 13], [19, 13], [20, 13], [21, 13], [22, 13], [23, 13], [24, 13], [25, 13], [26, 13], [27, 13], [14, 12], [17, 12], [12, 11], [13, 11], [16, 11], [15, 10], [15, 9]]

        if game_state.turn_number == 0:
            game_state.attempt_spawn(TURRET, starting_turrets)
            game_state.attempt_spawn(WALL, starting_walls)
            game_state.attempt_spawn(SUPPORT, starting_supports)

        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        else:
            # urgent defenses: turrets are most important
            game_state.attempt_spawn(TURRET, urgent_turrets)
            game_state.attempt_spawn(SUPPORT, urgent_supports)
            game_state.attempt_spawn(WALL, urgent_walls)
            # high defenses: channel is most important
            game_state.attempt_spawn(SUPPORT, high_supports)
            game_state.attempt_spawn(TURRET, high_turrets)
            game_state.attempt_spawn(WALL, high_walls)
            if game_state.get_resource(0) >= 1:
                # normal defenses: attempt to upgrade turret in corner first
                # TODO hoard until upgrade is possible
                game_state.attempt_upgrade([3,12])
                game_state.attempt_spawn(TURRET, normal_turrets)
                game_state.attempt_spawn(WALL, normal_walls)
                game_state.attempt_spawn(SUPPORT, normal_supports)
                # secondary upgrades
                game_state.attempt_upgrade([18,12])
                game_state.attempt_upgrade([4,12])
                game_state.attempt_upgrade([13,12])
                game_state.attempt_upgrade([24,12])
                game_state.attempt_upgrade([2,13])
                # low defenses
                game_state.attempt_spawn(TURRET, low_turrets)
                #game_state.attempt_spawn(WALL, low_walls)
                game_state.attempt_spawn(SUPPORT, low_supports)
                game_state.attempt_upgrade([4,11])
                game_state.attempt_upgrade([5,11])
                
    def attack(self,game_state):
        mp = game_state.get_resource(1)
        if mp >= 6:
            game_state.attempt_spawn(SCOUT, [15,1], 4)
            game_state.attempt_spawn(SCOUT, [16,2], 1000)
        else:
            game_state.attempt_spawn(SCOUT, [14,0], 1000)

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
