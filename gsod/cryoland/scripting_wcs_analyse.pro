;+
; NAME:
;       scripting_wcs_analyse.pro
;
; PURPOSE:
;	   - demonstrate how data access can be combined with data analysis
; 	   - demonstrate the automated access to an OGC-WCS 2.0/EO-WCS interface to 
; 		 gather information about the service and receive data
; 	   - use WCS 2.0/EO-WCS to define an Area-of-Interest (AOI) and a Time-of-Interest (TOI)
;		 and use this information to query Datasets and Dataset Series
;	   - send a DescribeCoverageSet request to gather information about data availability for the AOI and TOI
;      - send a series of EO-WCS (GetCoverage) requests to the OGC-WCS/EO-WCS interface of the CryoLand instance 
;		 and receive the data
; 	   - extract values from the received coverages
; 	   - calculate some pixel statistic for each image 
; 	   - create a plot over the time-series requested
;
; CATEGORY:
;       Demonstration - Proof of Concept to demonstrate the EO-WCS functionality when implemented
; 		in a Users Application (eg. in a GIS / Expert System) 
;
; CALLING SEQUENCE:
;       scripting_wcs_analyse
;
; USAGE:
;       scripting_wcs_analyse
;       scripting_wcs_analyse, output = <path to storage location>
;       scripting_wcs_analyse, output = <path to storage location>, /INFO
;       scripting_wcs_analyse, /INFO
;
; INPUT PARAMETERS:
;       None
;
; KEYWORD PARAMETERS:
; 		OUTPUT ---  path to the location where the received (downloaded) datasets shall be stored.
;					If not provided then the default location will be used
; 					Defaults: Linux = your HOME-Directory , Windows = C:\, MacOS - "?"
;       /INFO  ---  this will provide a bunch of additional output to help to explain
;					the functionality and the flow of requests to the WCS/EO-WCS interfaces as well 
; 					as its exploitation.
;					For the first set of request and data anaylsis steps each step is interrupted by
;					a "Pause"; to continue you neeed to Press any key.
; 		LOGFILE --  path and filename where the logfile should be written.  If not provided output is 
; 					on the screen (= default).
;
;
; OUTPUT:
; ;		- Requested data files which are downloaded and stored 
;       - 3 graphic windows, and with /INFO Keyword set some descriptive text
;
; COMMON BLOCKS:
;       None
;
; SIDE EFFECTS:
;       None
;
; NOTES:
;       This script has been developed and tested under Linux only. 
; 		It might therefore be necessary to apply some changes under Windows or MacOS
;
;
; RESTRICTIONS - PREREQUISITES:
;       This script uses the following Linux routines for external calls:
;			- curl:  a routine to issue the http calls (required)
;			- xmllint:  to nicely format returned xml-responses (optional, only if the 
;			 /INFO Keyword is set; could be commented out) 
;		This script doesn't use advanced features (like IDL's XML handling) in order to run under older 
;		versions as well as under the free OpenSource version GDL (-> GnuDataLanguage). However, for GDL there 
;		need to be some minor changes applied (indicated in the code - search for GDL), and there are also some 
;		unresolved issues when plotting the results, which are not resolve yet).
;
;
; DISCLAIMER:
;		Copyright:	EOX IT Service GmbH;  2013
;					Vienna / Austria
;
; MODIFICATION HISTORY:
;       CS-2013/03/11 -- Christian Schiller [CS] email: christian dot schiller at eox dot at
;       
; LICENSING:
;
; Permission is hereby granted, free of charge, to any person obtaining a copy
; of this software and associated documentation files (the "Software"), to deal
; in the Software without restriction, including without limitation the rights
; to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
; copies of the Software, and to permit persons to whom the Software is 
; furnished to do so, subject to the following conditions:
; 
; The above copyright notice and this permission notice shall be included in all
; copies of this Software or works derived from this Software.
; 
; THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
; IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
; FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
; AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
; LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
; OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
; THE SOFTWARE.
;
;-



;-----------------------------------------------------------------------------
; BEGIN Function Block
;-----------------------------------------------------------------------------

;========================================================================== 
;========================================================================== 

PRO BOX, X0, Y0, X1, Y1, color , device=device  

		; Call POLYFILL:
	if keyword_set(device) then POLYFILL, [X0, X0, X1, X1], [Y0, Y1, Y1, Y0], COL = color , /device  $
		else  POLYFILL, [X0, X0, X1, X1], [Y0, Y1, Y1, Y0], COL = color

END

