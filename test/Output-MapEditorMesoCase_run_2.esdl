<?xml version='1.0' encoding='UTF-8'?>
<esdl:EnergySystem xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:esdl="http://www.tno.nl/esdl" id="51f76bad-d3ea-499e-b362-70b4d14154de" description="Standard file Meso Case" esdlVersion="v2207" name="MapEditorMesoCase" version="11">
  <energySystemInformation xsi:type="esdl:EnergySystemInformation" id="9ce2523e-96dd-4112-85aa-50470bbe8e15">
    <quantityAndUnits xsi:type="esdl:QuantityAndUnits" id="e7b4d32f-6a73-49d8-8232-729dd7855ddf">
      <quantityAndUnit xsi:type="esdl:QuantityAndUnitType" description="Energy in GJ" physicalQuantity="ENERGY" multiplier="GIGA" unit="JOULE" id="eb07bccb-203f-407e-af98-e687656a221d"/>
      <quantityAndUnit xsi:type="esdl:QuantityAndUnitType" id="share_of_energy_demand" physicalQuantity="ENERGY" description="%" unit="PERCENT"/>
      <quantityAndUnit xsi:type="esdl:QuantityAndUnitType" id="avg_costs" physicalQuantity="COST" description="eur/MWh" unit="EURO"/>
    </quantityAndUnits>
    <carriers xsi:type="esdl:Carriers" id="6f5ed289-a1a4-419f-b230-19a41d76536a">
      <carrier xsi:type="esdl:GasCommodity" id="344d205a-1c31-4c4c-85a8-c3aa181a7057" name="CH4"/>
      <carrier xsi:type="esdl:EnergyCommodity" id="d6d532f3-92d0-4bcd-9f40-dc629a9bd1be" name="H2"/>
      <carrier xsi:type="esdl:EnergyCommodity" id="8a313264-6d2c-41b8-a04e-e1a4cacccf5b" name="H2O"/>
      <carrier xsi:type="esdl:EnergyCommodity" id="e6485461-1606-4cd4-833c-8967f4941d19" name="N2"/>
      <carrier xsi:type="esdl:EnergyCommodity" id="f76c3a6c-d4ca-4e5e-b351-d849075f4087" name="O2"/>
      <carrier xsi:type="esdl:EnergyCommodity" id="ff6a5c83-a673-478b-92ff-66937a592dac" name="CO2"/>
      <carrier xsi:type="esdl:EnergyCarrier" id="e8346314-97f4-455c-804c-488d68de223b" name="Electricity">
        <cost xsi:type="esdl:SingleValue" id="f42f3990-2379-48a9-aba6-ff98f9ad8dde" value="5.0">
          <profileQuantityAndUnit xsi:type="esdl:QuantityAndUnitType" description="Cost in EUR/MWh" perMultiplier="MEGA" physicalQuantity="COST" unit="EURO" perUnit="WATTHOUR" id="931dab9e-8a05-41de-b750-7d716784556a"/>
        </cost>
        <energyContentUnit xsi:type="esdl:QuantityAndUnitType" physicalQuantity="ENERGY" id="ea1f1a9c-d588-4f7f-8088-0868216e43b9"/>
        <emissionUnit xsi:type="esdl:QuantityAndUnitType" perMultiplier="GIGA" physicalQuantity="EMISSION" multiplier="KILO" id="7c7e55ef-5fc7-411d-9038-c2bd053829aa" perUnit="JOULE" unit="GRAM"/>
      </carrier>
    </carriers>
  </energySystemInformation>
  <instance xsi:type="esdl:Instance" id="b3a80d08-e9b7-4a5e-ac54-69c9327c151b" name="Yara Site">
    <area xsi:type="esdl:Area" id="cad0d10c-6a2f-4876-a773-02085060554f" name="nl">
      <area xsi:type="esdl:Area" id="46cdcfee-e304-4b55-aa20-5d024bf2af17" name="Untitled area">
        <asset xsi:type="esdl:Electrolyzer" name="yara_electrolyzer" id="21570d9f-8d1f-4df4-bf3d-d4ac7eea47d3" state="DISABLED">
          <geometry xsi:type="esdl:Point" lat="51.27920606558368" lon="3.8512229919433594"/>
          <behaviour xsi:type="esdl:InputOutputRelation" mainPort="203f3a36-f9b0-4f8e-99fb-80917d485bdb">
            <mainPortRelation xsi:type="esdl:PortRelation" ratio="9.01" port="7a0816bb-ff7a-4002-82f5-b71cf1eab4ac">
              <quantityAndUnit xsi:type="esdl:QuantityAndUnitType" id="2b1d3d40-aa8f-44b5-9892-a597b70e61f9" unit="GRAM" multiplier="MEGA"/>
            </mainPortRelation>
            <mainPortRelation xsi:type="esdl:PortRelation" ratio="203.0" port="cfb83f0a-b8d2-4af1-acb0-0e58455ca843">
              <quantityAndUnit xsi:type="esdl:QuantityAndUnitType" id="0c02dad0-d833-4bd2-a42a-36edddbefc05" unit="JOULE" multiplier="GIGA"/>
            </mainPortRelation>
          </behaviour>
          <costInformation xsi:type="esdl:CostInformation" id="a3962cae-4af1-4fca-bf9a-f7599d39486a">
            <investmentCosts xsi:type="esdl:SingleValue" id="e88ebac1-e909-4463-909b-038e7ed3857b" value="1.0">
              <profileQuantityAndUnit xsi:type="esdl:QuantityAndUnitType" id="f4d513b6-c4e9-42ad-aa0f-8fbe424d3edd" physicalQuantity="COST" description="Cost in EUR" unit="EURO"/>
            </investmentCosts>
          </costInformation>
          <KPIs xsi:type="esdl:KPIs">
            <kpi xsi:type="esdl:StringKPI" value="1." name="yara_production_h2_electrolysis"/>
            <kpi xsi:type="esdl:IntKPI" id="TEACOS_Was_Optional_yara_electrolyzer" value="1" name="1"/>
          </KPIs>
          <port xsi:type="esdl:InPort" connectedTo="2a0328b6-5e7b-4aa3-95ba-d64afa86e05a" id="cfb83f0a-b8d2-4af1-acb0-0e58455ca843" carrier="e8346314-97f4-455c-804c-488d68de223b" name="In_Electricity"/>
          <port xsi:type="esdl:OutPort" connectedTo="ffccae3a-fdd1-48c1-9023-d3f073a6f725" id="203f3a36-f9b0-4f8e-99fb-80917d485bdb" carrier="d6d532f3-92d0-4bcd-9f40-dc629a9bd1be" name="H2_out"/>
          <port xsi:type="esdl:InPort" connectedTo="ccf5d762-abf5-4c6d-8665-b2c4173b56bc" id="7a0816bb-ff7a-4002-82f5-b71cf1eab4ac" carrier="8a313264-6d2c-41b8-a04e-e1a4cacccf5b" name="Water_In"/>
          <port xsi:type="esdl:OutPort" connectedTo="c14bb774-48cc-4fcd-81d5-a96d47a1c894" id="66a1fbd7-49b5-403b-98aa-aa75ab263b96" carrier="e8346314-97f4-455c-804c-488d68de223b" name="Out_Electricity"/>
          <port xsi:type="esdl:OutPort" connectedTo="07918488-eb3f-49b1-a090-7072d48b1593" id="59fdda72-3cca-43e3-9ef9-9fc2e22bde0e" carrier="f76c3a6c-d4ca-4e5e-b351-d849075f4087" name="O2_OutPort"/>
        </asset>
        <asset xsi:type="esdl:ElectricityDemand" name="ElectricityDummyDemand" id="814880dd-b0c4-4f0c-9654-1ddc1c70049f">
          <geometry xsi:type="esdl:Point" lat="51.276387290096615" lon="3.8584756851196294"/>
          <port xsi:type="esdl:InPort" connectedTo="66a1fbd7-49b5-403b-98aa-aa75ab263b96" id="c14bb774-48cc-4fcd-81d5-a96d47a1c894" carrier="e8346314-97f4-455c-804c-488d68de223b" name="In"/>
        </asset>
        <asset xsi:type="esdl:GasConversion" name="yara_SMR" type="SMR" id="74c94568-be15-4110-bc07-4afc56fee0c1" state="ENABLED">
          <geometry xsi:type="esdl:Point" lat="51.277649049078" lon="3.8482618331909184"/>
          <behaviour xsi:type="esdl:InputOutputRelation" mainPort="321fa0db-9d48-43a6-ab53-7a53df2c86ce">
            <mainPortRelation xsi:type="esdl:PortRelation" ratio="3.58" port="91db20dd-8c56-444b-98bb-194f097d4ea5">
              <quantityAndUnit xsi:type="esdl:QuantityAndUnitType" id="653b01fb-8f62-4127-be1e-40c2a2bebdea" unit="GRAM" multiplier="MEGA"/>
            </mainPortRelation>
            <mainPortRelation xsi:type="esdl:PortRelation" ratio="3.72" port="847cbb1f-bdf4-4d53-a8df-57efa417a019">
              <quantityAndUnit xsi:type="esdl:QuantityAndUnitType" id="627212d7-3ddd-4f11-b0f7-c809e4209bbb" unit="GRAM" multiplier="MEGA"/>
            </mainPortRelation>
            <mainPortRelation xsi:type="esdl:PortRelation" ratio="4.67" port="a68ff1c2-9454-40aa-9982-ffe1e165a9b3">
              <quantityAndUnit xsi:type="esdl:QuantityAndUnitType" id="915df1da-38a8-4c0d-8e78-64e9836a1e4e" unit="GRAM" multiplier="MEGA"/>
            </mainPortRelation>
            <mainPortRelation xsi:type="esdl:PortRelation" ratio="4.67" port="1a788cf1-7cd6-43a9-8414-041e583aee7a">
              <quantityAndUnit xsi:type="esdl:QuantityAndUnitType" id="7fb014d7-b5d5-4cd1-987c-243e817dfec3" unit="GRAM" multiplier="MEGA"/>
            </mainPortRelation>
            <mainPortRelation xsi:type="esdl:PortRelation" ratio="6.46" port="dafb4a5d-7f50-4401-8f7b-419db1276660">
              <quantityAndUnit xsi:type="esdl:QuantityAndUnitType" id="40d900f2-7c41-466c-8beb-7b647c52e0c7" unit="GRAM" multiplier="MEGA"/>
            </mainPortRelation>
            <mainPortRelation xsi:type="esdl:PortRelation" ratio="1.39" port="b5c5ce43-3f6d-4cc3-b27c-51f42385f67e">
              <quantityAndUnit xsi:type="esdl:QuantityAndUnitType" id="b475ab2b-da07-4a2b-a9f3-7d2577d54c3f" unit="GRAM" multiplier="MEGA"/>
            </mainPortRelation>
          </behaviour>
          <costInformation xsi:type="esdl:CostInformation" id="04576045-79e9-4f51-b72a-49adc727e7c7">
            <investmentCosts xsi:type="esdl:SingleValue" id="a2ff47f4-6bdc-48a3-af6e-47c565b4298f" value="1.0">
              <profileQuantityAndUnit xsi:type="esdl:QuantityAndUnitType" id="4b03ab76-468b-466c-a0b6-315bc5bd2674" physicalQuantity="COST" description="Cost in EUR" unit="EURO"/>
            </investmentCosts>
          </costInformation>
          <KPIs xsi:type="esdl:KPIs">
            <kpi xsi:type="esdl:StringKPI" value="0." name="yara_production_h2_smr"/>
            <kpi xsi:type="esdl:IntKPI" id="TEACOS_Was_Optional_yara_SMR" value="1" name="1"/>
          </KPIs>
          <port xsi:type="esdl:InPort" connectedTo="6b3f9a8d-1515-4486-bbce-6b985ca0efb5" id="91db20dd-8c56-444b-98bb-194f097d4ea5" carrier="344d205a-1c31-4c4c-85a8-c3aa181a7057" name="Port"/>
          <port xsi:type="esdl:OutPort" connectedTo="0afe53d4-8bf6-4ce0-90da-e589f2b5d1ff" id="1a788cf1-7cd6-43a9-8414-041e583aee7a" carrier="e6485461-1606-4cd4-833c-8967f4941d19" name="Out_N2"/>
          <port xsi:type="esdl:OutPort" connectedTo="c49fa3f2-2705-40d2-8d62-539d28e5c571" id="dafb4a5d-7f50-4401-8f7b-419db1276660" carrier="ff6a5c83-a673-478b-92ff-66937a592dac" name="Out_CO2"/>
          <port xsi:type="esdl:OutPort" connectedTo="ffccae3a-fdd1-48c1-9023-d3f073a6f725" id="321fa0db-9d48-43a6-ab53-7a53df2c86ce" carrier="d6d532f3-92d0-4bcd-9f40-dc629a9bd1be" name="Out_H2"/>
          <port xsi:type="esdl:InPort" connectedTo="ff1e9fdf-6f55-4e07-8a0f-291bc6256c04" id="a68ff1c2-9454-40aa-9982-ffe1e165a9b3" carrier="e6485461-1606-4cd4-833c-8967f4941d19" name="In_N2"/>
          <port xsi:type="esdl:InPort" connectedTo="78425d36-6f37-4cda-8b00-e370d4d69ec2" id="b5c5ce43-3f6d-4cc3-b27c-51f42385f67e" carrier="f76c3a6c-d4ca-4e5e-b351-d849075f4087" name="In_O2"/>
          <port xsi:type="esdl:InPort" connectedTo="ccf5d762-abf5-4c6d-8665-b2c4173b56bc" id="847cbb1f-bdf4-4d53-a8df-57efa417a019" carrier="8a313264-6d2c-41b8-a04e-e1a4cacccf5b" name="In_H2O"/>
        </asset>
        <asset xsi:type="esdl:GenericConsumer" name="GenericConsumer_H2" id="7d721bb9-f949-4891-b444-e6e2357563af">
          <geometry xsi:type="esdl:Point" lat="51.2749509903577" lon="3.856158256530762"/>
          <port xsi:type="esdl:InPort" connectedTo="203f3a36-f9b0-4f8e-99fb-80917d485bdb 321fa0db-9d48-43a6-ab53-7a53df2c86ce" id="ffccae3a-fdd1-48c1-9023-d3f073a6f725" carrier="d6d532f3-92d0-4bcd-9f40-dc629a9bd1be" name="In_SMR">
            <profile xsi:type="esdl:SingleValue" id="39780856-b465-4214-a113-756f6f9186b8" value="100.0">
              <profileQuantityAndUnit xsi:type="esdl:QuantityAndUnitReference" reference="eb07bccb-203f-407e-af98-e687656a221d"/>
            </profile>
          </port>
        </asset>
        <asset xsi:type="esdl:SinkConsumer" name="Consumer_N2" id="a113f602-eaef-4dfa-b7f3-4568b4cecf47">
          <geometry xsi:type="esdl:Point" lat="51.27324616510048" lon="3.848776817321778"/>
          <port xsi:type="esdl:InPort" connectedTo="1a788cf1-7cd6-43a9-8414-041e583aee7a" id="0afe53d4-8bf6-4ce0-90da-e589f2b5d1ff" carrier="e6485461-1606-4cd4-833c-8967f4941d19" name="In"/>
        </asset>
        <asset xsi:type="esdl:ElectricityProducer" name="ElectricityProducer" id="ebe77404-e686-418f-830a-d48f96cae650">
          <geometry xsi:type="esdl:Point" lat="51.28489027133621" lon="3.8484120368957524"/>
          <port xsi:type="esdl:OutPort" id="2a0328b6-5e7b-4aa3-95ba-d64afa86e05a" connectedTo="cfb83f0a-b8d2-4af1-acb0-0e58455ca843" carrier="e8346314-97f4-455c-804c-488d68de223b" name="Out"/>
        </asset>
        <asset xsi:type="esdl:Import" name="Import_N2" id="0ec05565-ad45-4771-9b65-b3f6d7e2e17b">
          <geometry xsi:type="esdl:Point" lat="51.28371574661717" lon="3.84572982788086"/>
          <port xsi:type="esdl:OutPort" id="ff1e9fdf-6f55-4e07-8a0f-291bc6256c04" connectedTo="a68ff1c2-9454-40aa-9982-ffe1e165a9b3" carrier="e6485461-1606-4cd4-833c-8967f4941d19" name="Out"/>
        </asset>
        <asset xsi:type="esdl:Import" name="Import_O2" id="3e563f62-a496-4b30-8cf0-f4a0102bbd10">
          <geometry xsi:type="esdl:Point" lat="51.282749423668605" lon="3.8440132141113286"/>
          <port xsi:type="esdl:OutPort" id="78425d36-6f37-4cda-8b00-e370d4d69ec2" connectedTo="b5c5ce43-3f6d-4cc3-b27c-51f42385f67e" carrier="f76c3a6c-d4ca-4e5e-b351-d849075f4087" name="Out"/>
        </asset>
        <asset xsi:type="esdl:GenericProducer" name="GenericProducer_CH4" id="53696bad-beff-4959-a376-7410ef3c006c">
          <geometry xsi:type="esdl:Point" lat="51.281514648092795" lon="3.8418674468994145"/>
          <port xsi:type="esdl:OutPort" id="6b3f9a8d-1515-4486-bbce-6b985ca0efb5" connectedTo="91db20dd-8c56-444b-98bb-194f097d4ea5" carrier="344d205a-1c31-4c4c-85a8-c3aa181a7057" name="Out"/>
        </asset>
        <asset xsi:type="esdl:SinkConsumer" name="Consumer_CO2" id="15c6ed1b-765c-42dc-be92-86986bed29c4">
          <geometry xsi:type="esdl:Point" CRS="WGS84" lat="51.274212687972586" lon="3.8516521453857426"/>
          <port xsi:type="esdl:InPort" connectedTo="dafb4a5d-7f50-4401-8f7b-419db1276660" id="c49fa3f2-2705-40d2-8d62-539d28e5c571" carrier="ff6a5c83-a673-478b-92ff-66937a592dac" name="In"/>
        </asset>
        <asset xsi:type="esdl:Import" name="Import_H2O" id="733b0935-0846-430d-87bc-29dfb6d9913e">
          <geometry xsi:type="esdl:Point" lat="51.28446731707717" lon="3.847103118896485"/>
          <port xsi:type="esdl:OutPort" id="ccf5d762-abf5-4c6d-8665-b2c4173b56bc" connectedTo="7a0816bb-ff7a-4002-82f5-b71cf1eab4ac 847cbb1f-bdf4-4d53-a8df-57efa417a019" carrier="8a313264-6d2c-41b8-a04e-e1a4cacccf5b" name="Out"/>
        </asset>
        <asset xsi:type="esdl:SinkConsumer" name="Consumer_O2" id="284b55f8-4585-4586-b07e-a121efe49360">
          <geometry xsi:type="esdl:Point" lat="51.27861547932833" lon="3.859763145446778"/>
          <port xsi:type="esdl:InPort" connectedTo="59fdda72-3cca-43e3-9ef9-9fc2e22bde0e" id="07918488-eb3f-49b1-a090-7072d48b1593" carrier="f76c3a6c-d4ca-4e5e-b351-d849075f4087" name="In"/>
        </asset>
      </area>
      <KPIs xsi:type="esdl:KPIs" description="Meso-case" id="meso-case">
        <kpi xsi:type="esdl:DistributionKPI" id="source_of_electricity_production" name="Elektriciteitsmix">
          <distribution xsi:type="esdl:StringLabelDistribution">
            <stringItem xsi:type="esdl:StringItem" value="44229.401114500324" label="Import"/>
            <stringItem xsi:type="esdl:StringItem" value="4039200.0000000065" label="Zon"/>
            <stringItem xsi:type="esdl:StringItem" value="27179999.99999995" label="Wind"/>
            <stringItem xsi:type="esdl:StringItem" value="3423887.808510637" label="Biogas"/>
            <stringItem xsi:type="esdl:StringItem" value="444735.37548065174" label="Biomassa"/>
            <stringItem xsi:type="esdl:StringItem" value="158498819.36676764" label="Kolen"/>
            <stringItem xsi:type="esdl:StringItem" value="330153313.22030866" label="Aardgas"/>
            <stringItem xsi:type="esdl:StringItem" value="1155607.7060133421" label="Groengas"/>
            <stringItem xsi:type="esdl:StringItem" value="334800.0000000005" label="Water"/>
            <stringItem xsi:type="esdl:StringItem" value="14303665.260000002" label="Nucleair"/>
            <stringItem xsi:type="esdl:StringItem" value="12779706.220492072" label="Olie"/>
            <stringItem xsi:type="esdl:StringItem" value="20611298.87999998" label="Afval"/>
          </distribution>
        </kpi>
        <kpi xsi:type="esdl:DoubleKPI" value="33944971208.6682" id="total_costs" name="Totale systeemkosten"/>
        <kpi xsi:type="esdl:DoubleKPI" value="4.263152384861102" id="dashboard_reduction_of_co2_emissions_versus_1990" name="Reductie CO2-emissies t.o.v. 1990"/>
        <kpi xsi:type="esdl:DoubleKPI" value="165485.4404449378" id="total_co2_emissions" name="CO2-emissies totaal"/>
        <kpi xsi:type="esdl:DoubleKPI" value="0.0005270004216" id="interconnector_co2" name="CO2-emissies import (gewogen gemiddelde)"/>
        <kpi xsi:type="esdl:DoubleKPI" value="2080.18229166666" id="merit_order_onshore_wind_turbines_capacity_in_merit_order_table" name="Opgesteld vermogen wind op land"/>
        <kpi xsi:type="esdl:DoubleKPI" value="1920.0" id="merit_order_onshore_wind_turbines_full_load_hours_in_merit_order_table" name="Vollasturen wind op land"/>
        <kpi xsi:type="esdl:DoubleKPI" value="33.565267217593075" id="merit_order_price_average" name="Gemiddelde elektriciteitsprijs"/>
      </KPIs>
    </area>
  </instance>
</esdl:EnergySystem>
