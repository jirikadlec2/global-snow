from pygsod import downgsod

gsodOgg = downgsod.downGSOD(user = 'jirikadlec2@gmail.com',
    password='jirikadlec2@gmail.com', destinationFolder='C:/dev/gsod_data',
    stations='114140-99999', firstyear=1980)
#connect to ftp
gsodOgg.connectFTP()
#download data
gsodOgg.allYears()