;========================================================================== 
;========================================================================== 
PRO pause


DO_WAIT=1
move_to=''
newline=string(10B)  

	if (DO_WAIT eq 1) then begin
		print,newline
		read,move_to,Prompt='Press Any Key to Continue: '
    endif

END

;========================================================================== 
;==========================================================================
FUNCTION get_today

	date=systime()
	day=strtrim(strmid(date,7, 3),2) 
	month=strtrim(strmid(date, 4, 3),2)
	year=strtrim(strmid(date, 20, 4),2)


	CASE month OF
		'Jan': digit_month='01'
		'Feb': digit_month='02'
		'Mar': digit_month='03'
		'Apr': digit_month='04'
		'May': digit_month='05'
		'Jun': digit_month='06'
		'Jul': digit_month='07'
		'Aug': digit_month='08'
		'Sep': digit_month='09'
		'Oct': digit_month='10'
		'Nov': digit_month='11'
		'Dec': digit_month='12'
	ENDCASE

	if (strlen(day) eq 1) then digit_day='0'+day else digit_day=strtrim(day,2)
	if (strlen(day) eq 1) then digit_yday='0'+day-1 else digit_yday=strtrim(day-1,2)
	digit_today = year+'-'+digit_month+'-'+digit_day
	digit_yesterday= year+'-'+digit_month+'-'+digit_yday
	digit_selected=[ digit_yesterday+'T00:00Z', digit_today+'T23:59Z' ]

RETURN, digit_selected

END
;========================================================================== 
;==========================================================================

;-----------------------------------------------------------------------------
; END Function Block
;-----------------------------------------------------------------------------




;=============================================================================
;#################################################################################
;#################################################################################
;
; MAIN    -  scripting_wcs_analyse
;
;#################################################################################
;#################################################################################
;=============================================================================
PRO scripting_wcs_analyse, output=output, info=info, logfile=logfile



; ########## GENERAL DEFAULT DEFINITIONS #########
; do not change unless you know what you are doing

sep=path_sep()        		; directory separator
osversion = StrUpCase(!version.os_family)

  CASE osversion OF
    'UNIX':	BEGIN 	
		spawn,'echo $HOME',myhome, /sh	; get the users home directory
		spawn,'pwd', cur_dir, /sh		
		END
    'WINDOWS': BEGIN
		myhome='c:\'
		cur_dir='c:\'
		END
    'MACOS':	BEGIN
    	myhome=''
		cur_dir=''
		END 	
     else:		BEGIN
    	myhome=''
		cur_dir=''
		END 	
  ENDCASE




if (NOT(keyword_set(LOGFILE))) then uid=-1 else openw,uid,logfile,/get_lun
newline=string(10B)        ;linefeed 
err_flag=0
cnt=0
loop=0

; define some settings for the displays
	; use this line for IDL
DEVICE, DECOMPOSED=0  , RETAIN=2, SET_FONT='Helvetica Bold Italic', /TT_FONT  
	; use this line for GDL
;DEVICE, DECOMPOSED=0  
loadct,38, /SILENT

; Make the axes black
!P.BACKGROUND=255
!P.COLOR=0


; ### END OF GENERAL DEFINITIONS #########




; ### User-Specific Definitions ###
; change setting as required by your system

; set default output location or use the path provided with the OUTPUT parameter
IF (NOT(KEYWORD_SET(output))) then  def_output_path=myhome   else def_output_path=output


;  colors used for the bar charts
colors=[ 87, 203, 250, 135, 35, 189, 255, 0 ]


; ### End User-Specific Definitions ###




; ### Demo-Specific Definitions ###
; change setting as required 

; Be aware that not all combinations of Datasets, AOI, and TOI will return results
; You may change/add them to your liking/needs. They are mainly here to provide a demonstration 
; on how an automated system may work. You can always change TOI, AOI, or solely use the direct input 
; at the corresponding Input selection. 
toi=strarr(8,2)
toi[0,*]=['2013-02-01T00:00Z', '2013-02-08T23:00Z']
toi[1,*]=['2012-04-10T00:00Z', '2012-04-10T23:00Z']
toi[2,*]=['2012-03-10T00:00Z', '2012-04-04T23:00Z']
toi[3,*]=['2012-03-09T00:00Z', '2012-03-16T23:00Z']
toi[4,*]=['2012-11-26T00:00Z', '2012-12-03T23:00Z']
toi[5,*]=['2011-03-01T00:00Z', '2011-03-31T23:00Z']
toi[6,*]=['2013-03-01T00:00Z', '2013-03-08T23:00Z']
toi[7,*]=['YESTERDAY','TODAY']


