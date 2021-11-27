import abc
from sokolib import *

class AbstractPlayer:
    __metaclass__ = abc.ABCMeta
    game: GameState

    def __init__(self,game: GameState):
        self.game = game
        pass

    @abc.abstractmethod
    def play(self):
        pass

    def move_player(self,dir: GridLocation):
        id: GridLocation = self.game.pp.id + dir
        self.game.obama = False

        if not self.game.maze.in_bounds(id):
            raise IllegalMoveException
        
        if not self.game.maze.passable(id):
            raise IllegalMoveException
        try:
            idx = self.game.stones.index(Stone(id[0],id[1]))
            stone = self.game.stones[idx]
            id2 = id + dir
            if not self.game.maze.passable(id2): #check if maze itself is passable
                raise IllegalMoveException
            elif Stone(id2[0],id2[1]) in self.game.stones:
                raise IllegalMoveException
            else:
                stone.id = id + dir
                self.game.obama = True #we changed something
        except ValueError:
            pass

        self.game.pp.id = id
        self.game.moves += 1

        id2 = self.game.pp.id
        if self.game.obama == False:
            if id2 in self.game.visited:
                self.game.visited[id2] += 1
            else:
                self.game.visited[id2] = 1
        else:
            self.game.reset_visited()