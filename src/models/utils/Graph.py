from itertools import compress
import copy

class Graph:
    def __init__(self,n_vertices):
        super().__init__()
        self.n_vertices = n_vertices
        self.adj = [[] for i in range(n_vertices)]
        self.arrive_to = [[] for i in range(n_vertices)]
        self.all_reach = [set() for i in range(n_vertices)]
        self.all_not_reach = [set() for i in range(n_vertices)]
    

    def __repr__(self):
        a = ""
        for vertice in range(self.n_vertices):
            a += "V: " + str(vertice) + " -> " + str(self.adj[vertice])[1:-1] + "\n"
        return a

    def add_edge(self, vertice1, vertice2):
        self.adj[vertice1].append(vertice2)
        self.arrive_to[vertice2].append(vertice1)
    
    def get_arrive_to(self, vertice):
        arrive_to = list(filter(lambda vert: vert != vertice, self.arrive_to[vertice]))
        if arrive_to == [-1]:
            return None
        else:
            return arrive_to

    def get_adj(self, vertice):
        adj = list(filter(lambda vert: vert != vertice, self.adj[vertice]))
        if adj == [-1]:
            return None
        else:
            return adj
    
    def remove_vertice(self, vertice):
        for adj in self.adj[vertice]:
            if adj != -1:
                self.arrive_to[adj].remove(vertice)
        for arrive_to in self.arrive_to[vertice]:
            if arrive_to != -1:
                self.adj[arrive_to].remove(vertice)
        self.adj[vertice] = [-1]
        self.arrive_to[vertice] = [-1]
        self.all_reach[vertice] = set({-1})
        self.all_not_reach[vertice] = set({-1})

    #iterative DFS
    def DFS(self, v, visited): 
          
        stack = []
        stack.append(v) 
        while(len(stack)):
            # Pop a vertex from stack
            v_t = stack.pop()

            # mark vertice as visited if it is not visited yet
            if not visited[v_t]:
                visited[v_t] = True
            
            #iterate over all nodes of the vertice to add them to the stack and expand later
            for node in self.adj[v_t]:
                if not visited[node]:
                    stack.append(node)
        
      
    # Returns count of not reachable  
    # nodes from vertex v.  
    # it uses iterative DFS
    def vertice_analysis(self, v, global_visited):

        # Mark all the vertices as not visited  
        visited = [False] * self.n_vertices
        #iterate over all adjcent vertices of v
        for adj_v in self.adj[v]:
            #if adjacent vertice is already visited
            if global_visited[adj_v] == True:
                visited[adj_v] = True

        self.DFS(v, visited)
        
        return visited

    def get_all(self):

        visited = [False]*self.n_vertices

        for vertice in range(len(self.adj)-1, -1, -1):
            
            #get booleans list and reach indexes
            visited_bool_for_vertex = self.vertice_analysis(vertice, visited)
            visited_bool_for_vertex[vertice] = False # remove own value from list
            reach = set(compress(range(len(visited_bool_for_vertex)), visited_bool_for_vertex))
            
            #if vertice reaches any node (adj)
            if len(reach) > 0:
                # add nodes that are reached by adjacent nodes already calculated (since the vertices are traversed in reverse order and each adjacent node is bigger than vertice then all the adjacent nodes were already calculated)
                for reach_elem in reach:
                    try:
                        self.all_reach[vertice].update(self.all_reach[reach_elem])
                    except:
                        self.all_reach[vertice] = copy.deepcopy(self.all_reach[reach_elem])

                #update boolean list with the new nodes added 
                for item in self.all_reach[vertice]:
                    visited_bool_for_vertex[item] = True

                # add adjacent nodes to the reach set of vertice
                try:
                    self.all_reach[vertice].update(reach)
                except:
                    self.all_reach[vertice] = copy.deepcopy(reach)

            
            visited[vertice] = True 

            # iterate over boolean list reversely to toggle values to calculate all_not_reach[vertice] list    
            for index in range(len(visited_bool_for_vertex)-1, vertice, -1):
                visited_bool_for_vertex[index] = not visited_bool_for_vertex[index]
            
            not_reach = set(compress(range(len(visited_bool_for_vertex)), visited_bool_for_vertex))

            # verify if not reach has any element in order to not set an empty set on all_not_reach[vertice]
            if len(not_reach) > 0:
                self.all_not_reach[vertice] = not_reach            
  
        return self.all_reach, self.all_not_reach

    #return a set of vertices that are not reached after removing the desired nodes as well as a list of vertices that are part of the subgraph created after removing the desired nodes
    # in order to get a total list of not_reached nodes,an update should be performed after this function considering that the index of a node on the vertices list has its corresponding list on the not_reach list, i.e, for the vertice "vertices[0]" the corresponding list of nodes to update the original list (all_not_reach) is available on not_reach[0]
    def get_reach_without_nodes(self, vertices_to_remove):
        
        vertices = set()
        for vertex_to_remove in vertices_to_remove:

            # add vertices that are smaller than the removed node and reach it
            # iterate over all vertices smaller than vertex_to_remove and add the ones that are able to reach vertex_to_remove and are not present in the list of vertices to be removed
            for index, reach_nodes in enumerate(self.all_reach[:vertex_to_remove]):
                if index in vertices_to_remove:
                    continue
                if vertex_to_remove in reach_nodes:
                    try:
                        vertices.add(index)
                    except:
                        vertices = set(index)
            
            # add vertices that were able to be reached from the removed node
            #iterate over the nodes reached from vertex_to_remove (elem) and add it if it is not part of the vertices to be removed 
            for reached_node in self.all_reach[vertex_to_remove]:
                if reached_node in vertices_to_remove:
                    continue
                try:
                    vertices.add(reached_node)
                except:
                    vertices = set(reached_node)

        vertices = sorted(vertices)
        
        graph = Graph(len(vertices))
        vertices = list(vertices)
        for index, vertice in enumerate(vertices):     
            for adj in self.adj[vertice]:
                try:
                    index2 = vertices.index(adj)
                    graph.add_edge(index, index2)
                except:
                    continue

        _, not_reach = graph.get_all()

        # update returned not reached nodes to the global vertices values 
        for index, no_original_list in enumerate(not_reach):
            if len(no_original_list) > 0:
                not_reach[index] = set(map(lambda x: vertices[x], no_original_list))      
        return not_reach, vertices
    
    
    def get_groupable_vertices(self):
        groupable = [[] for i in range(self.n_vertices)]
        for last_vertice in range(self.n_vertices-1, -1, -1):
            prev_vertices = self.arrive_to[last_vertice]
            for prev_vertice in prev_vertices:
                if len(self.adj[prev_vertice]) == 1:
                    groupable[prev_vertice] = [last_vertice]+groupable[last_vertice]
                    groupable[last_vertice] = []
                    break
        return groupable

                