; define some default values for the AOI
; select_aoi=(MinX, MaxX, MinY, MaxY)
aoi=strarr(8,4)
aoi[0,*]=[ '13.547241210937', '14.722778320312', '63.564086914063', '64.530883789063' ]	; Sweden
aoi[1,*]=[ '1.0235137939453', '1.0290069580078', '42.601486206055', '42.61247253418']   ; Pyrenean
aoi[2,*]=[ '10.674247741699', '10.735359191895', '46.994705200195', '47.052383422852']   ; Swiss
aoi[3,*]=[ '10','11','46','47' ]	; Austria -Alps
aoi[4,*]=[ '8.1515808105468', '8.1982727050781', '46.5517578125', '46.598449707031']	;  Swiss
aoi[5,*]=[ '34.795589447021', '34.843311309814', '58.707504272461', '58.750076293945' ]	; Sweden
aoi[6,*]=[ '26.165039062499','27.263671874999', '52.885375976563', '53.808227539063' ]  ; Baltic
aoi[7,*]=[ '32.908241271973', '32.914421081543', '59.118743896485', '59.125610351563' ]	; Sweden


; ### End Demo-Specific Definitions ###




; ### Service Definitions ###
; Definitions needed for accessing the CryoLand services 
; Don't change unless you know what you are doing.
server='http://neso.cryoland.enveo.at'



; DatasetSeries available at CryoLand (at the time of writing!). This list will change/be expanded
; during the CryoLand projects runtime.
; This is hardcoded here. A better solution is a GetCapabilitis request with "sections=DatasetsSeriesSummary" set
; and then analyse the returned XML. 
DSS=strarr(6)
DSS[0]='daily_FSC_PanEuropean_Optical'
DSS[1]='daily_SWE_PanEuropean_Microwave'
DSS[2]='daily_FSC_Baltic_Optical'
DSS[3]='multitemp_FSC_Scandinavia_Multisensor'
DSS[4]='daily_SCA_CentralEurope_Optical'
DSS[5]='daily_FSC_Alps_Optical'

; set the default datasetseries
DEF_DATASETSERIES='daily_FSC_PanEuropean_Optical'

; ### End of Service Definitions ###






; ---- Start of the processing code ---- 



; provide the available datasets or let the user define another one
	dss_choice=''
	print,newline
	print,'Please select the Number of the DatasetSeries to use (Default=1) OR enter (D) to enter another DatasetSeries name: '
	for di=0,(n_elements(DSS)-1) do print, di+1,': ',DSS[di]
	read, dss_choice
		CASE strupcase(dss_choice) OF
			'1': DATASETSERIES=DSS[0]
			'2': DATASETSERIES=DSS[1]
			'3': DATASETSERIES=DSS[2]
			'4': DATASETSERIES=DSS[3]
			'5': DATASETSERIES=DSS[4]
			'6': DATASETSERIES=DSS[5]
			'D' : BEGIN
				read, DATASETSERIES, Prompt=' Enter name of DatasetSeries: '
				print, newline
				END
			else: 	DATASETSERIES=DSS[0]
		ENDCASE



; provide some present TOIs or let the user define another TOI
	toi_choice=''
	print, newline
	print, 'Please select a Number for the Time-Range (Default=1) OR enter (T) to enter a new TOI: '
	for ti=0,(n_elements(toi[*,0])-1) do print, ti+1,': ', strtrim(toi[ti,*],2), format='(4(A,:,"  "))'
	read, toi_choice
		CASE strupcase(toi_choice) OF
			'1': select_toi=toi[0,*]
			'2': select_toi=toi[1,*]
			'3': select_toi=toi[2,*]
			'4': select_toi=toi[3,*]
			'5': select_toi=toi[4,*]
			'6': select_toi=toi[5,*]
			'7': select_toi=toi[6,*]
			'8': select_toi=get_today()
			'T': BEGIN
				print, 'Please enter the Time-Range. (Use the following formating for:  Dates: "YYYY-MM-DD" ; Time: "HH:MM")'
;				bdate = ''
;				btime = ''
;				edate = ''
;				etime = ''
				read, bdate, Prompt='Enter Begin-Date: '
				read, btime, Prompt='Enter Begin-Time: '
				read, edate, Prompt='Enter End-Date: '
				read, etime, Prompt='Enter End-Time: '
				print,newline
				select_toi=[ "'" +strtrim(bdate,2)+ "T" +strtrim(btime,2)+"Z'", "'" +strtrim(edate,2)+ "T" +strtrim(etime,2)+"Z'" ] 
				END
			else: select_toi=toi[5,*]
		ENDCASE



