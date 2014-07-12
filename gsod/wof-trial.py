import ulmo
import datetime

wsdl_one = 'http://icewater.usu.edu/LittleBearRiver/cuahsi_1_1.asmx?wsdl'
vals_one = ulmo.cuahsi.wof.get_values(wsdl_one,'LittleBearRiver:USU-LBR-EFLower', 'LittleBearRiver:USU41',
                                       '2005-01-01','2014-07-01')

wsdl = 'http://hydrodata.info/chmi-d/cuahsi_1_1.asmx?wsdl'
#variable_info = ulmo.cuahsi.wof.get_variable_info(wsdl, 'CHMI-D:8')
site_info = ulmo.cuahsi.wof.get_site_info(wsdl,'CHMI-D:217')
vals = ulmo.cuahsi.wof.get_values(wsdl, 'CHMI-D:217', 'CHMI-D:PRUTOK', '2014-01-01', datetime.date.today())
print vals