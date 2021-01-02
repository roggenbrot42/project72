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
    def __sub__(self,other):
        return GridLocation((self[0]-other[0],self[1]-other[1]))
        
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
        self.calculate_corners()

    def in_bounds(self,id: GridLocation) -> bool:
        (x,y) = id
        return 0 <= x < self.width and 0 <= y < self.height
    
    def passable(self, id: GridLocation) -> bool:
        return id not in self.walls

    def neighbors(self, id: GridLocation) -> list[GridLocation]: #define type!
        (x,y) = id
        neighbors = [(x+1,y), (x-1,y),(x,y-1), (x,y+1)]
        neighbors = [GridLocation(x) for x in neighbors]
        if (x + y) % 2 == 0: neighbors.reverse() # S N W E
        results = [i for i in neighbors if self.in_bounds(i)]
        results = [i for i in results if self.passable(i)]
        return results
 
    def calculate_corners(self) -> list[GridLocation]:
        tmp: list[GridLocation] = []
        for y in range(1,self.height):
            for x in range(1,self.width):
                tmp.append(GridLocation((x,y)))
        ids = [p for p in tmp if p not in self.walls]
        corners = []
        for id in ids:
            corn = [[(id[0],id[1]-1),(id[0]-1,id[1])],
                            [(id[0],id[1]-1),(id[0]+1,id[1])],
                            [(id[0],id[1]+1),(id[0]+1,id[1])],
                            [(id[0],id[1]+1),(id[0]-1,id[1])]]
            for cor in corn:
                if not self.passable(cor[0]) and not self.passable(cor[1]):
                    corners.append(GridLocation(id))
        self.corners = corners

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

    def move_player(self,dir: GridLocation):
        id: GridLocation = self.pp.id + dir
        self.obama = False

        if not self.maze.in_bounds(id):
            raise IllegalMoveException
        
        if not self.maze.passable(id):
            raise IllegalMoveException
        try:
            idx = self.stones.index(Stone(id[0],id[1]))
            stone = self.stones[idx]
            id2 = id + dir
            if not self.maze.passable(id2): #check if maze itself is passable
                raise IllegalMoveException
            elif Stone(id2[0],id2[1]) in self.stones:
                raise IllegalMoveException
            else:
                stone.id = id + dir
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
        height = int(file.readline()) + 2
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
        self.maze.calculate_corners()
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
        color = curses.COLOR_RED
        for key in self.visited:
                (x,y) = key
                self.stdscr.addstr(y,x,f'{self.visited[key]}',curses.color_pair(1))
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

class LocationUnreachableException(Exception):
    pass

class SimplePlayer(AbstractPlayer):
    def breadthFirst(self,start: GridLocation, goal: GridLocation, ignore_corners: bool=False) -> list[GridLocation]:
        
        openNodes = [start]
        parentNodes = dict()

        while openNodes:
            current = openNodes.pop()

            if current == goal:
                break

            neighbors = self.game.maze.neighbors(current)
            neighbors = [x for x in neighbors if Stone(x[0],x[1]) not in self.game.stones]
            for next in neighbors:
                if next in self.game.maze.corners and next != goal and ignore_corners == True:
                    continue
                if next not in parentNodes:
                    openNodes.append(next)
                    parentNodes[next] = GridLocation(current)
        
        path = [goal]
        try:
            if parentNodes:
                current = parentNodes.pop(goal)
        except:
            return []
        while True:
            if current == start:
                break
            path.insert(0,current)
            current = parentNodes.pop(current)
            if not current:
                break
        return path
    
    @staticmethod
    def path2moves(path: list[GridLocation]) -> list[GridLocation]:
        loc = GridLocation((0,0))
        moves = [loc]
        loc = path[0]
        for item in path[1:]:
            moves.append(item - loc)
            loc = item
        return moves

    def move_along_path(self,path: list[GridLocation]):
        for mv in path:
            dir = mv - self.game.pp.id
            self.game.move_player(dir)

    def play(self):
        self.game.render()
        #1 Select a stone to which you want to move
        stones = self.game.stones.copy()
        while stones:
            stone = stones[0]
            stone_init_id = stone.id

            #2 Select a goal onto which you want to move the stone
            goals = [x for x in self.game.goals if x not in self.game.stones]
            playerpos = self.game.pp.id
            
            while goals:
                goal = goals.pop()
                #see if there is a solution from the current stone to the current goal
                path = self.breadthFirst(stone.id, goal.id,True)
                if path:
                    dir = path[0] - stone.id
                else:
                    continue #no solution for this stone yet

                #see if we can move to the initial place at the stone
                place = stone.id - dir
                if place in self.game.maze.neighbors(stone.id): #place is not in wall
                    tmpath = self.breadthFirst(self.game.pp.id,place)
                    if not tmpath: #solution does not exist
                        continue
                    else:
                        self.move_along_path(tmpath)
                    self.game.render()
                else:
                    continue #no solution for this goal yet
                    # TODO: try moving stone to the side to see if we find a solution

                for mv in path:
                    dir = mv - stone.id
                    pushpoint = stone.id - dir
                    if pushpoint == self.game.pp.id: #no direction change
                        self.game.move_player(dir)
                    else: #direction change
                        tmpath = self.breadthFirst(self.game.pp.id, pushpoint)
                        if tmpath:
                            self.move_along_path(tmpath)
                            self.game.move_player(dir)
                        else: #impossible to move along this path, try pushing further
                            dir2 = stone.id - self.game.pp.id
                            try:
                                self.game.move_player(dir2)
                            except:
                                pass
                    self.game.render()
            if stone in self.game.goals:
                stones.remove(stone)
            else:
                stone.id = stone_init_id
                self.game.pp.id = playerpos

class HumanPlayer(AbstractPlayer):
    def play(self):
        self.game.render()
        while True:
            c = self.game.stdscr.getch()
            try:
                if c == curses.KEY_UP:
                    self.game.move_player(GridLocation((0,-1)))
                elif c == curses.KEY_DOWN:
                    self.game.move_player(GridLocation((0,1)))
                elif c == curses.KEY_LEFT:
                    self.game.move_player(GridLocation((-1,0)))
                elif c == curses.KEY_RIGHT:
                    self.game.move_player(GridLocation((1,0)))
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