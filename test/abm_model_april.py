from pathlib import Path

import pandas as pd
from geopandas import GeoDataFrame
import random
import numpy as np
import math

import mesa
import mesa_geo as mg

from shapely import geometry
from shapely.geometry.polygon import orient

from enum import Enum

import esdl
import uuid
from esdl.esdl_handler import EnergySystemHandler
from esdl import Point
from pyecore.resources import ResourceSet, URI
from loguru import logger
from tno.aimms_adapter.data_types import TeacosAdapterConfig

rset = ResourceSet()

""" Construct the Agent Class for the companies, using mesa and geo mesa"""


class Agent(mg.GeoAgent):
    def __init__(self, unique_id, initialState, model, building, geometry, crs):
        super().__init__(unique_id=unique_id, model=model, geometry=geometry, crs=crs)
        self.state = initialState
        self.building: esdl.AbstractBuilding() = building

        self.radius = self.model.radius
        self.socialFactor = None
        self.financialFactor = None
        self.chanceOfBuying = None
        self.wantToBuy = False
        self.bought = False

        self.funds = np.random.normal(self.model.budget)

        self.m2RooftopAvailable = 0
        self.PVPanelBatchSize = self.model.PVPanelBatchSize
        self.PVPanelsBought = 0
        self.PVPanelsInstalled = 0

        self.KPIs = self.building.KPIs.kpi
        self.yearlykWh = self.building.KPIs.kpi[2].value

    def calculateFinancialFactor(self):
        PVPanelLifetime = 25
        costPerkWh = 0.50
        PVPanelCost = self.model.costOfPVPanel
        PVPanelYearlySavings = self.model.PVPanelYearlykWh * costPerkWh
        PVPanelLifetimeSavings = PVPanelYearlySavings * PVPanelLifetime
        PVPanelROI = (PVPanelLifetimeSavings - PVPanelCost) / PVPanelCost
        PVPanelROIDisaggregrated = PVPanelROI / PVPanelLifetime
        self.financialFactor = min(1, PVPanelROIDisaggregrated)

    def calculateSocialFactor(self):
        self.socialFactor = sum([a.bought for a in self.model.space.get_neighbors_within_distance(self, self.radius)]) / (
                        len(
                            [a.building.name for a in self.model.space.get_neighbors_within_distance(self, self.radius)]
                            ))
    def combineFactors(self):
        self.chanceOfBuying = 0.33 * self.socialFactor + 0.66 * self.financialFactor

    def toBuyOrNotToBuy(self):
        if random.uniform(0, 1) <= self.chanceOfBuying:
            self.wantToBuy = True
            return True

    def checkFunding(self):
        if self.funds > (self.PVPanelBatchSize * self.model.costOfPVPanel):
            return True

    def checkRooftopSpace(self):
        if self.m2RooftopAvailable >= (
                self.model.sizeOfPVPanel * self.PVPanelBatchSize
        ):
            return True

    def checkLimit(self):
        if self.model.numberOfPVPanelsAvailable >= self.PVPanelBatchSize:
            return True

    def buyPVPanel(self):
        self.bought = True
        self.state = State.Bought
        self.PVPanelsBought = +self.PVPanelBatchSize
        self.model.numberOfPVPanelsBought = (
                self.model.numberOfPVPanelsBought + self.model.PVPanelBatchSize
        )
        self.model.numberOfPVPanelsAvailable = (
                self.model.numberOfPVPanelsAvailable - self.PVPanelBatchSize
        )
        self.funds = self.funds - (self.model.costOfPVPanel * self.PVPanelBatchSize)

    def checkIfPVPanelAlreadyExists(self):
        for asset in self.building.asset:
            if isinstance(asset, esdl.PVInstallation):
                return True

    """ Install the PV panel """

    def installPVPanel(self):
        if self.checkIfPVPanelAlreadyExists():
            for asset in self.building.asset:
                if isinstance(asset, esdl.PVInstallation):
                    asset.power = float(asset.power + ((self.model.PVPanelYearlykWh/1108.22)*1000))
        else:
            PVPanel = esdl.PVInstallation(
                name="PV Panel",
                id=str(uuid.uuid4()),
                power=float((self.model.PVPanelYearlykWh / 1108.22) * 1000),
                geometry=Point(lat=250.0, lon=200.0),
            )
            self.building.asset.append(PVPanel)
            """ Create an Out Port so the new asset can be connected to the rest of the network in the ESDL file"""
            for asset in self.building.asset:
                if isinstance(asset, esdl.esdl.EConnection):
                    for port in asset.port:
                        if port.name == "In":
                            InPortElec = port
            outPortPV = esdl.OutPort(id=str(uuid.uuid4()), connectedTo=[InPortElec])
            outPortPV.carrier = InPortElec.carrier
            for asset in self.building.asset:
                if isinstance(asset, esdl.esdl.PVInstallation):
                    asset.port.append(outPortPV)

        self.PVPanelsInstalled += self.PVPanelBatchSize
        self.m2RooftopAvailable -= self.model.sizeOfPVPanel * self.PVPanelBatchSize

    def changeStatusPV(self):
        """Change the status of the PV panel back to OPTIONAL for TEACOS and reset the power"""
        for asset in self.model.topLevelArea.asset:
            if isinstance(asset, esdl.esdl.PVInstallation):
                if asset.state == esdl.AssetStateEnum.ENABLED or asset.state == esdl.AssetStateEnum.DISABLED:
                    asset.state = esdl.AssetStateEnum.OPTIONAL
                if asset.power != 0:
                    asset.power = 0.0
                    print(type(asset.power), asset.power)

    """ Define steps taken by agent during the tick """
    def step(self):
        decisionMoments = [3, 6, 9, 12]
        if decisionMoments.count(self.model.tickCounter):
            self.calculateFinancialFactor()
            self.calculateSocialFactor()
            self.combineFactors()
            while (
                    self.toBuyOrNotToBuy()
                    and self.checkFunding()
                    and self.checkRooftopSpace()
                    and self.checkLimit()
            ):
                self.buyPVPanel()
                self.installPVPanel()
        if self.model.tickCounter == 12:
            self.changeStatusPV()


