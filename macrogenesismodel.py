# -*- coding: utf-8 -*-
from faust_macrogen_graph import parserutils, graphutils, eades_fas
from pathlib import Path
import networkx as nx
import matplotlib.pyplot as plt


filespath = Path('resources')
temppre_items = parserutils.xmlparser(filespath)
tempsyn_items = parserutils.xmlparser(filespath, False, False)
#date_items = ...

#%%
#####
# graph for tempsyn <relation>-elements
#####

#tpG = temppre Graph
tempsynG = nx.DiGraph()
for t in tempsyn_items:
    graphutils.add_egdes_from_node_list(tempsynG, t)

#print(list(tempsynG.nodes()))
    
    
pos = nx.shell_layout(tempsynG)
nx.draw_networkx_nodes(tempsynG, pos)
nx.draw_networkx_labels(tempsynG, pos)
nx.draw_networkx_edges(tempsynG, pos)    
    
#nx.draw_networkx(tempsynG)
plt.show()
print(nx.is_directed_acyclic_graph(tempsynG))

#%%
tempsynG_fas = eades_fas.eades_FAS(tempsynG, True) # seven percent of the edges of tpG are in the FAS
print(tempsynG_fas)

#atempysnG = acyclic tempsyn Graph
atempsynG = tempsynG.copy()
atempsynG.remove_edges_from(tempsynG_fas)
nx.draw_networkx(atempsynG)
plt.show()
print(nx.is_directed_acyclic_graph(atempsynG))



#%%
#####
# graph for temppre <relation>-elements
#####

#tpG = temppre Graph
temppreG = nx.DiGraph()
for t in temppre_items:
    graphutils.add_egdes_from_node_list(temppreG, t)


nx.draw_networkx(temppreG)
plt.show()



#%%
l = {}
for e in temppreG.edges():
    l[e] =temppreG.get_edge_data(e[0], e[1])
print(len(l))
#%%
temppreG_fas = eades_fas.eades_FAS(temppreG, True) # seven percent of the edges of tpG are in the FAS

#atemppreG = acyclic temppre Graph
atemppreG = temppreG.copy()
atemppreG.remove_edges_from(temppreG_fas)



####
# HIER WEITER
# keine doppelten (also keine (v,u) bei (u,v))
#
# Aufgabe a, b, c machen?!
#
#
#%%

fas_relation_overlap = []

for edges in tempsynG_fas:
    if edges in temppreG_fas:
        fas_relation_overlap.append(edges)

#should be empty       
print(fas_relation_overlap)



#%%

G2 = tpG.copy()

G2.remove_edges_from(fas)

c = 0
for component in nx.connected_component_subgraphs(tpG.to_undirected()):
    c += len(component.edges())
    print(len(component.edges()))
print("-")
print(c)
#%%
print(len(G.edges()))
print(len(G2.edges()))

print(nx.is_directed_acyclic_graph(G2))



