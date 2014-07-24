from pygsod import downgsod
import my_gsod
#my_gsod.get_all_files()

mydata = my_gsod.get_data('341100-99999', year=2013)

gsodOgg = downgsod.downGSOD(user = 'jirikadlec2@gmail.com',
    password='jirikadlec2@gmail.com', destinationFolder='C:/dev/gsod_data',
    stations=None, firstyear=1950)
#connect to ftp
gsodOgg.connectFTP()
#download data
gsodOgg.allYears()
