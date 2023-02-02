# -*- coding: utf-8 -*-

# !/usr/bin/env python
# coding: utf-8

# # Uniform ESDL-Aimms connection

# ## Introduction
# 
# This is a ready made code script that transforms an ESDL to a database that can be imported to into AIMMS. It uses
# two python packages 'pyesdl' and 'pymysql' made by respectively TNO and Mysql to transform an esdl file to SQL
# tables that can be read by AIMMS.



from pyecore.ecore import EEnum, EEnumLiteral
from pyecore.valuecontainer import EOrderedSet
from sqlalchemy import create_engine
import pymysql
from typing import Union, Tuple
from esdl.esdl_handler import EnergySystemHandler
from esdl import esdl
import pandas as pd

# ### Simple function that runs an SQL command
#

# In[3]:


'''
Converts a list of string to a string or an enum to its name
Returns the value itself if it is not a list or an enum
'''


def convert_to_string(esdl_attribute_value) -> str:
    if isinstance(esdl_attribute_value, EOrderedSet):
        return ','.join([convert_to_string(s) for s in esdl_attribute_value])
    if isinstance(esdl_attribute_value, EEnum):
        return esdl_attribute_value.name
    if isinstance(esdl_attribute_value, EEnumLiteral):
        return esdl_attribute_value.name
    else:
        return esdl_attribute_value


