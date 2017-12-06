import logging

logger=logging.getLogger(__name__)

from .knowledgebase import NodeSet

class NodeNameGenerator(object):
    '''
        Used for naming unnamed nodes.
    '''
    def __init__(self):
        self.i=0

    def get_name(self):
        name="no_name:"+str(self.i)
        self.i+=1
        return name

class Node(object):
    '''
        Represents a single node in the completion graph. Used to represent a
        single instance in the concept assertion and then expanded from
        there.
    '''

    def __init__(self,
            individual,
            children={},
            axioms=NodeSet("axioms"),
            labels=NodeSet("labels")):
            
        self.name=str(individual)
        self.axioms=axioms
        self.labels=labels
        self.children=children
        self.CONSISTENT=True
        logger.debug(f"Node {self.name} initialised.")

    def __eq__(self,other):
        return self.name==other

    def __repr__(self):
        return self.name

class Graph(object):
    '''
        Represents a completion graph of nodes.
    '''

    def __init__(self):
        self.root=None
        self.namer=NodeNameGenerator()
        self.nodes={}
        self.edges={}
        logger.debug(f"Initialised empty graph {self}.")

    def make_node(self,node=None,name=None):
        '''
            If the node to be generated is given, generate that node. Else
            generate a new node with the given name or a random name. Returns
            the name of the node.
        '''
        if node:
            name=node.name
            self.nodes[name]=node
        else:
            if name==None:
                name=self.namer.get_name()
            self.nodes[name]=Node(individual=name)
        logger.debug(f"made new node {name} in {self}")
        return name

    def make_edge(self,name,parent,child):
        '''
            Make an edge with label name from parent to child.
        '''
        parents=self.edges.setdefault(name)
        if parents!=None:
            parents.add(parent)
        else:
            self.edges[name]=set([parent])
        children_dict=self.nodes[parent].children
        children=children_dict.setdefault(name)
        if children==None:
            children_dict[name]=set([child])
        else:
            children.add(child)
        logger.debug(f"made edge {name} from {parent} to {child} in {self}")

    def edge_exists(self,parent,name,child):
        '''
            Returns true if an edge exists between given parent and child.
        '''
        parent=self.nodes[parent]
        children=parent.children.setdefault(name)
        if children != None and (child in children):
            return True
        else:
            return False

    def get_connected_children(self,parent,edge_name):
        '''
            returns a list of connected nodes to a parent node along the
            given edge.
        '''
        return list(map(lambda x:self.nodes[x],list(self.nodes[parent].children.setdefault(edge_name))))

    def contains(self,name):
        node=self.nodes.setdefault(name)
        return node!=None

    def get_node(self,name):
        if self.contains(name):
            return self.nodes[name]
        else:
            return None
