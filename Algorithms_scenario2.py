# -*- coding: utf-8 -*-
"""
Created on Sun Apr  3 17:01:34 2022

@author: Jaume
"""

import pandas as pd
import numpy as np
from helpers import distance
import networkx as nx
import csv
import cdlib
from cdlib import algorithms, readwrite





def weight_(result_obj):

    weight = 0
    if result_obj <= 5:
        weight = 1
    elif result_obj > 5 and result_obj < 50:
        weight = ((50-result_obj)/45)

    else:
         weight = 0
    
    return weight

def add_edge(ac1_id, ac1_lat, ac1_lon, ac2_id, ac2_lat, ac2_lon,edge):
    I = nx.Graph()    
    result = distance(ac1_lat, ac1_lon, ac2_lat, ac2_lon)
    result = np.squeeze(np.asarray(result))
    wh = weight_(result)
    ed = [ac1_id, ac2_id,wh]
    edge.append(ed)

    return edge

df = pd.read_csv('data_scenario2.csv', sep=",")


time_df = df['time '].unique()
#print(len(time_df))
count = 0
edge = []
graph = []
while count < len(time_df):
    sub_df = df.loc[(df['time '] == time_df[count])]
    alt_df_numpy = sub_df.to_numpy()
    G = nx.Graph()
    for position1 in alt_df_numpy:
        for position2 in alt_df_numpy:
            if position1[1] != position2[1]:
                #print(position1[1],position1[3],position1[4],position2[1],position2[3],position2[4])
                gra= add_edge(position1[1],position1[3],position1[4],position2[1],position2[3],position2[4],edge)
    edge = []
    
    
    graph.append(gra)


    count = count + 1


c=0
while c<len(graph):
    co = 0
    while co < len(graph[c]):

        G.add_weighted_edges_from([(graph[c][co])])
        
        
        co+=1


    com = algorithms.louvain(G)
    readwrite.write_community_json(com, "communitieslouvian.json")

    readwrite.write_community_csv(com, "communities.csv", ",")

    c+=1
