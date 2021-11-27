from sokolib import GridLocation, Stone, Node
from abstractplayer import AbstractPlayer

class SimplePlayer(AbstractPlayer):
    @staticmethod
    def manhattan(point1: GridLocation,point2: GridLocation):
        return abs(point1[0] - point2[0]) + abs(point1[1]-point2[1])

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


    def aStar(self,start, goal) -> list:
        openNodes: set[Node] = set()
        closedNodes: set[Node] = set()

        openNodes.add(start)

        while openNodes:
            current = min(openNodes, key=lambda o: self.manhattan(o,goal))
            if current == goal:
                path = []
                while current.parent:
                    path.append(current)
                    current = current.parent
                path.append(current)
                return path[::-1]
            #Remove the item from the open set
            openNodes.remove(current)
		    #Add it to the closed set
            closedNodes.add(current)
            #Loop through the node's children/siblings
            for node in self.game.maze.neighbors(current.id):
                #If it is already in the closed set, skip it
                if node in closedNodes:
                    continue
                #Otherwise if it is already in the open set
                if node in openNodes:
                    #Check if we beat the G score 
                    new_g = current.G + current.move_cost(node)
                    if node.G > new_g:
                        #If so, update the node to have a new parent
                        node.G = new_g
                        node.parent = current
                else:
                    #If it isn't in the open set, calculate the G and H score for the node
                    node.G = current.G + current.move_cost(node)
                    node.H = self.manhattan(node, goal)
                    #Set the parent to our current item
                    node.parent = current
                    #Add it to the set
                    openNodes.add(node)
        #return empty list, as there is not path leading to destination
        return []
    
    def move_along_path(self,path: list[GridLocation]):
        for mv in path:
            dir = mv - self.game.pp.id
            self.game.move_player(dir)

    def play(self):
        self.game.render()
        #1 Select a stone that you want to move to
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
