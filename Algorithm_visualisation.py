from cProfile import label
from zipfile import ZIP_BZIP2
import pandas as pd
import numpy as np
from helpers import distance
import networkx as nx
import csv
import indicators as i
from complexity_indicators import Complexity
import plotly.express as px
import plotly.graph_objects as go
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import numpy as np
from pylab import *


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
Strength_Sector = []
while co < 11:
    co += 1
    text = '_data_7.csv'
    df = pd.read_csv(text, sep=",")
    time_df = df['time '].unique()
    count = 0
    edge = []
    graph = []
    complex_com = [['Pool']]
    compl_com = []
    percent = []
    data = []
    z = []
    z1 = []
    z2 = []
    z3 = []
    while count < len(time_df):
        sub_df = df.loc[(df['time '] == time_df[count])]
        alt_df_numpy = sub_df.to_numpy()
        T = nx.Graph()
        for position1 in alt_df_numpy:
            for position2 in alt_df_numpy:
                if position1[1] != position2[1]:
                    gra= add_edge(position1[1],position1[3],position1[4],position2[1],position2[3],position2[4],edge)
        edge = []
        
        graph.append(gra)
        c=0
        T=nx.Graph()
        while c<len(graph[count]):
            if graph[count][c][2] > 0:
                T.add_edge(graph[count][c][0],graph[count][c][1],weight=graph[count][c][2])
            c+=1
        

        comp = Complexity(T,threshold=0.5)
        nodes,percentage = comp.granular_complexity(T,draw=True)
        #print(comms)
        nodes = sorted(nodes, reverse=False)
        compl_com.append(nodes)
        if len(complex_com)>0:
            c = 0
            d = 0
            while c < len(complex_com):
                if nodes != complex_com[c]: 
                    c += 1
                    d += 1
                else:
                    c +=1
            if c == d:
                complex_com.append(nodes)
        else: 
            complex_com.append(nodes)
        percent.append(percentage[0])
        c = 0
        
        count = count + 1
    time = list(time_df)
    while c < len (complex_com):
        co = 0
        percents = []
        while co < len(compl_com):
            if complex_com[c] == compl_com[co]:
                percents.append(percent[co])
                co += 1
            else:
                percents.append(0)
                co += 1
        data.append(list(percents))
        c += 1

    complex_com = list(complex_com)
    complex_com=[str(com).replace("[","").replace("]","") for com in complex_com]

    fig = px.imshow(data,
                labels=dict(x="Time", y="Complex_Community", color="Percentage of overall complexity"),
                x=time, y= complex_com,
                color_continuous_scale='Jet')
    fig.show()