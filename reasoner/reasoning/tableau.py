import logging

logger=logging.getLogger(__name__)

from ..knowledgebase.axioms import And,Or,Not,RoleAssertion
from ..knowledgebase.graph import Graph
from ..common.constructors import Concept,Some,All

from copy import deepcopy

def add_concept_to_node(graph,concept,node_name):
    '''
        Adds concept to node_name. If a node labelled node_name does not
        exist, it will be created.
    '''
    if not graph.contains(node_name):
        graph.make_node(name=node_name)
    graph.get_node(node_name).add_concept(concept)
    return graph

def make_model_copies(models_list):
    copy_list=[]
    for model in models_list:
        copy_list.append(Graph(**model.get_copy()))
    return copy_list

def consume_and_axiom(and_axiom,model_struct):
    '''
        Adds A,B to the axiom_list for Axiom (A AND B).
        returns model_struct with axiom_list modified accordingly.
    '''
    graph,axioms,known_models,node_name=model_struct
    axioms.append(and_axiom.term_a)
    axioms.append(and_axiom.term_b)
    return (graph,axioms,known_models,node_name)

def consume_or_axiom(or_axiom,model_struct):
    '''
        Performs DFS on remaining tree and returns the first satisfiable
        model_struct.
    '''
    graph,axioms,known_models,node_name=model_struct
#   Create a copy of the axioms list.

    axiomsA=axioms[:]
    axiomsB=axioms[:]
    axiomsA.append(or_axiom.term_a)
    axiomsB.append(or_axiom.term_b)

#   Create a copy of known models.
    known_copy=make_model_copies(known_models)

#   Make a copy of the state of the graph.
    graph_copy=deepcopy(graph)

#   Search both sub trees using DFS.
    struct1=search_model((graph,axiomsA,known_models,node_name))
    struct2=search_model((graph_copy,axiomsB,known_copy,node_name))

#   Compose the model_struct using the first satisfiable model in the search.
    if struct1[0].is_consistent():
        final_struct=(struct1[0],struct1[1],struct1[2]+struct2[2],struct1[3])
    else:
        final_struct=(struct2[0],struct2[1],struct1[2]+struct2[2],struct2[3])

    return final_struct

def insert_for_some(graph,role,concept,node):
    children=graph.get_connected_children(node,role)
    for child in children:
        if child.contains(concept):
            return graph
    new_node=graph.make_node()
    graph.make_edge(role,node,new_node)
    node=graph.get_node(name=new_node)
    node.add_concept(concept)
    return graph

def insert_for_all(graph,role,concept,node):
    children=graph.get_connected_children(node,role)
    for child in children:
        child.add_concept(concept)

    return graph


def consume_role_axiom(axiom,struct):
    '''
        Tableau rules for SOME and ALL assertions.
    '''
    graph,axioms,models,node=struct
    if not graph.contains(node):
        graph.make_node(name=node)

    if axiom.type=="SOME":
        graph=insert_for_some(graph,axiom.name,axiom.concept,node)
        return (graph,axioms,models,node)

    elif axiom.type=="ALL":
        graph=insert_for_all(graph,axiom.name,axiom.concept,node)
        return (graph,axioms,models,node)

def consume_role_assertion(axiom,struct):
    '''
        Tableau rules for role assertions - R(a,b).
    '''
    graph,axioms,models,node=struct
    if not graph.contains(node[0]):
        graph.make_node(name=node[0])
    if not graph.contains(node[1]):
        graph.make_node(name=node[1])
    graph.make_edge(axiom.role,node[0],node[1])
    return (graph,axioms,models,node)

def search_model(model_struct):
    '''
        Performs DFS to search for a satisfiable model given the axiom.
        The struct is a tuple of the form (graph,axiom_list,final_states,node_name)
        initialised as (Graph(),[first_axiom],[],node_name)
    '''
    graph=model_struct[0]
    axiom_list=model_struct[1]
    known_models=model_struct[2]
    node_name=model_struct[3]
    logger.debug(f"Axioms to process {axiom_list}")

    if len(axiom_list):
        element=axiom_list.pop()
        logger.debug(f"Consuming axiom: {element}")
    else:
        if graph.is_consistent():
            logger.debug(f"Graph {graph} is consistent.")
            known_models.append(graph)
        else:
            logger.debug(f"Graph {graph} is inconsistent.")
        return (graph,axiom_list,known_models,node_name)

    axiom_type=type(element)
    current_struct=(graph,axiom_list,known_models,node_name)

    if axiom_type==Concept or axiom_type==Not:
        graph=add_concept_to_node(graph,element,node_name)
        return search_model(current_struct)

    elif axiom_type==RoleAssertion:
        struct=consume_role_assertion(element,current_struct)
        return search_model(struct)

    elif axiom_type==Some:
        struct=consume_role_axiom(element,current_struct)
        return search_model(struct)

    elif axiom_type==All:
        struct=consume_role_axiom(element,current_struct)
        return search_model(struct)

    elif axiom_type==And:
        struct=consume_and_axiom(element,current_struct)
        return search_model(struct)

    elif axiom_type==Or:
        return consume_or_axiom(element,current_struct)