; provide some present AOIs or let the user define another AOI
	aoi_choice=''
	print, newline
	print, 'Please select a Number for the AOI (Default=1) OR enter (C) to define a new AOI: '
	for ai=0,(n_elements(aoi[*,0])-1) do print, ai+1,': ', aoi[ai,*], format='(2(A,:),4(F15.11))' 
	read, aoi_choice
		CASE strupcase(aoi_choice) OF
			'1': select_aoi=aoi[0,*]
			'2': select_aoi=aoi[1,*]
			'3': select_aoi=aoi[2,*]
			'4': select_aoi=aoi[3,*]
			'5': select_aoi=aoi[4,*]
			'6': select_aoi=aoi[5,*]
			'7': select_aoi=aoi[6,*]
			'8': select_aoi=aoi[7,*]			
			'C': BEGIN
			; 		minx=''
			; 		maxx=''
			; 		miny=''
			; 		maxy=''
			 		print, 'Please enter 4 Coordinates values (decimal degrees) for the AOI. Use negative values for South and West, respectively:'
			 		read, minx, Prompt='Enter minX: '
			 		read, maxx, Prompt='Enter maxX: '
			 		read, miny, Prompt='Enter minY: '
			 		read, maxy, Prompt='Enter maxY: '
			 		select_aoi=[string(minx), string(maxx), string(miny), string(maxy) ]
			END
			else: select_aoi=aoi[5,*]
		ENDCASE





