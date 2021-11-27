import re
import curses
import copy

class GridLocation(tuple):  
    def __add__(self,other):
        return GridLocation((self[0]+other[0],self[1]+other[1]))
    def __sub__(self,other):
        return GridLocation((self[0]-other[0],self[1]-other[1]))

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
    
    def passable(self, id: GridLocation) -> bool: #todo: include stones
        return id not in self.walls

    def neighbors(self, id: GridLocation) -> list[GridLocation]:
        (x,y) = id
        neighbors = [(x+1,y), (x-1,y),(x,y-1), (x,y+1)]
        neighbors = [GridLocation(x) for x in neighbors]
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

class Node(object):
    def __init__(self,value,id: GridLocation):
        self.value = value
        self.id = id
        self.refresh()

    def refresh(self):
        self.parent: GridLocation = None
        self.H = 0
        self.G = 0

    def move_cost(self,other):
        return 0 if self.value == '.' else 1

class GameState:

    maze: Maze
    visited: dict[tuple[int,int]] = dict()
    init_stones = list()
    stones = list()
    goals = list()
    obama = False # Merkel
    moves = 0

    def __init__(self,stdscr):
        self.stdscr = stdscr
        
    
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