# G = Graph(15)
# G.add_edge(0,1)
# G.add_edge(2,3)
# G.add_edge(3,4)
# G.add_edge(4,5)
# G.add_edge(5,6)
# G.add_edge(7,9)
# G.add_edge(8,9)
# G.add_edge(7,8)
# G.add_edge(8,10)
# G.add_edge(9,10)
# G.add_edge(10,11)
# G.add_edge(11,12)
# G.add_edge(13,13)
# G.add_edge(8, 14)
# groupable = G._get_groupable_vertices()
# for index, elem in enumerate(groupable):
#     print(index, ":", elem)
# reach, not_reach = G.get_all()
# for index, elem in enumerate(not_reach):
#     print(index, ":", elem)
# print("AFTER")
# vertices_to_remove = {9,10}
# not_reach_t, vertices = G.get_reach_without_nodes(vertices_to_remove)

# not_reach_a = copy.deepcopy(not_reach)
# reach_a = copy.deepcopy(reach)
# #update global list of not reach to incorporate the nodes not reached after remove.
# for index, vertice in enumerate(vertices):
#     try:
#         not_reach_a[vertice].update(not_reach_t[index])
#         if len(reach_a[vertice]) > 0:
#             reach_a[vertice] -= not_reach_t[index]
#     except:
#         not_reach_a[vertice] = not_reach_t[index]

# #empty sets for vertices that were removed
# for to_remove in vertices_to_remove:
#     not_reach_a[to_remove] = {}
#     reach_a[to_remove] = {}

# for a in range(len(not_reach_a)):
#     if (len(reach_a[a])) > 0:
#         reach_a[a] -= vertices_to_remove
#     if len(not_reach_a[a]) > 0:
#         not_reach_a[a] -= vertices_to_remove

# for vertice, set_reach in enumerate(reach):
#     for other_vertice in set_reach:
#         adj = G.get_adj(vertice)
#         if not other_vertice in adj:
#             arrive_to_other_vertice = G.get_arrive_to(other_vertice)
#             print("FROM ", vertice, " TO ", other_vertice, ":")
#             for arrive_to_vertice in arrive_to_other_vertice:
#                 if arrive_to_vertice in set_reach:
#                     print("IT CAN: ", arrive_to_vertice)


# for index, elem in enumerate(reach_a):
#     print(index, ":", elem)

  
