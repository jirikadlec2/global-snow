;+
; NAME:
;       scripting_wcs_donwload.pro
;
; PURPOSE:
; 	 - demonstrate the automated access to an OGC-WCS 2.0/EO-WCS interface to 
; 		 gather information about the service and receive data
;	   - the script expects the input via commandline parameters. If no input is provided, default values will be used.
;		   It is intended to be mainly used with the same parameters (same Area & same DatasetSeries just with a 
;		   changing date e.g. yesterday's image. I.e. it could be run atomatically on a daily base ( every morning)
; 		 to receive the latest image (see also below: "USER-SPECIFIC DEFINITIONS" and "DEFAULT VALUES"). 
;	   - send a DescribeCoverageSet request to gather information about data availability for the AOI and TOI
;    - send a series of EO-WCS (GetCoverage) request to the OGC-WCS/EO-WCS interface of the CryoLand instance 
;		   and receive the data
;
; CATEGORY:
;      Demonstration - Proof of Concept to demonstrate the EO-WCS functionality when implemented
; 		 in a User's Application (eg. in a GIS / Expert System) 
;
; CALLING SEQUENCE:
;       scripting_wcs_download
;
; USAGE:
;       scripting_wcs_donwload
;       scripting_wcs_donwload, output = <path to storage location>
;       scripting_wcs_donwload, output = <path to storage location>, logfile = <path & name of logfile>
;       scripting_wcs_donwload, output = <path to storage location>, logfile = <path & name of logfile>, 
;				toi = ['2013-03-01T00:00Z', '2013-03-08T23:00Z']
;       scripting_wcs_donwload, output = <path to storage location>, logfile = <path & name of logfile>, 
;				toi = ['2013-03-01T00:00Z', '2013-03-08T23:00Z'], aoi = [ '10.0','11.0','46.0','47.0' ]
;       scripting_wcs_donwload, output = <path to storage location>, logfile = <path & name of logfile>, 
;				toi = ['2013-03-01T00:00Z', '2013-03-08T23:00Z'], aoi = [ '10.0','11.0','46.0','47.0' ],
;				dss = 'FSC_Alps'
;
;	There are the Sections  "USER-SPECIFIC DEFINITIONS" and  "DEFAULT VALUES"  where you may change the default 
; 	behaviour of this script. 
;
;
; INPUT PARAMETERS:
;       None
;
; KEYWORD PARAMETERS:
; 		OUTPUT ---  path to the location where the received (donwloaded) datasets shall be stored.
;					  If not provided then the default location will be used
; 					Defaults: Linux = your HOME-Directory , Windows = C:\, MacOS - "?"
; 		LOGFILE --  path and filename where the logfile should be written.  If not provided output is 
; 					on the screen (= default).
;		  TOI	   ---  Time of Interest with Start-Time and Endtime e.g. toi=['2013-03-01T00:00Z', '2013-03-08T23:00Z']
; 		AOI	   ---  Area of Interest, providing the corner coordinates of the Bounding Box e.g.
;					aoi=[ '10.0','11.0','46.0','47.0' ]
;		  DSS	   ---  DataSertSeries provided by CryoLand e.g. dss='FSC_Alps'
;					at the time of writing the following DatasetSeries are avialable: 
;					'daily_FSC_PanEuropean_Optical', 'daily_SWE_PanEuropean_Microwave', 'daily_FSC_Baltic_Optical', 
;					'multitemp_FSC_Scandinavia_Multisensor', 'daily_SCA_CentralEurope_Optical', 'daily_FSC_Alps_Optical'
;					(this list will change during the CryoLand projects runtime.)
;
;
; OUTPUTS:
;			If the LOGFILE is provided at the command-line then no output is provided. If no LOGFILE is given 
; 			then the same information is printed to the screen
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
;
;		This script doesn't use advanced features (like IDL's XML handling) in order to run under older 
;		version as well as under the free OpenSource version GDL (-> GnuDataLanguage). However, for GDL there 
;		might need to be some minor changes applied.
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
; MAIN    -  scripting_wcs_donwload
;
;#################################################################################
;#################################################################################
;=============================================================================
PRO scripting_wcs_download, output=output, aoi=aoi, toi=toi, dss=dss, logfile=logfile




