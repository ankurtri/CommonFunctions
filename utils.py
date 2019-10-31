from retrying import retry
import numpy as np
import pandas as pd
import datetime
import pyodbc
import smtplib
import socks
from email.mime.multipart import MIMEMultipart

@retry(stop_max_attempt_number=10,wait_random_min=2000, wait_random_max=4000)
def pull_weather_data(date, time_period='hourly',Latitude=24.45,Longitude=-77.02):
    # # Download historical weather data from darksky API
    URL = 'https://api.darksky.net/forecast/<API-KEY-VALUE>/{},{},{}'
    
    link = URL.format(Latitude,Longitude,int(date.timestamp()))
    try:
        req = request.urlopen(link)
        req_json = json.loads(req.read())
        req_data = req_json[time_period]['data'] 
        df = pd.DataFrame.from_dict(req_data)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        return df
    except Exception as e:
        print(e)
        return

def mean_absolute_percentage_error(y_true, y_pred): 
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

def generate_regression_metrics(model,X,Y):
    prediction = model.predict(X)
    R_square = r2_score(Y,prediction)
    rmse = np.sqrt(mean_squared_error(Y,prediction))
    mae =  mean_absolute_error(Y,prediction)
    mape = mean_absolute_percentage_error(Y,prediction)
    return {"R_square":R_square,"rmse":rmse,"mae":mae,"mape":mape}
    
def get_model_variable_sensitivity(model,inData,column,colLocalizedValue=None):
    """
    Get model variable sensitivity of any of the sklearn model for the regression analysis.
    
    model - is the sklearn model object
    inData -is the modeling data with all the modeling cols in the right order
    column - the column of interest
    colLocalizedValue - is the localized value of the given column of intereset 
    around which we are looking for the sensitivty value
    """
    inData = inData.copy()
    valCnt = inData[column].value_counts().shape[0]
    #Handling the case where we have only two unique values for the column of interest
    if valCnt in [2,3,4,5]:
        minVal = inData[column].min()
        maxVal = inData[column].max()
        inData = inData[inData[column]==minVal]
        MeanTargetPredictionOrig = model.predict(inData).mean()
        newData = inData.copy()
        newData.loc[:,column] = maxVal
        MeanTargetPredictionNew = model.predict(newData).mean()
        colshiftrange = maxVal-minVal
        sensitivity = (MeanTargetPredictionNew-MeanTargetPredictionOrig)/colshiftrange
        return ("discrete-%d"%valCnt,sensitivity)
        
    q1 = inData[column].quantile(0.25)                 
    q3 = inData[column].quantile(0.75)
    iqr = q3 - q1
    #let's shift the value of the column by 10% of the iqr value
    colshiftrange = iqr/10.0
    #in case the evaluation happens around the localized area then update the inData value 
    if colLocalizedValue:
        selectedRange = inData[column].between(colLocalizedValue-0.5*colshiftrange,colLocalizedValue+0.5*colshiftrange)
        if selectedRange.sum()>40:
            inData = inData[selectedRange]
        else:
            print("For column %s getting overall sensitivity numbers"%column)
        
    MeanTargetPredictionOrig = model.predict(inData).mean()
    newData = inData.copy()
    newData.loc[:,column] = newData[column] + colshiftrange
    MeanTargetPredictionNew = model.predict(newData).mean()
    sensitivity = (MeanTargetPredictionNew-MeanTargetPredictionOrig)/colshiftrange
    return ("continuous",sensitivity)
    
def CompileCSVs(datadir,filenameprefix,encoding="utf-8",datetime_col=None,datetime_format=None,
                datettime_cutoff=None,keep_disk_copy=True):
    """
    Read the set of files which have filenameprefix under the folder datadir.
    This also creates a backup zipped file and copy pastes the files read into it.
    Apart from the backup that is creates, it also creates one compiled file for future iteration
    
    datetime_col and datetime_format would be used to filter out the data 
    and only keep the latest data as per the Cutoff data
    """
    BackupZipFile = os.path.join(datadir,"Backup.zip")
    #defining filehandle with the function specific scope
    filehandle = []
    if os.path.exists(BackupZipFile) == False:
        filehandle = zipfile.ZipFile(BackupZipFile,
                                     mode="x",
                                     compression=zipfile.ZIP_DEFLATED,
                                     compresslevel=9)
    else:
        filehandle = zipfile.ZipFile(BackupZipFile,
                                     mode="a")
    
    fileNames = glob.glob(os.path.join(datadir,filenameprefix+"*.csv"))
    outData = pd.DataFrame()
    for file in fileNames:
        try:
            inData = pd.read_csv(file,low_memory=False,encoding=encoding)
            outData = pd.concat([outData,inData],axis=0,sort=False,ignore_index=True).drop_duplicates()
            print(file,inData.shape)
            #Not backing up the compiled files
            if "%s_Compiled_"%(filenameprefix) not in os.path.basename(file):
                filehandle.write(filename=file,
                                 arcname=os.path.basename(file))
            os.remove(file)
            
        except Exception as e:
            print("Caught Error in reading file %s: %s"%(file,e))
    
    filehandle.close()
    
    if datettime_cutoff is None:
        datettime_cutoff = DATECUTOFF
    if datetime_col:
        filterSeries = pd.to_datetime(outData[datetime_col],format = datetime_format) >= datettime_cutoff
        outData = outData[filterSeries]
        print("Filtered old data and rows dropped from %d to %d."%(filterSeries.shape[0],outData.shape[0]))
    if keep_disk_copy:
        compliedDataFilename = os.path.join(datadir,filenameprefix) \
                                            + pd.Timestamp.now().strftime("_Compiled_%Y-%m-%d %H%M%S.csv")
        
        outData.to_csv(compliedDataFilename,index=False)
    return outData.copy()