class UniversalLink:
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

    def __del__(self):
        self.conn.close()
        self.engine.dispose()

    def esdl_to_db(self, esdl_filename) -> Tuple[bool, str]:
        """

        :param esdl_filename: file to convert to database
        :return: tuple (success (True/False), error message)
        """
        print(f'Processing ESDL...')
        esh = EnergySystemHandler()
        try:
            esh.load_file(esdl_filename)
            print(f'Parsing ESDL...')
            self.parse_esdl(esh)
            return True, 'Ok'
        except Exception as e:
            return False, str(e)

    def get_sql(self, query):
        try:
            result = pd.read_sql(query, self.database_url)
            return result
        except pymysql.Error as e:
            print("Error: unable to fetch data %d: %s" % (e.args[0], e.args[1]))

    def create_AIMMS_sql(self, DB, SetofTables, SetofAttributes):

        print(f"Removing and recreate database {DB}")
        self.cursor.execute('DROP DATABASE IF EXISTS ' + DB + ';')
        self.cursor.execute('create database ' + DB + ';')
        self.conn.select_db(DB)

        #     query = "SELECT concat('DROP TABLE IF EXISTS `', table_name, '`;') FROM information_schema.tables WHERE table_schema = '"+ DB + "';"
        #     cursor.execute(query)
        #     Tables = cursor.fetchall()
        #     for i in Tables:
        #         cursor.execute(i[0])

        try:
            query = []
            query.append("""CREATE TABLE `log_table` (`id` int(11) NOT NULL AUTO_INCREMENT,
                              `log` varchar(1000) DEFAULT NULL,
                              PRIMARY KEY (`id`))""")
            for i in range(len(SetofTables)):
                query.append('create table ' + SetofTables[i] + '(' + ','.join(SetofAttributes[i]) + ')')
            #         query = [
            # '        create table Assets(aggregated varchar(100),aggregationCount varchar(100),assetType varchar(100),commissioningDate varchar(100),decommissioningDate varchar(100),description varchar(100),id varchar(100) Primary Key,installationDuration varchar(100),manufacturer varchar(100),name varchar(1500),originalIdInSource varchar(100),owner varchar(100),shortname varchar(1500),state varchar(100),surfaceArea varchar(100),technicalLifetime varchar(100));',
            # '        create table Arcs(NameNode1 varchar(100), idNode1 varchar(100), nameNode2 varchar(100), idNode2 varchar(100), Carrier varchar(100), maxPower varchar(100), simultaneousPower varchar(100),PRIMARY KEY (idNode1, idNode2));',
            # '        create table Producers(id varchar(100) Primary Key, name varchar(1500), prodType varchar(100), OperationalHours varchar(100), fullLoadHours varchar(100), power varchar(100));',
            # '        create table Conversions(id varchar(100) Primary Key,name varchar(1500), efficiency varchar(100), power varchar(100));',
            # '        create table Consumers(id varchar(100) Primary Key,name varchar(1500), consType varchar(100), power varchar(100));',
            # '        create table Transports(id varchar(100) Primary Key,name varchar(1500), efficiency varchar(100), capacity varchar(100));',
            # '        create table Products(stateOfMatter varchar(100), energyCarrierType varchar(100), id varchar(100) Primary Key,  emission varchar(100), name varchar(1500), energyContent varchar(100));',
            # '        create table Buildings(id varchar(100) Primary Key, floorArea varchar(100), buildingYear varchar(100), originalIdInSource varchar(100),surfaceArea varchar(100), name varchar(1500), height varchar(100), asset1 varchar(100), asset2 varchar(100),asset3 varchar(100),asset4 varchar(100));']
            for i in query:
                self.cursor.execute(i)

            # Progress update
            print('SQL-file created from ESDL-file')
            print(query)
        except pymysql.Error as e:
            print("Error: unable to create table %d: %s" % (e.args[0], e.args[1]))

    def write_table_to_Sql(self, DB, Sheet, val):
        # Build query
        numofcol = self.get_sql(
            "SELECT COUNT(*) as NumberofCol from INFORMATION_SCHEMA.COLUMNS where table_schema = '" + DB + "' and table_name = '" + Sheet + "';")
        numb = numofcol['NumberofCol'][0]
        query = 'INSERT INTO ' + DB + '.' + Sheet + ' VALUES (' + numb * '%s,'
        query = query[:-1] + ');'
        print(query)
        # Check query
        self.cursor.executemany(query, val)
        print('INSERT ' + Sheet + ' COMPLETE')
        self.conn.commit()

    def ExtractDataESDL(self, TableName, Instances, SetofAttributes, SetofTables, SetofValues):

        if Instances == []:
            return
        valInstance = []
        for m in Instances:
            temp = tuple()
            for d in dir(m):
                e = getattr(m, d)
                if e == None:
                    temp += (None,)
                else:
                    if e == object:
                        temp += (e.id)
                    # add values of singleValue profiles in commodity prices
                    if isinstance(e, esdl.SingleValue):
                        temp += (str(e.value),)
                    else:
                        temp += (e,)
            valInstance.append(temp)

        InstanceAttr = tuple()
        for d in dir(Instances[0]):
            if d == 'id':
                InstanceAttr += (d + ' varchar(100) Primary Key',)
            else:
                InstanceAttr += (d + ' varchar(100)',)

        SetofAttributes.append(InstanceAttr)
        SetofTables.append(TableName)
        SetofValues.append(valInstance)

    def parse_esdl(self, esh, event=None, context=None):
        # xml_string = esh.to_string()
        # print(xml_string)

        SetofTables = []
        SetofAttributes = []
        SetofValues = []

        Assets = esh.get_all_instances_of_type(esdl.EnergyAsset)
        valAssets = []
        for n in Assets:
            tup = (n.id,
                   n.eClass.__name__,
                   n.aggregated,
                   n.aggregationCount,
                   n.assetType,
                   n.commissioningDate,
                   n.decommissioningDate,
                   n.description,
                   n.installationDuration,
                   n.manufacturer,
                   n.name,
                   n.originalIdInSource,
                   n.owner,
                   n.shortName,
                   n.state,
                   n.surfaceArea,
                   n.technicalLifetime,
                   n.costInformation.id if n.costInformation else None)
            if n.geometry:
                geo = n.geometry
                if type(n.geometry) == esdl.MultiLine:
                    geo = n.geometry.line
                if type(n.geometry) == esdl.Line:
                    geo = n.geometry.point[0]
                if type(n.geometry) == esdl.MultiPolygon:
                    geo = n.geometry.polygon
                if type(n.geometry) == esdl.Polygon:
                    if not n.geometry.interior:
                        geo = n.geometry.exterior.point[0]
                    elif not n.geometry.exterior:
                        geo = n.geometry.interior.point[0]
                tup = tup + (geo.lat, geo.lon)
            else:
                tup = tup + (None, None)
            valAssets.append(tup)

        if (Assets != []):
            SetofTables.append('Assets')
            SetofAttributes.append(('id varchar(100) Primary key',
                                    'esdlType varchar(100)',
                                    'aggregated varchar(100)',
                                    'aggregationCount varchar(100)',
                                    'assetType varchar(100)',
                                    'commissioningDate varchar(100)',
                                    'decommissioningDate varchar(100)',
                                    'description varchar(100)',
                                    'installationDuration varchar(100)',
                                    'manufacturer varchar(100)',
                                    'name varchar(1500)',
                                    'originalIdInSource varchar(100)',
                                    'owner varchar(100)',
                                    'shortname varchar(1500)',
                                    'state varchar(100)',
                                    'surfaceArea varchar(100)',
                                    'technicalLifetime varchar(100)',
                                    'costInformation_id varchar(100)',
                                    'lat varchar(100)',
                                    'lon varchar(100)'))
            SetofValues.append(valAssets)

        Producers = esh.get_all_instances_of_type(esdl.Producer)
        valProducers = [(n.id,
                         n.eClass.name,
                         n.name,
                         n.prodType,
                         n.operationalHours,
                         n.fullLoadHours,
                         convert_to_string(n.type) if hasattr(n, 'type') else None,
                         n.power)
                        for n in Producers]
        if (Producers != []):
            SetofAttributes.append(('id varchar(100) Primary key',
                                    'esdlType varchar(100)',
                                    'name varchar(1500)',
                                    'prodType varchar(100)',
                                    'operationalHours varchar(100)',
                                    'fullLoadHours varchar(100)',
                                    'type varchar(100)',
                                    'power varchar(100)'))
            SetofTables.append('Producers')
            SetofValues.append(valProducers)

        Consumers = esh.get_all_instances_of_type(esdl.Consumer)
        valConsumers = [(n.id, n.eClass.name, n.name, n.consType,
                         convert_to_string(n.type) if hasattr(n, 'type') else None, n.power)
                        for n in Consumers]

        if (Consumers != []):
            SetofAttributes.append(('id varchar(100)  Primary Key',
                                    'esdlType varchar(100)',
                                    'name varchar(1500)',
                                    'consType varchar(100)',
                                    'type varchar(100)',
                                    'power varchar(100)'))
            SetofTables.append('Consumers')
            SetofValues.append(valConsumers)

        Singlevalueprofiles = esh.get_all_instances_of_type(esdl.SingleValue)
        AssetProfiles = []
        valAssetProfiles = []
        for n in Assets:
            for p in n.port:
                for pr in p.profile:
                    AssetProfiles.append(pr)
                    if (pr in Singlevalueprofiles):
                        valAssetProfiles.append((n.id,
                                                 n.name,
                                                 'null',
                                                 'null',
                                                 'null',
                                                 'null',
                                                 'null',
                                                 pr.id,
                                                 'null',
                                                 'null',
                                                 pr.value,
                                                 pr.name,
                                                 'null',
                                                 'null',
                                                 'null'))
                    else:
                        valAssetProfiles.append((n.id,
                                                 n.name,
                                                 pr.dataSource,
                                                 pr.endDate,
                                                 pr.field, pr.filters,
                                                 pr.host,
                                                 pr.id,
                                                 pr.interpolationMethod,
                                                 pr.measurement,
                                                 pr.multiplier,
                                                 pr.name,
                                                 pr.profileQuantityAndUnit,
                                                 pr.profileType,
                                                 pr.startDate))
        if (valAssetProfiles != []):
            SetofAttributes.append(('id_Asset varchar(100)',
                                    'name_Asset varchar(100)',
                                    'dataSource varchar(100)',
                                    'endDate varchar(100)',
                                    'field varchar(100)',
                                    'filters varchar(100)',
                                    'host varchar(100)',
                                    'id varchar(100)',
                                    'interpolationMethod varchar(100)',
                                    'measurement varchar(100)',
                                    'multiplier varchar(100)',
                                    'name varchar(1500)',
                                    'profileQuantityAndUnit varchar(100)',
                                    'profileType varchar(100)',
                                    'startDate varchar(100)'))
            SetofTables.append('AssetProfiles')
            SetofValues.append(valAssetProfiles)

        Conversions = esh.get_all_instances_of_type(esdl.Conversion)
        valConversions = [
            (n.id, n.eClass.name, n.name, n.efficiency, convert_to_string(n.type) if hasattr(n, 'type') else None,
             n.power)
            for n in Conversions]
        if (Conversions != []):
            SetofAttributes.append(('id varchar(100)  Primary Key',
                                    'esdlType varchar(100)',
                                    'name varchar(1500)',
                                    'efficiency varchar(100)',
                                    'type varchar(100)',
                                    'power varchar(100)'))
            SetofTables.append('Conversions')
            SetofValues.append(valConversions)

        Transports = esh.get_all_instances_of_type(esdl.Transport)
        valTransports = [(n.id,
                          n.eClass.name,
                          n.name,
                          n.efficiency,
                          convert_to_string(n.type) if hasattr(n, 'type') else None,
                          n.capacity)
                         for n in Transports]
        if (Transports != []):
            SetofAttributes.append(('id varchar(100)  Primary Key',
                                    'esdlType varchar(100)',
                                    'name varchar(1500)',
                                    'efficiency varchar(100)',
                                    'type varchar(100)',
                                    'capacity varchar(100)'))
            SetofTables.append('Transports')
            SetofValues.append(valTransports)

        Storages = esh.get_all_instances_of_type(esdl.Storage)
        valStorages = [(n.id,
                        n.eClass.name,
                        n.name,
                        n.chargeEfficiency,
                        n.dischargeEfficiency,
                        n.selfDischargeRate,
                        n.fillLevel,
                        n.maxChargeRate,
                        n.maxDischargeRate,
                        convert_to_string(n.type) if hasattr(n, 'type') else None,
                        n.capacity)
                       for n in Storages]
        if (Storages != []):
            SetofAttributes.append(('id varchar(100)  Primary Key',
                                    'esdlType varchar(100)',
                                    'name varchar(1500)',
                                    'chargeEfficiency varchar(100)',
                                    'dischargeEfficiency varchar(100)',
                                    'selfDischargeRate varchar(100)',
                                    'fillLevel varchar(100)',
                                    'maxChargeRate varchar(100)',
                                    'maxDischargeRate varchar(100)',
                                    'type varchar(100)',
                                    'capacity varchar(100)'))
            SetofTables.append('Storages')
            SetofValues.append(valStorages)

        Arcs = esh.get_all_instances_of_type(esdl.OutPort)
        valArcs = []
        for a in Arcs:
            for b in a.connectedTo:
                valArcs.append((a.energyasset.name,
                                a.energyasset.id,
                                a.name,
                                a.id,
                                b.energyasset.name,
                                b.energyasset.id,
                                b.name,
                                b.id,
                                a.carrier.name if a.carrier else None,
                                a.carrier.id if a.carrier else None,
                                1))
                if a.carrier is None:
                    print(
                        f'Note: Arc {a.id} with name {a.name} of assets {a.energyasset.name} misses attribute (carrier)')

        if len(Arcs) > 0:
            SetofAttributes.append(('Node1_name varchar(1500)',
                                    'Node1_id varchar(100)',
                                    'Outport_name varchar(1500)',
                                    'Outport_id varchar(100)',
                                    'Node2_name varchar(1500)',
                                    'Node2_id varchar(100)',
                                    'Inport_name varchar(1500)',
                                    'Inport_id varchar(100)',
                                    'PRIMARY KEY (Node1_id, Node2_id)',
                                    'carrier varchar(100)',
                                    'carrier_id varchar(100)',
                                    'CostDummy varchar(100)'))
            SetofTables.append('Arcs')
            SetofValues.append(valArcs)
        #     valArcs = [(a.energyasset.name,
        #                 a.energyasset.id,
        #                 a.name,
        #                 a.id,
        #                 b.energyasset.name,
        #                 b.energyasset.id,
        #                 b.name,
        #                 b.id,
        #                 a.carrier.name,
        #                 a.carrier.id,
        #                 a.maxPower,
        #                 b.maxPower,
        #                 a.simultaneousPower,
        #                 b.simultaneousPower,
        #                 1)
        #                  for a in Arcs for b in a.connectedTo]
        #     SetofAttributes.append(('Node1_name varchar(1500)',
        #                             'Node1_id varchar(100)',
        #                             'Outport_name varchar(1500)',
        #                             'Outport_id varchar(100)',
        #                             'Node2_name varchar(1500)',
        #                             'Node2_id varchar(100)',
        #                             'Inport_name varchar(1500)',
        #                             'Inport_id varchar(100)',
        #                             'PRIMARY KEY (Node1_id, Node2_id)',
        #                             'carrier varchar(100)',
        #                             'carrier_id varchar(100)',
        #                             'maxPower_Out varchar(100)',
        #                             'maxPower_In varchar(100)',
        #                             'simultaneousPower_Out varchar(100)',
        #                             'simultaneousPower_In varchar(100)',
        #                             'CostDummy varchar(100)'))
        #     SetofTables.append('Arcs')
        #     SetofValues.append(valArcs)

        #     Processes = esh.get_all_instances_of_type(esdl.InputOutputRelation)
        # #     Processes = [a.behaviour for a in Conversions]
        # #     print(Processes)
        #     valProcesses = []
        #     for a in Processes:
        #         for i in a.mainPortRelation:
        #             if type(i.port) == esdl.InPort:
        #                 itype = 'In'
        #             else:  itype = 'Out'
        #             tup = (a.mainPort.id, a.name, a.mainPortQuantityAndUnit, a.id, itype)
        #             for j in dir(i):
        #                 k = getattr(i, j)
        #                 if (type(k) == type(None) or type(k) == float):
        #                     tup += (k,)
        #                     print(j,k)
        #                 else:
        #                     tup += (k.id,)
        #             valProcesses.append(tup)
        #     if(Processes != []):
        #         SetofAttributes.append(('mainPort  varchar(100)',
        #                                 'name  varchar(100)',
        #                                 'mainPortQuantityAndUnit  varchar(100)',
        #                                 'id  varchar(100)',
        #                                 'portType varchar(100)',
        #                                 'port varchar(100)',
        #                                 'quantityAndUnit varchar(100)',
        #                                 'ratio varchar(100)'))
        #         SetofTables.append('Processes')
        #         SetofValues.append(valProcesses)

        # valArcs=[]
        #     for a in Arcs:
        #         for b in a.connectedTo:
        #             if (a.carrier != None):
        #                 valArcs.append(a.energyasset.name,
        #                                a.energyasset.id,
        #                                a.name,
        #                                a.id,
        #                                b.energyasset.name,
        #                                b.energyasset.id,
        #                                b.name,
        #                                b.id,
        #                                a.carrier.name,
        #                                a.carrier.id,
        #                                1)

        Processes = Conversions
        valProcesses = []
        for a in Conversions:
            if (len(a.port) > 1):
                for b in a.port:
                    ratio = 1
                    if (a.behaviour):
                        for i in a.behaviour:
                            mainport = i.mainPort
                            for j in i.mainPortRelation:
                                if (j.port == b):
                                    ratio = j.ratio
                                    break;

                    else:
                        ratio = a.efficiency
                        mainport = a.port[1]
                    if type(a.port[0]) == esdl.InPort:
                        atype = 'In'
                    else:
                        atype = 'Out'
                    if type(b) == esdl.InPort:
                        btype = 'In'
                    else:
                        btype = 'Out'
                    # print(mainport)
                    # print(mainport.carrier)
                    # print(b)
                    if (mainport.carrier != None):
                        tup = (
                            'null', mainport.id, mainport.carrier.id, atype, b.id, btype, a.id, a.name, ratio,
                            b.carrier.id,
                            b.carrier.name)
                        valProcesses.append(tup)
                    else:
                        print(f'Note that process {b.id} misses attribute (carrier)')

        if (valProcesses != []):
            SetofAttributes.append(('quantityAndUnit varchar(100)',
                                    'mainPortId varchar(100)',
                                    'mainPortCarrierId varchar(100)',
                                    'mainPortType varchar(100)',
                                    'portId varchar(100)',
                                    'portType varchar(100)',
                                    'conversionId varchar(100)',
                                    'conversionname varchar(1500)',
                                    'ratio varchar(100)',
                                    'carrierId varchar(100)',
                                    'carriername varchar(1500)'))
            SetofTables.append('Processes')
            SetofValues.append(valProcesses)

        Carriers = esh.get_all_instances_of_type(esdl.Carrier)
        valCarriers = [(p.id,
                        p.name,
                        p.cost.value if p.cost and p.cost.value else None)
                       for p in Carriers]
        if (Carriers != []):
            SetofAttributes.append(('id varchar(100) Primary Key',
                                    'name varchar(1500)',
                                    'cost varchar(100)'))
            SetofTables.append('Carriers')
            SetofValues.append(valCarriers)

        EnergyCarriers = esh.get_all_instances_of_type(esdl.EnergyCarrier)
        valEnergyCarriers = [(p.id,
                              p.stateOfMatter,
                              p.energyCarrierType,
                              p.emission,
                              p.name,
                              p.energyContent)
                             for p in EnergyCarriers]
        if (EnergyCarriers != []):
            SetofAttributes.append(('id varchar(100) Primary Key',
                                    'stateOfMatter varchar(100)',
                                    'energyCarrierType varchar(100)',
                                    'emission varchar(100)',
                                    'name varchar(1500)',
                                    'energyContent varchar(100)'))
            SetofTables.append('EnergyCarriers')
            SetofValues.append(valEnergyCarriers)

        GasCommodities = esh.get_all_instances_of_type(esdl.GasCommodity)
        if (GasCommodities != []):
            self.ExtractDataESDL('GasCommodities', GasCommodities, SetofAttributes, SetofTables, SetofValues)

        ElectricityCommodities = esh.get_all_instances_of_type(esdl.ElectricityCommodity)
        if (ElectricityCommodities != []):
            self.ExtractDataESDL('ElectricityCommodities', ElectricityCommodities, SetofAttributes, SetofTables,
                                 SetofValues)

        EnergyCommodities = esh.get_all_instances_of_type(esdl.EnergyCommodity)
        if (EnergyCommodities != []):
            self.ExtractDataESDL('EnergyCommodities', EnergyCommodities, SetofAttributes, SetofTables, SetofValues)

        Commodities = esh.get_all_instances_of_type(esdl.Commodity)
        valCommodities = [(h.id, h.name)
                          for h in Commodities]
        if (Commodities != []):
            SetofAttributes.append(('id varchar(100)  Primary Key',
                                    'name varchar(1500)'))
            SetofTables.append('Commodities')
            SetofValues.append(valCommodities)

        Matters = esh.get_all_instances_of_type(esdl.Matter)
        if (Matters != []):
            self.ExtractDataESDL('Matters', Matters, SetofAttributes, SetofTables, SetofValues)
        #     Matters = esh.get_all_instances_of_type(esdl.Matter)
        #     valMatters =[]
        #     for m in Matters:
        #         temp = tuple()
        #         for d in dir(m):
        #             e = getattr(m, d)
        #             if e == None:
        #                 temp+= (None,)
        #             else:
        #                 temp+=(e,)
        #         valMatters.append(temp)

        #     MatterAttr = tuple()
        #     for d in dir(Matters[0]):
        #         if d == 'id':
        #             MatterAttr += (d  + ' varchar(100) Primary Key',)
        #         else:
        #             MatterAttr += (d  + ' varchar(100)',)
        #     SetofAttributes.append(MatterAttr)
        #     SetofTables.append('Matters')
        #     SetofValues.append(valMatters)

        #     Buildings = esh.get_all_instances_of_type(esdl.Building)
        #     ExtractDataESDL('Buildings',Buildings, SetofAttributes, SetofTables, SetofValues)
        Buildings = esh.get_all_instances_of_type(esdl.Building)
        valBuildings = [(a.id,
                         a.floorArea,
                         a.buildingYear,
                         a.originalIdInSource,
                         a.surfaceArea,
                         a.name,
                         a.buildinginformation[0].height,
                         a.geometry.exterior.point[0].lat,
                         a.geometry.exterior.point[0].lon)
                        for a in Buildings]
        if (Buildings != []):
            SetofAttributes.append(('id varchar(100) Primary Key',
                                    'floorArea varchar(100)',
                                    'buildingYear varchar(100)',
                                    'originalIdInSource varchar(100)',
                                    'surfaceArea varchar(100)',
                                    'name varchar(1500)',
                                    'height varchar(100)',
                                    'Lat varchar(100)',
                                    'Lon varchar(100)'))
            SetofTables.append('Buildings')
            SetofValues.append(valBuildings)

            MapAssetToBuilding = [b for a in Buildings for b in a.asset]
            valMapAssetToBuilding = [(b.id, b.name, a.id, a.name, '1') for a in Buildings for b in a.asset]
            SetofAttributes.append(('id_Asset varchar(100) Primary Key',
                                    'name_Asset varchar(100)',
                                    'id_Building varchar(100)',
                                    'name_Building varchar(700)',
                                    'Dummy varchar(100)'))
            SetofTables.append('MapAssetToBuilding')
            SetofValues.append(valMapAssetToBuilding)

        KPIs = esh.get_all_instances_of_type(esdl.KPI)
        valKPIs = [(k.id,
                    k.name,
                    k.value if type(k) in [esdl.IntKPI, esdl.DoubleKPI, esdl.StringKPI] else None)
                   for k in KPIs]
        # for k in KPIs:
        #     if type(k) in [esdl.IntKPI, esdl.DoubleKPI, esdl.StringKPI]:
        #         print(type(k))
        #         valKPIs.append((k.id,k.name,k.value))
        #     elif type(k) == esdl.DistributionKPI:
        #         valKPIs.append((k.id, k.name, 'null'))
        #     else:
        #         print("KPI type: ", type(k), " is not supported")
        SetofAttributes.append(('id_KPI varchar(100)',
                                'name_KPI varchar(100)',
                                'value_KPI varchar(100)'))
        SetofTables.append('KPIs')
        SetofValues.append(valKPIs)

        KPIsBuildings = []
        valKPIsBuildings = []
        if (Buildings != []):
            for b in Buildings:
                ks = b.KPIs
                if (ks):
                    KPIsBuildings.append(ks)
                    for i in range(len(ks.kpi)):
                        temp = (ks.kpi[i].id,
                                ks.kpi[i].name,
                                ks.kpi[i].value if type(ks.kpi[i]) in [esdl.IntKPI, esdl.DoubleKPI,
                                                                       esdl.StringKPI] else None,
                                b.id,
                                b.name)
                        valKPIsBuildings.append(temp)

        if (valKPIsBuildings != []):
            SetofAttributes.append(('id_KPI varchar(100)',
                                    'name_KPI varchar(100)',
                                    'value_KPI varchar(100)',
                                    'id_building varchar(100)',
                                    'name_building varchar(1500)'))
            SetofTables.append('KPIsBuildings')
            SetofValues.append(valKPIsBuildings)

        KPIsAssets = []
        valKPIsAssets = []
        if (Assets != []):
            for b in Assets:
                ks = b.KPIs
                if (ks):
                    KPIsAssets.append(ks)
                    for i in range(len(ks.kpi)):
                        temp = (ks.kpi[i].id,
                                ks.kpi[i].name,
                                ks.kpi[i].value if type(ks.kpi[i]) in [esdl.IntKPI, esdl.DoubleKPI,
                                                                       esdl.StringKPI] else None,
                                b.id,
                                b.name)
                        valKPIsAssets.append(temp)

            SetofAttributes.append(('id_KPI varchar(100)',
                                    'name_KPI varchar(100)',
                                    'value_KPI varchar(100)',
                                    'id_asset varchar(100)',
                                    'name_asset varchar(100)',
                                    'PRIMARY KEY (id_KPI, id_asset)'))
            SetofTables.append('KPIsAssets')
            SetofValues.append(valKPIsAssets)

        CostInformations = esh.get_all_instances_of_type(esdl.CostInformation)
        valCostInformations = []
        for a in Assets:
            c = a.costInformation
            if (a.costInformation):
                temp = (a.id, a.name)
                for d in dir(c):
                    e = getattr(c, d)
                    if e == None or type(e) == str:
                        temp += (None,)
                    else:
                        temp += (e.value,)
                valCostInformations.append(temp)
        CostInformationsAtt = ('AssetId varchar(100)', 'Assetname varchar(1500)')
        if (CostInformations != []):
            for d in dir(CostInformations[0]):
                CostInformationsAtt += (d + ' varchar(100)',)
            SetofAttributes.append(CostInformationsAtt)
            SetofTables.append('CostInformations')
            SetofValues.append(valCostInformations)

        Constraints = []
        valConstraints = []
        for a in Assets:
            for b in a.constraint:
                Constraints.append(b)
                # print(type(b.attributeReference))
                temp = (a.id, a.name, b.id, b.name, b.attributeReference)
                c = b.range
                if (c):
                    temp += (c.id, c.name, c.minValue, c.maxValue)
                else:
                    temp += (None, None, None, None)

                valConstraints.append(temp)

        #             ('NodeId varchar(100)',
        #                       'Nodename varchar(1500)',
        #                       ' varchar(100)',
        #                       'Constraintname varchar(1500)',
        #                       'ConstraintAttribute varchar(100)',
        #                       'RangeId varchar(100)',
        #                       'Rangename varchar(1500)',
        #                       'minValue varchar(100)',
        #                       'maxValue varchar(100)')
        if (Constraints != []):
            SetofAttributes.append(('Node_Id varchar(100)',
                                    'Node_name varchar(1500)',
                                    'Constraint_Id varchar(100)',
                                    'Constraint_name varchar(1500)',
                                    'Constraint_Attribute varchar(100)',
                                    'range_Id varchar(100)',
                                    'range_name varchar(1500)',
                                    'min varchar(100)',
                                    'max varchar(100)'))
            SetofTables.append('Constraints')
            SetofValues.append(valConstraints)

        QuantityAndUnitTypes = esh.get_all_instances_of_type(esdl.QuantityAndUnitType)
        valCarrierQuantityAndUnitTypes = []
        valEnergyContentUnit = []
        valEmissionUnits = []
        for c in Carriers:
            e = c.emissionUnit
            if (e):
                temp = (c.id, c.name, 'emissionUnit')
                for d in dir(e):
                    a = getattr(e, d)
                    if a == None:
                        temp += (None,)
                    else:
                        temp += (a,)
                valEmissionUnits.append(temp)
                valCarrierQuantityAndUnitTypes.append(temp)
            if c not in Commodities:
                f = c.energyContentUnit
                if (f):
                    temp = (c.id, c.name, 'energyContentUnit')
                    for d in dir(f):
                        a = getattr(f, d)
                        if a == None:
                            temp += (None,)
                        else:
                            temp += (a,)
                    valEnergyContentUnit.append(temp)
                    valCarrierQuantityAndUnitTypes.append(temp)

        CarrierQuantityAndUnitTypesAtt = (
            'CarrierId varchar(100)', 'CarrierDescription varchar(100)', 'type varchar(100)')
        if (QuantityAndUnitTypes != []):
            for d in dir(QuantityAndUnitTypes[0]):
                CarrierQuantityAndUnitTypesAtt += (d + ' varchar(100)',)
            SetofAttributes.append(CarrierQuantityAndUnitTypesAtt)
            SetofTables.append('CarrierQuantityAndUnitTypes')
            SetofValues.append(valCarrierQuantityAndUnitTypes)

        valAssetQuantityAndUnitTypes = []
        valAssetQuantityAndUnitReferences = []
        valAssetQuantityAndUnitInfluxDB = []

        QuantityAndUnitReferences = esh.get_all_instances_of_type(esdl.QuantityAndUnitReference)
        InfluxDBProfiles = esh.get_all_instances_of_type(esdl.InfluxDBProfile)
        for a in Assets:
            for p in a.port:
                for pr in p.profile:
                    temp = (a.id, a.name, p.id)
                    if (pr in QuantityAndUnitReferences):
                        pr = pr.reference
                    if (pr in InfluxDBProfiles):
                        temp += (pr.id,
                                 pr.profileType,
                                 pr.profileQuantityAndUnit,
                                 pr.name,
                                 pr.interpolationMethod,
                                 pr.dataSource,
                                 pr.multiplier)
                        valAssetQuantityAndUnitInfluxDB.append(temp)
                        temp = (a.id, a.name, p.id)
                        pr = pr.profileQuantityAndUnit

                    if (type(pr) == esdl.QuantityAndUnitType):
                        for q in dir(QuantityAndUnitTypes[0]):
                            e = getattr(pr, q)
                            if e == None:
                                temp += (None,)
                            else:
                                temp += (e,)
                        valAssetQuantityAndUnitTypes.append(temp)
                    else:
                        print(f"Profile type {type(pr)} is not supported")

        if (len(QuantityAndUnitTypes) > 0):
            AssetQuantityAndUnitTypesAtt = ['asset_id varchar(100)', 'asset_name varchar(100)', 'port_id varchar(100)']
            for d in dir(QuantityAndUnitTypes[0]):
                AssetQuantityAndUnitTypesAtt += (d + ' varchar(100)',)
            SetofAttributes.append(AssetQuantityAndUnitTypesAtt)
            SetofTables.append('AssetQuantityAndUnitTypes')
            SetofValues.append(valAssetQuantityAndUnitTypes)
        if (len(InfluxDBProfiles) > 0):
            AssetQuantityAndUnitInfluxDBAtt = ['asset_id varchar(100)', 'asset_name varchar(100)',
                                               'port_id varchar(100)']
            AssetQuantityAndUnitInfluxDBAtt += ('id varchar(100)',
                                                'profileType varchar(100)',
                                                'profileQuantityAndUnit varchar(100)',
                                                'name varchar(100)',
                                                'interpolationMethod varchar(100)',
                                                'dataSource varchar(100)',
                                                'multiplier varchar(100)')
            SetofAttributes.append(AssetQuantityAndUnitInfluxDBAtt)
            SetofTables.append('AssetQuantityAndUnitInfluxDB')
            SetofValues.append(valAssetQuantityAndUnitInfluxDB)

        #     GenericProfiles = esh.get_all_instances_of_type(esdl.GenericProfile)
        #     valGenericProfiles = [(p.profileType,
        #                            p.profileQuantityAndUnit,
        #                            p.name,
        #                            p.interpolationMethod,
        #                            p.dataSource,
        #                            p.setProfile,
        #                            p.id,
        #                            p.getProfile)
        #                            for p in GenericProfiles]
        #     SetofAttributes.append(('profileType varchar(100)',
        #                           'profileQuantityAndUnit varchar(100)',
        #                           'name varchar(1500)',
        #                           'interpolationMethod varchar(100)',
        #                           'dataSource varchar(100)',
        #                           'setProfile varchar(100)',
        #                           'id varchar(100) Primary Key',
        #                           'getProfile varchar(100)'))
        #     SetofTables.append('GenericProfiles')
        #     SetofValues.append(valGenericProfiles)

        #     SingleValues = esh.get_all_instances_of_type(esdl.SingleValue)
        #     valSingleValues = [(p.id, p.value) for p in SingleValues]
        #     SetofAttributes.append(('id varchar(100) Primary Key', 'value varchar(100)'))
        #     SetofTables.append('SingleValues')
        #     SetofValues.append(valSingleValues)

        self.create_AIMMS_sql(self.database_name, SetofTables, SetofAttributes)

        #   for loop that writes the tuple of values to the new database in the corresponding table.
        for a in range(len(SetofTables)):
            print('Exporting:', SetofTables[a])  # , SetofValues[a])
            self.write_table_to_Sql(self.database_name, SetofTables[a], SetofValues[a])

