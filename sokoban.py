import argparse
import re
import curses
from curses import wrapper
import random
import time
import copy
import abc

class GameItem:
    x = -1
    y = -1
    type == "None"

    def __init__(self,x,y):
        self.x = x
        self.y = y
    
    def __eq__(self,other):
        if self.x == other.x and self.y == other.y:
            return True
        else:
            return False
    def __lt__(self,other):
        if not isinstance(other, GameItem):
            return False
        else:
            return (self.x,self.y)<=(other.x,other.y)

class Goal(GameItem):
    type = "Player"

    def __str__(self):
        return "X"

class PlayerItem(GameItem):
    type = "Player"
    
    def __str__(self):
        return "P"

class Stone(GameItem):
    type = "Stone"
    
    def __str__(self):
        return "O"

class IllegalMoveException(Exception):
    pass

class GameState:

    pp = PlayerItem(-1,-1)
    maze = None
    visited = None
    stones = list()
    goals = list()
    sizex = -1
    sizey = -1
    obama = False # Merkel

    def move_player(self,xdir,ydir):
        x = self.pp.x+xdir
        y = self.pp.y+ydir
        self.obama = False

        if x > self.sizex or x < 1:
            raise IllegalMoveException
        if y > self.sizey or y < 1:
            raise IllegalMoveException
        
        if self.maze[y][x] == '#':
            raise IllegalMoveException
        try:
            idx = self.stones.index(Stone(x,y))
            stone = self.stones[idx]
            if self.maze[y+ydir][x+xdir] == '#': 
                raise IllegalMoveException
            else:
                stone.x = x + xdir
                stone.y = y + ydir
                self.obama = True #we changed something
        except ValueError:
            pass

        self.pp.x = x
        self.pp.y = y
        if self.obama == False:
            self.visited[y][x] += 1
        else:
            self.reset_visited()
    
    def reset_visited(self):
        for i,row in enumerate(self.visited):
            for c,val in enumerate(row):
                if type(self.visited[i][c]) == int:
                    self.visited[i][c] = 0
        self.visited[self.pp.y][self.pp.x] = 1


    def load(self,file):
        sizex = int(file.readline())
        sizey = int(file.readline())
        maze = [['#' for x in range(sizex+2)] for y in range(sizey+2)]
        pp = PlayerItem(-1,-1)
        goals = list()
        stones = list()

        pat_np = re.compile("[.#]{{1,{}}}".format(sizex))
        pat_p = re.compile("[.XOP#]{{1,{}}}".format(sizex))

        ln = 1
        for tmp in file:
            line = tmp.rstrip()
            if pat_np.fullmatch(line) == None:
                if pat_p.fullmatch(line) == None:
                    raise Exception("Malformed row, invalid character or length! Line number: {} length: {}".format(ln,len(line)))
                else:
                    for c,val in enumerate(line,1):
                        if val == 'P':
                            pp.x = c
                            pp.y = ln
                            line = line.replace("P",".")
                        elif val == 'O':
                            stones += [Stone(c,ln)]
                            line = line.replace("O",".",1)
                        elif val == 'X':
                            goals += [Goal(c,ln)]
                            line = line.replace("X",".",1)

            linelist = list(line)
            maze[ln][1:1+len(linelist)] = linelist
            ln = ln+1
        if len(stones) != len(goals):
            raise Exception("Error: Number of goals and stones is not equal")
    
        self.maze = maze
        self.visited = [[0 if el == '.' else el for el in row] for row in self.maze]
        self.visited[pp.y][pp.x] = 1
        self.pp = pp
        self.stones = stones
        self.goals = goals
        self.sizex = sizex
        self.sizey = sizey
    
    def is_won(self):
        if self.stones == self.goals:
            return True
        else:
            return False

    def is_lost(self):  #basically check for cornered stones
        for st in self.stones:
            if st in self.goals:
                continue
            if self.maze[st.y-1][st.x] == '#' and self.maze[st.y][st.x-1] == '#': #top left corner
                return True
            if self.maze[st.y-1][st.x] == '#' and self.maze[st.y][st.x+1] == '#': #top right corner
                return True
            if self.maze[st.y+1][st.x] == '#' and self.maze[st.y][st.x+1] == '#': #bottom right corner
                return True
            if self.maze[st.y+1][st.x] == '#' and self.maze[st.y][st.x-1] == '#': #bottom left corner
                return True
        return False
    
    def render(self,screen): #this is shit, should be replaced by render tree for more complex games
        str = ""
        for line in self.maze:
            str = str + '\n' + ''.join(line)
        screen.addstr(0, 0,str)

        #color = curses.COLOR_BLACK
        for y,line in enumerate(self.visited,0):
            for x,place in enumerate(line):
                if place == 0:
                    color = curses.COLOR_BLACK
                elif place == 1:
                    color = curses.COLOR_BLUE
                elif place == 2:
                    color = curses.COLOR_RED
                else:
                    continue
                screen.addch(y+1,x,f'{place}')
        
        for g in self.goals:
            screen.addstr(g.y+1,g.x,"X")
        screen.addstr(self.pp.y+1,self.pp.x,"P")
        for st in self.stones:
            screen.addstr(st.y+1,st.x,"O")

