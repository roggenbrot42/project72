from sokolib import GridLocation, IllegalMoveException
from abstractplayer import AbstractPlayer
import curses

class HumanPlayer(AbstractPlayer):
    def play(self):
        self.game.render()
        while True:
            c = self.game.stdscr.getch()
            try:
                if c == curses.KEY_UP:
                    self.move_player(GridLocation((0,-1)))
                elif c == curses.KEY_DOWN:
                    self.move_player(GridLocation((0,1)))
                elif c == curses.KEY_LEFT:
                    self.move_player(GridLocation((-1,0)))
                elif c == curses.KEY_RIGHT:
                    self.move_player(GridLocation((1,0)))
                elif c == ord('q'):
                    break  # Exit the while loop
                else:
                    pass
            except IllegalMoveException:
                pass
            self.game.render()

            if self.game.is_won():
                break
            if self.game.is_lost():
                break
