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
    '''
    Initiates main class and connects to database using host/database/user/password
    '''

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

    '''
    Main function that loads esh + file from database, runs the core function parse_esdl and catches errors
    '''

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

    '''
    Auxiliary function that reads from (newly created) sql file on the database using pandas
    '''

    def get_sql(self, query):
        """
        :param query: SQL-related command
        :return: result: dataframe with SQL file related information
        """
        try:
            result = pd.read_sql(query, self.database_url)
            return result
        except pymysql.Error as e:
            print("Error: unable to fetch data %d: %s" % (e.args[0], e.args[1]))

    '''
    Creates SQL database (deletes old database if name already exists)
    '''

    def create_AIMMS_sql(self, DB, SetofTables, SetofAttributes):
        """
        :param DB: database name
        SetofTables: list of table names (see parse_esdl)
        SetofAttributes: list of tuples, each tuple containing the attributes of the corresponding table in SetofTables
        """
        print(f"Removing and recreate database {DB}")
        self.cursor.execute('DROP DATABASE IF EXISTS ' + DB + ';')
        self.cursor.execute('create database ' + DB + ';')
        self.conn.select_db(DB)

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

    '''
    Writes data to corresponding table in the SQL file
    '''

    def write_table_to_Sql(self, DB, Sheet, val):
        """
        :param DB: database name
        Sheet: Table name (i.e. SetofTables[i])
        val: Data to be written (i.e. SetofValues[i])
        """
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

    '''
    Reads and saves data for certain (right format) esdl instances
    '''

    def ExtractDataESDL(self, TableName, Instances, SetofAttributes, SetofTables, SetofValues):
        """
        :param Tablename: string with table name
        Instances: instance to read from (output of esdl.get_all_instances_of_type)
        SetofTables/SetofAttributes/SetofValues: lists to which to append extracted data
        """
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

    '''
    Core function which extracts data from ESDL file, stores relevant data in SetofValues/SetofAttributes/SetofTables
    and creates and writes to a new AIMMS-friendly SQL file 

    Since most tables have different properties and only specific data is required, each table is treated seperately. 
    For each desired table this function:
    i) Opens the corresponding instance from ESDL
    ii) Reads the desired attributes and stores them in the temporary list "valXXX"
    iii) Checks if the instance exists/is non-empty and if so:
    iv) Stores the table name to SetofTables, the attribute names (formatted for SQL) to SetofAttributes and the data to SetofValues

    The following 25 tables are currently read: 
    Assets, Producers, Consumers, AssetProfiles, Conversions, 
    Transports, Storages, Arcs, Processes, Carriers, EnergyCarriers, GasCommodities, 
    ElectricityCommodities, ElectricityCommodities, EnergyCommodities, Commodities, 
    Matters, Buildings, KPIs, KPIsBuildings, KPIsAssets, CostInformations, Constraints, 
    CarrierQuantityAndUnitTypes, AssetQuantityAndUnitTypes
    '''

    def parse_esdl(self, esh, event=None, context=None):
        """
        :param esh: input given by esh.load_file(esdl_filename)
        """

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

        CostInformations = esh.get_all_instances_of_type(esdl.CostInformation)
        valCostInformations = []
        valCostUnits = []
        for a in Assets:
            c = a.costInformation
            if (a.costInformation):
                temp = (a.id, a.name)
                for d in dir(c):
                    e = getattr(c, d)
                    if e == None or type(e) == str:
                        temp += (None,)
                    elif type(e) == int:
                        temp += (e,)
                    else:
                        temp += (e.value,)
                        if e.profileQuantityAndUnit:
                            pr = e.profileQuantityAndUnit
                            unit = (a.id, a.name, d)
                            if (pr in QuantityAndUnitReferences):
                                pr = pr.reference
                            if (pr in InfluxDBProfiles):
                                print(f"Profile type {type(pr)} is not supported")
                                # unit += (pr.id,
                                #          pr.profileType,
                                #          pr.profileQuantityAndUnit,
                                #          pr.name,
                                #          pr.interpolationMethod,
                                #          pr.dataSource,
                                #          pr.multiplier)
                                # valCostUnits.append(unit)
                                pr = pr.profileQuantityAndUnit
                            if (type(pr) == esdl.QuantityAndUnitType):
                                for q in dir(QuantityAndUnitTypes[0]):
                                    f = getattr(pr, q)
                                    if f == None:
                                        unit += (None,)
                                    else:
                                        unit += (f,)
                                valCostUnits.append(unit)
                            else:
                                print(f"Profile type {type(pr)} is not supported")
                            print(unit)
                valCostInformations.append(temp)
        CostInformationsAtt = ('AssetId varchar(100)','AssetName varchar(100)')
        if (CostInformations != []):
            for d in dir(CostInformations[0]):
                CostInformationsAtt += (d + ' varchar(100)',)
            SetofAttributes.append(CostInformationsAtt)
            SetofTables.append('CostInformations')
            SetofValues.append(valCostInformations)

        CostUnitAtt = ('AssetId varchar(100)', 'AssetName varchar(100)', 'CostType varchar(100)')
        print(CostUnitAtt)
        if valCostUnits != []:
            for d in dir(QuantityAndUnitTypes[0]):
                CostUnitAtt += (d + ' varchar(100)',)
            SetofAttributes.append(CostUnitAtt)
            SetofTables.append('UnitCostinformation')
            SetofValues.append(valCostUnits)


        Constraints = []
        valConstraints = []
        for a in Assets:
            for b in a.constraint:
                Constraints.append(b)
                temp = (a.id, a.name, b.id, b.name, b.attributeReference)
                c = b.range
                if (c):
                    temp += (c.id, c.name, c.minValue, c.maxValue)
                else:
                    temp += (None, None, None, None)

                valConstraints.append(temp)
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

        self.create_AIMMS_sql(self.database_name, SetofTables, SetofAttributes)

        #  for loop that writes the tuple of values to the new database in the corresponding table.
        for a in range(len(SetofTables)):
            print('Exporting:', SetofTables[a])
            self.write_table_to_Sql(self.database_name, SetofTables[a], SetofValues[a])


import os
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()  # load environmental variables such as database credentials and input file from the .env file (see .env-template)

    from tno.aimms_adapter.settings import EnvSettings

    print("ESDL-AIMMS Universal link")
    print(f'Processing ESDL...')

    # use sqlAlchemy to connect to (any) database, instead of using direct connection
    # this removes the pandas warning

    ul = UniversalLink( EnvSettings.db_host(),  EnvSettings.db_name(), EnvSettings.db_user(), EnvSettings.db_password())
    inputfilename = "ESDLs\KPIs Meso Iter\output_file_2_ETM_KPI.esdl"
    print('ESDL:', "...", inputfilename)
    success, error = ul.esdl_to_db(inputfilename)
