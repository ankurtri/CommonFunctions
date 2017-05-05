def create_EDD(Dataframe):
    """
    It expects a pandas.DataFrame as input and outputs EDD in dataframe format as well
    """
    Numeric_col_Order=[]
    Objects_col_Order=[]
    
    Data_types = Dataframe.dtypes
    Unique_dataTypes= Data_types.unique()
    
    Number_of_rows = Dataframe.shape[0]
    
    NAN_Vals = pd.isnull(Dataframe).sum()
    NAN_Vals= pd.DataFrame(NAN_Vals).reset_index()
    NAN_Vals.columns=['Variable','NMiss']
    
    EDD = pd.DataFrame()
    
    for datatype in Unique_dataTypes:
        RelevantCols = [i for i in Data_types[Data_types==datatype].index]
        #print "Handling" ,len(RelevantCols),"variables of",datatype,"type"
        if datatype in [float,int,'int64']:
            # Check_Min_Max
            Num_Stats = Dataframe[RelevantCols].describe().T
            Num_Stats['Zero_Var'] = 0
            
            for col in RelevantCols:
                if Dataframe[col].var()==0:
                   Num_Stats.loc[col,'Zero_Var'] = 1
                   print "came for zero var", col
            
            
            Numeric_col_Order = [i for i in Num_Stats.columns]
            Num_Stats['type'] = datatype
            
            EDD = pd.concat([EDD,Num_Stats],axis=0)
    
        elif datatype == object:
            
            Object_Stats =pd.DataFrame()
            for col in RelevantCols:
                A= Dataframe[col].value_counts()*100.0/Number_of_rows
                n_categories = A.shape[0]
                A = pd.DataFrame(A)
                A.reset_index(inplace=True)
                A.columns=['Value','Percentage']
                A['Category'] = ['Unique_Val-' + np.str(i) for i in A.index]
                A['OutText'] = map(lambda i,j: np.str(i) + "-" + np.str(round(j,2))+"%",A.Value,A.Percentage)
                A.index = A.Category
                A.drop(labels=['Value','Percentage','Category'],axis=1,inplace=True)
                A=A.T
                A.index=[col]
                A['n_category']=n_categories
                Object_Stats = pd.concat([Object_Stats,A],axis=0)
                
            Object_Stats['ID_col'] = Object_Stats['n_category']==Number_of_rows
            Object_Stats['Zero_Var'] = Object_Stats['n_category']==1
            #print A.T
                
            if len(Object_Stats.columns)>10:
                Required_COls=['Unique_Val-' + np.str(i) for i in range(10)]
                Required_COls = Required_COls + [i for i in Object_Stats.columns if i.startswith('Unique_Val-')==False]
                Object_Stats = Object_Stats[Required_COls]            
                
            Objects_col_Order = [i for i in Object_Stats.columns]
            
            Object_Stats['type'] = "STRING"
            EDD = pd.concat([EDD,Object_Stats],axis=0)
                
        else :
            print "No handle avaiable for datatype= ",datatype
    
    
    EDD.index.name="Variable"
    EDD.reset_index(inplace=True)
    EDD = EDD.merge(NAN_Vals,on='Variable')

    COLORDER = ['Variable','type','NMiss']+ Numeric_col_Order + Objects_col_Order    
    
    return EDD[COLORDER].copy()