; sent a DescribeCoverageSet request to the server to see which datasets are avialable for
; the chosen TOI, AOI and Dataset

		; the request is first plugged together and the user's choices are added
		; here it is a DescribeEOCoverageSet Request
	base_desccov='/cryoland/ows?service=wcs&version=2.0.0&request=describeeocoverageset&eoid='+DATASETSERIES+'&subset=x,http://www.opengis.net/def/crs/EPSG/0/4326('+select_aoi[0]+','+select_aoi[1]+')&subset=y,http://www.opengis.net/def/crs/EPSG/0/4326('+select_aoi[2]+','+select_aoi[3]+')&subset=phenomenonTime(%22'+select_toi[0]+'%22,%22'+select_toi[1]+'%22)'

		
	print, newline,'==> Sending DescribeEOCoverageSet Request...'

		; combine the request with the curl command and the server information
		; below 2 options are provided -> depending if /INFO has been set or not
	if  ( keyword_set(INFO) AND loop eq 0 ) then begin
		; if /INFO is set then do some extra formatting of the response using 'xmllint' to have a nicer output
		request=[ 'curl "'+server+base_desccov+'" -k -o '+def_output_path+'/result_describeeocoverageset.xml ;   xmllint  --format  --output  '+def_output_path+'/result_describeeocoverageset.xml  ' +def_output_path+'/result_describeeocoverageset.xml' ]
	endif else begin 
		request=[ 'curl -s "'+server+base_desccov+'" -k -o '+def_output_path+'/result_describeeocoverageset.xml ;   xmllint  --format  --output  '+def_output_path+'/result_describeeocoverageset.xml  ' +def_output_path+'/result_describeeocoverageset.xml' ]
	end


		; if /INFO is set and it is the first loop - then print some extra information
	if  ( keyword_set(INFO) AND loop eq 0 ) then begin
		print, newline, request
		pause
	endif

		; issue the actual request (using 'curl') via a call to the OS 
	if osversion eq 'UNIX' then begin
		spawn,  request , res_d, count=cres_d, /sh
	endif else begin
		if osversion eq 'WINDOWS' then 	begin
			spawn,  request , res_d, count=cres_d, /HIDE
		endif else begin
			spawn,  request , res_d, count=cres_d
		endelse
	endelse
	
	if (cres_d gt 0) then begin
		print, '---- ERROR ---- '+newline + res_d + newline 
		;return 
	endif

	
		; Extract the coverageIDs, from the xml response stored as file
	tag1=[ '<wcs:CoverageId>', '</wcs:CoverageId>']
	tag_begintime=[ '<gml:beginPosition>', '</gml:beginPosition>' ]
    tag_endtime=[ '<gml:endPosition>', '</gml:endPosition>' ] 


	print, newline
	print, '==> Evaluating Response of the DescribeEOCoverageSet Request...'

		; read the DescribeEOCoverageSet response and extract the CoverageIDs
	openr, lun1, def_output_path+'/result_describeeocoverageset.xml' , /get_lun
	i=0
	j=0
	tmp=''

	while not EOF(lun1) do begin
		readf, lun1,tmp 		; check how many lines there are
 		if strlen(tmp) gt 1 then i=i+1   ;check for emty lines 
		if strpos(tmp, tag1[0],0) gt -1 then j=j+1   ; check number of CoverageId  
	endwhile

	if (j eq 0 ) then begin
		print, newline ,'====================================================================='
		print, '  ***  Sorry, for this selection is currently no dataset available.  ***'
		print, '====================================================================='
		return
	endif
	
	point_lun,lun1,0	; reset the file to the beginning
	coverageid=strarr(j)
	begintime=strarr(j)
	endtime=strarr(j)
	j=0
	k=0
	m=0
	
		; step through the file and read CoverageId's as well as BeginTime and EndTime of each 
		; found coverage - be aware that the DatasetSeriesDescriptions will also show up 
	while m le n_elements(coverageid)-1 do begin
		readf,lun1,tmp

		if strlen(tmp) gt 1 then begin
			if strpos(tmp, tag1[0],0) gt -1 then begin
				pos1=strpos(tmp,'Id>',0)
				pos2=strpos(tmp,'</wcs',0)
				coverageid[j]=strmid(tmp, pos1+3, (pos2-pos1-3) )
				j=j+1
			endif else begin
				if strpos(tmp, tag_begintime[0],0) gt -1 then begin
					pos1=strpos(tmp,'beginPosition>',0)
					pos2=strpos(tmp,'</gml',0)
					begintime[k]=strmid(tmp, pos1+14, (pos2-pos1-14) )
					k=k+1
				endif else begin
					if strpos(tmp, tag_endtime[0],0) gt -1 then begin
						pos1=strpos(tmp,'endPosition>',0)
						pos2=strpos(tmp,'</gml:',0)
						endtime[m]=strmid(tmp, pos1+12, (pos2-pos1-12) )
						m=m+1
					endif
				endelse
			endelse
		endif
	endwhile

	free_lun,lun1

		; print out the number and CoverageIDs of the available coverages found for the 
		; DatasetSeries, TOI, and AOI
 	print, 'Number of available coverages: ', strtrim(n_elements(coverageid),2), newline
  	for j=0, n_elements(coverageid)-1 do   print, 'Available CoverageId:  '+strtrim(j+1,2)+' -- '+coverageid[j]

		; print minimum and maximum of begintime[] and the endtime[], respecively
	print, newline, 'Datasets are available between: ',min(begintime[*]), ' and ', max(endtime[*])


		; get prepared for analysing the received images
		; create 5 arrays to store the actual data in (1 for snow, 1 no_snow, 1 for clouds, 1 for 0/255 values, 1 for all other values)
	snow=fltarr(n_elements(coverageid))
	n_snow=lonarr(n_elements(coverageid))
	n_nosnow=lonarr(n_elements(coverageid))
	n_cloud=lonarr(n_elements(coverageid))
	n_nil=lonarr(n_elements(coverageid))
	n_other=lonarr(n_elements(coverageid))

	xaxis=lindgen(n_elements(coverageid))+1


		; get a first file to gather information about the actual size of the requested datasets 
		; prepare the basic request construct - here it is a GetCoverage Request
	base_getcov='/cryoland/ows?service=wcs&version=2.0.0&request=getcoverage&coverageid='+coverageid[cnt]+'&format=image/tiff&subset=x,http://www.opengis.net/def/crs/EPSG/0/4326('+select_aoi[0]+','+select_aoi[1]+')&subset=y,http://www.opengis.net/def/crs/EPSG/0/4326('+select_aoi[2]+','+select_aoi[3]+')&outputcrs=epsg:4326&rangesubset=gray'

		; prepare the request using 'curl' via a call to the OS
	request=[ 'curl -s "'+server+base_getcov+'" -k -o  '+def_output_path+'/'+coverageid[cnt]  ]
	
		; issue the actual request 
	if osversion eq 'UNIX' then begin
		spawn,  request , res_d, count=cres_d, /sh
	endif else begin
		if osversion eq 'WINDOWS' then 	begin
			spawn,  request , res_d, count=cres_d, /HIDE
		endif else begin
			spawn,  request , res_d, count=cres_d
		endelse
	endelse
	if (cres_d gt 0) then begin
		print,'Error with accessing coverages:'
		return
	endif else begin 
			; get the dimenesions of the returned image -- needed for the data analysis part
		dim_mask=size(read_tiff(def_output_path+'/'+coverageid[0]))
	endelse

		; get the spatial resolution of the images 
	resolution=strmid(coverageid, 4, strpos(coverageid, 'deg',0)-4)


		; use the images size to define the size of the display window
	if dim_mask[1] lt 400 then shp_xwin=400 else shp_xwin=dim_mask[1]
	if dim_mask[2] lt 400 then shp_ywin=400 else shp_ywin=dim_mask[2]


