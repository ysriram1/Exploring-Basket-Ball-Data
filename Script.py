# -*- coding: utf-8 -*-
"""
Created on Thu May 26 13:19:51 2016

@author: SYARLAG1
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
os.chdir('/Users/Sriram/Desktop/DePaul/Q3/CSC478/CSC478Project')


def createData(returnValues = False):
    '''reads the data from the folder containing all the data files
    and returns a final nested list with all the data in it if argument
    is set to true. Running this function will automatically generate a file
    called 'fullData.csv' containing all the datapoints for this file. 
    ''' 
    #Reading in the Stats data (X). All the data is by player, so we need to filter it after reading in to get only the data we need
    allData = []
    colNames = []
    count = 0 
    for i in range(1,102):
        if i<10: filename = '00%s.csv'%i 
        elif i < 100: filename = '0%s.csv'%i
        elif i >= 100: filename = '%s.csv'%i
    
        textLines = open('./data/PlayerStats/%s.csv'%filename, 'r').read().split('\n')
        
        for index, line in enumerate(textLines):
            line = line.strip()
            if index in [0,1,2,23,44,65,86]: #these are the lines that we dont want to include in the data (they are columnnames, empty lines etc)
                if index == 2 and count == 0:
                    colNames.append(line.split(','))
                    count += 1
                continue
            allData.append(line.split(','))
    
    subData = []
    ##Subsetting data to only include year 1979 to 2016
    for datapoint in allData:
        if int(datapoint[2][:4]) in list(range(1979,2017)):
            subData.append(datapoint)
        
    #Reading in the position labels (Y)
    namePositionDict = {}
    for i in range(1979,2017):
        textLines = open('./data/PlayerPosition/leagues_NBA_%s_totals_totals.csv'%i,'r').read().split('\n')
        for line in textLines[1:]:
            line = line.strip()
            terms = line.split(',')
            if terms[1] in namePositionDict.keys():
                continue
            if terms[2] == 'SF-SG': terms[2] == 'SG-SF'
            if terms[2] == 'C-PF': terms[2] == 'PF-C'
            namePositionDict[terms[1]] = terms[2]
            
    df = pd.DataFrame(data, columns = colNames[0])
        
    position = []

    for name in df.Player:
        position.append(namePositionDict[name])
    
    df['Position'] = position
    
    ##We add the values of the Y-column to the current data and create a pandas dataframe for preprocessing
    df.to_csv('./fullData.csv') #saving the necessary data    
    #Reading the player offensive and defensive rating data:
    OffRatingDict = {}
    DefRatingDict = {}
    for i in range(1,152):
        filename = './data/PlayerRating/%s.csv'%i
        text = open(filename, 'r').read().split('\n')
        for index, line in enumerate(text):
            if index not in [0,1,2,23,44,65,86]:
                words = line.split(',')
                if words[1] not in OffRatingDict.keys():
                    OffRatingDict[words[1]] = []
                    DefRatingDict[words[1]] = []
                OffRatingDict[words[1]].append(words[20])
                DefRatingDict[words[1]].append(words[21])
    
    if returnValues:
        return subData, colNames[0], namePositionDict, OffRatingDict, DefRatingDict
    
data, colNames, namePositionDict, offDict, defDict = createData(True)
###########################################################################################################

#Reading in the data
df_raw = pd.read_csv('./fullData.csv', na_filter = [' '])

df_raw = df_raw.drop(['Rk', 'Season', 'Age', 'Tm','MP', 'Lg', 'FG%', '2P%', '3P%', 'eFG%', 'FT%', 'TS%'], axis=1) #we will not be using these columns
df_raw = df_raw.drop(df_raw.columns[0], axis = 1)
df_raw.describe()
df_raw.shape

#Data Preprocessing

def mainDataPreprocess(df = df_raw):
    '''This function takes in the raw pandas dataframe and performs basic preprocessing.
    First we remove all the NA values. The main task that is performed is to replace multiple 
    instances for a single player with a single instance. Scaling has been performed seperately 
    for each analytics task. This is because we need to perform a different type of normalization 
    for clustering, PCA, and classification. 
    '''
    #Removing the NA values
    #We will first compress the data. Each player has multiple rows so will 
    #compress this to only have one row per player.
    df_in = pd.DataFrame()
    fill_na = lambda x: x.fillna(x.mean()) if sum(x.isnull()) < x.shape[0] else 0
    mode = lambda x: x.mode() if len(x) > 1 else x #return a single position
    last = lambda x: x.iloc[-1] if len(x) > 1 else x #return the last age of the player
    for colName in df_raw.columns.values:
        if colName == 'Player': continue
        if colName == 'Position': 
            df_in[colName] = df_raw.groupby('Player', axis=0)[colName].agg(mode)
            continue
        elif colName == 'G':
            df_in[colName] = df_raw.groupby('Player', axis=0)[colName].agg(last)
            continue
        else:
             df_raw[colName] = df_raw.groupby('Player', axis=0)[colName].transform(fill_na) #first we fill in all the missing values by the mean
             df_in[colName] = df_raw.groupby('Player', axis=0)[colName].mean() #we store the means of multiple values for each player

    names = df_in.index; positions = df_in.Position; 
    ValueMatrix = np.array(df_in.drop(['Position'], axis = 1))
    
    return names, pd.Series(positions, dtype = 'category'), ValueMatrix 

player, Y_position, X = mainDataPreprocess()

##Here we create a new variable that provides the offensive rating for each player

def OffDefRating(offDict = offDict, defDict = defDict, names = player):
    '''Takes the previously created offensive score and defensive scores previously 
    created and finds the mean score for each player and outputs that value for all
    the players in our main dataframe
    '''
    offRating = []
    defRating = []
    for name in names:
        total = sum(int(i) if i not in ['', ' '] else 0 for i in offDict[name])
        length = sum(1 if i != ' ' else 0 for i in offDict[name])
        offRating.append(int(float(total)/length))
        total = sum(int(i) if i not in ['', ' '] else 0 for i in defDict[name])
        length = sum(1 if i != ' ' else 0 for i in defDict[name])
        defRating.append(int(float(total)/length))
    return offRating, defRating

Y_off, Y_def = OffDefRating() 

##Here we create a new variable that identifies if a player is in the hall of fame or not. 
##A player with '*' at the end of his name belongs to the hall of fame. This variable will
##be populated by True or False

def halloffameVar(names = player):
    '''Takes the names of the players and returns a new variable that indicates wether (True) or 
    not (False) that player belongs to the Hall of Fame. 
    '''
    HofF = pd.Series(index=player)
    for name in player:
        if name[-1] == '*':
            HofF[name] = True
        else:
            HofF[name] = False
    return HofF
    
Y_HofF = halloffameVar(names = player)

#Data Exploration
##First we perform PCA and find the number of PCs contibute to 95% of the variation
##In order to do this, we first center and scale the data
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

fit = StandardScaler().fit(X)
X_norm = fit.transform(X)

pca = PCA().fit(X_norm)

val = 0
count = 0
for i in pca.explained_variance_ratio_:
    val += i
    count += 1
    if val >= 0.95:
        break
print('The number of principal components needed to account for 95% of the variation is ', count)

print('The first two Principal Components explain %0.02f percent of the variation'%pca.explained_variance_ratio_[[0,1]].sum())

X_pca_2 = PCA(n_components = 2).fit(X_norm).transform(X_norm)

##Looking at PCA for the position values
posKV = {} #creating a new variable to color the datapoints properly
for value, key in enumerate(set(Y_position)): posKV[key] = value + 1
colors = [posKV[key] for key in Y_position]

plt.scatter(X_pca_2[:,0], X_pca_2[:,1], c = colors)
plt.xlabel('Principal Component 1'); plt.ylabel('Principal Component 2')
plt.title('Plot of first 2 PCs and datapoints colored by player position')


#Based on the plot above, we can see that there is a variation among th 10classes. The distinction
#is not perfectly visible but there definitely seems to be differences with the classes. The arrangement
#doesnot look random. The legend has been left out on purpose. It serves no purpose in aiding the point that 
#point that is being coveryed here.

##Looking at PCA for the Hall of Fame values
plt.scatter(X_pca_2[:,0], X_pca_2[:,1], c = Y_HofF)
plt.xlabel('Principal Component 1'); plt.ylabel('Principal Component 2')
plt.title('Plot of first 2 PCs and datapoints colored by Hall of Fame Status')

#Looking at the plot below, there doesnt seem to be any discernable pattern in the data. 
#this could also be caused as a result of the fact of that there are very few HofF players
#only 54 out of 1478. Since this is the case, we also try to classify using LDA (lineat dis-
#criminant analysis)

##Looking at the variation between defensive Rating and offensive Rating by the player position
pos_rating = pd.DataFrame(Y_position); pos_rating['Def'] = Y_def; pos_rating['Off'] = Y_off
pr_agg = pd.DataFrame(); pr_agg['Def'] = pos_rating.groupby('Position')['Def'].mean() - 100
pr_agg['Off'] = pos_rating.groupby('Position')['Off'].mean() - 100 #subtracting 100 for better comparison
pr_agg.plot(kind = 'bar')


##Looking at the mean ratings for HoF players vs the rest


#TASK 1: CLUSTERING

from sklearn.cluster import KMeans, k_means



