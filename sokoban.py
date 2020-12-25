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
    type = str()
    sym = str()

    def __init__(self,x,y):
        self.x = x
        self.y = y
    
    def __eq__(self,other) -> bool:
        if self.x == other.x and self.y == other.y:
            return True
        else:
            return False

    def __lt__(self,other) -> bool:
        if not isinstance(other, GameItem):
            return False
        else:
            return (self.x,self.y)<=(other.x,other.y)

    def __str__(self) -> str:
        return self.sym

class Goal(GameItem):
    type = "Goal"
    sym = '▢'

class FilledGoal(GameItem):
    type = "FilledGoal"
    sym = '▣'

class PlayerItem(GameItem):
    type = "Player"
    sym = '♕'

class Stone(GameItem):
    type = "Stone"
    sym = '◇'

class IllegalMoveException(Exception):
    pass

GridLocation = tuple[int,int]

class Maze:
    def __init__(self,width: int, height: int):
        self.width = width
        self.height = height
        self.walls: list[tuple[int,int]] = []
    
    def in_bounds(self,id: GridLocation) -> bool:
        (x,y) = id
        return 0 <= x < self.width and 0 <= y < self.height
    
    def passable(self, id: GridLocation) -> bool:
        return id not in self.walls

    def neighbors(self, id: GridLocation): #define type!
        (x,y) = id
        neighbors = [(x+1,y), (x-1,y),(x,y-1), (x,y+1)]
        if (x + y) % 2 == 0: neighbors.reverse() # S N W E
        results = filter(self.in_bounds, neighbors)
        results = filter(self.passable, results)
        return results

class GameState:
    pp = PlayerItem(-1,-1)
    maze = list(list())
    maze_object: Maze
    visited: dict[tuple[int,int]] = dict()
    stones = list()
    goals = list()
    sizex = -1
    sizey = -1
    obama = False # Merkel

    def move_player(self,xdir: int,ydir: int):
        x = self.pp.x+xdir
        y = self.pp.y+ydir
        self.obama = False

        if x > self.sizex or x < 1:
            raise IllegalMoveException
        if y > self.sizey or y < 1:
            raise IllegalMoveException
        
        if self.maze[y][x] == '■':
            raise IllegalMoveException
        try:
            idx = self.stones.index(Stone(x,y))
            stone = self.stones[idx]
            if self.maze[y+ydir][x+xdir] == '■': 
                raise IllegalMoveException
            else:
                stone.x = x + xdir
                stone.y = y + ydir
                self.obama = True #we changed something
        except ValueError:
            pass

        id = (self.pp.x,self.pp.y)
        self.pp.x = x
        self.pp.y = y
        if self.obama == False:
            if id in self.visited:
                self.visited[id] += 1
            else:
                self.visited[id] = 1
        else:
            self.reset_visited()
    
    def reset_visited(self):
        self.visited = dict()
        self.visited[(self.pp.x,self.pp.y)] = 0


    def load(self,file):
        sizex = int(file.readline())
        sizey = int(file.readline())
        self.maze_object = Maze(sizex, sizey)
        maze = [['■' for x in range(sizex+2)] for y in range(sizey+2)]
        pp = PlayerItem(-1,-1)
        goals = list()
        stones = list()

        pat_np = re.compile("[.■]{{1,{}}}".format(sizex))
        pat_p = re.compile("[.■"+PlayerItem.sym+Stone.sym+Goal.sym+"]{{1,{}}}".format(sizex))

        ln = 1
        for tmp in file:
            line = tmp.rstrip()
            if pat_np.fullmatch(line) == None:
                if pat_p.fullmatch(line) == None:
                    raise Exception("Malformed row, invalid character or length! Line number: {} length: {}".format(ln,len(line)))
                else:
                    for c,val in enumerate(line,1):
                        if val == PlayerItem.sym:
                            pp.x = c
                            pp.y = ln
                            line = line.replace(PlayerItem.sym,".")
                        elif val == Stone.sym:
                            stones += [Stone(c,ln)]
                            line = line.replace(Stone.sym,".",1)
                        elif val == Goal.sym:
                            goals += [Goal(c,ln)]
                            line = line.replace(Goal.sym,".",1)
            #old
            linelist = list(line)
            maze[ln][1:1+len(linelist)] = linelist
            #new
            r = ln-1
            self.maze_object.walls += [(i,r) for i,v in enumerate(line) if v=='■']

            ln = ln+1
        if len(stones) != len(goals):
            raise Exception("Error: Number of goals and stones is not equal")
    
        self.maze = maze
        self.pp = pp
        self.reset_visited()
        self.stones = stones
        self.goals = goals
        self.sizex = sizex
        self.sizey = sizey
    
    def is_won(self) -> bool:
        if self.stones == self.goals:
            return True
        else:
            return False

    def is_lost(self) -> bool:  #basically check for cornered stones
        for st in self.stones:
            if st in self.goals:
                continue
            if self.maze[st.y-1][st.x] == '■' and self.maze[st.y][st.x-1] == '■': #top left corner
                return True
            if self.maze[st.y-1][st.x] == '■' and self.maze[st.y][st.x+1] == '■': #top right corner
                return True
            if self.maze[st.y+1][st.x] == '■' and self.maze[st.y][st.x+1] == '■': #bottom right corner
                return True
            if self.maze[st.y+1][st.x] == '■' and self.maze[st.y][st.x-1] == '■': #bottom left corner
                return True
        return False
    
    def render(self,screen): #this is shit, should be replaced by render tree for more complex games

        for y,line in enumerate(self.maze,0):
            screen.addstr(y, 0,"".join(line))

        color = curses.COLOR_BLACK
        for key in self.visited:
                (x,y) = key
                screen.addch(y,x,f'{self.visited[key]}',color)
    
        for g in self.goals:
            screen.addstr(g.y,g.x,Goal.sym)
        screen.addstr(self.pp.y,self.pp.x,PlayerItem.sym)
        for st in self.stones:
            screen.addstr(st.y,st.x,Stone.sym)

class AbstractPlayer:
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def play(self,file,stdscr,game: GameState):
        pass

class RandomPlayer(AbstractPlayer):
    @staticmethod
    def check_visited(game: GameState,dx: int,dy: int):
        (x,y) = (game.pp.x + dx,game.pp.y + dy)
        if (x,y) not in game.visited:
            return True
        else:
            return game.visited.get((x,y)) < 2

    def play(self,file,stdscr,game: GameState):
        filebase = file.tell()
        lost = 0
        for i in range(100000):
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
                except (IllegalMoveException,TypeError):
                    continue

                game.render(stdscr)
                stdscr.refresh()
                #time.sleep(1/120)
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

def run_game(stdscr,args):
    curses.curs_set(0)
    curses.use_default_colors()
    game = GameState()

    if args.human == True:
        player = HumanPlayer()
    else:
        player = RandomPlayer()
    
    player.play(args.mazefile,stdscr,game)
    
    if game.is_won():
        print("Won!!!")
    else:
        print("Lost :(")

if __name__ == "__main__":
    print("Project72 Sokoban Game Solver")
    
    parser = argparse.ArgumentParser()
    parser.add_argument('mazefile', type=argparse.FileType('r',encoding='utf8'))
    parser.add_argument('--human',action='store_true',help="switch to human player")
    args = parser.parse_args()

    version = args.mazefile.readline().rstrip()
    if version != "Project72-Mazefile":
        print(version)
        raise Exception("Invalid filetype")

    wrapper(run_game,args)