# # In[3]:

# import sys

# conn = pymysql.connect(
#     host= Host,
#     user=User,
#     password=PW)
# cursor = conn.cursor()

# def str_to_class(classname):
#     return getattr(sys.modules[__name__], classname)


# def Check_dir(my_class):
#     Attributes = [dir(n) for n in my_class]
#     AllAttributes = set(sum(Attributes, []))
#     return AllAttributes

# if __name__ == "__main__" :
#     #The next set contains all the ESDL classes that have been included in the last main function
#     ThingsInESDL = get_sql("Select table_schema as database_name, table_name from information_schema.tables where table_type = 'BASE TABLE'and table_schema = '" + DB + "' order by database_name, table_name;").table_name
#     for i in ThingsInESDL:
#         print(i)
#         dirThing = Check_dir(str_to_class(i))
#         print(i, ': ')
#         for j in dirThing:
#             print('   ',j)

# conn.close()

# if __name__ == "__main__":
#     load_dotenv()  # load environmental variables such as database credentials and input file from the .env file (see .env-template)
#
#     Filename = os.getenv("ESDL_INPUT_FILENAME")
#     Outputfile = os.getenv("ESDL_OUTPUT_FILENAME")
#     Host = os.getenv("DATABASE_HOST")
#     DB = os.getenv("DATABASE_NAME")
#     User = os.getenv("DATABASE_USER")
#     PW = os.getenv("DATABASE_PASSWORD")
#
#     print("ESDL-AIMMS Universal link")
#     print(f"Config: db={DB}, host={Host}, inputFile={Filename}, outputFile={Outputfile}")
#     print(f'Processing ESDL...')
#
#     # use sqlAlchemy to connect to (any) database, instead of using direct connection
#     # this removes the pandas warning
#
#     ul = UniversalLink(Host, DB, User, PW)
#     print(ul.esdl_to_db(Filename))
#
