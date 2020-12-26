import argparse
import re
import curses
from curses import wrapper
import random
import time
import copy
import abc

class GridLocation(tuple):  
    def __add__(self,other):
        return GridLocation((self[0]+other[0],self[1]+other[1]))
        
class GameItem:
    id = GridLocation((-1,-1))
    type = str()
    sym = str()

    def __init__(self,x,y):
        self.id = GridLocation((x,y))
    
    def __eq__(self,other) -> bool:
        return self.id == other.id

    def __lt__(self,other) -> bool:
        if not isinstance(other, GameItem):
            return False
        else:
            return (self.id[0],self.id[1])<=(other.id[0],other.id[1])

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

class Maze:
    def __init__(self,width: int, height: int):
        self.width = width
        self.height = height
        self.walls: list[GridLocation] = []
        self.walls += [(x,0) for x in range(0,width)]
        for y in range(0,height):
            for x in [0, width-1]:
                self.walls += [(x,y)]
        self.walls += [(x,height-1) for x in range(0,width)]

    def in_bounds(self,id: GridLocation) -> bool:
        (x,y) = id
        return 0 <= x < self.width and 0 <= y < self.height
    
    def passable(self, id: GridLocation) -> bool:
        return id not in self.walls

    def neighbors(self, id: GridLocation): #define type!
        (x,y) = id
        neighbors = [(x+1,y), (x-1,y),(x,y-1), (x,y+1)]
        if (x + y) % 2 == 0: neighbors.reverse() # S N W E
        results = [i for i in neighbors if self.in_bounds(i)]
        results = [i for i in results if self.passable(i)]
        return results