; ########## GENERAL DEFAULT DEFINITIONS #########
; do not make changes in this section unless you know what you are doing

sep=path_sep()        		; directory separator
osversion = StrUpCase(!version.os_family)

  CASE osversion OF
    'UNIX':	BEGIN 	
		spawn,'echo $HOME',myhome, /sh	; get the user's home directory
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

newline=string(10B)        ;linefeed 

; ### END OF GENERAL DEFINITIONS #########





;  ### USER-SPECIFIC DEFINITIONS ###
;  change setting as required by your system
;
	; Time of Interest - this setting will request the latest image
DEF_TOI=['YESTERDAY','TODAY']
	; another example - requesting a time-series
;DEF_TOI=['2013-03-01T00:00Z', '2013-03-08T23:00Z']

; Area of Interest
DEF_AOI=[ '10.0','11.0','46.0','47.0' ]	; Austria -Alps
	; another example
;DEF_AOI=[ '13.547', '15.722', '62.564', '64.831' ]	; Sweden

	; DatasetSeries of Interest
	; at the time of writing the following DatasetSeries are avialable: 
	;'daily_FSC_PanEuropean_Optical', 'daily_SWE_PanEuropean_Microwave', 'daily_FSC_Baltic_Optical', 
	;'multitemp_FSC_Scandinavia_Multisensor', 'daily_SCA_CentralEurope_Optical', 'daily_FSC_Alps_Optical'
	;       (this list will change during the CryoLand projects runtime.)
DEF_DATASETSERIES='daily_FSC_Alps_Optical'
	; another example
;DEF_DATASETSERIES='daily_FSC_PanEuropean_Optical'

;  ### END of USER-SPECIFIC DEFINITIONS ###




; ### DEFAULT VALUES are set here - to be used by default and if not provided via the commandline

	; set default output location or use the path provided with the OUTPUT parameter
	; changed the  def_output_path=  to your needs
IF (NOT(KEYWORD_SET(OUTPUT))) THEN  def_output_path=myhome   ELSE def_output_path=OUTPUT



; for the following defaults, changes should not be necessary -> change them in the  "USER-SPECIFIC DEFINITIONS"

; set default AOI if AOI is not provided at commandline
IF (NOT(KEYWORD_SET(AOI))) THEN  select_aoi=DEF_AOI   ELSE select_aoi=AOI

	; set default TOI if TOI is not provided at commandline
IF (NOT(KEYWORD_SET(TOI))) THEN BEGIN
	IF (DEF_TOI[0] eq 'YESTERDAY') THEN select_toi=get_today() ELSE select_toi=DEF_TOI
ENDIF ELSE select_toi=TOI

	; set default AOI if AOI is not provided at commandline
IF (NOT(KEYWORD_SET(DSS))) THEN  DATASETSERIES=DEF_DATASETSERIES   ELSE DATASETSERIES=DSS

	; if no logfile is provided at commandline - the output goes to the screen
IF (NOT(keyword_set(LOGFILE))) THEN uid=-1 ELSE openw,uid,logfile,/get_lun, /append

; ### END of DEFAULT VALUES are set here 










; ## don't make changes below - unless you know what you are doing


; ### Service Definitions ###
; Definitions needed for accessing the CryoLand services 
; Don't change unless you know what you are doing.
server='http://neso.cryoland.enveo.at'
scriptname='scripting_wcs_download.pro'



; ### Start of Code section ###

	; provide indication of script start (runtime)
printf,uid,'[',systime(),'] - Starting:  ',scriptname
printf,uid, 'User selections:  '
printf,uid, 'AOI:  ', select_aoi
printf,uid, 'TOI:  ', select_toi 
printf,uid, 'DATASETSERIES:  ', datasetseries


err_flag=0
cnt=0


