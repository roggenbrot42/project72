from abstractplayer import AbstractPlayer
from sokolib import *
import random
import time

class RandomPlayer(AbstractPlayer):
    @staticmethod
    def check_visited(game: GameState,id):
        if id not in game.visited:
            return True
        else:
            return game.visited.get(id) < 2

    def play(self):
        lost = 0
        for i in range(100000):
            self.game.reset()

            self.game.render()
            
            random.seed(time.time())

            stuck = 0

            while self.game.is_won() == False:
                # Computer Random Player

                neighbors = self.game.maze.neighbors(self.game.pp.id)
                random.shuffle(neighbors)
                mv = neighbors[0]

                try:
                    if RandomPlayer.check_visited(self.game,mv):
                        self.game.move_player(mv-self.game.pp.id)
                    else:
                        stuck += 1
                except:
                    stuck += 1

                self.game.render()
                #time.sleep(1/120)
                if self.game.is_won():
                    break
                elif self.game.is_lost() or stuck == 4:
                    lost += 1
                    break
