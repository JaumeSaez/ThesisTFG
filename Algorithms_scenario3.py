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
import json
from cdlib import TemporalClustering
import json
from json import dumps
import indicators as i




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
co = 10
while co < 11:
    co += 1
    text = 'data_' + str(co) + '.csv'
    df = pd.read_csv('data_scenario3.csv', sep=",")
    time_df = df['time '].unique()
    #print(len(time_df))
    count = 0
    edge = []
    graph = []
    tc = TemporalClustering()
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
        #print(time_df[count])
        c=0
        G=nx.Graph()
        #print(graph)
        while c<len(graph[count]):
            G.add_weighted_edges_from([(graph[count][c])])
            
            c+=1
        #print(G.edges.data('weight'))
        com = algorithms.louvain(G)
        tc.add_clustering(com, time_df[count])

        
        #comunities = str(time_df[count])
        #comunities = comunities+".json"
        #readwrite.write_community_json(com, comunities)
        
        count = count + 1

    result = tc.get_observation_ids()


    for r in result:
        comunities = tc.get_clustering_at(r)
        #print(comunities)

    jaccard = lambda x, y:  len(set(x) & set(y)) / len(set(x) | set(y))
    matches = tc.community_matching(jaccard, two_sided=True)

    time = 10
    results={}
    
    for match in matches:
        # match (ti_cid,tj_cid,score)
        c1 = match[0]
        c2 = match[1]
        score = match[2]

        if score == 1.0:
            t1, idx1 = c1.split("_")
            t2, idx2 = c2.split("_")
            community = tc.get_community(c1)
            community = tuple(community)
            if len(community) > 1:
                
                if (community) in results.keys():
                    curr_start_time, curr_end_time = results[community]
                    t2 = int(t2)
                    if t2 == (curr_end_time + time): #check if they are consecutive e.g. from 10, 20

                        results[community] = (curr_start_time, t2) #update the entry to have new end time

                    
                else:
                    results[community] = (int(t1),int(t2))
    print("Results of "+ text+ " : ",results)
    print(results.keys())
    complexity = list(results.keys())
    times = list(results.values())
    complex = str(complexity[0]).replace('(', '[').replace(')',']').replace(' ,', '')
    data_type = int 
    res = [ele for ele in complexity if not isinstance(ele, data_type)]

    cos = 0
    while cos < len (res):
        counts = (int(times[cos][0]/10))
        cots = 0
        edges = []
        graphs = []
        while counts <= (int(times[cos][1]/10)):
            sub_df = df.loc[(df['time '] == time_df[counts])]
            alt_df_numpy = sub_df.to_numpy()
            I = nx.Graph()
            for position1 in alt_df_numpy:
                for position2 in alt_df_numpy:
                    if position1[1] != position2[1]:
                        #print(position1[1],position1[3],position1[4],position2[1],position2[3],position2[4])
                        gra = []
                        gra= gra + add_edge(position1[1],position1[3],position1[4],position2[1],position2[3],position2[4],edges)                    
            edges = []
            graphs.append(gra)
            cot=0
            #cots = 0           
            I=nx.Graph()
            while cot < len(graphs[cots]):
                I.add_weighted_edges_from([(graphs[cots][cot])])
                cot+=1
            
            a = []
            b = 0
            while b < len(res[cos]):
                a.append(res[cos][b])
                b += 1
            H = I.subgraph(a)
            print ("-------------------","\n","in time ",time_df[counts],"the comunity ",res[cos],
            "\n"," ED is: ", i.ED(H), " Strength is: ", i.Strength(H), " CC is: ",i.CC(H)," NND is: " ,i.NND(H),
            "\n","-------------------","\n","in time ",time_df[counts],"the complexity of sector is: ",
            "\n"," ED is: ", i.ED(I), " Strength is: ", i.Strength(I), " CC is: ",i.CC(I)," NND is: " ,i.NND(I))
            cots += 1
            counts += 1
        cos += 1
