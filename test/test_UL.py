import time

import requests

from tno.aimms_adapter import EnvSettings
from tno.aimms_adapter.universal_link.Uniform_ESDL_AIMMS_link import UniversalLink
from tno.aimms_adapter.universal_link.Write_TO_ESDL import OutputESDL

inputfilename = 'test/Tholen-simple v04-26kW_output.esdl'

Host = EnvSettings.db_host()
DB = EnvSettings.db_name()
User =EnvSettings.db_user()
PW = EnvSettings.db_password()
ul = UniversalLink(Host, DB, User, PW)
print(ul.esdl_to_db(inputfilename))

# requests.post(EnvSettings.teacos_API_url())
#
# outputfilename = 'test/Test_Output.esdl'
# time.sleep(20)
# OutputESDL(EnvSettings.db_name(), inputfilename, outputfilename)