; sent a DescibeCoverageSet request to the server to see what datasets are avialable for
; the chosen TOI, AOI and Dataset

		; the request is first plugged together and the user's choices are added
		; here it is a DescribeEOCoverageSet Request
	base_desccov='/cryoland/ows?service=wcs&version=2.0.0&request=describeeocoverageset&eoid='+DATASETSERIES+'&subset=x,http://www.opengis.net/def/crs/EPSG/0/4326('+select_aoi[0]+','+select_aoi[1]+')&subset=y,http://www.opengis.net/def/crs/EPSG/0/4326('+select_aoi[2]+','+select_aoi[3]+')&subset=phenomenonTime(%22'+select_toi[0]+'%22,%22'+select_toi[1]+'%22)'

		
	printf,uid, '==> Sending DescribeEOCoverageSet Request...'

			; combine the request with the curl command and the server information
		request=[ 'curl -s "'+server+base_desccov+'" -k -o '+def_output_path+'/result_describeeocoverageset.xml ;   xmllint  --format  --output  '+def_output_path+'/result_describeeocoverageset.xml  ' +def_output_path+'/result_describeeocoverageset.xml' ]

; uncomment if you like to have the requests documented in the logfile
;	printf,uid,request

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
		printf,uid, '---- ERROR ---- '+newline + res_d + newline 
		;return 
	endif

	
		; Extract the coverageIDs, from the  xml response stored as file
	tag1=[ '<wcs:CoverageId>', '</wcs:CoverageId>']

;	printf,uid, newline
	printf,uid, '==> Evaluating Response of the DescribeEOCoverageSet Request...'

		; read the DescribeEOCoverageSet response and extract the CoverageIDs
	openr, lun1, def_output_path+'/result_describeeocoverageset.xml' , /get_lun
	i=0
	j=0
	tmp=''

	while not EOF(lun1) do begin
		readf, lun1,tmp 		; check how many lines there are
 		if strlen(tmp) gt 1 then i=i+1   ;check for empty lines 
		if strpos(tmp, tag1[0],0) gt -1 then j=j+1   ; check number of CoverageIDs  
	endwhile

	if (j eq 0 ) then begin
;		printf,uid, newline ,'====================================================================='
		printf,uid, '================================================================================='
		printf,uid, '  ***  Sorry, currently there are no datasets available for this selection.  *** '
		printf,uid, '================================================================================='
		return
	endif
	
	point_lun,lun1,0	; reset the file to the beginning
	coverageid=strarr(j)
	j=0

	while not EOF(lun1) do begin
		readf,lun1,tmp

		if strlen(tmp) gt 1 then begin
			if strpos(tmp, tag1[0],0) gt -1 then begin
				pos1=strpos(tmp,'Id>',0)
				pos2=strpos(tmp,'</wcs',0)
				coverageid[j]=strmid(tmp, pos1+3, (pos2-pos1-3) )
				j=j+1
			endif
		endif
	endwhile

	free_lun,lun1

		; print out the number and CoverageIDs of the available coverages found for the 
		; DatasetSeries, TOI, and AOI
 	printf,uid, 'Number of available coverages: ', strtrim(n_elements(coverageid),2)		; , newline
  	for j=0, n_elements(coverageid)-1 do   printf,uid, 'Available CoverageId:  '+strtrim(j+1,2)+' -- '+coverageid[j]


				; get all the files with the chosen Dataset, AOI and TOI
	for cnt=0, n_elements(coverageid)-1 do begin
		printf,uid,'==> Downloading Coverage: # '+strtrim(cnt+1,2)
		
			; # GetCoverage
			; define the "base" request
		base_getcov='/cryoland/ows?service=wcs&version=2.0.0&request=getcoverage&coverageid='+coverageid[cnt]+'&format=image/tiff&subset=x,http://www.opengis.net/def/crs/EPSG/0/4326('+select_aoi[0]+','+select_aoi[1]+')&subset=y,http://www.opengis.net/def/crs/EPSG/0/4326('+select_aoi[2]+','+select_aoi[3]+')&outputcrs=epsg:4326&rangesubset=gray'

			; construct the request
		request=[ 'curl -s "'+server+base_getcov+'" -k -o  '+def_output_path+'/'+coverageid[cnt]  ]

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
			printf,uid, res_d
		endif

	endfor




printf,uid,'[',systime(),'] - *** D O N E ***:  ',scriptname
close,/all


END 	; end of main procedure
;=============================================================================
; END of MAIN 
;=============================================================================