; 
; 		; calculate the approx. area of a pixel 
	r= 6378.137   ; from WGS-84
	deg_rad = !PI/180D
	km_vert = (2.*r*!PI)/360D   ; in the Lat direction the km/degree is constant
	center = (float(select_aoi(3))+float(select_aoi(2)))/2.
	dif_sn = abs(float(select_aoi(3))-float(select_aoi(2)))
	dif_we = abs(float(select_aoi(0))-float(select_aoi(1)))


		; the radius at the Lat-circle
	rad_n = r*cos(select_aoi(3)*deg_rad)
	rad_c = r*cos(center*deg_rad)
	rad_s = r*cos(select_aoi(2)*deg_rad)

		; km per degree at that Lat
	km_hor_n = 2*!pi*rad_n/360D
	km_hor_c = 2*!pi*rad_c/360D
	km_hor_s = 2*!pi*rad_s/360D

		; pixel resolution at the Lat-circle in meter
	pix_res_c = km_hor_c*dif_we/dim_mask[1]

		; line resolution in [m]
	line_res = dif_sn*km_vert/dim_mask[2]



		; set parameters for the plots
	minval=0
	yaxis=[0,100]			; because it's always max 100%
	yaxis2=[0,dim_mask[4]]
	del = 1./6.		; Width of bars in data units

	; create plot windows
		window, 0,xsize=1000,ysize=400
        window, 1,xsize=1000,ysize=500
        window, 2,xsize=shp_xwin, ysize=shp_ywin

	
		; define various stuff for the plots (axis, etc.)
	wset,0
	;!P.COLOR=0
	plot,  [min(xaxis),max(xaxis)+1], [0,120] , /nodata, xtitle='No. of Coverages', ytitle='Avg. Snowcover of Valid Pixel', $
		XTHICK=3, YTHICK=2, ystyle=16, xcharsize=2 , ycharsize=2 , thick=2, font=1, xmargin=[12,3], $
		ymargin=[7,2]	, symsize=1.5	


		; due to the switching between the plot windows the settings have to be saved and newly set after each switching - otherwise the colors will screw up
	winset0y=!y
	winset0x=!x
	
	wset,1
	;!P.COLOR=0
	plot, [min(xaxis),max(xaxis)+1], [0.0001,dim_mask[4]], yrange=yaxis2, /nodata, /ynozero, ytickformat='(I9)', font=1, $
		xtitle='No. of Coverages', ytitle='Pixelnumber', XTHICK=2, YTHICK=2, ystyle=16,  $
		thick=3, xcharsize=2 , ycharsize=2,  xmargin=[15,3], ymargin=[10,2]	;,/Ylog

	winset1y=!y
	winset1x=!x


		; arrays to calculate and store the fractional snow cover per pixel per image
	rep_area10=fltarr(n_elements(coverageid))
	rep_area20=fltarr(n_elements(coverageid))
	rep_area30=fltarr(n_elements(coverageid))
	rep_area40=fltarr(n_elements(coverageid))
	rep_area50=fltarr(n_elements(coverageid))
	rep_area60=fltarr(n_elements(coverageid))
	rep_area70=fltarr(n_elements(coverageid))
	rep_area80=fltarr(n_elements(coverageid))
	rep_area90=fltarr(n_elements(coverageid))
	rep_area100=fltarr(n_elements(coverageid))



				; get all the files with the chosen Dataset, AOI and TOI
	for cnt=0, n_elements(coverageid)-1 do begin
		print,newline
		print,'==> Downloading Coverage: # '+strtrim(cnt+1,2)
			; # GetCoverage

			; define the "base" request
		base_getcov='/cryoland/ows?service=wcs&version=2.0.0&request=getcoverage&coverageid='+coverageid[cnt]+'&format=image/tiff&subset=x,http://www.opengis.net/def/crs/EPSG/0/4326('+select_aoi[0]+','+select_aoi[1]+')&subset=y,http://www.opengis.net/def/crs/EPSG/0/4326('+select_aoi[2]+','+select_aoi[3]+')&outputcrs=epsg:4326&rangesubset=gray'

			; construct the request
		if  ( keyword_set(INFO) AND loop eq 0 ) then begin
			request=[ 'curl "'+server+base_getcov+'" -k -o  '+def_output_path+'/'+coverageid[cnt]  ]
		endif else begin 
			request=[ 'curl -s "'+server+base_getcov+'" -k -o  '+def_output_path+'/'+coverageid[cnt]  ]
		end
		
			; if /INFO is set then print it so we see something on the screen
		if  ( keyword_set(INFO) AND loop eq 0 ) then begin 
			print,request
			pause
		endif

			; issue the request 
		if osversion eq 'UNIX' then begin
			spawn,  request , res_d, count=cres_d, /sh
		endif else begin
			if osversion eq 'WINDOWS' then 	begin
				spawn,  request , res_d, count=cres_d, /HIDE
			endif else begin
				spawn,  request , res_d, count=cres_d
			endelse
		endelse
		
		if (cres_d gt 0) then begin
			print, res_d
		endif

			; now extract the value out of the TIFF file
		in_img=read_tiff(def_output_path+'/'+coverageid[cnt]) 

		wset,2
			; change the colortable, to C/W, so the images don't look weired
		loadct,0, /SILENT
			; change the colortable back - so the bar charts are colored
		tv,in_img
		loadct,38, /SILENT
		

		idx=where(in_img gt 100 AND in_img le 200 , count)
		if (count gt 0) then  begin
				;	print, 'Valid data: ', count
 			if ( ( keyword_set(INFO) AND loop eq 0 ) AND count le 100 ) then begin
 				print, 'Valid data: ',newline, in_img[idx]
 				pause
 			endif

				; calculate the mean of valid values and store in array
			snow[cnt]= mean(in_img[idx]-100)
			n_snow[cnt]=count

		endif ; else 	print, 'No valid Snow-Data encountered in the current selection'

		no_pix=dim_mask[1]*dim_mask[2]
		print, count, (strtrim(count,2)/float(no_pix))*100, format='("Overall valid snow data: ",I," pixel  ( ",F5.2 ," %)" )' 



			; count the basic type classes
		cloud=where(in_img eq 30, count)
		if (count gt 0) then n_cloud[cnt]=count

		nil=where(in_img eq 0 OR in_img eq 255, count)
		if (count gt 0) then n_nil[cnt]=count

		nosnow=where(in_img eq 100 OR in_img eq 50, count)
		if (count gt 0) then n_nosnow[cnt]=count

		other=where( (in_img lt 100 or in_img gt 200) AND in_img ne 30 and in_img ne 0 and in_img ne 255 and in_img ne 50, count)
		if (count gt 0) then n_other[cnt]=count
			

			; if a FSC_ DatasetSeries has been chosen, calculate some extra "area based" statistics
			; for the Fractional Snow Cover"
			; now count the FSC pixel classes and then calculate the representative area for each class
			; this shall be done only for FSC datsets
		search='FSC_'
		valids=strpos(coverageid[cnt], search )
		if (valids ne -1) then begin
			idx10=where(in_img ge 101 AND in_img le 110 , count)
			if (count gt 0) then  rep_area10[cnt]=count*0.1*pix_res_c*line_res
				
			idx20=where(in_img ge 111 AND in_img le 120 , count)
			if (count gt 0) then  rep_area20[cnt]=count*0.2*pix_res_c*line_res

			idx30=where(in_img ge 121 AND in_img le 130 , count)
			if (count gt 0) then  rep_area30[cnt]=count*0.3*pix_res_c*line_res

			idx40=where(in_img ge 131 AND in_img le 140 , count)
			if (count gt 0) then  rep_area40[cnt]=count*0.4*pix_res_c*line_res
			
			idx50=where(in_img ge 141 AND in_img le 150 , count)
			if (count gt 0) then  rep_area50[cnt]=count*0.5*pix_res_c*line_res

			idx60=where(in_img ge 151 AND in_img le 160 , count)
			if (count gt 0) then  rep_area60[cnt]=count*0.6*pix_res_c*line_res

			idx70=where(in_img ge 161 AND in_img le 170 , count)
			if (count gt 0) then  rep_area70[cnt]=count*0.7*pix_res_c*line_res

			idx80=where(in_img ge 171 AND in_img le 180 , count)
			if (count gt 0) then  rep_area80[cnt]=count*0.8*pix_res_c*line_res

			idx90=where(in_img ge 181 AND in_img le 190 , count)
			if (count gt 0) then  rep_area90[cnt]=count*0.9*pix_res_c*line_res

			idx100=where(in_img ge 191 AND in_img le 200 , count)
			if (count gt 0) then  rep_area100[cnt]=count*1.0*pix_res_c*line_res

		endif



		wset,0
		!y=winset0y
		!x=winset0x
		plots, xaxis[cnt], snow[cnt] , psym=2, color=colors[2], symsize=1.5	
		plots, xaxis[cnt], snow[cnt] , psym=6, color=colors[2], symsize=1.5	

		allpts=[ [n_snow], [n_nosnow], [n_cloud], [n_nil], [n_other] ]
		barnames=['n_snow', 'n_nosnow', 'n_cloud', 'n_nil', 'n_other' ]


			; provide info about the size of the image downloaded
		if loop eq 0 then begin
			;print, newline
			print, "Image X-Size:   ", dim_mask[1]
			print, "Image Y-Size:  ", dim_mask[2]
			print, "Number of Pixels: ", no_pix
			print,newline
		endif


		if  ( keyword_set(INFO) AND loop eq 0 ) then begin
			print, 'Average Snowcover: ',xaxis[cnt], snow[cnt],'%'
			print, ' n_snow:   ' ,allpts[0,0]
			print, ' n_nosnow: ' ,allpts[0,1]
			print, ' n_cloud:  ' ,allpts[0,2]
			print, ' n_nil:    ' ,allpts[0,3]
			print, ' n_other:  ' ,allpts[0,4]
			pause
		endif
		


		if  ( keyword_set(INFO) AND loop eq (n_elements(coverageid)-1) ) then begin
			print, newline, newline
			print, "Pixel Size in km2: ", pix_res_c*line_res
			print, 'coverage#  -   average %   -   n_snow  -  n_nosnow  -  n_cloud   -   n_other'
			for ii=0, (n_elements(coverageid)-1) do begin
					print,ii+1,': ',snow[ii],allpts[ii,0], allpts[ii,1], allpts[ii,2],allpts[ii,4]
			endfor
	        print,newline
		endif



		wset,1
		!y=winset1y
		!x=winset1x
		
			; create the annotations/legend
		xbase=200
		ybase=20
		xblock=20
		yblock=10
		
		if ( loop eq 0 ) then begin
			for an=0, n_elements(allpts[0,*])-1 do begin
				xshift=an*140
				BOX, xbase+xshift, ybase, xbase+(xblock+xshift),  ybase+yblock, colors[an], /device
					; this line for IDL
				XYOUTS, xbase+(2*xblock)+xshift, ybase, barnames[an], font=1, charsize=2,  /device 
					; this line for GDL
				;XYOUTS, xbase+(2*xblock)+xshift, ybase, barnames[an],  charsize=2,  /device 
			endfor
		endif


			; do the bar chart
		for iscore=0,4 do begin			
			xoff = iscore * del - 2 * del
			
			for iday=0,n_elements(xaxis)-1 do $
			 	box, xaxis[iday]+xoff, minval, xaxis[iday]+xoff+del, allpts[iday, iscore], colors[iscore]
		endfor	

		loop=loop+1
	endfor

	area_sum=(rep_area10+rep_area20+rep_area30+rep_area40+rep_area50+rep_area60+rep_area70+rep_area80+rep_area90+rep_area100)
		
		
		; now connect all snow points, which have a value above zero (ignore fully clouded images)
	snowidx=where(snow gt 0, count)
	if count gt 0 then begin
		snowval=snow[snowidx]
		xval=xaxis[snowidx]
	
		wset,0
		!y=winset0y
		!x=winset0x
		for cnt1=0, count-1 do  plots, xval[cnt1], snowval[cnt1], color=colors[2], linestyle=solid, /continue, thick=2
	endif

	print,newline
	print, "Pixel Size in km2: ", strmid(strtrim(pix_res_c*line_res,2),0,6)
	print, 'coverage#  -  total snow coverage  -  n_snow  -  n_nosnow  -  n_cloud   -   n_other'
	for ni=0,(n_elements(area_sum)-1) do begin
		print,ni+1,': ',area_sum[ni],' km2  - ',allpts[ni,0], allpts[ni,1], allpts[ni,2],allpts[ni,4]
	endfor





END 	; end of main procedure
;=============================================================================
; END of MAIN 
;=============================================================================