def ConnectSQLserver(connectionProperty=None):
    """
    If DSN is provided then DSN is used for the pyODBC connection.
    Otherwise it refers to the connectionProperty for other key-values for connection property
    """
    if "DSN" in connectionProperty:
        DSN  = connectionProperty.get("DSN")
        conn = pyodbc.connect("DSN=%s;Trusted_Connection=yes;"%(DSN))
        return DSN
    elif connectionProperty is not None:
        DatabaseName   = connectionProperty.get("Database","")
        try:
            DatabaseServer = connectionProperty.get("Server","")
        except Exception as e:
            print("Provide the Databse Server Address")
            print(e)
        
        conn = pyodbc.connect("""Driver={SQL Server};
                              Server=%s;
                              Database=%s;
                              Trusted_Connection=yes;"""%(DatabaseServer,DatabaseName))
        return conn
    
    else:
        return None

def mode_evaluation(Series):
    """
    This function expects a pandas.Series and returns the mode of the data.
    In case of conflict it returns one of the mode value
    """
    valcnts = Series.value_counts()
    if len(valcnts)>=1:
        return valcnts.index[0]
    return np.NaN

def season_of_date(date):
    """
    The function expects a date and depending on which month the date falls returns the season of date.
    """
    year = str(date.year)
    month = date.month   
    
    if ((date.year not in range(2010,2099)) or (date.month  not in range(1,13))):
        return np.NaN

    if month != 12 and date <= pd.to_datetime(year+'-03-20'):
        return 'winter'

    if  month == 12 and date >= pd.to_datetime(year+'-12-20'):
        return 'winter'
    if date >= pd.to_datetime(year+'-03-20') and date <= pd.to_datetime(year+'-06-20'):
        return 'spring'
    
    if date >= pd.to_datetime(year+'-06-20') and date <= pd.to_datetime(year+'-09-22'):
        return 'summer'
    
    if date >= pd.to_datetime(year+'-09-22') and date <= pd.to_datetime(year+'-12-20'):
        return 'fall'
    
def date_time_milliseconds(datetimeDateObject):
    """
    This functions counts the milliseconds from 1st Jan 1970 to the datetime object
    """
    datetimeObj = datetime.datetime.combine(datetimeDateObject,datetime.datetime.min.time())
    milliseconds = int((datetimeObj-datetime.datetime(1970,1,1)).total_seconds()*1000)
    return milliseconds

def milliseconds_to_datetime(milliseconds):
    """
    This function converts the milliseconds from 1 Jan 1970 to the date-time object
    """
    seconds = int(milliseconds/1000)
    datetimeObj = datetime.datetime(1970,1,1) + datetime.timedelta(seconds=seconds)
    #2019-08-02 18:11:46
    return datetimeObj.strftime("%Y-%m-%d %H:%M:%S")

def convert_df_to_html(df,float_format=None):
    if float_format:
        return str(df.to_html(col_space=8,justify="center",na_rep = "-", float_format=float_format))
    
    return str(df.to_html(col_space=8,justify="center",na_rep = "-", float_format=lambda x: "%.0f"%x))


@retry(stop_max_attempt_number=5,wait_random_min=2000, wait_random_max=4000)
def send_email(smtp_host = 'smtp.gmail.com',
               smtp_port=465,
               proxy_host=None,
               proxy_port=None,
               From=None,
               From_password=None,
               To = None,
               CC = None,
               message=""):
    if proxy_host:
        socks.setdefaultproxy(socks.HTTP,proxy_host,proxy_port)
        socks.wrapmodule(smtplib)
    #server = smtplib.SMTP(host=smtp_host, port=smtp_port)
    
    context = smtplib.ssl.create_default_context()
    with smtplib.SMTP_SSL(host=smtp_host, port=smtp_port,context=context) as server:
        try:
            if From_password:
                server.login(From, From_password)
        except Exception as e:
            print(e)
            return
        
        msg = MIMEMultipart('alternative')
        # setup the values of the message
        msg['From']    = From
        
        if isinstance(To,list):
            To = ",".join(To)
            
        msg['To']      = To
        
        if CC:
            msg['CC']  = CC
            
        msg['Subject'] = "This is a TEST Email"             

        # add in the message body
        msg.attach(MIMEText(message, 'html'))
        
        try:
            server.send_message(msg)
            return 0
        except Exception as e:
            print(e)
            return
        
class TicTocTimer(object):
    def __init__(self, name=None):
        self.name = name

    def __enter__(self):
        self.tstart = datetime.datetime.now()

    def __exit__(self, type, value, traceback):
        if self.name:
            print('[%s]' % self.name,)
        seconds=(datetime.datetime.now() - self.tstart).total_seconds()
        print('Elapsed: %s seconds' %seconds)