class AbstractPlayer:
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def play(self,file,stdscr,game):
        pass

class RandomPlayer(AbstractPlayer):
    @staticmethod
    def check_visited(game,dx,dy):
        mvx = game.pp.x + dx
        mvy = game.pp.y + dy
        if game.visited[mvy][mvx] == 2:
            return False
        else:
            return True

    def play(self,file,stdscr,game):
        filebase = file.tell()
        lost = 0
        for i in range(1000):
            file.seek(filebase)
            game.load(args.mazefile)

            game.render(stdscr)
            stdscr.refresh()
            stdscr.addstr(13,0,"Lost: {}".format(lost))
            
            random.seed(time.time())

            stuck = 0

            while game.is_won() == False:
                # Computer Random Player
            
                mv = random.randint(0,3)
            
                try:
                    if mv == 0 and RandomPlayer.check_visited(game,0,-1): #down
                        game.move_player(0,-1)
                    elif mv == 1 and RandomPlayer.check_visited(game,0,1): #up
                        game.move_player(0,1)
                    elif mv == 2 and RandomPlayer.check_visited(game,-1,0): #left
                        game.move_player(-1,0)
                    elif mv == 3 and RandomPlayer.check_visited(game,1,0): #right
                        game.move_player(1,0)
                    else:
                        stuck += 1
                except IllegalMoveException:
                    continue
                game.render(stdscr)
                stdscr.refresh()
                time.sleep(1/3)
                if game.is_won():
                    break
                elif game.is_lost() or stuck == 4:
                    lost += 1
                    break
class HumanPlayer(AbstractPlayer):
    def play(self,file,stdscr,game):
        game.load(args.mazefile)

        game.render(stdscr)
        stdscr.refresh()
        while True:
            c = stdscr.getch()
            try:
                if c == curses.KEY_UP:
                    game.move_player(0,-1)
                elif c == curses.KEY_DOWN:
                    game.move_player(0,1)
                elif c == curses.KEY_LEFT:
                    game.move_player(-1,0)
                elif c == curses.KEY_RIGHT:
                    game.move_player(1,0)
                elif c == ord('q'):
                    break  # Exit the while loop
                else:
                    pass
            except IllegalMoveException:
                pass
            game.render(stdscr)

            if game.is_won():
                stdscr.erase()
                break
            if game.is_lost():
                stdscr.erase()
                break

if __name__ == "__main__":
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()
    stdscr.keypad(True)


    print("Project72 Sokoban Game Solver")
    
    parser = argparse.ArgumentParser()
    parser.add_argument('mazefile', type=argparse.FileType('r',encoding='utf8'))
    args = parser.parse_args()

    version = args.mazefile.readline().rstrip()
    if version != "Project72-Mazefile":
        print(version)
        raise Exception("Invalid filetype")

    curses.curs_set(0)
    game = GameState()

    #player = HumanPlayer()
    player = RandomPlayer()
    
    player.play(args.mazefile,stdscr,game)

    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()
    
    if game.is_won():
        print("Won!!!")
    else:
        print("Lost :(")