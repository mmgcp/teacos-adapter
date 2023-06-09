#!/usr/bin/env python
# coding: utf-8

from sqlalchemy import create_engine
from uuid import uuid4
from typing import Tuple

from esdl.esdl_handler import EnergySystemHandler
from esdl import esdl
import pymysql
import pandas as pd
import datetime
import time


# if __name__ == "__main__":
#     Schema = DB
#     Training = SQLESDL(Schema)
#     print(Training.getAttributes())
#     print(Training.Assets)


# # Class that reads the SQL back in. Used to check if the data is ordered correctly and edits the ESDL

# In[8]:


class SQLESDL:
    def __init__(self, host: str, database: str, user: str, password: str):
        print("ESDL-AIMMS Universal link starting...")
        # use sqlAlchemy to connect to (any) database, instead of using direct connection
        # this removes the pandas warning

        self.database_url = f"mysql+pymysql://{user}:{password}@{host}"
        print(f"Connecting to mysql+pymysql://{user}:*****@{host},  db={database}")
        self.database_name = database
        self.engine = create_engine(self.database_url)
        self.conn = self.engine.raw_connection()
        self.cursor = self.conn.cursor()
        start = datetime.datetime.now()
        done = False
        counter = 0
        while done == False:
            counter += 1
            self.log_table = self.get_sql(
                "SELECT * FROM " + self.database_name + ".log_table;"
            )
            if (
                len(self.log_table.index) > 0
                and self.log_table.iloc[-1].log == "Finished DB Write"
            ):
                end = datetime.datetime.now()
                done = True
            else:
                if counter > 60:
                    raise Exception("Logging failed")
                    exit(1)
                time.sleep(1)

        self.tables = self.get_sql(
            "Select table_schema as database_name, table_name from information_schema.tables where table_type = 'BASE TABLE'and table_schema = '"
            + self.database_name
            + "' order by database_name, table_name;"
        )
        for i in self.tables.table_name:
            if i != "log_table":
                setattr(
                    self,
                    i,
                    self.get_sql("SELECT * FROM " + self.database_name + "." + i + ";"),
                )

    def __del__(self):
        self.conn.close()
        self.engine.dispose()

    def db_to_esdl(self, esdl_filename, output_esdl_filename) -> Tuple[bool, str]:
        """
        :param esdl_filename: original esdl file
        :param output_esdl_filename: file the database has to convert to
        :return: tuple (success (True/False), error message)
        """
        print(f"Generating ESDL...")
        esh = EnergySystemHandler()
        try:
            esh.load_file(esdl_filename)
            print(f"Parsing Results...")
            self.generate_esdl(esh, output_esdl_filename)
            return True, "Ok"
        except Exception as e:
            return False, str(e)

    def db_to_esdl_str(self, esdl_str_in) -> Tuple[bool, str, str]:
        """
        :param esdl_str_in: original esdl file
        :return: tuple (success (True/False), error message, esdl_string_out)
        """
        print(f"Generating ESDL...")
        esh = EnergySystemHandler()
        try:
            esh.load_from_string(esdl_str_in)
            print(f"Parsing Results...")
            esdl_str_out = self.generate_esdl_str(esh)
            return True, "Ok", esdl_str_out
        except Exception as e:
            return False, str(e), ""

    def get_sql(self, query):
        try:
            result = pd.read_sql(query, self.database_url)
            return result
        except pymysql.Error as e:
            print("Error: unable to fetch data %d: %s" % (e.args[0], e.args[1]))

    def getAttributes(self):
        return dir(self)

    def _generate_esdl(self, esh, context={"User": "Test"}):
        if hasattr(self, "Producers"):
            dfProducers = self.Producers
            Producers = esh.get_all_instances_of_type(esdl.Producer)
            for p in Producers:
                p.power = float(dfProducers.loc[dfProducers["id"] == p.id].power)
        if hasattr(self, "Producers"):
            dfAssetProfiles = self.AssetProfiles
            AssetProfiles = esh.get_all_instances_of_type(esdl.GenericProfile)
            for p in AssetProfiles:
                if type(p) == esdl.InfluxDBProfile:
                    dfField = dfAssetProfiles.loc[dfAssetProfiles["field"] == p.field]
                    if type(dfField) == pd.Series:
                        p.multiplier = float(dfField.multiplier)

        df2 = self.KPIs
        df3 = df2.where(df2.id_KPI.str.contains("TEACOS_Was_Optional_")).dropna()

        print(df3)
        projname = []
        for i, row in df3.iterrows():
            Assetname = row.id_KPI.replace("TEACOS_Was_Optional_", "")
            projname.append(Assetname)
            query = (
                "SELECT * FROM "
                + self.database_name
                + ".Assets where `name` =  '"
                + Assetname.lstrip()
                + "';"
            )
            AssetId = self.get_sql(query).id[0]

            changables = esh.get_by_id(AssetId)
            changables_kpi_list = changables.KPIs
            if not changables_kpi_list:
                changables.KPIs = esdl.KPIs(id=str(uuid4()))

            KPIsInFile = esh.get_all_instances_of_type(esdl.IntKPI)
            KPIids = [i.id for i in KPIsInFile]
            if row.id_KPI not in KPIids:
                print("First Run", row.value_KPI)
                kpiwasoptional = esdl.IntKPI(
                    id=row.id_KPI, name=row.name_KPI, value=int(row.value_KPI)
                )
                changables.KPIs.kpi.append(kpiwasoptional)
                print(kpiwasoptional, AssetId, 1)

        asset = esh.get_all_instances_of_type(esdl.Asset)
        proj = []
        for a in asset:
            if a.state.value == 2:
                projname.append(a.name if a.name else None)
                #             kpiwasoptional = esdl.IntKPI(name = 'TEACOS_was_optional',value = 1)
                #             a.kpi = kpiwasoptional
                #             print(a.name, a.kpi.name)
                proj.append(a.id)
            elif a.name in projname:
                proj.append(a.id)

        if hasattr(self, "Assets"):
            df = self.Assets
            df = df[df["id"].isin(proj)]
            print(df.state)
            for i, row in df.iterrows():
                changables = esh.get_by_id(row.id)
                print(changables.name, changables.state, row.state)
                changables.state = row.state

        df4 = df2.where(df2.id_KPI.str.contains("TEACOS_Inversted_W_")).dropna()
        print(df4)
        for i, row in df4.iterrows():
            Assetname = row.id_KPI.replace("TEACOS_Inversted_W_", "")
            query = (
                "SELECT * FROM "
                + self.database_name
                + ".Assets where `name` =  '"
                + Assetname.lstrip()
                + "';"
            )
            AssetId = self.get_sql(query).id[0]

            changables = esh.get_by_id(AssetId)
            changables_kpi_list = changables.KPIs
            if not changables_kpi_list:
                changables.KPIs = esdl.KPIs(id=str(uuid4()))
            print(row.value_KPI)

            if row.id_KPI in KPIids:
                kpi = [i for i in KPIsInFile if i.id == row.id_KPI]
                kpi[0].value = int(row.value_KPI)
            else:
                kpiConstraints = esdl.IntKPI(
                    id=row.id_KPI, name=row.name_KPI, value=int(row.value_KPI)
                )
                changables.KPIs.kpi.append(kpiConstraints)

    def generate_esdl(self, esh, outputfile, context={"User": "Test"}):
        self._generate_esdl(esh, context)

        print(esh.to_string())
        esh.save_as(outputfile)

    def generate_esdl_str(self, esh, context={"User": "Test"}) -> str:
        self._generate_esdl(esh, context)
        return esh.to_string()


# if __name__ == "__main__":
#     Schema = DB
#     Training = SQLESDL(Schema)
#     print(Training.getAttributes())


# # Function that writes output to ESDL

# In[ ]:


# from dotenv import load_dotenv
# import os
#
# if __name__ == "__main__":
#     Filename = os.getenv("ESDL_INPUT_FILENAME")
#     Outputfile = os.getenv("ESDL_OUTPUT_FILENAME")
#     Host = os.getenv("DATABASE_HOST")
#     DB = os.getenv("DATABASE_NAME")
#     User = os.getenv("DATABASE_USER")
#     PW = os.getenv("DATABASE_PASSWORD")
#
#     Test = SQLESDL(Host, DB, User, PW)
#     print(Test.db_to_esdl(Filename, Outputfile))
