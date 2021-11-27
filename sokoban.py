import argparse
import curses
from curses import wrapper
from sokolib import *
from simpleplayer import SimplePlayer
from humanplayer import HumanPlayer

def run_game(stdscr,args):
    curses.curs_set(0)
    curses.use_default_colors()
    game = GameState(stdscr)
    game.load(args.mazefile)

    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, 15, 6)
    curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_CYAN)

    if args.human == True:
        player = HumanPlayer(game)
    else:
        player = SimplePlayer(game)
    
    while True:
        player.play()
        if game.is_won():
            stdscr.addstr(0,0,"Won!!!")
        else:
            stdscr.addstr(0,0,"Lost :(")
        if stdscr.getch() == 'q':
            return

if __name__ == "__main__":
    print("Project72 Sokoban Game Solver")
    
    parser = argparse.ArgumentParser()
    parser.add_argument('mazefile', type=argparse.FileType('r',encoding='utf8'))
    parser.add_argument('--human',action='store_true',help="switch to human player")
    parser.add_argument('--test-curses', action='store_true',help='test curses features')
    args = parser.parse_args()

    version = args.mazefile.readline().rstrip()
    if version != "Project72-Mazefile":
        print(version)
        raise Exception("Invalid filetype")

    wrapper(run_game,args)