class State(Enum):
    HasntBought = 0
    Bought = 1


def number_state(model, state):
    return sum([1 for a in model.schedule.agents if a.state is state])


def numberHasntBought(model):
    return number_state(model, State.HasntBought)


def numberBought(model):
    return number_state(model, State.Bought)


def panelsBought(model):
    return model.numberOfPVPanelsBought


class TholenModel(mesa.Model):
    """A model with some number of agents."""

    def __init__(
            self,
            radius,
            budget,
            PVPanelBatchSize,
            CostOfPVPanel,
            input_esdl_file_path,
            output_esdl_file_path = None
    ):
        self.space = mg.GeoSpace()
        self.schedule = mesa.time.RandomActivation(self)
        self.tickCounter = 0
        self.energySystem = None
        self.radius = radius
        self.budget = budget

        self.numberOfPVPanelsWanted = 0
        self.numberOfPVPanelsAvailable = 0
        self.numberOfPVPanelsBought = 0
        self.costOfPVPanel = CostOfPVPanel
        self.sizeOfPVPanel = 2
        self.PVPanelBatchSize = PVPanelBatchSize

        self.PVPanelYearlykWh = 375
        self.totalRooftopArea = 0
        self.totalPower = 0

        self.TEACOSDecision = None

        if output_esdl_file_path is None:
            self.output_esdl_file_path = f"output/random_runs/{str(uuid.uuid4())}" \
                                         f"/{Path(input_esdl_file_path).stem}.esdl"
        else:
            self.output_esdl_file_path = output_esdl_file_path

        """ Initialize datacollector """

        # ''' Mengs Datacollector '''
        # self.datacollector = mesa.DataCollector(
        #     agent_reporters={"Bought": "bought",
        #                      "Financial Factor": "financialFactor",
        #                      "Social Factor": "socialFactor",
        #                      "Chance of Buying": "chanceOfBuying",
        #                      "Budget": "funds",
        #                      "Rooftop": "m2RooftopAvailable",
        #                      }
        # )

        """EMA workbench specific datacollector """
        self.datacollector = mesa.DataCollector(
            {
                "Agents With Solar Panels": numberBought,
                "Agents Without Solar Panels": numberHasntBought,
                "Solar Panels Bought": panelsBought,
            }
        )

        """ Load ESDL-file into the model  """
        esh = EnergySystemHandler()
        esh.load_file(input_esdl_file_path)
        # esh.load_file(f"../data/{filename}")
        self.energySystem = esh.get_energy_system()
        self.instance = self.energySystem.instance[0]
        self.topLevelArea = self.instance.area
        self.buildingList = self.topLevelArea.asset

        """ Create two empty lists with all Polygons and IDs, which will be used later on to get the roof surface of the buildings """
        listOfPolygons = []
        listOfIDs = []

        """ Create the agents by looping over the Building asset in the ESDL-file, using inheritance """
        for i, building in enumerate(self.buildingList):
            """Define which assets are used, in this case the Abstract Building asset from the ESDL-file"""
            if building is not None and isinstance(
                    building, esdl.esdl.AbstractBuilding
            ):
                """Save the Polygons and IDs per building in the lists"""
                listOfPolygons.append(
                    geometry.Polygon(
                        [
                            [p.lon, p.lat]
                            for p in building.geometry.eContents[0].eContents
                        ]
                    )
                )
                listOfIDs.append(i)

                """ Create the agent """
                agent = Agent(
                    unique_id=i,
                    model=self,
                    initialState=State.HasntBought,
                    building=building,
                    crs="epsg:3857",
                    geometry=geometry.Polygon(
                        [
                            [p.lon, p.lat]
                            for p in building.geometry.eContents[0].eContents
                        ]
                    ),
                )

                """ Add the agents to the model """
                self.schedule.add(agent)
                self.space.add_agents(agent)

        """ Start to convert Polygon area to square meters """
        data = {"unique_id": listOfIDs, "geometry": listOfPolygons}

        df = pd.DataFrame(data)
        gdf = GeoDataFrame(df)
        gdf.crs = 3857

        """ A function to get square meters from the used projection """

        def gpd_geographic_area(geodf):
            if not geodf.crs and geodf.crs.is_geographic:
                raise TypeError("geodataframe should have geographic coordinate system")

            geod = geodf.crs.get_geod()

            def area_calc(geom):
                if geom.geom_type not in ["MultiPolygon", "Polygon"]:
                    return np.nan

                # For MultiPolygon do each separately
                if geom.geom_type == "MultiPolygon":
                    return np.sum([area_calc(p) for p in geom.geoms])

                # orient to ensure a counter-clockwise traversal.
                # See https://pyproj4.github.io/pyproj/stable/api/geod.html
                # geometry_area_perimeter returns (area, perimeter)
                return geod.geometry_area_perimeter(orient(geom, 1))[0]

            return geodf.geometry.apply(area_calc)

        """ Get the square meters from the polygons """
        listOfSquareMeters = gpd_geographic_area(gdf)

        """ Assign square meters of Rooftop available per agent """
        for agent, area in zip(self.schedule.agents, listOfSquareMeters):
            setattr(agent, "m2RooftopAvailable", area)

        """ Calculate how many PV Panels are wanted based on TEACOS output """
        for object in self.buildingList:
            if (
                    isinstance(object, esdl.PVInstallation)
                    and object.state == esdl.AssetStateEnum.ENABLED
            ):
                self.totalPower += object.power
                self.TEACOSDecision = object.state
            else:
                self.TEACOSDecision = object.state

            self.totalPower = self.totalPower / 1000

        kWhyearlyWanted = self.totalPower * 1108.22

        self.numberOfPVPanelsWanted = math.ceil(kWhyearlyWanted / self.PVPanelYearlykWh)
        self.numberOfPVPanelsAvailable = self.numberOfPVPanelsWanted

    def step(self):
        """Advance the model by one step"""
        self.tickCounter = self.tickCounter + 1
        self.datacollector.collect(self)
        self.schedule.step()

        if self.tickCounter == 12:
            uri = URI(self.output_esdl_file_path)
            logger.info(f"Saving model state in {self.output_esdl_file_path}")
            resource = rset.create_resource(uri)
            resource.append(self.energySystem)
            resource.save()

            sumofpanelpower = 0
            for a in self.space.agents:
                for asset in a.building.asset:
                    if isinstance(asset, esdl.esdl.PVInstallation):
                        sumofpanelpower += asset.power
            print(sumofpanelpower)

    def run_model(self, n):
        for i in range(n):
            self.step()

