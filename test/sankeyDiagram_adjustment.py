import os.path

import esdl
from esdl.esdl_handler import EnergySystemHandler
import plotly.graph_objects as go


def generate_sankey(esdl_file_path: str, TEACOSDecision: bool = None, TEACOSPower: float = None):
    sourceList = []
    sinkList = []
    valueList = []
    nodeColourList = []
    linkColourList = []
    sumList = []
    AgentMJList = []
    pinkhex = "rgba(215, 198, 225, 0.5)"
    pinknode = "#9C75B9"
    purplehex = "rgba(205, 208, 236, 0.5)"
    purplenode = "#8892D0"
    darkbluehex = "rgba(198, 222, 233, 0.5)"
    darkbluenode = "#7FAEDF"
    lightbluehex = "rgba(200, 236, 223, 0.5)"
    lighbluenode = "#7CD6C8"
    lightgreennode = "#8EE0A7"
    wattageconvertor = 3.6

    esh = EnergySystemHandler()
    # esh.load_file('../ESDLs-Input/Tholen_Input.esdl')

    esh.load_file(esdl_file_path)
    energySystem = esh.get_energy_system()
    instance = energySystem.instance[0]
    topLevelArea = instance.area
    AssetList = topLevelArea.asset

    for asset in AssetList:
        if isinstance(asset, esdl.AbstractBuilding):
            for a in asset.asset:
                if isinstance(a, esdl.ElectricityDemand):
                    for port in a.port:
                        if isinstance(port, esdl.InPort):
                            for profile in port.profile:
                                remainingMJ = 0

                                if a.name == "Gebouwgebonden elektriciteitsgebruik":
                                    sourceList.append(2)
                                    sinkList.append(3)
                                    valueList.append(profile.multiplier)
                                    linkColourList.append(lightbluehex)

                                    remainingMJ = remainingMJ + profile.multiplier

                                if a.name == "Procesgebonden elektriciteitsgebruik":
                                    sourceList.append(2)
                                    sinkList.append(4)
                                    valueList.append(profile.multiplier)
                                    linkColourList.append(lightbluehex)

                                    remainingMJ = remainingMJ + profile.multiplier

                                for a in asset.asset:
                                    if isinstance(a, esdl.PVInstallation):
                                        wattGenerated = a.power
                                        MJGenerated = wattGenerated * wattageconvertor
                                        sourceList.append(7)
                                        sinkList.append(2)
                                        AgentMJList.append(min(remainingMJ, MJGenerated))
                                        valueList.append(min(remainingMJ, MJGenerated))
                                        linkColourList.append(pinkhex)
                                        remainingMJ = max(0, remainingMJ - MJGenerated)

                                sourceList.append(1)
                                sinkList.append(2)
                                valueList.append(remainingMJ)
                                linkColourList.append(darkbluehex)

                                sumList.append(remainingMJ)

    if TEACOSDecision == True or TEACOSDecision == None:
        for asset in AssetList:
            if isinstance(asset, esdl.PVInstallation) and (asset.state == esdl.AssetStateEnum.ENABLED or asset.state == esdl.AssetStateEnum.OPTIONAL):
                sourceList.append(6)
                sinkList.append(0)
                if TEACOSPower == None:
                    TEACOSPower = asset.power * wattageconvertor
                valueList.append(sum(sumList))
                linkColourList.append(pinkhex)
            if isinstance(asset, esdl.PVInstallation) and asset.state == esdl.AssetStateEnum.ENABLED:
                TEACOSDecision = True
                TEACOSPower
            if isinstance(asset, esdl.PVInstallation) and asset.state == esdl.AssetStateEnum.DISABLED:
                TEACOSDecision = False

    # if TEACOSDecision == True or TEACOSDecision == None:
    #     sourceList.append(5)
    #     sinkList.append(0)
    #     valueList.append(sum(sumList) - TEACOSPower)
    # else:
    #     sourceList.append(5)
    #     sinkList.append(0)
    #     valueList.append(sum(sumList))
    # linkColourList.append(pinkhex)
    if TEACOSDecision == False:
        sourceList.append(5)
        sinkList.append(0)
        valueList.append(sum(sumList))
        linkColourList.append(pinkhex)

    sum(sumList)
    sourceList.append(0)
    sinkList.append(1)
    valueList.append(sum(sumList))
    linkColourList.append(purplehex)

    label = ["Electricity Cable",
             "Electricity Network",
             "Electricity Connector",
             "Gebouwgebonden Eletriciteitgebruik", "Procesgebonden Elektriciteitsgebruik",
             "Elektricity Supply",
             "PV Installation TEACOS",
             "PV Panel Agents"
             ]

    nodeColourList = [purplenode,
                      darkbluenode,
                      lighbluenode,
                      lightgreennode, lightgreennode,
                      pinknode,
                      pinknode,
                      pinknode
                      ]

    x = [0.25, 0.5, 0.75, 1.0, 1.0, 0.0, 0.0, 0.0]
    y = [0.50, 0.5, 0.50, 0.2, 0.8, 0.2, 0.5, 0.8]

    link = dict(source=sourceList, target=sinkList, value=valueList, color=linkColourList)
    node = dict(label=label, x=x, y=y, pad=150, thickness=10, color=nodeColourList)
    data = go.Sankey(link=link, node=node)
    fig = go.Figure(data)
    # filename_stem = os.path.splitext(os.path.basename(esdl_file_path))[0]
    # fig.update_layout(title_text=f"Sankey Diagram of {filename_stem}", font_size=10)
    fig.show()
    fig.write_image(f"{esdl_file_path}.png")
    return TEACOSDecision, TEACOSPower, sum(AgentMJList)


if __name__ == "__main__":
    generate_sankey("../output/Tholen-Five-Buildings-Central-PV_Iterations_5_Time_2023-05-18T13:45:22.362909/Tholen-Five-Buildings-Central-PV_A=1_T=2", TEACOSDecision=True, TEACOSPower=180000)
    # generate_sankey("../output/Tholen_Input_Iterations_5/Tholen_Input_A=5_T=5")