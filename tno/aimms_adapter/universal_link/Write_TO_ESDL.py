#!/usr/bin/env python
# coding: utf-8
import os
from dotenv import load_dotenv
from pyecore.ecore import EEnum, EEnumLiteral
from pyecore.valuecontainer import EOrderedSet
from sqlalchemy import create_engine
import pymysql
from uuid import uuid4 

# In[1]:
load_dotenv()


Filename = os.getenv("ESDL_INPUT_FILENAME")
Outputfile = os.getenv("ESDL_OUTPUT_FILENAME")
Host = os.getenv("DATABASE_HOST")
DB = os.getenv("DATABASE_NAME")
User = os.getenv("DATABASE_USER")
PW = os.getenv("DATABASE_PASSWORD")

from esdl.esdl_handler import EnergySystemHandler
from esdl import esdl
import pymysql
import pandas as pd
import warnings
warnings.filterwarnings("ignore", message= ".*pandas only support SQLAlchemy connectable.*")



database_url = f"mysql+pymysql://{User}:{PW}@{Host}"
engine = create_engine(database_url)
conn = engine.raw_connection()
cursor = conn.cursor()



def get_sql(query):
    try:
        result = pd.read_sql(query, database_url)
        return result
    except pymysql.Error as e:
        print("Error: unable to fetch data %d: %s" %(e.args[0], e.args[1]))

class SQLESDL:
    def __init__(self, DB):
        self.tables = get_sql("Select table_schema as database_name, table_name from information_schema.tables where table_type = 'BASE TABLE'and table_schema = '" + DB + "' order by database_name, table_name;")
        self.DB= DB
        
        for i in self.tables.table_name:
            setattr(self, i,get_sql('SELECT * FROM '+DB+'.'+i+ ';'))

    
    def getAttributes(self):    
        return dir(self)


    
 
if __name__ == "__main__":
    Schema = DB
    Training = SQLESDL(Schema)
    print(Training.getAttributes())
    print(Training.Assets)
    




# # Class that reads the SQL back in. Used to check if the data is ordered correctly and edits the ESDL

# In[8]:



class SQLESDL:
    def __init__(self, DB):
        self.tables = get_sql("Select table_schema as database_name, table_name from information_schema.tables where table_type = 'BASE TABLE'and table_schema = '" + DB + "' order by database_name, table_name;")
        self.DB= DB
        
        for i in self.tables.table_name:
            setattr(self, i,get_sql('SELECT * FROM '+DB+'.'+i+ ';'))

    
    def getAttributes(self):    
        return dir(self)


    
 
if __name__ == "__main__":
    Schema = DB
    Training = SQLESDL(Schema)
    print(Training.getAttributes())




# # Function that writes output to ESDL

# In[ ]:



def OutputESDL(Schema, inputfilename, outputfilename, context= {'User': 'Test'}):
   
    
    Training = SQLESDL(Schema)
    esh = EnergySystemHandler()
    es = esh.load_file(inputfilename)
    asset = esh.get_all_instances_of_type(esdl.Asset)
    proj = []
    for a in asset:
        if a.state.value == 2:
#             kpiwasoptional = esdl.IntKPI(name = 'TEACOS_was_optional',value = 1)
#             a.kpi = kpiwasoptional
#             print(a.name, a.kpi.name)
            proj.append(a.id)
    
    df = Training.Assets
    df = df[df['id'].isin(proj)]
    print(df.state)
    for i,row in df.iterrows():
        changables = esh.get_by_id(row.id)
        print(changables.name, changables.state, row.state)
        changables.state = row.state
        
    dfProducers = Training.Producers
    Producers = esh.get_all_instances_of_type(esdl.Producer)
    for p in Producers:
        p.power = float(dfProducers.loc[dfProducers["id"]==p.id].power)
        
    dfAssetProfiles = Training.AssetProfiles
    AssetProfiles = esh.get_all_instances_of_type(esdl.GenericProfile)
    for p in AssetProfiles:
        if type(p) == esdl.InfluxDBProfile:
            p.multiplier = float(dfAssetProfiles.loc[dfAssetProfiles["field"]==p.field].multiplier)


    df2 = Training.KPIs
    df3 = df2.where(df2.id_KPI.str.contains('TEACOS_Was_Optional_')).dropna()

    print(df3)
    for i,row in df3.iterrows():
        Assetname = row.id_KPI.replace("TEACOS_Was_Optional_",'')
        query = "SELECT * FROM "+Schema+ ".Assets where `name` =  '"+ Assetname.lstrip() +"';"
        AssetId = get_sql(query).id[0]
        
        changables = esh.get_by_id(AssetId)
        changables_kpi_list = changables.KPIs
        if not changables_kpi_list:
            changables.KPIs = esdl.KPIs(id=str(uuid4()))

        
        kpiwasoptional = esdl.IntKPI(id = row.id_KPI,name = '1', value = 1)
        changables.KPIs.kpi.append(kpiwasoptional)
        print(kpiwasoptional, AssetId,1)
    
    
    df4 = df2.where(df2.id_KPI.str.contains('TEACOS_Inversted_W_')).dropna()
    print(df4)
    for i,row in df4.iterrows():
        Assetname = row.id_KPI.replace("TEACOS_Inversted_W_",'')
        query = "SELECT * FROM "+Schema+ ".Assets where `name` =  '"+ Assetname.lstrip() +"';"
        AssetId = get_sql(query).id[0]
        
        changables = esh.get_by_id(AssetId)
        changables_kpi_list = changables.KPIs
        if not changables_kpi_list:
            changables.KPIs = esdl.KPIs(id=str(uuid4()))

        
        kpiConstraints = esdl.IntKPI(id = row.id_KPI,name = row.name_KPI, value = int(row.value_KPI))
        changables.KPIs.kpi.append(kpiConstraints)
    
    print(esh.to_string())
    esh.save_as(outputfilename)

    conn.close()
    
    
if __name__ == "__main__":
    OutputESDL(DB)



    engine.dispatch
