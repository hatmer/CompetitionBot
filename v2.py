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
        self.lastRoundEnemyHealth = 30
        self.side = 'right'
        

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
        self.attack(game_state)
        

    def build_defences(self, game_state):
        # how to use the first 12 SP
        starting_turrets = [[7, 11], [19, 11]]
        starting_supports = [[13,2],[14,2]]

        # urgent defenses: essential to protect and score
        core_turrets = [[7, 11], [19, 11], [24,12], [3,12], [13,11]]
        core_supports = [[13,2],[14,2]]
        
        

        # secondary defenses
        secondary_supports = [[13,3],[14,3],[13,4],[14,4]] # square
        secondary_turrets = [[10,11],[16,11],[23,11],[4,11],[24,11],[3,11],[10,10], [13,10],[14,11],[9,11],[15,11],[12,11],[17,11],[18,11]]
        
        corner_walls = [[0,13], [27,13],[1, 12], [2, 12], [26,12],[25,12]]
        turret_walls = [[23, 12],[4, 12],[22,12],[6, 12], [7, 12], [8, 12], [12, 12], [13, 12], [14, 12], [18, 12], [19, 12], [20, 12], [24, 12],[10,12],[16,12],[5,12],[21,12],[8,12],[9,12],[18,12],[17,12],[11,9],[15,12]]

        #extra_walls
        #final_walls = [[24,10],[23,9],[22,8],[3,10],[4,9],[5,8],[6,7],[7,6],[21,7],[20,6]]
        
        final_supports = [[12,3],[15,3],[12,4],[15,4],[13,5],[14,5],[13,6],[14,6]]
        # setup
        if game_state.turn_number == 0:
            game_state.attempt_spawn(TURRET, starting_turrets)
            game_state.attempt_spawn(SUPPORT, starting_supports)
            game_state.attempt_upgrade(starting_turrets[0])
            game_state.attempt_upgrade(starting_turrets[1])
        
        else:
            
                
            # core defenses and attack setup: make sure they are there
            game_state.attempt_spawn(TURRET, core_turrets)
            game_state.attempt_spawn(SUPPORT, core_supports)
            game_state.attempt_spawn(WALL, corner_walls)
            if game_state.turn_number > 25:
                for wall in corner_walls:
                    game_state.attempt_upgrade(wall)
            # essential upgrades: all turrets and supports
            do_secondary = True
            for unit in core_turrets+core_supports:
                game_state.attempt_upgrade(unit)
                if not self.is_upgraded(game_state,unit):
                    do_secondary = False
            
            if do_secondary and game_state.get_resource(SP) >= 1:
                # walls, supports, turrets
                ok = True
                
                game_state.attempt_spawn(WALL, turret_walls)
                # upgrade the corner walls
                #for wall in corner_walls:
                #    game_state.attempt_upgrade(wall)
                #    if not self.is_upgraded(game_state,wall):
                #        ok = False
                if ok:
                    game_state.attempt_spawn(SUPPORT, secondary_supports)
                    # upgrade the supports
                    for support in secondary_supports:
                        game_state.attempt_upgrade(support)
                        if not self.is_upgraded(game_state,support):
                            ok = False
                if ok:
                    game_state.attempt_spawn(TURRET, secondary_turrets)
                    # upgrade the turrets
                    for turret in secondary_turrets:
                        game_state.attempt_upgrade(turret)
                        if not self.is_upgraded(game_state,turret):
                            ok = False
                # deal with many destroyers and cannonball scouts
                #if ok:
                    #game_state.attempt_spawn(WALL, final_walls)

                    #for wall in turret_walls:
                    #    game_state.attempt_upgrade(wall)
                    #    if not self.is_upgraded(game_state,wall):
                    #        ok = False

                # beef up scouts with remaining SP
                if ok:
                    game_state.attempt_spawn(SUPPORT, final_supports)
                    for support in final_supports:
                        game_state.attempt_upgrade(support)
                
            
                
                
                
    def attack(self,game_state):
        scoredLastRound = (not (self.lastRoundEnemyHealth == game_state.enemy_health)) or game_state.turn_number == 0
        mp = game_state.get_resource(MP)

        if game_state.turn_number < 15 or mp >= min(game_state.turn_number - 10, 20):
            if (self.side == 'right' and scoredLastRound) or (self.side == 'left' and not scoredLastRound):
                self.side = 'right'
                spawn = [14,0]
            else:
                self.side = 'left'
                spawn = [13,0]

            if not scoredLastRound:
                game_state.attempt_spawn(SCOUT, [spawn[0], spawn[1]+1], int(mp / 3))
                game_state.attempt_spawn(SCOUT, spawn, 1000)
            else:
                game_state.attempt_spawn(SCOUT, spawn, 1000)

            self.lastRoundEnemyHealth = game_state.enemy_health



    def is_upgraded(self,game_state, unit):
        x = unit[0]
        y = unit[1]
        return len(game_state.game_map[x,y]) and game_state.game_map[x,y][0].upgraded


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