def run_model(
        config: TeacosAdapterConfig,
        radius=0.0075,
        budget=1000,
        PVPanelBatchSize=2,
        CostOfPVPanel=500,
        steps=12,
):
    logger.info("Initializing Tholen model...")

    my_model = TholenModel(
        radius=radius,
        budget=budget,
        PVPanelBatchSize=PVPanelBatchSize,
        CostOfPVPanel=CostOfPVPanel,
        input_esdl_file_path=config.input_esdl_file_path,
        output_esdl_file_path=config.output_esdl_file_path,
    )

    logger.info(f"Running ABM with input ESDL file {config.output_esdl_file_path}...")
    my_model.run_model(steps)
    logger.info("Finished running ABM.")

    outcomes = my_model.datacollector.get_model_vars_dataframe()

    return {
        "model_uri": config.output_esdl_file_path,
        "TIME": list(range(steps)),
        "Number of Agents that bought Solar Panels": outcomes[
            "Agents With Solar Panels"
        ].tolist(),
        "Number of Agents that haven't bought Solar Panels": outcomes[
            "Agents Without Solar Panels"
        ].tolist(),
        "Number of Solar Panels Bought": outcomes["Solar Panels Bought"].tolist(),
    }


if __name__ == "__main__":
    config = TeacosAdapterConfig(
        input_esdl_file_path="../manual_loop/Tholen_Manual_T3_A2.esdl",
        output_esdl_file_path="../manual_loop/Tholen_Manual_T3_A3.esdl",
    )

    run_model(config)