class GameState:
    init_pp = PlayerItem(0,0)
    pp = PlayerItem(0,0)
    maze: Maze
    visited: dict[tuple[int,int]] = dict()
    init_stones = list()
    stones = list()
    goals = list()
    obama = False # Merkel
    moves = 0

    def __init__(self,stdscr):
        self.stdscr = stdscr

    def move_player(self,xdir: int,ydir: int):
        id: GridLocation = self.pp.id + GridLocation((xdir,ydir))#(self.pp.id[0]+xdir,self.pp.id[1]+ydir)
        self.obama = False

        if not self.maze.in_bounds(id):
            raise IllegalMoveException
        
        if not self.maze.passable(id):
            raise IllegalMoveException
        try:
            idx = self.stones.index(Stone(id[0],id[1]))
            stone = self.stones[idx]
            id2 = (id[0]+xdir,id[1]+ydir)
            if not self.maze.passable(id2): #check if maze itself is passable
                raise IllegalMoveException
            elif Stone(id2[0],id2[1]) in self.stones:
                raise IllegalMoveException
            else:
                stone.id = (id[0] + xdir,id[1] + ydir)
                self.obama = True #we changed something
        except ValueError:
            pass

        self.pp.id = id
        self.moves += 1

        id2 = self.pp.id
        if self.obama == False:
            if id2 in self.visited:
                self.visited[id2] += 1
            else:
                self.visited[id2] = 1
        else:
            self.reset_visited()
        
    
    def reset_visited(self):
        self.visited = dict()
        self.visited[self.pp.id] = 0


    def load(self,file):
        width = int(file.readline()) + 2 #include walls
        height = int(file.readline()) +2
        self.maze = Maze(width, height)

        pat_np = re.compile("[.■]{{1,{}}}".format(width))
        pat_p = re.compile("[.■"+PlayerItem.sym+Stone.sym+Goal.sym+"]{{1,{}}}".format(width))

        y = 1 #initial y to account for walls
        initx = 1 #initial x
        for tmp in file:
            line = tmp.rstrip()
            if pat_np.fullmatch(line) == None:
                if pat_p.fullmatch(line) == None:
                    raise Exception("Malformed row, invalid character or length! Line number: {} length: {}".format(y,len(line)))
                else:
                    for x,val in enumerate(line,initx):
                        if val == PlayerItem.sym:
                            self.pp = PlayerItem(x,y)
                            self.init_pp = PlayerItem(x,y)
                            #line = line.replace(PlayerItem.sym,".")
                        elif val == Stone.sym:
                            self.stones += [Stone(x,y)]
                            self.init_stones += [Stone(x,y)]
                            #line = line.replace(Stone.sym,".",1)
                        elif val == Goal.sym:
                            self.goals += [Goal(x,y)]
                            #line = line.replace(Goal.sym,".",1)

            self.maze.walls += [(x+initx,y) for x,v in enumerate(line) if v=='■']

            y = y+1
        if len(self.stones) != len(self.goals):
            raise Exception("Error: Number of goals and stones is not equal")
        self.reset_visited()
    
    def reset(self):
        self.pp = self.init_pp #immutable
        self.stones = copy.deepcopy(self.init_stones)
        self.reset_visited()
        self.obama = False
        self.moves = 0
    
    def is_won(self) -> bool:
        if self.stones == self.goals:
            return True
        else:
            return False

    def is_lost(self) -> bool:  #basically check for cornered stones
        for st in self.stones:
            if st in self.goals:
                continue
            corners = [[(st.id[0],st.id[1]-1),(st.id[0]-1,st.id[1])],
                        [(st.id[0],st.id[1]-1),(st.id[0]+1,st.id[1])],
                        [(st.id[0],st.id[1]+1),(st.id[0]+1,st.id[1])],
                        [(st.id[0],st.id[1]+1),(st.id[0]-1,st.id[1])]]
            for corner in corners:
                if not self.maze.passable(corner[0]) and not self.maze.passable(corner[1]):
                    return True
            return False
    
    def render(self): #this is shit, should be replaced by render tree for more complex games
        #render empty spaces
        for i in range(0,self.maze.height):
            self.stdscr.addstr(i, 0,"."*self.maze.width)
        #render walls
        for w in self.maze.walls:
            self.stdscr.addstr(w[1],w[0],'■')
        #render visited layer
        color = curses.COLOR_BLACK
        for key in self.visited:
                (x,y) = key
                self.stdscr.addstr(y,x,f'{self.visited[key]}',color)
        #render goals
        for g in self.goals:
            self.stdscr.addstr(g.id[1],g.id[0],Goal.sym)
        #render player
        self.stdscr.addstr(self.pp.id[1],self.pp.id[0],PlayerItem.sym)
        #render stones
        for st in self.stones:
            self.stdscr.addstr(st.id[1],st.id[0],Stone.sym)
        
        #render UI elements:
        self.stdscr.addstr(self.maze.height,0,"Moves: {}".format(self.moves))

        self.stdscr.refresh()

class AbstractPlayer:
    __metaclass__ = abc.ABCMeta

    def __init__(self, game: GameState):
        self.game = game

    @abc.abstractmethod
    def play(self):
        pass

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
                        self.game.move_player(mv[0]-self.game.pp.id[0],mv[1]-self.game.pp.id[1])
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

class HumanPlayer(AbstractPlayer):
    def play(self):
        self.game.render()
        while True:
            c = self.game.stdscr.getch()
            try:
                if c == curses.KEY_UP:
                    self.game.move_player(0,-1)
                elif c == curses.KEY_DOWN:
                    self.game.move_player(0,1)
                elif c == curses.KEY_LEFT:
                    self.game.move_player(-1,0)
                elif c == curses.KEY_RIGHT:
                    self.game.move_player(1,0)
                elif c == ord('q'):
                    break  # Exit the while loop
                else:
                    pass
            except IllegalMoveException:
                pass
            self.game.render()

            if self.game.is_won():
                self.game.screens_erase()
                break
            if self.game.is_lost():
                self.game.screens_erase()
                break

def run_game(stdscr,args):
    curses.curs_set(0)
    curses.use_default_colors()
    game = GameState(stdscr)
    game.load(args.mazefile)

    if args.human == True:
        player = HumanPlayer(game)
    else:
        player = RandomPlayer(game)
    
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
    args = parser.parse_args()

    version = args.mazefile.readline().rstrip()
    if version != "Project72-Mazefile":
        print(version)
        raise Exception("Invalid filetype")

    wrapper(run_game,args)