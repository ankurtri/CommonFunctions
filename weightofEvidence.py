import numpy as np
import pandas as pd

def weightofEvidence(df,colname,targetCol,minimum_freq=500):
    X = df[colname]
    Y= df[targetCol]
    category_count = X.value_counts().reset_index()
    category_count.columns= [colname,'#Freq']
                             
    overalleventCount = Y.value_counts().to_dict()
    crossTabEventCount = pd.crosstab(X,Y).reset_index()
    crossTabEventCount = crossTabEventCount.merge(category_count,on=colname)
    
    for key in overalleventCount.keys():
        crossTabEventCount.loc[:,"eventrate%s"%str(key)] = crossTabEventCount.loc[:,key]/overalleventCount.get(key,np.NaN)
    crossTabEventCount.loc[:,"%s_woe"%colname] = np.log((crossTabEventCount['eventrate0']+0.5)/(crossTabEventCount['eventrate1']))
    crossTabEventCount.loc[:,"%s_iv"%colname]  = (crossTabEventCount['eventrate0'] - crossTabEventCount['eventrate1'])*crossTabEventCount["%s_woe"%colname]
    crossTabEventCount = crossTabEventCount[crossTabEventCount['#Freq']>=minimum_freq]
    
    crossTabEventCount.to_csv("./woes/%s_woes.csv"%colname,index=False)
    return crossTabEventCount

def create_risk_vars(df,COLLIST,targetCol):
    for col in COLLIST:
        print("Creating the Woes for Colname = %s"%col)
        weightofEvidence(df,col,targetCol)
    
def add_risk_vars(df,CharCOLS,targetCol=None,CREATEWOES=True):
    if CREATEWOES == True :
        if targetCol == None :
            print("provide the target column to start training")
            return
        
        create_risk_vars(df,CharCOLS,targetCol)
        
    for colname in CharCOLS:
        woedata = pd.read_csv("./woes/%s_woes.csv"%colname)
        woedata = woedata.loc[:,[colname,'%s_woe'%colname,'%s_iv'%colname]]
        df = df.merge(woedata,how='left',on=colname)
        
    df.replace([np.inf,-np.inf],np.NaN,inplace=True)
    df.loc[:,pd.isnull(df['%s_woe'%colname])] = 0
    df.loc[:,pd.isnull(df['%s_iv'%colname])] = 0
    return df.copy()
    
