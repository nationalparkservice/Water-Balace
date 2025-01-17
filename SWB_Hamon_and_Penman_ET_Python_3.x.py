# ---------------------------------------------------------------------------
# Last Edited: 20200103 - KRS
#
# Anaconda Environment - PythonDemo
# SpatialWaterBalance_Hamon_and_Penman_ET.py
# Created on: 2020xxxx
# Description:  Script runs a monthly water balance model following
# logic defined in Lutz et. al 2010 and Dilts et. al 2015 Journal of Biogreography.
# Logic has been added to run the monthly water balance calculations across mulitple consecutive years.
#
# Lutz, J. A., van Wagtendonk, J.W and Franklin, J.F. (2010) Climatic water deficit,
# tree species ranges and climate change in Yosemite Nationa Park. Journal of Biogeopgrahpy, 37 (5), 936- 950.
#
# Dilts, T.E., P.J. Weisberg, C.M. Dencker., and J.C. Chambers. 2015. Functionally relevant climate variables
# for arid lands: a climatic water deficit approach for modelling desert shrub distributions. Journal of Biogeography.

# Output: Water Balance Related Rasters at a monthly time step including: Potential Evapotranspiration, Actual Evapotranspiration, Soil Water Balance,
# Water Deficit, Water Input, Rain, Snow Input, SnowPack, Snow Melt
#
# Derived By: Kirk Sherrill (Data Manager/GIS Analyst - Inventory and Monitoring Division - NPS)
# Script has been modified to process successive years of data (i.e. water balance across numerous years (e.g. 2000, 2001, 2002, ...)

# Processing logic has been added to derive evapotransprition using either a 'Penman-Monteith' (Physically Based) or 'Hamon' (Emperically Based)
# equations

###################################################
# Start of Parameters requiring set up.
###################################################

#Input Files
startYear = 2003    ##Start Year of Processing
endYear = 2007      ##End Year of Processing

snapRaster = r'D:\ROMN\working\WaterBalance\GRSA\GIS\GRSA_10km_AWS_0_150cm_Infill_100mm.tif'   #Raster for which output products will be snapped to
outCellSize = 10    #Output cell size for final parameters

#Hamon ET variables Mean Temp and Precip Variable only
tmeanDir = r'E:\SWB\GRSA\PRISM_2000_2016\TMEAN\Resampled'    ##Directory with the tmean variables to be used (e.g. 30 year normals 1981-2010 - 800m)
pptDir = r'E:\SWB\GRSA\PRISM_2000_2016\PPT\Resampled'        ##Directory with the PRISM ppt variables to be used (e.g. 30 year normals 1981-2010 - 800m)

#Penmon-Monteith ET variables (Daymet- NetCDF)
pptDir = r'F:\Daymet\Conus\Monthly\tif\prcp\GRSA\10m'         ##Directory with the ppt variables
tmaxDir = r'F:\Daymet\Conus\Monthly\tif\tmax\GRSA\10m'       ##Directory with the tmax variables
tminDir = r'F:\Daymet\Conus\Monthly\tif\tmin\GRSA\10m'       ##Directory with the tmin variables .tif files preprocessed to 10m
vpDir = r'F:\Daymet\Conus\Monthly\tif\vp\GRSA\10m'         ##Direcotry with the vapour pressure variables
sRad = r'F:\Daymet\Conus\Monthly\tif\srad\GRSA\10m'          ##Direcotry with the Solar Radiation variables (note Daymet sRad unit is W/m2)
dayl = r'F:\Daymet\Conus\Monthly\tif\dayl\GRSA\10m'          ##Directory with the Day Length variables
sweDir = r''                                                ##Directory with the SWE variables

heatLoadIndex = "Yes"       ##Switch ("Yes"|"No") defining if Heat Load Index (Topographic Factors Slope and Aspect) should be included in PET Calculation (See Eq 16 Dilts et. al. 2015 Biogeography)
etEquation = "Penman-Monteith"  ##Switch ("Hamon"|"Penman-Monteith") defining if the Evapotranspiration Equation to be used.
rasterHeatLoad = "N/A"       ##Switch("Dir Path"|"N/A") Optinal variable to define a previously derived Heat Load Index.  If set to "N/A" script will derive using Aspect, Slope and Latitude Inputs

#Misc Input Data Sets
septSnowPack = r'D:\ROMN\working\WaterBalance\GRSA\GIS\Sept_SnowPack_AllZero.tif'  ##Raster with default September Snow Pack for first year of processing - assumption is no snowpack at end of water year
latitude = r'D:\ROMN\working\WaterBalance\GRSA\GIS\Latitude_GRSA.tif' ##Raster with Latitude values (GCS) for the AOA (Not used if Daymet Daylegnth is being used, Match cell size and snap to input climatic variables.
aspectRas = r'D:\ROMN\working\WaterBalance\GRSA\GIS\aspect_albers_GRSA_10km.tif'#Aspect Raster
slopeRas = r'D:\ROMN\working\WaterBalance\GRSA\GIS\slope_albers_GRSA_10km.tif' #Slope Raster
elevation = r'D:\ROMN\working\WaterBalance\GRSA\GIS\dem_albers_GRSA_10km.tif' #Dem Raster

soilAWS = r'D:\ROMN\working\WaterBalance\GRSA\GIS\GRSA_10km_AWS_0_150cm_Infill_100mm.tif'   ##Available water supply (mm) raster from gSSURGO data to a define soil depth (e.g. 0-150 cm, etc.), Null values have been infilled with a near Mean AWS value of 125 mm.
percAWSInitial = 10   ##The percent (0-100%)of AWS by soil to be used in the initial previous month (September) calculation of the soil water balance.

#DayLength Rasters Definition
deriveDayLengthRasters = "No"     ##Switch ("Yes"|"No") defining if Average Day Length rasters (Hours) by month should be derived (Yes) or use Daymet average daylength rasters (No) in
                            ##place of manually derived.  Note as of 2015/08/31 - equations for Manually derived day Length Calculations are not working correctly.
avgMonthlyDayLengthRasters = r'D:\ROMN\working\Climate\Daymet\GRSA_Average_DayLength'   ## Average monthly day length rasters - obtained from Daymet Data.
dayLengthWildCard = "*Average_dayl_2010"   ##WildCard Syntax for DayLength Rasters (not used if manually derived day Length.  Month and .tif are always the end suffix - Not Appliciable if using Daymet Data and Penman-Monteith ET

#Output and Workspace Parameters
outDir = r'F:\SWB\GRSA\Penman_ET'   ## Location for output
workspace = r'F:\SWB\GRSA\Penman_ET\workspace'      ## Workspace for Processing
logFileName = workspace + "\AAA_GRSA_Penman_ET_logFile.txt"          ##Logfile Name

#######################################
## Below are paths which are hard coded
#######################################
# Import system modules
import sys, string, os, math, glob, traceback
#import pandas as pd
##import geopandas as geopd
import numpy as np
import gdal

#Import GDAL
from osgeo import gdal
from gdalconst import *
import osr  #GDAL Projections

#Import netCDF4 library for reading netCDF files
import netCDF4

##################################
# Checking for working directories
##################################

if os.path.exists(workspace):
    pass
else:
    os.makedirs(workspace)

#Check if LogFile Exists
if os.path.exists(logFileName):
    pass
else:
    logFile = open(logFileName, "w")    #Creating log file if it doesn't exist
    logFile.close()

deleteList = [] #Default delete list
def timeFun():          #Function to Grab Time
    from datetime import datetime
    b=datetime.now()
    messageTime = b.isoformat()
    return messageTime
#################################################
##

def main():
    try:

        yearRange = range(startYear, endYear + 1)

        for year in yearRange:

            #Loop thru months to derive monthly variables
            monthList = ["10","11","12","01","02","03","04","05","06","07","08","09"]
            monthCount = 1
            for month in monthList:

                ## Add logic to add the change of year value after Oct,Nov,Dec months'  - - KRS 20171228
                if month not in ["10","11","12"]:
                    year = year + 1

                #Define the tmin path
                dirPath_Name = tminDir + "\\*MonAvg_" + str(year) + month + "*.tif"  #Directory Path and wildcard syntx for the srad NC File'
                tmin_NC = glob.glob(dirPath_Name)

                #Create the tmin array
                tmin_np = raster2array(tmin_NC[0])

                #Define the tmax path
                dirPath_Name = tmaxDir + "\\*MonAvg_" + str(year) + month + "*.tif"  #Directory Path and wildcard syntx for the srad NC File'
                tmax_NC = glob.glob(dirPath_Name)

                #Create the tmax array
                tmax_np = raster2array(tmax_NC[0])

                #Derive the avgTemp dataset
                monthlyTempMean = calc_avgTemp(tmin_np, tmax_np)

                #Define the month precip
                dirPath_Name = pptDir + "\\*Monttl_" + str(year) + month + "*.tif"  #Directory Path and wildcard syntx for the srad NC File'
                ppt_NC = glob.glob(dirPath_Name)

                #Create the ppt array
                monthlyPrecip = raster2array(ppt_NC[0])

                #Create Monthly Melt Factors, Rain and Snow Fractions
                out1 = meltFactorRainSnow(monthlyTempMean, monthlyPrecip, month, year)

                meltFactor = out1[0]
                rainFraction = out1[1]
                snowFraction = out1[2]
                outArraySize = out1[3]  #Define the output Array cell sizes based upon the input monthlyTempMean Raster

                #Derive the Snow Melt, Snow Pack and Monthly Water Input
                snowMeltSnowPackWaterMonthly(meltFactor, monthlyPrecip, snowFraction, rainFraction, month, monthCount, monthList, year)

                if deriveDayLengthRasters == "Yes" and year == startYear:  #Manually Dervied Day Average Day Length Rasters (only necessary the first year)
                    #Calculate the Solar Declination angle for the month - Logic I believe is correct 20150831 - KRS
                    monthSolarDec = solarDeclination(month)

                    #Monthly Day Length Calculation Equation 11   ####Equation for DayLength Calulcation is incorrect as of 20170211 - KRS
                    avgDayLengthRas = dayLengthRas(latitude, monthSolarDec, month)

                elif year == startYear:  #Using Daymet Daylength Output - Must Convert from Seconds to Hours (only necessary the first year)
                    wildCardSyntax = dayLengthWildCard + month + ".tif"
                    monthlyDayLength = glob.glob(avgMonthlyDayLengthRasters + "\\" + wildCardSyntax)

                    monthlyDayLengthHr = outDir + "\\MonthlyDLHr_" + str(month) + ".tif"

                    #Define Numpy Array Monthly Day Length
                    dayLength_Sec_NP = raster2array(monthlyDayLength[0])

                    divide_3600_NP = raster2array(monthlyDayLength[0])
                    #Create Raster with value 225 every where
                    divide_3600_NP[divide_3600_NP > -999] = 3600

                    #Calculate Hours Day Lenth Array
                    hoursDL_NP2 = np.divide(dayLength_Sec_NP, divide_3600_NP)
                    del dayLength_Sec_NP
                    del divide_3600_NP

                    #Set Null (ie. <= 1 Hour) Values to NaN
                    #hoursDL_NP2[hoursDL_NP2 <= 1] = np.NaN  #Array indexing to NaN is not working (12/28/2017 KRS)

                    array2raster(monthlyDayLength[0], monthlyDayLengthHr,hoursDL_NP2)
                    del hoursDL_NP2
                    messageTime = timeFun()
                    print ("Derived Monthly Day Lenght Raster - " + month + " - " + monthlyDayLengthHr + " - " + messageTime)

                    avgDayLengthRas = monthlyDayLengthHr
                    monthSolarDec = "Null"

                if heatLoadIndex.lower() == "yes":  #Calculate PET using Heat Load Index (only necessary the first year)

                    #Derive Heat Load Index - Only necessary on first monthly loop
                    if rasterHeatLoad == "N/A" and monthCount == 1 and year == startYear:

                        #Derive Folded Aspect - Equation 14 Dilts. et. al. 2015
                        aspFoldedRas = aspectFolded(aspectRas, monthlyTempMean)

                        #Derive Heat Load Aspect - Equation 15 Dilts. et. al. 2015
                        outheatLoad = heatLoadIndexFun(aspFoldedRas, slopeRas, latitude, outArraySize)
                        heatLoadIndexRas = outheatLoad

                    else:    #Heatload already derived
                        outheatLoad = outDir + "\\HeatLoadIndex.tif"
                        heatLoadIndexRas = outheatLoad

                    ##########
                    #Calculate PET with Heat Index Included with 'Hamon' or 'Penman-Monteith' equations
                    ##########

                    if etEquation == "Hamon":

                        petHeatLoad(avgDayLengthRas, monthSolarDec, monthlyTempMean, heatLoadIndexRas, month, year)

                    elif etEquation == "Penman-Monteith":

                        #Derive the 'Penman-Monteith' ET
                        out_Penman_ET = Penman_Montieth(year, month)

                        #Caluclate the Penman ET with the Heat Load Correction (Penman ET * heatload
                        petHeatLoad_wPenman(out_Penman_ET, heatLoadIndexRas)

                    else:
                        print ("No Evapotranspiration forumula was defined.  Exiting script now, define the 'etEquation' parameter before proceeding")
                        sys.exit()


                elif heatLoadIndex == "No":   #Not using Heat Index

                    ##########
                    #Calculate PET no Heat Index Included with 'Hamon' or 'Penman-Monteith' equations
                    ##########

                    if etEquation == "Hamon":

                        #Derive the Potential Evapotranspiration Equation 9 (Lutz et. al.)
                        potEvapoTrans(avgDayLengthRas, monthSolarDec, latitude, monthlyTempMean, month, year)

                    elif etEquation == "Penman-Monteith":

                        # Derive the 'Penman-Monteith' ET
                        Penman_Montieth(year, month)

                    else:
                        print ("no Evapotranspiration forumula was defined.  Exiting script now, define the 'etEquation' parameter before proceeding")
                        exit()

                ##Set Yearly value back after processing a month - KRS 20171228
                if month not in ["10","11","12"]:
                    year = year - 1

                ###############
                #Clean up routine
                #################

                deleteList = glob.glob(workspace + "\\*.tif*")

                for file in deleteList:
                    try:
                        os.remove(file)

                    except:
                        print ("Failed to Delete " + str(file))
                        traceback.print_exc(file=sys.stdout)

                monthCount +=1

            ##############################################################
            #After Creation of the Monthly Water Input and PET Raster - Derive Water Balance Output Variables:
            ###########################################
            #Calculate the Initial Soil Water Balance - Equation 12, subsequent calculation will remove the fraction removed from Soil Water Storage (eg. 13) where PET < Water Input.
            ###########################################

            #Loop thru months to derive monthly variables
            monthCount = 1
            for month in monthList:
                out4 = soilWaterBalance(soilAWS, monthCount, month, monthList, year)
                monthCount += 1

            #####################
            #Calculate Actual Evapotranspiration - Using PET, Soil Water Storage Removed and Water Input
            ###########################################

            monthCount = 1
            for month in monthList:
                outAET = actualEvapoTrans(month, year)
                monthCount += 1

            ###########################################
            #Calculate Water Deficit = Potential Evapotranspiration - Actual Evapotranspiration
            ###########################################

            monthCount = 1
            for month in monthList:
                outDeficit = waterDeficit(month, year)
                monthCount += 1



            ###################################
            ################################### 20200130
            #These Functions need to be defiend from 'WaterBalance_SingleYear_GDAL_Numpyt_Py3pt6_nNewVar_20190603
            ###########################################
            # Calculate Annual Water Deficit (CumlCWD Dilts et. al 2015) Sum of months in year(Potential Evapotranspiration Monthly - Actual Evapotranspiration Monthly)
            ###########################################

            outAnnualWaterDeficit = annualWaterDeficit(monthList)

            ###########################################
            # Calculate Water Supply = SnowMelt + Rain Input
            ###########################################

            monthCount = 1
            for month in monthList:
                outwaterSupply = waterSupply(month)
                monthCount += 1

            ###########################################
            # Calculate Water Supply - AET.  Where AET > Water Supply value is set to Zero.  - New Function 20190603
            ###########################################
            monthCount = 1
            for month in monthList:
                outWSAET = WSAET(month)
                monthCount += 1

            ###########################################
            # Calculate Spring Water Supply - AET.  Where AET > Water Supply value is set to Zero.  - New Function 20190603
            # Dervied by Summing the monthly Water Supply - AET for all spring months (March, April, May).  When Monthly AET > water supply, water supply value is set to zero.
            # Output Raster - 'WS_AETSpr'
            monthListSpring = ["03", "04", "05"]
            outWsAETspr = WSAET_Spr(monthListSpring)

            ###########################################
            # Calculate Monthly RunOff - Runoff is where WaterSupply is > AET and the Soil Water Holding Capacity is Exceeded (SWB + WaterSupply is > Soil Water Holding Capacity).
            # (Water Supply - AET, where neg (i.e. AET great WaterSupply, set to zero)
            # Output Raster - RunOff_{Month}
            ###########################################
            monthCount = 1
            for month in monthList:
                outRunOff = RunOff(month)
                monthCount += 1

            ###########################################
            # Spring Monthly RunOff - Runoff is where WaterSupply is > AET and the Soil Water Holding Capacity is Exceeded (SWB + (WaterSupply - AET (i.e. WS_AET)) is > Soil Water Holding Capacity).
            # (Water Supply - AET, where neg (i.e. AET greater WaterSupply, set to zero).  i.e. When the soil water bucket overflows, the water is lost as runoff.
            # Monthly RunOff for months March, April, May are summed for 'SpringRunOff'
            # Output Raster - 'RunOffSpr'
            ############################################
            monthListSpring = ["03", "04", "05"]
            outWsAETspr = SpringRunOff(monthListSpring)

            #################
            #Clean up routine
            #################

            deleteList = glob.glob(workspace + "\\*.tif")
            for file in deleteList:
                try:
                    os.remove(file)

                except:
                    print ("Failed to Delete " + str(file))
                    traceback.print_exc(file=sys.stdout)


            messageTime = timeFun()
            print ("Completed Processing Water Balance Parameters for: " + str(year) + " - " + messageTime)
            scriptMsg = ("Completed Processing Water Balance Parameters for: " + str(year) + " - " + messageTime)
            logFile = open(logFileName, "a")
            logFile.write(scriptMsg + "\n")
            logFile.close()

            #End of Processing for the 'year'

    except:
        messageTime = timeFun()
        scriptMsg = "ClimateWaterDeficit_GDAL_Numpy.py - " + messageTime
        print ("Error ClimateWaterDeficit_GDAL_Numpy.py\nSee log file " + logFileName + " for more details - " + messageTime)
        logFile = open(logFileName, "a")
        logFile.write(scriptMsg + "\n")
        traceback.print_exc(file=sys.stdout)
        logFile.close()


def raster2array(rasterfn):
    raster = gdal.Open(rasterfn)
    band = raster.GetRasterBand(1)
    return band.ReadAsArray()



def getNoDataValue(rasterfn):
    raster = gdal.Open(rasterfn)
    band = raster.GetRasterBand(1)
    return band.GetNoDataValue()

def array2raster(rasterfn,newRasterfn,array):
    raster = gdal.Open(rasterfn)
    geotransform = raster.GetGeoTransform()
    originX = geotransform[0]
    originY = geotransform[3]
    pixelWidth = geotransform[1]
    pixelHeight = geotransform[5]
    cols = raster.RasterXSize
    rows = raster.RasterYSize

    driver = gdal.GetDriverByName('GTiff')
    outRaster = driver.Create(newRasterfn, cols, rows, 1, gdal.GDT_Float32)
    outRaster.SetGeoTransform((originX, pixelWidth, 0, originY, 0, pixelHeight))
    outband = outRaster.GetRasterBand(1)
    outband.WriteArray(array)
    outRasterSRS = osr.SpatialReference()
    outRasterSRS.ImportFromWkt(raster.GetProjectionRef())
    outRaster.SetProjection(outRasterSRS.ExportToWkt())
    outband.FlushCache()

#Fuction derives the Monthly Melt Factor, Rain and Snow Fractions Equations 1-5 Lutz et. al. Biogeography 2010 Appendix S1)
def meltFactorRainSnow(monthlyTempMean, monthlyPrecip, month, year):

    try:

        #Define the Snow Melt Factor (Fm)
        outMeltFactor = outDir + "\\MealtFactor_" + str(year) + "_" + month + ".tif"

        #Define Numpy Array
        meltFactor = monthlyTempMean

        outArraySize = meltFactor.shape
        #Index values between 0 and 6
        testTrue = np.where(np.logical_and(meltFactor>0, meltFactor<6))
        #Multiply index locations by x * 0.167
        meltFactor[testTrue] *= 0.167

        #Set less than zero to 0 nad >= 6  to 1
        meltFactor[meltFactor <= 0] = 0
        meltFactor[meltFactor >= 6] = 1


        #Export array to raster
        array2raster(soilAWS,outMeltFactor,meltFactor)
        messageTime = timeFun()
        print ("Derived Melt Factor for Year/Month - " + str(year) + "_" + month + " - " + outMeltFactor + " - " + messageTime)

        ############################
        #Equation 4 - Rain Fraction - rainFraction = (Raster(outMeltFactor) * Raster(monthlyPrecip[0]))
        ############################
        outRainFrac = outDir + "\\Rain_" + str(year) + "_" + month + ".tif"

        #Multiply Arrays
        rainFraction = np.multiply(meltFactor, monthlyPrecip)
        rainFraction[rainFraction <0]= np.NaN
        del meltFactor

        #Export array to raster
        array2raster(soilAWS, outRainFrac, rainFraction)
        del rainFraction

        messageTime = timeFun()
        print ("Derived Rain Fraction for Year/Month - " + str(year) + "_" + month + " - " + outRainFrac + " - " + messageTime)

        ############################
        #Equation 5 - Snow Fractions (snowFraction = ((1- Raster(outMeltFactor)) * Raster(monthlyPrecip)))
        ############################

        outSnowFrac = outDir + "\\Snow_" + str(year) + "_" + month + ".tif"

        snowFrac1 = monthlyTempMean
        #Create Raster with value 1 every where
        snowFrac1[snowFrac1 > -999] = 1.0

        #Calculate (1-MeltFactor)
        outMeltFactor_NP= raster2array(outMeltFactor)
        snowFrac2 = np.subtract(snowFrac1, outMeltFactor_NP)
        del snowFrac1

        #Caclulate: (1- Raster(outMeltFactor)) * Raster(monthlyPrecip)
        snowFrac3 = np.multiply(snowFrac2, monthlyPrecip)
        del snowFrac2
        del monthlyPrecip

        #Export Monthly Snow
        array2raster(soilAWS, outSnowFrac, snowFrac3)
        del snowFrac3
        messageTime = timeFun()
        print ("Derived Snow Fraction for Year/Month - " + str(year) + "_" + month + " - " + outSnowFrac + " - " + messageTime)

        return outMeltFactor, outRainFrac, outSnowFrac, outArraySize

    except:
        messageTime = timeFun()
        print ("Error on MeltFactorRainSnow Function during year/month - " + str(year) + "_" + month)
        traceback.print_exc(file=sys.stdout)
        sys.exit()


#Function Derives the Snow Melt, Snow Pack and Monthly Water Input - Equations 6-8 Dilts et. al. Biogeography 2015 Appendix S1)
def snowMeltSnowPackWaterMonthly(meltFactor, monthlyPrecip, snowFraction, rainFraction, month, monthCount, monthList, year):

    try:

        #Snow Pack Calculation (Equation 7) - Assumption is being made the snow pack at the end of a water year in september in zero.
        #Monthly Climate Water Deficit Variables are by default set to calculate starting in October.

        #Logic to define the snowpack variable to be used in calculations
        if monthCount == 1 and year == startYear:
            previousMonth = "09"

            if year == startYear: #If first year of processing then use the default septSnowPack'

                snowPackPrevious = septSnowPack

        else:

            previousMonth = monthList[monthCount - 2]

            if month == "01": ##For January will want to the snow pack for Dec of the previous year

                snowPackPrevious = outDir + "\\SnowPack_" + str(year - 1) + "_" + previousMonth + ".tif"

            else:

                snowPackPrevious = outDir + "\\SnowPack_" + str(year) + "_" + previousMonth + ".tif"


        #Verify snowPackPrevious exists
        if not os.path.exists(snowPackPrevious):
            messageTime = timeFun()
            print ("Previous Months snowpack for year_month: " + str(year) + "_" + month + " raster - " + snowPackPrevious + " doesn't exist - " + messageTime)
            scriptMsg = ("Previous Months snowpack for month: " + str(year) + "_" + month + " raster - " + snowPackPrevious + " doesn't exist - " + messageTime)
            logFile = open(logFileName, "a")
            logFile.write(scriptMsg + "\n")
            logFile.close()
            sys.exit()

        ###################################
        #Snow Pack Calculation (Equation 7) derives for this Month. SnowPack = ((pow((1-Raster(meltFactor)),2)) *Raster(monthlyPrecip[0]) + (1-Raster(meltFactor)) * Raster(snowPackPrevious))
        ###################################
        outSnowPack = outDir + "\\SnowPack_" + str(year) + "_" + month + ".tif"

        rasterVal1 = raster2array(meltFactor)
        #Create Raster with value 1 every where
        rasterVal1[rasterVal1 > -999] = 1.0

        #Calculate (1-MeltFactor)
        outMeltFactor_NP= raster2array(meltFactor)
        snowPackEq1 = np.subtract(rasterVal1, outMeltFactor_NP)

        del rasterVal1
        del outMeltFactor_NP
        #Caclulate (1-MeltFactor) ^ 2
        snowPackEq1Pow = np.power(snowPackEq1, 2)

        #Calculate ((1- MeltFactor) ^ 2) * monthlyPrecip[0]
        #monthlyPrecip_NP= raster2array(monthlyPrecip[0]) #Create Numpy Array for monthly precip
        snowPackEq1Left = np.multiply(snowPackEq1Pow, monthlyPrecip)
        del snowPackEq1Pow
        #del monthlyPrecip_NP

        #Calculate (1-Raster(meltFactor)) * Raster(snowPackPrevious)) - Right Side of Equation
        snowPackPrevious_NP= raster2array(snowPackPrevious) #Create Numpy Array for Monthly SnowPack
        snowPackEq1Right = np.multiply(snowPackEq1, snowPackPrevious_NP)

        del snowPackEq1
        #Cacluate the middle addition of the Right and Left sides of equation  to yeild the snowPack output
        snowPack_NP = np.add(snowPackEq1Left, snowPackEq1Right)
        snowPack_NP[snowPack_NP < 0] = np.NaN
        array2raster(meltFactor,outSnowPack,snowPack_NP)
        messageTime = timeFun()
        print ("Derived Snow Pack for Year_Month - " + str(year) + "_" + month + " - " + outSnowPack + " - " + messageTime)
        del snowPack_NP
        del snowPackEq1Right

        ###################################
        #Snow Melt Calculation (Equation 6) - Must derive the Snow Pack (eq 7) Before Snow Melt can be calculated  SnowMelt = (meltFactor * (snowFraction + snowPackPrevious))
        ###################################
        #Snow Fraction Numpy Array
        snowFraction_NP = raster2array(snowFraction)

        #Cacluatle the snowMelt right side of equation
        snowMeltRight_NP = np.add(snowFraction_NP, snowPackPrevious_NP)

        del snowFraction_NP

        #Calculate snow Melt full equation

        rasterVal1 = raster2array(meltFactor)
        outSnowMelt = outDir + "\\SnowMelt_" + str(year) + "_" + month + ".tif"
        snowMelt_NP = np.multiply(rasterVal1, snowMeltRight_NP)
        array2raster(meltFactor,outSnowMelt,snowMelt_NP)
        messageTime = timeFun()
        print ("Derived Snow Melt for Year_Month - " + str(year) + "_" + month + " - " + outSnowMelt + " - " + messageTime)

        del snowMeltRight_NP
        del rasterVal1

        ######################################################
        #Monthly Water Input/Supply to the System (Equation 8) = RainFraction + SnowMelt
        ######################################################

        rainFraction_NP = raster2array(rainFraction)
        waterInput_NP = np.add(rainFraction_NP, snowMelt_NP)
        outWaterInput = outDir + "\\WaterInput_" + str(year) + "_" + month + ".tif"
        array2raster(meltFactor,outWaterInput,waterInput_NP)
        messageTime = timeFun()
        print ("Derived Water Input for Year_Month - " + str(year) + "_" + month + " - " + outWaterInput + " - " + messageTime)

        del snowMelt_NP
        del rainFraction_NP
        del waterInput_NP

        logFile = open(logFileName, "a")
        scriptMsg = ("Successfully ran snowMeltSnowPackWaterMonthly Function for Year_Month: " + str(year) + "_" + month + messageTime)
        logFile.write(scriptMsg + "\n")
        logFile.close()

        return outWaterInput

    except:
        messageTime = timeFun()
        print ("Error on MeltFact Function during Year_Month: " + str(year) + "_" + month)
        traceback.print_exc(file=sys.stdout)
        sys.exit()

#Function Derives the Potential Evapotranspiration Equation # 9 in Dilts et. al. Biogeography 2015 Appendix S1) without Heat Load
def potEvapoTrans(avgDayLengthRas, monthSolarDec, latitude, monthlyTempMean, month, year):

    try:

        if os.path.exists(avgDayLengthRas):
            dayLengthRaster = avgDayLengthRas
        else:
            dayLengthRaster = avgDayLengthRas[0]
        #Derive Saturation Vapour Pressure Equation 10
        outSatVapour = satVapourPressure(monthlyTempMean, month, year)

        #Calculate Potential Evapotranpiration using the input Saturation vapour pressure and DayLength Calculations Equation 9
        #Get days in the month
        numDays = daysInMonth(year, month)

        #Define Numpy Array
        monthlyTempMean_NP = raster2array(monthlyTempMean[0])

        NP_273pt2= raster2array(monthlyTempMean[0])
        #Create Raster with value 273.2 every where
        NP_273pt2[ NP_273pt2 > -999] = 273.2

        #Right Side of Right Side of PotEvapTranspiration
        PETRight1_NP = np.add(monthlyTempMean_NP, NP_273pt2)
        del NP_273pt2
        del monthlyTempMean_NP

        #Make Array for Sat Vap Pressure
        satVapour_NP = raster2array(outSatVapour)

        #Calculate: outSatVapour / (monthlyTempMean[0] + 273.2)))
        PETRight2_NP = np.divide(satVapour_NP, PETRight1_NP)
        del satVapour_NP
        del PETRight1_NP

        #Define Numpy Array
        dayLengthRaster_NP = raster2array(dayLengthRaster)

        #Calcualte: dayLengthRaster * ((outSatVapour)/ (monthlyTempMean + 273.2))
        outPETRightNo_HeatLoad_NP = np.multiply(dayLengthRaster_NP, PETRight2_NP)
        outPETRightNo_HeatLoad_NP[outPETRightNo_HeatLoad_NP < -10000] = np.NaN
        del dayLengthRaster_NP
        del PETRight2_NP

        #Caculate Left side of PET equation
        left = 29.8 * numDays
        NP_29pt8xDays= raster2array(monthlyTempMean[0])
        #Create Raster with value 29.8 x Days
        NP_29pt8xDays[NP_29pt8xDays > -999] = left

        #Caculate PET
        potEvapTran_NP = np.multiply(NP_29pt8xDays, outPETRightNo_HeatLoad_NP)
        potEvapTran_NP[potEvapTran_NP < -10000] = np.NaN
        del NP_29pt8xDays
        del outPETRightNo_HeatLoad_NP

        ###########

        monthPETNoZero = workspace + "\\PET_NatRes_NoZero_" + str(month) + ".tif"
        array2raster(monthlyTempMean[0], monthPETNoZero, potEvapTran_NP)
        messageTime = timeFun()
        print ("PET values less than zero set to zero for month - " + month + " - " +  monthPETNoZero + " - " + messageTime)

        #Logic was added 20160701  - Con(Raster(monthlyTempMean[0]) < 0, 0, Raster(monthPETNoZero))
        #Set PET to zero if the TMEAN is less than 0, no PET.  It would be easy to add a parameterized minimum temperature other than 0 above which PET occurs.

        petAbove_NP = raster2array(monthlyTempMean[0])

        #Set cells with monthly Mean Temp <= 0 to 0
        petAbove_NP[petAbove_NP <= 0] = 0

        #If Greater Than zero monthly mean temps set value to 1
        petAbove_NP[petAbove_NP > 0] = 1

        #Multiply - where mean monthly temp is greater than 1 = 1 * monthlyPETNoZero
        petFinal_NP = np.multiply(petAbove_NP, potEvapTran_NP)
        del petAbove_NP
        del potEvapTran_NP
        petFinal_NP[petFinal_NP < 0] = np.NaN

        #Export Final PET Array to Raster
        monthPotEvapTran = outDir + "\\PET_" + str(year) + "_" + str(month) + ".tif"
        array2raster(monthlyTempMean[0], monthPotEvapTran, petFinal_NP)
        del petFinal_NP
        messageTime = timeFun()
        print ("PET set to zero when Mean temp for month is below zero for year month - " + str(year) + " - " + str(month) + " - " +  monthPotEvapTran + " - " + messageTime)
        #####

        return monthPotEvapTran

    except:
        messageTime = timeFun()
        print ("Error on pet Function during month - " + month)
        traceback.print_exc(file=sys.stdout)
        sys.exit()

#Function derives the PET Penman with the heat load correction (Penman PET * Heat Load Index)
def petHeatLoad_wPenman(out_Penman_ET, heatLoadIndexRas):
    try:

        penman_ET_np = raster2array(out_Penman_ET)
        outheatLoad_np = raster2array(heatLoadIndexRas)

        petHeatLoad_wPenman_np = np.multiply(penman_ET_np, outheatLoad_np)

        del penman_ET_np
        del outheatLoad_np

        #Export Penman ET with Heatload Array to Raster
        petHeatLoad_wPenman = outDir + "\\PET_Penman_wHL_" + str(year) + "_" + str(month) + ".tif"
        array2raster(soilAWS, petHeatLoad_wPenman, petHeatLoad_wPenman_np)

        messageTime = timeFun()
        print("Derived PET Penman with Heat Load for year month - " + str(year) + " - " + str(month) + " - " + petHeatLoad_wPenman + " - " + messageTime)

        #Should we set to 0 where SWE is greater than zero? - Yes


        return petHeatLoad_wPenman_np

    except:
        messageTime = timeFun()
        print("Error on petHeatLoad_wPenman Function during month - " + month)
        traceback.print_exc(file=sys.stdout)
        sys.exit()


#Function Derives the Potential Evapotranspiration Equation with inclusion of the Heat Load Index Equations(14 and 15) equation # 16 in Dilts et. al. Biogeography 2015 Appendix S1)
def petHeatLoad(avgDayLengthRas, monthSolarDec, monthlyTempMean, rasterHeatLoad, month, year):

    try:

        if os.path.exists(avgDayLengthRas):
            dayLengthRaster = avgDayLengthRas
        else:
            dayLengthRaster = avgDayLengthRas[0]

        #Derive Saturation Vapour Pressure Equation 10
        outSatVapour = satVapourPressure(monthlyTempMean, month, year)

        #Calculate Potential Evapotranspiration using the input Saturation vapour pressure and DayLength Calculations Equation 9
        #Get days in the month
        numDays = daysInMonth(year, month)

        ##################################
        #Derive Right side of PET Equation = (rasterHeatLoad * dayLengthRaster * (outSatVapour / (monthlyTempMean[0] + 273.2)))
        ##################################

        #Right Side Equation Left Side First Multiplication (rasterHeatLoad * dayLengthRaster)
        #Define Numpy Array
        rasterHeatLoad_NP = raster2array(rasterHeatLoad)

        #Define Numpy Array
        dayLengthRaster_NP = raster2array(dayLengthRaster)

        #Calculate (rasterHeatLoad * dayLengthRaster)
        PETRightLeft_NP = np.multiply(rasterHeatLoad_NP, dayLengthRaster_NP)
        del rasterHeatLoad_NP
        del dayLengthRaster_NP

        #Calculate Right Side Equation Right Side: outSatVapour / (monthlyTempMean[0] + 273.2)))
        #Define Numpy Array
        monthlyTempMean_NP = raster2array(monthlyTempMean[0])

        NP_273pt2= raster2array(monthlyTempMean[0])
        #Create Raster with value 273.2 every where
        NP_273pt2[ NP_273pt2 > -999] = 273.2

        #Right Side of Right Side of PotEvapTranspiration
        PETRight1_NP = np.add(monthlyTempMean_NP, NP_273pt2)
        del NP_273pt2
        del monthlyTempMean_NP

        #Make Array for Sat Vap Pressure
        satVapour_NP = raster2array(outSatVapour)

        #Calculate: outSatVapour / (monthlyTempMean[0] + 273.2)))
        PETRight2_NP = np.divide(satVapour_NP, PETRight1_NP)
        del satVapour_NP
        del PETRight1_NP

        #Final PET Right Side Cacluation:
        outPETRight_NP = np.multiply(PETRightLeft_NP, PETRight2_NP)
        del PETRightLeft_NP
        del PETRight2_NP

        #Set no Data to NaN
        outPETRight_NP[outPETRight_NP < -10000] = np.NaN

        #################################
        # Derived Left Side of PET w Heat Load
        #################################
        left = 29.8 * numDays

        NP_29pt8xDays= raster2array(monthlyTempMean[0])
        #Create Raster with value 29.8 x Days
        NP_29pt8xDays[NP_29pt8xDays > -999] = left

        potEvapTran_NP = np.multiply(NP_29pt8xDays, outPETRight_NP)
        del outPETRight_NP
        del NP_29pt8xDays
        potEvapTran_NP[potEvapTran_NP < -10000] = np.NaN

        #If PET values less than zero, set PET value to zero: Con(Raster(monthPotEvapTranNat) < 0, 0, Raster(monthPotEvapTranNat))
        potEvapTran_NP[potEvapTran_NP < 0] = 0

        #Logic was added 20160701  - Con(Raster(monthlyTempMean[0]) < 0, 0, Raster(monthPETNoZero))
        #Set PET to zero if the TMEAN is less than 0, no PET.  It would be easy to add a parameterized minimum temperature other than 0 above which PET occurs. (e.g. Jennings et. al. 2018).

        petAbove_NP = raster2array(monthlyTempMean[0])

        #Set cells with monthly Mean Temp <= 0 to 0
        petAbove_NP[petAbove_NP <= 0] = 0

        #If Greater Than zero monthly mean temps set value to 1
        petAbove_NP[petAbove_NP > 0] = 1

        #Multiply - where mean monthly temp is greater than 1 = 1 * monthlyPETNoZero
        petFinal_NP = np.multiply(petAbove_NP, potEvapTran_NP)
        del petAbove_NP
        del potEvapTran_NP
        petFinal_NP[petFinal_NP < 0] = np.NaN

        #Export Final PET Array to Raster
        monthPotEvapTran = outDir + "\\PET_" + str(year) + "_" + str(month) + ".tif"
        array2raster(monthlyTempMean[0], monthPotEvapTran, petFinal_NP)
        del petFinal_NP
        messageTime = timeFun()
        print ("PET set to zero when Mean temp for month is below zero for year/month - " + str(year) + "_" + str(month) + " - " +  monthPotEvapTran + " - " + messageTime)

        return monthPotEvapTran

    except:
            messageTime = timeFun()
            print ("Error on petHEatLoad Function during month - " + month)
            traceback.print_exc(file=sys.stdout)
            sys.exit()


#Define the mid day value in a month
def dayYearMidMonth(month):
    try:
        if month == "01":
            day = 15
        elif month == "02":
            day = 46
        elif month == "03":
            day = 74
        elif month == "04":
            day = 105
        elif month == "05":
            day = 135
        elif month == "06":
            day = 166
        elif month == "07":
            day = 196
        elif month == "08":
            day = 227
        elif month == "09":
            day = 258
        elif month == "10":
            day = 288
        elif month == "11":
            day = 319
        else:
            day = 349
        #print day
        return day

    except:
        messageTime = timeFun()
        print ("Error JulianDayMidMonth - " + month)
        traceback.print_exc(file=sys.stdout)
        sys.exit()

#Monthly Solar Declination 15th Day of the month (needed for equation 11 - Day Length) Out put is Degrees - Not sure if Radian's or Degree's is desired? - KRS 20150824
def solarDeclination(month):
    try:        #Get Julian Day
        outDayMid = dayYearMidMonth(month)
        dayMid = int(outDayMid)

        #Degrees Declination
        var1 = (360.0 / 365.0)
        var2 = dayMid - 81
        var3 = var1 * var2
        var4 = math.sin(math.radians(var3))
        var5 = math.sin(math.radians(23.45))
        equation = var4 * var5
        #equation = (math.sin(((360.0/365.0)*(dayMid - 81))) * (math.sin(23.45)))  #Equation in One Calculation
        outSolarDec = math.degrees(math.asin(equation)) #Output Solar Declination Value

        print ("Solar Delination Angle for month - " + month +  " is: " + str(outSolarDec))
        return outSolarDec

    except:
        messageTime = timeFun()
        print ("Error solarDeclination Function - " + month)
        traceback.print_exc(file=sys.stdout)
        sys.exit()


#Function derives the average day length raster for the 15th day of the month - equation 11 Dilts et. al. Biogeography 2015 Appendix S1)
#Equation for DayLength Calulcation is incorrect as of 20170211 and has not been migrated from ArcPY
def dayLengthRas(latitude, monthSolarDec, month):
    try:

        angVelocity = 0.2618    #Default angular velocity of the Earth's rotation in (radian hr-1)

        'Create Latitude Radians Raster'
        latRadians = workspace + "\\Latitude_Radians.tif"
        if os.path.exists(latRadians):
            print ("Latitude Radians Raster Already Exists - " + latRadians)
        else:
            lR = Raster(latitude) * (180 / math.pi)
            lR.save(latRadians)
            messageTime = timeFun()
            print ("Derived Latitude Radians Rasters - " + latRadians + " - " + messageTime)

        negMonthSolarDec = -1 * monthSolarDec   #Creating negative solar declination value
        outCalc1 = workspace + "\\DayLength_Calc1_" + month + ".tif"
        calc1 = (negMonthSolarDec * Tan(Raster(latRadians)))
        calc1.save(outCalc1)
        messageTime = timeFun()
        print ("Completed DayLength Cal1 - " + month + " - " + outCalc1 + " - " + messageTime)

        dayLength = outDir + "\\DayLengthHours_" + month + ".tif"
        calc2 = ((2 * ACos(Raster(outCalc1))) / angVelocity)
        calc2.save(dayLength)
        messageTime = timeFun()
        print ("Completed Day Length Caluclation for - " + month + " - " + dayLength + " - " + messageTime)

        return dayLength

    except:
        messageTime = timeFun()
        print ("Error dayLenghtRas - " + month)
        traceback.print_exc(file=sys.stdout)
        sys.exit()


#Function calculates the Saturaration Vapour Pressure at mean temperature Ta - equation 10 Dilts et. al. Biogeography 2015 Appendix S1) - Hamon Equation when Mean Temp is available.
def satVapourPressure(monthlyTempMean, month, year):
    try:

        #Saturation Vapor Pressure Equation 10 Right Side equation
        outSVPRight = workspace + "\\SVP_Right_" + month + ".tif"

        #Define Numpy Array
        monthlyTempMean_NP = raster2array(monthlyTempMean[0])

        NP_17pt3= raster2array(monthlyTempMean[0])
        #Create Raster with value 17.3 every where
        NP_17pt3[NP_17pt3 > -999] = 17.3

        #Left Side of Right Side Sat Vap Pressure Equation
        satVapour1_NP = np.multiply(NP_17pt3, monthlyTempMean_NP)
        satVapour1_NP[satVapour1_NP<-999] = np.nan
        del NP_17pt3

        NP_237pt3= raster2array(monthlyTempMean[0])
        #Create Raster with value 237.3 every where
        NP_237pt3[NP_237pt3 > -999] = 237.3

        #Right Side of Right Side Sat Vap Pressure Equation
        satVapour2_NP = np.add(NP_237pt3, monthlyTempMean_NP)
        satVapour2_NP[satVapour2_NP<-999] = np.nan

        del NP_237pt3
        del monthlyTempMean_NP

        #Calculate Right Side of Sat Vap Pressure Equation
        satVapourRight_NP = np.divide(satVapour1_NP, satVapour2_NP)
        del satVapour1_NP
        del satVapour2_NP

        #SVP Equation Left and Right side
        #Calculate the exponential of the Right side of Sat Vap Pressure Equation
        satVapour3_NP = np.exp(satVapourRight_NP)
        del satVapourRight_NP

        NP_pt611= raster2array(monthlyTempMean[0])
        #Create Raster with value 0.611 every where
        NP_pt611[NP_pt611 > -999] = 0.611

        #Calculate 0.611 * (Exp(outSVPRight_NP))
        final_satVapour_NP = np.multiply(NP_pt611, satVapour3_NP)
        del NP_pt611
        del satVapour3_NP

        #Set no Data to NaN
        final_satVapour_NP[final_satVapour_NP < -10] = np.NaN

        outSatVapPressure = outDir + "\\Saturation_Vap_Pressure_" + str(year) + "_" + month + ".tif"
        #Export Array to a Raster
        array2raster(monthlyTempMean[0],outSatVapPressure,final_satVapour_NP)
        messageTime = timeFun()
        print ("Derived Saturation Vapor Pressure for year/month - " + str(year) + "_" + month + " - " + outSatVapPressure + " - " + messageTime)
        del final_satVapour_NP

        return outSatVapPressure
    except:
        messageTime = timeFun()
        print ("Error satVapourPressure - " + month)
        traceback.print_exc(file=sys.stdout)
        sys.exit()

#Returns the number of days in a month
def daysInMonth(year, month):
    import calendar
    try:

        intMonth = int(month)
        intYear = int(year)
        out = calendar.monthrange(year, intMonth)
        numDays = out[1]
        messageTime = timeFun()
        print ("Number of Days in Month - " + str(month) + " is: " + str(numDays) + " - " + messageTime)

        return numDays

    except:
        messageTime = timeFun()
        print ("Error satVapourPressure - " + month)
        traceback.print_exc(file=sys.stdout)
        sys.exit()

#Function Calculate the Initial Soil Water Balance (SWS) (eq. 12 Dilts. et. al.) using Soil Water Holding Capacity (i.e. Soil AWS), Water Input (e.q. 8), Potential Evapotranspiration (e.q. 16 or 9), and Prevous Months Soil
#For locations with PET > Water Input, the fraction removed from Soil Water Storage (eg 13) must be substracted for the final monthly SBS.
def soilWaterBalance(soilAWS, monthCount, month, monthList, year):

    try:

        #Logic is setup for calculation of October Monthly variables first and for first year
        if monthCount == 1 and year == startYear:
            previousMonth = "09"
            percMult = (percAWSInitial / 100.0)

            percMult_NP = raster2array(soilAWS)
            percMult_NP[percMult_NP > -10000] = percMult

            soilAWS_NP = raster2array(soilAWS)

            initialAWS_NP = np.multiply(percMult_NP, soilAWS_NP)
            initialAWS_NP[initialAWS_NP > 500] = np.NaN
            del percMult_NP
            del soilAWS_NP

            initialAWSOut = outDir + "\\InitialMonth_SWB_Percent_" + str(percAWSInitial) + ".tif"
            array2raster(soilAWS, initialAWSOut, initialAWS_NP)
            del initialAWS_NP

            messageTime = timeFun()
            print ("Derived Initial Percent AWS-Montlhy Water Balance to be used in month October Soil Water Balance calc - " + initialAWSOut + " - " + messageTime)

            #For Month of October, caculating Soil Moisture using Water Input Sept, PET Sept, and for Soil Moisture previous month AWS at defined variable percAWSInitial
            waterInputRas = outDir + "\\WaterInput_" + str(year) + "_"+ month + ".tif"
            petRasSyntax = outDir + "\\PET_*" + str(year) + "_" + month + ".tif"
            petRasList = glob.glob(petRasSyntax)
            petRas = (petRasList[0])
            swbPrevious = initialAWSOut
            swbOut = outDir + "\\SWB_" + str(year) + "_" + month + ".tif"

            ###########################################
            #Calculate Amount Removed From Soil Water Storage - Equation 13 Dilts. et. al. 2015
            ###########################################

            out_SWSR = soilWaterStorageRemoved(month, monthCount, monthList, year)

            #Run Funcion that calculates the Current Months Soil Water Balance value (Equation 12) when Water Input >= PET,
            #else Water Injput < PET remove water from SWB equation 13
            outMonthSWB = monthSWB(waterInputRas, petRas, swbPrevious, swbOut, month, year)

        elif month in ["10","11","12"]:  #All 10,11,12 months not in the first year

            previousMonth = monthList[monthCount - 2]
            waterInputRas = outDir + "\\WaterInput_" + str(year) + "_" + month + ".tif"
            petRasSyntax = outDir + "\\PET_*" + str(year) + "_" + month + ".tif"
            petRasList = glob.glob(petRasSyntax)
            petRas = (petRasList[0])
            swbPrevious = outDir + "\\SWB_" + str(year) + "_" + previousMonth + ".tif"
            swbOut = outDir + "\\SWB_" + str(year) + "_" + month + ".tif"

            ###########################################
            #Calculate Amount Removed From Soil Water Storage - Equation 13 Dilts. et. al. 2015
            ###########################################

            out_SWSR = soilWaterStorageRemoved(month, monthCount, monthList, year)

            #Run Funcion that calculates the Current Months Soil Water Balance value (Equation 12) when Water Input >= PET,
            #else Water Injput < PET remove water from SWB equation 13

            outMonthSWB = monthSWB(waterInputRas,petRas, swbPrevious, swbOut, month, year)

        ## Add logic to add the change of year value after Oct,Nov,Dec months'  - - KRS 20171228
        elif month not in ["10","11","12"]:
            year = year + 1

            previousMonth = monthList[monthCount - 2]
            waterInputRas = outDir + "\\WaterInput_" + str(year) + "_" + month + ".tif"
            petRasSyntax = outDir + "\\PET_*" + str(year) + "_" + month + ".tif"
            petRasList = glob.glob(petRasSyntax)
            petRas = (petRasList[0])

            if month == "01":
                swbPrevious = outDir + "\\SWB_" + str(year - 1) + "_" + previousMonth + ".tif"
            else:
                swbPrevious = outDir + "\\SWB_" + str(year) + "_" + previousMonth + ".tif"

            swbOut = outDir + "\\SWB_" + str(year) + "_" + month + ".tif"

            year = year - 1  #Set year back to the loop year
            ###########################################
            #Calculate Amount Removed From Soil Water Storage - Equation 13 Dilts. et. al. 2015
            ###########################################

            out_SWSR = soilWaterStorageRemoved(month, monthCount, monthList, year)

            #Run Funcion that calculates the Current Months Soil Water Balance value (Equation 12) when Water Input >= PET,
            #else Water Injput < PET remove water from SWB equation 13

            outMonthSWB = monthSWB(waterInputRas,petRas, swbPrevious, swbOut, month, year)


        return outMonthSWB

    except:
        messageTime = timeFun()
        print ("Error soilWaterBalance - ")
        traceback.print_exc(file=sys.stdout)
        sys.exit()

#Function calculates the Folded Aspect - Equation 14 Dilts Et. al. 2015 = aspFold = Abs(180 - (Abs((aspectRas) - 225))))
#Note monthlyTempMean list is being used for spatial reference of output Folder Aspect
def aspectFolded(aspectRas, monthlyTempMean):
    try:

        #Define Numpy Array
        aspectFold_NP = raster2array(aspectRas)

        minus_225_NP = raster2array(aspectRas)
        #Create Raster with value 225 every where
        minus_225_NP[minus_225_NP > -999] = 225.0

        #Subtract 225 from Aspect Array
        aspectFold_NP2 = np.subtract(aspectFold_NP, minus_225_NP)
        del minus_225_NP
        del aspectFold_NP

        #Caluclate Absolute Value
        aspectFold_Abs_NP2 = np.absolute(aspectFold_NP2)
        del aspectFold_NP2

        NP_180 = raster2array(aspectRas)
        #Create Raster with value 180 every where
        NP_180[NP_180 > -999] = 180.0

        #Caluclate: Abs(180 - (Abs((Raster(aspectRas) - 225))
        aspectFold_Left1 = np.subtract(NP_180, aspectFold_Abs_NP2)
        del NP_180
        del aspectFold_Abs_NP2

        #Calculate left side Absolute
        aspectFold_Last = np.absolute(aspectFold_Left1)
        del aspectFold_Left1

        #Set Less than zero to Null (i.e. np.NaN)
        aspectFold_Last[aspectFold_Last < 0] = np.NaN

        #Export Aspect Folder Array to Raster
        outAspFold = outDir + "\\Folded_Aspect.tif"
        array2raster(aspectRas,outAspFold,aspectFold_Last)
        del aspectFold_Last
        messageTime = timeFun()
        print ("Folded Aspect Derived - " + outAspFold + " - " + messageTime)

        return outAspFold

    except:
        messageTime = timeFun()
        print ("Error aspedFolded")
        traceback.print_exc(file=sys.stdout)
        sys.exit()

#Function calculates the Heat Load Index - Equation 15 Dilts Et. al. 2015
def heatLoadIndexFun (aspFoldedRas, slopeRas, latitude, outArraySize):
    try:

        import math
        outheatLoad = outDir + "\\HeatLoadIndex.tif"
        slopeRasRadOut = outDir + "\\Slope_Radians.tif"

        if str(os.path.exists(slopeRasRadOut)) == "False":
            #Convert Slope, latitude and Folded Aspect to Radians (from Degree's) - ArcGIS Sin and Cos functions expect Radian input values.
            NP_180 = raster2array(slopeRas)
            #Create Raster with value 180 every where
            NP_180[NP_180 > -999] = 180.0

            NP_Pie = raster2array(slopeRas)
            #Create Raster with value 180 every where
            NP_Pie[NP_Pie > -999] = math.pi

            #Calculate (180/math.pi)
            slopeRasRadRight = np.divide(NP_180, NP_Pie)

            del NP_180
            del NP_Pie

            #Define Numpy Array - slope
            slope_NP = raster2array(slopeRas)

            #Calculate Raster(slopeRas) / (180 / (math.pi))
            slopeRasRad_NP = np.divide(slope_NP, slopeRasRadRight)

            del slope_NP
            del slopeRasRadRight

            #Set Less than zero to Null (i.e. np.NaN)
            slopeRasRad_NP[slopeRasRad_NP < 0] = np.NaN

            #Export Slope in Radians Array to Raster
            array2raster(slopeRas,slopeRasRadOut,slopeRasRad_NP)
            messageTime = timeFun()
            print ("Slope Raster in Radian Derived - " + slopeRasRadOut + " - " + messageTime)
            del slopeRasRad_NP

        #Calculate Latitude in Radians: Raster(latitude) / (180/ (math.pi))
        latRadOut = outDir + "\\Latitude_Radians.tif"
        if str(os.path.exists(latRadOut)) == "False":

            NP_180 = raster2array(latitude)
            #Create Raster with value 180 every where
            NP_180[NP_180 > -999] = 180.0

            NP_Pie = raster2array(latitude)
            #Create Raster with value 180 every where
            NP_Pie[NP_Pie > -999] = math.pi

            #Calculate (180/math.pi)
            latRasRadRight = np.divide(NP_180, NP_Pie)

            del NP_180
            del NP_Pie

            #Define Numpy Array - Latitude
            lat_NP = raster2array(latitude)

            #Calculate Raster(latitude) / (180 / (math.pi))
            latRasRad_NP = np.divide(lat_NP, latRasRadRight)

            del lat_NP
            del latRasRadRight

            #Set Less than zero to Null (i.e. np.NaN)
            latRasRad_NP[latRasRad_NP < 0] = np.NaN

            #Export Latitude in Radians Array to Raster
            array2raster(latitude,latRadOut,latRasRad_NP)
            messageTime = timeFun()
            print ("Latitude Raster in Radian Derived - " + latRadOut + " - " + messageTime)
            del latRasRad_NP

        #Cacluate Folded Aspect in Radians = Raster((aspFoldedRas)) / (180/ (math.pi))
        aspFoldRadOut = outDir + "\\FoldedAspect_Rad.tif"
        if str(os.path.exists(aspFoldRadOut)) == "False":

            NP_180 = raster2array(aspFoldedRas)
            #Create Raster with value 180 every where
            NP_180[NP_180 > -999] = 180.0

            NP_Pie = raster2array(aspFoldedRas)
            #Create Raster with value 180 every where
            NP_Pie[NP_Pie > -999] = math.pi

            #Calculate (180/math.pi)
            foldAspRadRight = np.divide(NP_180, NP_Pie)

            del NP_180
            del NP_Pie

            #Define Numpy Array - fold aspect
            foldedAspect_NP = raster2array(aspFoldedRas)

            #Calculate Raster(latitude) / (180 / (math.pi))
            foldedAspectRasRad_NP = np.divide(foldedAspect_NP, foldAspRadRight)

            del foldedAspect_NP
            del foldAspRadRight

            #Set Less than zero to Null (i.e. np.NaN)
            foldedAspectRasRad_NP[foldedAspectRasRad_NP > 3.2] = np.NaN

            #Export Fold Aspect in Radians Array to Raster
            array2raster(aspFoldedRas,aspFoldRadOut,foldedAspectRasRad_NP)
            messageTime = timeFun()
            print ("Folder Aspect Raster in Radian Derived - " + aspFoldRadOut + " - " + messageTime)
            del foldedAspectRasRad_NP

        ###########################
        #Calculate Head Load Index - calHL = ((0.339 + (0.808 * (Cos(latRadOut) * Cos(slopeRasRadOut))) - (0.196 * (Sin(latRadOut) * Sin(slopeRasRadOut))) - (0.482 * (Cos(aspFoldRadOut) * Sin(slopeRasRadOut)))
        ###########################

        #########
        #heatLoad Calculation Left Side Equation - (0.339 + (0.808 * (Cos(Raster(latRadOut)) * Cos(Raster(slopeRasRadOut)))))
        #########

        #Slope Radians NP Array
        slopeRasRad_NP = raster2array(slopeRasRadOut)

        #Cosine of Slope in Radians
        slopeRasRad_COS = np.cos(slopeRasRad_NP)
        del slopeRasRad_NP

        #Latitude Radians NP Array
        latRasRad_NP = raster2array(latRadOut)

        #Cosine of latitude in Radians
        latRasRad_COS = np.cos(latRasRad_NP)
        del latRasRad_NP

        #Cos Latitude Radians * Cos Slope Radians
        cosLatSlopeRad = np.multiply(latRasRad_COS,slopeRasRad_COS)
        del latRasRad_COS
        del slopeRasRad_COS

        #Calculate (0.808 * (Cos Latitude Radians * Cos Slope Radians))
        #Create Raster with value 0.808 every where
        NP_pt808 = raster2array(slopeRasRadOut)
        NP_pt808[NP_pt808 > -999] = 0.808
        #NP_pt808.resize((outArraySize), refcheck = False)


        HL_LeftMid = np.multiply(NP_pt808,cosLatSlopeRad)
        del cosLatSlopeRad
        del NP_pt808

        #Calculate Left hand side of HL equation =  0.339 + ((0.808 * (Cos(Raster(latRadOut)) * Cos(Raster(slopeRasRadOut)))))
        #Create Raster with value 0.339 every where
        NP_pt339 = raster2array(slopeRasRadOut)
        NP_pt339[NP_pt339 > -999] = 0.339
        #NP_pt339.resize((outArraySize), refcheck = False)

        #Left hand side of HL Equation
        HL_Left = np.add(NP_pt339, HL_LeftMid)
        del NP_pt339
        del HL_LeftMid
        print ("Left side of Heat Load Equation has been calculated")

        #########
        #heatLoad Calculation Middle of Equation = (0.196 * (Sin(Raster(latRadOut)) * Sin(Raster(slopeRasRadOut))))
        #########

        #Slope Radians NP Array
        slopeRasRad_NP = raster2array(slopeRasRadOut)

        #Sin of Slope in Radians
        slopeRasRad_SIN = np.sin(slopeRasRad_NP)
        del slopeRasRad_NP

        #Latitude Radians NP Array
        latRasRad_NP = raster2array(latRadOut)

        #Sin of latitude in Radians
        latRasRad_SIN = np.sin(latRasRad_NP)
        del latRasRad_NP

        #Sin Latitude Radians * Sin Slope Radians
        sinLatSlopeRad = np.multiply(latRasRad_SIN,slopeRasRad_SIN)
        del latRasRad_SIN
        del slopeRasRad_SIN

        #Calculate (0.196 * (SIN Latitude Radians * SIN Slope Radians))
        #Create Raster with value 0.808 every where
        NP_pt196 = raster2array(slopeRasRadOut)
        NP_pt196[NP_pt196 > -999] = 0.196

        HL_Middle = np.multiply(NP_pt196,sinLatSlopeRad)
        del sinLatSlopeRad
        del NP_pt196
        print ("Middle part of Heat Load Equation has been calculated")

        #########
        #heatLoad Calculation Right side of Equation = (0.482 * (Cos(Raster(str(aspFoldRadOut))) * Sin(Raster(slopeRasRadOut)))))
        #########

        #Slope Radians NP Array
        slopeRasRad_NP = raster2array(slopeRasRadOut)

        #Sin of Slope in Radians
        slopeRasRad_SIN = np.sin(slopeRasRad_NP)
        del slopeRasRad_NP


        #Folded Aspect Radians NP Array
        aspFoldRad_NP = raster2array(aspFoldRadOut)

        #COS Aspect Folded in Radians
        aspFoldRad_COS = np.cos(aspFoldRad_NP)
        del aspFoldRad_NP

        #Sin Latitude Radians * Sin Slope Radians
        sinLatSlopeRad = np.multiply(aspFoldRad_COS,slopeRasRad_SIN)
        del aspFoldRad_COS
        del slopeRasRad_SIN

        #Calculate (0.482 * (Cos Folded Aspect * Sin Slope Radians))
        #Create Raster with value 0.482 every where
        NP_pt482 = raster2array(slopeRasRadOut)
        NP_pt482[NP_pt482 > -999] = 0.482

        HL_Right = np.multiply(NP_pt482,sinLatSlopeRad)
        del sinLatSlopeRad
        del NP_pt482
        print ("Right side of Heat Load Equation has been calculated")

        #########
        #heatLoad Calculation Left, Middle, and Right side of Equation
        #########

        HLSub1 = np.subtract(HL_Left, HL_Middle)
        del HL_Left
        del HL_Middle

        finalHL = np.subtract(HLSub1, HL_Right)
        finalHL[finalHL < -10] = np.NaN
        del HLSub1
        del HL_Right

        #Export Heat Load Index to a Raster
        array2raster(aspFoldedRas,outheatLoad,finalHL)
        messageTime = timeFun()
        print ("Folder Aspect Raster in Radian Derived - " + aspFoldRadOut + " - " + messageTime)
        del finalHL

        #Heat load calculation with ArcPY
        #calHL = ((0.339 + (0.808 * (Cos(Raster(latRadOut)) * Cos(Raster(slopeRasRadOut))))) - (0.196 * (Sin(Raster(latRadOut)) * Sin(Raster(slopeRasRadOut)))) - (0.482 * (Cos(Raster(str(aspFoldRadOut))) * Sin(Raster(slopeRasRadOut)))))

        messageTime = timeFun()
        print ("Heat Load Index Created - " + outheatLoad + " - " + messageTime)
        scriptMsg = ("Heat Load Index Created - " + outheatLoad + " - " + messageTime)

        return outheatLoad
    except:
        messageTime = timeFun()
        print ("Error heatLoadIndexFun - " + messageTime)
        traceback.print_exc(file=sys.stdout)
        sys.exit()

#When Water Input >= PET calculates equation 12 Dilts et. al. 2015 - Water Input (eq 8), PET (eq 16 or 9), Soil Water Balance Previous Month(eq 12)
#else Water Input < PET remove swater from SWB equation 13
def monthSWB(waterInputRas,petRas, swbPrevious, swbOut, month, year):

    try:

             ##Define the year + 1 for 01-09 months
            if month not in ["10","11","12"]:
                year = year + 1

            #Initial Right hand side of equation 12 for September Initial Water Balance: ((waterInputRas) - petRas) + swbPrevious)

            waterInput_NP = raster2array(waterInputRas)
            petRas_NP = raster2array(petRas)

            swbRight1_NP = np.subtract(waterInput_NP, petRas_NP)
            del waterInput_NP
            del petRas_NP

            swbPrevious_NP = raster2array(swbPrevious)

            swbRight_NP = np.add(swbRight1_NP, swbPrevious_NP)
            del swbRight1_NP
            del swbPrevious_NP

                #Turning off temporary workspace rasters post de-bugging
##            swbRightOut = workspace  + "\\SWB_Right_" + month + ".tif"
##            array2raster(waterInputRas, swbRightOut, swbRight_NP)
##            messageTime = timeFun()
##            print ("Initial Right hand side Water Balance equation 12 for month - " + month + " - " +  swbRightOut + " - " + messageTime)

            #Select Minimum of Maximum AWS (Soil Max) or Right Hand Current Monthly Water Balance - applying equation 12 here
            soilAWS_NP = raster2array(soilAWS) #Note Soil AWS doesn't have same No Data Extent as other climatic inputs could create Edge colculation issues

            #Perform the Con statement: Con(soilAWS) >= swbRightOut = swbRightOut, else (i.e. soilAWS < swbRightOut) = soilAWS
            #Arcpy syntax: calcSWB = Con(Raster(soilAWS) >= Raster(swbRightOut), Raster(swbRightOut), Raster(soilAWS))
            calcSWB_NP = np.where(soilAWS_NP >= swbRight_NP, swbRight_NP, soilAWS_NP)
            del soilAWS_NP
            del swbRight_NP
            calcSWB_NP[calcSWB_NP < -500] = np.NaN


            outSWB_Wm_gte_PET = workspace + "\\SWB_Wm_gte_PET_" + str(year) + "_" + month + ".tif"
            array2raster(soilAWS, outSWB_Wm_gte_PET, calcSWB_NP)
            messageTime = timeFun()
            print ("Output Soil Water Balance equation 12 Wm >= PET - " + str(year) + "_" + month + " - " +  outSWB_Wm_gte_PET + " - " + messageTime)
            del calcSWB_NP


            outRemovedSWS = outDir + "\\SWS_To_Remove_PET_gt_Wm_" + str(year) + "_" + str(month) + ".tif"
            #Define Raster with amount to be removed when PET > Water Input

            #Create the Soil Water Balance Raster with water removed when PET > Water Input, this will be input to the month SWB where PET > Wm
            #Calculate: (swbPrevious) - (outRemovedSWS)
            swbPrevious_NP = raster2array(swbPrevious)
            outRemovedSWS_NP = raster2array(outRemovedSWS)

            SWB_EvapRemoved_NP = np.subtract(swbPrevious_NP, outRemovedSWS_NP)
            del swbPrevious_NP
            del outRemovedSWS_NP


            SWB_EvapRemoved = workspace + "\\SWB_wSoilWater_Removed_Wm_gte_PET_" + str(year) + "_" + str(month) + ".tif"
            array2raster(swbPrevious, SWB_EvapRemoved, SWB_EvapRemoved_NP)
            messageTime = timeFun()
            print ("SWB with amount removed when PET > Water Input - " + month + " - " +  SWB_EvapRemoved + " - " + messageTime)
            del SWB_EvapRemoved_NP


            ## Logic for Final Soil Water Balance Equation calculation where PET > Water Input apply logic of equation 13 and line below of AET Calculation (ie. aetOut_wPETgtWaterInput).
            ## Else where PET <= Water Input, AET = PET.  Arcpy Syntax = Con(Raster(waterInputRas)>= Raster(petRas), Raster(outSWB_Wm_gte_PET), Raster(SWB_EvapRemoved))
            waterInput_NP = raster2array(waterInputRas)
            petRas_NP = raster2array(petRas)
            outSWB_Wm_gte_PET_NP = raster2array(outSWB_Wm_gte_PET)
            SWB_EvapRemoved_NP = raster2array(SWB_EvapRemoved)

            outSWB_NP = np.where(waterInput_NP >= petRas_NP, outSWB_Wm_gte_PET_NP, SWB_EvapRemoved_NP)
            del waterInput_NP
            del petRas_NP
            del outSWB_Wm_gte_PET_NP
            del SWB_EvapRemoved_NP

            outSWB = outDir + "\\SWB_" + str(year) + "_" + month + ".tif"     #Output Soil Water Balance Raster
            array2raster(waterInputRas, outSWB, outSWB_NP)
            messageTime = timeFun()
            print ("Output Soil Water Balance derived for month - " + month + " - " +  outSWB + " - " + messageTime)

            deleteList = glob.glob(workspace + "\\*.tif*")

            for file in deleteList:
                try:
                    os.remove(file)
                except:
                    print ("Failed to Delete " + str(file))
                    traceback.print_exc(file=sys.stdout)


            ##Set Yearly value back after processing a 01-09 month
            if month not in ["10","11","12"]:
                year = year - 1


            return outSWB
    except:
        messageTime = timeFun()
        print ("Error monthSWB - " + messageTime)
        traceback.print_exc(file=sys.stdout)
        sys.exit()

#Function calculates the Fraction of precipitation removed from soil water storage, when PET is greater than Water Input (i.e. PET > Wm)(equation 13 Dilts et. al. 2015  Uses Soil Water Balance (eq 12),
# Potential Evapotranspiration (eq 16), Monthly Water Input (eq 8), and Maximum Available Water Holding capacity (Input AWS raster).
def soilWaterStorageRemoved(month, monthCount, monthList, year):

    try:

        if monthCount == 1 and year == startYear:  #Use the initial SWB from previous month as defined by the defined % (via variable - percAWSInitial) of Available Soil water holding capacity
            swbPrevious = outDir + "\\InitialMonth_SWB_Percent_" + str(percAWSInitial) + ".tif"

        elif month in ["10","11","12"]:  #All 10,11,12 months not in the first year
            previousMonth = monthList[monthCount - 2]
            swbPrevious = outDir + "\\SWB_" + str(year) + "_" + str(previousMonth) + ".tif"


        ## Add logic to add the change of year value after Oct,Nov,Dec months'  - - KRS 20171228
        elif month not in ["10","11","12"]:
            year = year + 1
            previousMonth = monthList[monthCount - 2]

            if month == "01":
                swbPrevious = outDir + "\\SWB_" + str(year - 1) + "_" + str(previousMonth) + ".tif"
            else:
                swbPrevious = outDir + "\\SWB_" + str(year) + "_" + str(previousMonth) + ".tif"


        petRasSyntax = outDir + "\\PET_*" + str(year) + "_" + str(month) + ".tif"
        petRasList = glob.glob(petRasSyntax)
        pet = (petRasList[0])

        waterInput = outDir + "\\WaterInput_" + str(year) + "_" + str(month) + ".tif"

        #Initial Equation for outRightSWSR: (-1 * ((Raster(pet) - Raster(waterInput)) / Raster(soilAWS)))
        pet_NP = raster2array(pet)
        waterInput_NP = raster2array(waterInput)

        outRightSWSR1_NP = np.subtract(pet_NP, waterInput_NP)
        del pet_NP
        del waterInput_NP

        soilAWS_NP = raster2array(soilAWS)

        outRightSWSR2_NP = np.divide(outRightSWSR1_NP, soilAWS_NP)
        del outRightSWSR1_NP
        del soilAWS_NP

        neg1_NP = raster2array(pet)
        neg1_NP[neg1_NP > -1000] = -1.0

        outRightSWSR_NP = np.multiply(neg1_NP, outRightSWSR2_NP)
        del neg1_NP

        #Temporary workspace rasters turned off post migration
##        outRightSWSR = workspace + "\\RightSWSR_" + str(month) + ".tif"
##        array2raster(pet, outRightSWSR, outRightSWSR_NP)
##        messageTime = timeFun()
##        print ("Derived Right Side Soil Water Storage Removed - " + month + " - " +  outRightSWSR + " - " + messageTime)

        #Equation 13 Final Calc: (1 - Exp(outRightSWSR)) * Raster(swbPrevious)
        exp_OutRightSWSR_NP = np.exp(outRightSWSR_NP)
        del outRightSWSR2_NP

        Val1_NP = raster2array(pet)
        Val1_NP[Val1_NP > -1000] = 1.0

        SWSR_int_NP = np.subtract(Val1_NP, exp_OutRightSWSR_NP)
        del Val1_NP
        del exp_OutRightSWSR_NP

        swbPrevious_NP = raster2array(swbPrevious)

        outRemovedSWS_NP = np.multiply(SWSR_int_NP, swbPrevious_NP)
        del swbPrevious_NP
        del SWSR_int_NP
        outRemovedSWS = outDir + "\\SWS_To_Remove_PET_gt_Wm_" + str(year) + "_" + str(month) + ".tif"
        array2raster(pet,outRemovedSWS,outRemovedSWS_NP)
        del outRemovedSWS_NP
        messageTime = timeFun()
        print ("Derived Soil Water Storage removed for month - " + month + " - " +  outRemovedSWS + " - " + messageTime)

        ##Set Yearly value back after processing a month - KRS 20171228
        if month not in ["10","11","12"]:
            year = year - 1


    except:
        messageTime = timeFun()
        print ("Error soilWaterStorageRemoved - " + messageTime)
        traceback.print_exc(file=sys.stdout)
        sys.exit()


#Function calculates Actual Evapotranspiration.  If PET > Wm (i.e. water Input) AET is the smallest between (PET - Monthly) or (Soil Water Storage Removed + Monthly Water Input) (Eq 13 and Line Below)
# Else when PET <= Wm then AET = PET.
def actualEvapoTrans(month, year):

    try:


         ##Add logic to add the change of year value after Oct,Nov,Dec months'  - - KRS 20171228
        if month not in ["10","11","12"]:
            year = year + 1

        petRasSyntax = outDir + "\\PET_*" + str(year) + "_" + str(month) + ".tif"
        petRasList = glob.glob(petRasSyntax)
        pet = (petRasList[0])

        sws_rem = outDir + "\\SWS_To_Remove_PET_gt_Wm_" + str(year) + "_" + str(month) + ".tif"
        waterInput = outDir + "\\WaterInput_" + str(year) + "_" + str(month) + ".tif"

        ###Logic to calculate AET when the PET > water input

        sws_rem_NP = raster2array(sws_rem)
        waterInputNP = raster2array(waterInput)
        #Calculate sws_rem + waterInput
        sws_waterInput_NP = np.add(sws_rem_NP, waterInputNP)
        del sws_rem_NP
        del waterInputNP


        #Retain smallest value between PET or SWS_Removed + Water Input = Actual Evapotranspiration - Line below Equation 13
        #Note - out_swsr_waterInput = sws_waterInput_NP

        pet_NP = raster2array(pet)

        aetOut_wPETgtWaterInput_NP = np.where(pet_NP >= sws_waterInput_NP, sws_waterInput_NP, pet_NP)
        del sws_waterInput_NP
        del pet_NP


        # Final AET calculation where PET > Water Input apply logic of equation 13 and line below of AET Calculation (ie. aetOut_wPETgtWaterInput).
        # Else where PET <= Water Input, AET = PET.

        waterInputNP = raster2array(waterInput)
        #aetOut_wPETgtWaterInput_NP = raster2array(aetOut_wPETgtWaterInput)
        pet_NP = raster2array(pet)

        aetCalcFin_NP = np.where(pet_NP > waterInputNP, aetOut_wPETgtWaterInput_NP, pet_NP)
        del waterInputNP
        del aetOut_wPETgtWaterInput_NP
        del pet_NP

        aetOut = outDir + "\\AET_" + str(year) + "_" + str(month) + ".tif"
        array2raster(waterInput, aetOut, aetCalcFin_NP)
        del aetCalcFin_NP
        messageTime = timeFun()
        print ("Actual Evapotranspiration - Dervied for month - " + month + " - " +  aetOut + " - " + messageTime)


        ##Set Yearly value back after processing a month - KRS 20171228
        if month not in ["10","11","12"]:
            year = year - 1

        #############
        #Clean up routine
        #################

        deleteList = glob.glob(workspace + "\\*.tif*")

        for file in deleteList:
            try:
                os.remove(file)

            except:
                print ("Failed to Delete " + str(file))
                traceback.print_exc(file=sys.stdout)

    except:
        messageTime = timeFun()
        print ("Error actualEvapoTrans function - " + messageTime)
        traceback.print_exc(file=sys.stdout)
        sys.exit()

#Function calculates the Water Deficit which is the difference between (PET - Monthly) and (AET - Monthly)
def waterDeficit(month, year):

    try:


        ##Add logic to add the change of year value after Oct,Nov,Dec months'  - - KRS 20171228
        if month not in ["10","11","12"]:
            year = year + 1


        petRasSyntax = outDir + "\\PET_*" + str(year) + "_" + str(month) + ".tif"
        petRasList = glob.glob(petRasSyntax)
        pet = (petRasList[0])

        aet = outDir + "\\AET_" + str(year) + "_" + str(month) + ".tif"

        pet_NP = raster2array(pet)
        aet_NP = raster2array(aet)

        outDeficit_NP = np.subtract(pet_NP, aet_NP)
        del pet_NP
        del aet_NP

        outDeficit = outDir + "\\WaterDeficit_" + str(year) + "_" + str(month) + ".tif"
        array2raster(pet, outDeficit, outDeficit_NP)
        messageTime = timeFun()
        print ("Water Deficit for year/month - " + str(year) + "_" + month + " - " +  outDeficit + " - " + messageTime)

        ##Set Yearly value back after processing a month - KRS 20171228
        if month not in ["10","11","12"]:
            year = year - 1

    except:
        messageTime = timeFun()
        print ("Error waterDeficit function - " + messageTime)
        traceback.print_exc(file=sys.stdout)
        sys.exit()




#Function used to derive the physically based FOA Penman-Montieth evapotranspiration value
# FAO Penman-Montieth Equation is defined at: http://www.fao.org/docrep/X0490E/x0490e06.htm#TopOfPage Equation 6)
def Penman_Montieth(year, month):

    try:
        #Top Left Term of FAO Penman-Monteith (0.408 Delta(Rn-G))
        #QC Code Debug Complete 20190103 KRS
        Penman_topLeft_np = Penman_topLeft(year, month)
        messageTime = timeFun()
        print ("Successfully finished function 'Penman_topLeft' - " + " - " + messageTime)

        #Top Middle Term of FAO Penman-Monteith (900/corrected_tavg)*gamma
        #QC Code Debug Complete 20190103 KRS
        Penman_topMiddle_np = Penman_topMiddle(year, month)
        messageTime = timeFun()
        print ("Successfully finished function 'Penman_topMiddle' - " + " - " + messageTime)

        #Top Right Term of FAO Penman-Monteith u2*(Es-Ea)
        #QC Code Debug Complete 20190103 KRS
        Penman_topRight_np = Penman_topRight(year, month)
        messageTime = timeFun()
        print ("Successfully finished function 'Penman_topRight' - " + " - " + messageTime)

        #Derives the Penman Top Term (topmiddle_term*topright_term) + topleft_term
        #QC Code Debug Complete 20190103 KRS
        Penman_topTerm_np = Penman_topTerm(Penman_topLeft_np, Penman_topMiddle_np, Penman_topRight_np)
        messageTime = timeFun()
        print("Successfully finished function 'Penman_topTerm' - " + " - " + messageTime)

        #Derive the Penman Bottom Right Term: gamma *(1 + wind_correction)
        #QC Code Debug Complete 20190103 KRS
        penman_bottomRightTerm_np = Penman_bottomRightTerm()
        messageTime = timeFun()
        print("Successfully finished function 'Penman_bottomRightTerm' - " + " - " + messageTime)

        #Derive overall Bottom term delta + gamma *(1 + wind_correction)
        #QC Code Debug Complete 20190103 KRS
        penman_bottomTerm_np = Penman_bottomTerm(year, month, penman_bottomRightTerm_np)
        messageTime = timeFun()
        print("Successfully finished function 'Penman_bottomTerm' - " + " - " + messageTime)

        #Derive overall Penman-Monteith ET Equation:  (Penman_topTerm_np/penman_bottomTerm_np)
        #QC Code Debug Complete 20190103 KRS
        penman_Eto_np = Penman_FullTerm(Penman_topTerm_np, penman_bottomTerm_np)
        messageTime = timeFun()
        print("Successfully finished function 'Penman_FullTerm' - " + " - " + messageTime)

        ############################################################
        #If SWE is Greater than zero no Potential Evapotranspiration  - Code need to be QC'd post create of SWE datasets 20200103 - KRS
        ############################################################
        dirPath_Name = sweDir + "\\*monavg_" + str(year) + month + "*.tif"  # Directory Path and wildcard syntax
        swe_NC = glob.glob(dirPath_Name)

        # Create the SWE array
        swe_np = raster2array(swe_NC[0])
        #Where SWE >0, set to 0, else Penman ET
        penman_Eto_np_swe = np.where(swe_np > 0, 0, penman_Eto_np)

        #Export the Penman-Monteith Eto Array
        if heatLoadIndex.lower() == "yes": #This will be a workspace PET raster'
            outPenmanEto = workspace + "\\PET_Penman_" + str(year) + "_" + month + ".tif"
        else:
            outPenmanEto = outDir + "\\PET_Penman_" + str(year) + "_" + month + ".tif"

        #Export penman_Eto_np with SWE >0 set to 0 Array to a Raster
        array2raster(soilAWS,outPenmanEto, penman_Eto_np_swe)
        messageTime = timeFun()
        print("Derived Penman Eto with SWE correction (i.e. >0 set to zero) for year/month - " + str(year) + "_" + month + " - " + outPenmanEto + " - " + messageTime)

        return outPenmanEto

    except:
        messageTime = timeFun()
        print ("Error Penman_Montieth function - " + messageTime)
        traceback.print_exc(file=sys.stdout)
        sys.exit()


#Top Left Term of FAO Penman-Monteith (0.408 Delta(Rn-G) - Initial Development finished 2018/07/23 - KRS
#QC Initial Code Complete 20191230 - KRS
def Penman_topLeft(year, month):

    try:

        #Derive Delta - Debug QC Completed 20191230 - KRS
        out_Delta = calc_Delta(year, month)

        #Derive Inverse Relative Distance - Using the mid Month Day value - Completed 2018/7/6
        #Debug QC Completed 20191231
        inverse_rel_distance = calc_inverse_rel_distance(month)

        #Derive sunset_hour_angle - Code Completed 2018/7/6; Debug QC Completed 20191231
        sunset_hour_angle_NP = calc_sunset_hour_angle(latitude, month)

        #Derive  Ra: extra-terrestrial radiation in MJ/m2/day. Equation 21 of Ch3 FAO doc. - Completed 2018/7/6; Debug QC Completed 20191231
        Ra_np= calc_Ra(inverse_rel_distance,sunset_hour_angle_NP,latitude, month)

        #Derive N = Maximum Daylength - Completed 2018/7/6 - Not being used due to function CalcRS not being used - KRS
        #N_np = calc_daylength(sunset_hour_angle_NP)

        #############################
        #Derive Rs (MJ/m2/day) - Completed 2018/7/6 - I believe this is the equivalent of the Daymet sRad data product so calculaton is not necessary - KRS
        #Rs_np =CalcRs(Ra_NP, year, month, N_np)

        #Function to convert the native Daymet sRad (W/m2) to (MJ/m2/day)
        # Debug QC Completed 20200102
        Rs_np = calc_sRad_MJM2Day(month, year)
        ##############################

        #Derive Rnl: net long-wave radiation in MJ/m2/day - Completed 2018/7/18; Code Debug Complete 20200102 KRS
        Rnl_np = calc_Rnl(tmaxDir,tminDir,Rs_np, Ra_np, year, month)

        #Derive Incoming Net Shortwave Radiation - Completed 20180719; Code Debug Complete 20200102 KRS
        Rn_np = calc_Rn(Rnl_np, Rs_np)

        ##############################
        #Check if next month is known for Soil Heat Flux Density Calculations
        outNextMonth = checkNextMonth(year, month)

        if outNextMonth == "Yes":
            #Derive monthly Soil Heat Flux Density (G - (MJ/m2/day)) using equations 43 when Next Month Is available
            #Code Debug Complete 20200103 KRS
            G_np = calc_G_nextMonthKnown(year, month)

        else:
            #Derive monthly Soil Heat Flux Density (G - (MJ/m2/day)) using equations 44 when Next Month Is NOT available
            G_np = calc_G_nextMonthUnknown(year, month)

        ##############################

        #################################################
        #Calculate the Top Left parameter (.408*D)

        pt408_np = raster2array(out_Delta)

        #Create Raster with value 0.408 every where
        pt408_np[pt408_np > -999] = 0.408

        out_Delta_np = raster2array(out_Delta)
        #Calculate 0.408*D
        pt408_delta_np = np.multiply(pt408_np, out_Delta_np)
        del pt408_np
        del out_Delta_np

        #Calculate the (Rn-G) (i.e. Net Radiation minus Soil heat flux density)
        Rn_minus_G_np = np.subtract(Rn_np, G_np)

        #Calculate the .408*D*(Rn-G)
        Penman_topLeft_np = np.multiply(pt408_delta_np, Rn_minus_G_np)
        del pt408_delta_np
        del Rn_minus_G_np

        #Export Penman Top Left to an output format (.tif in this case - may want to export all to .nc?
        outPenmanTopLeft = outDir + "\\PenmanTopLeft_" + str(year) + "_" + str(month) + ".tif"
        array2raster(soilAWS, outPenmanTopLeft, Penman_topLeft_np)
        messageTime = timeFun()
        print ("Successfully derived 'Penman_topLeft_np' for year/month - " + str(year) + "_" + month + " - " +  outPenmanTopLeft + " - " + messageTime)

        return Penman_topLeft_np

    except:
        messageTime = timeFun()
        print ("Error Function 'Penman_topLeft - " + messageTime)
        traceback.print_exc(file=sys.stdout)
        sys.exit()


#Function derives the Penman-Monteith top middle equation ((900/Tavg + 273)*gamma)
def Penman_topMiddle(year, month):

    try:

        ##########################
        #Caluclate the Tavg array
        dirPath_Name = tminDir + "\\*monavg_" + str(year) + month + "*.tif"  #Directory Path and wildcard syntx
        tmin_NC = glob.glob(dirPath_Name)

        #Create the tmin array
        tmin_np = raster2array(tmin_NC[0])


        dirPath_Name = tmaxDir + "\\*monavg_" + str(year) + month + "*.tif"  #Directory Path and wildcard syntx
        tmax_NC = glob.glob(dirPath_Name)

        #Create the tmax array
        tmax_np = raster2array(tmax_NC[0])

        #Derive average temp from Tmin and Tmax
        Tavg_np = calc_avgTemp(tmin_np, tmax_np)

        ###############################
        #Derive the array with 900
        Array_900_np = Tavg_np
        Array_900_np[Array_900_np > -100000] = 900.0

        #Calculate 900/Tavg
        Array_900_divide_Tavg_np = np.divide(Array_900_np,Tavg_np)
        del Array_900_np
        del Tavg_np

        #Derive the Kelvin array
        Array_273_np = Array_900_divide_Tavg_np
        Array_273_np[Array_273_np > -100000] = 273.0

        #Calculate the (900/Tavg) + 273
        leftTerm_np = np.add(Array_900_divide_Tavg_np, Array_273_np)
        del Array_900_divide_Tavg_np
        del Array_273_np

        #Derive atmopsheric pressure; QC Code Debug Complete 20200103 KRS
        atmos_pressure_np = calc_atmospheric_pressure(elevation)

        #Derive Gamma; QC Code Debug Complete 20200103 KRS
        gamma_np = calc_gamma(atmos_pressure_np)

        #Derive the: ((900/Tavg + 273)*gamma)
        Penman_topMiddle_np = np.multiply(leftTerm_np, gamma_np)
        del leftTerm_np

        return Penman_topMiddle_np

    except:
        messageTime = timeFun()
        print ("Error Function 'Penman_topMiddle' - " + messageTime)
        traceback.print_exc(file=sys.stdout)
        sys.exit()

#Function derives the Penman-Monteith top right equation: u2*(Es-Ea)
#u2 = wind speed at 2m height, set to 2 m/s by default
#Es_minus_Ea = vapor pressure deficit in KPa
#Es = Saturation vapour pressure (KPa)
#Ea = Actual vapour pressure (KPa)

def Penman_topRight(year, month):

    try:
        # Mean saturation vapor pressure derived from air temperature(Es)

        #Derive Es: Step 10. Es = e(Tmax)+ e(TMIN)/2
        # e(Tmax) = 0.6108exp((17.27*Tmax) / (TMax + 237.3))
        # e(Tmin) = 0.6108exp((17.27*Tmin) / (TMin + 237.3));QC Code Debug Complete 20200103 - KRS
        Es_np = calc_Es(month, year)

        #Step 11 - Actual vapor pressure (ea) derived from rleative humidity - Completed 20180810
        #Derive Ea:Step 11. Ea = (e(Tmin)[RHmax/100] + e(Tmax)[RHmin/100])/2
        #QC Code Debug Complete 20200103 - KRS
        Ea_np = calc_Ea(month, year)

        #Derive (Es - Ea)
        Es_minus_Ea_np = np.subtract(Es_np, Ea_np)
        del Es_np
        del Ea_np

        #####Currently setting the default wind speed value to 2 m/s - KRS 20180824
        #Derive the wind speed at 2m height, set to 2 m/s by default - David did you do this in Row U in your worksheet?  Seems to be an incrementation number
        u2_np = Es_minus_Ea_np
        #Create Raster with value 2 every where
        u2_np[u2_np > -100000] = 2.0

        #Derive final Penman_TopRight: u2*(Es-Ea)
        Penman_topRight_np = np.multiply(u2_np,Es_minus_Ea_np)
        #del u2_np
        del Es_minus_Ea_np

        return Penman_topRight_np

    except:
        messageTime = timeFun()
        print ("Error Function 'Penman_topRight' - " + messageTime)
        traceback.print_exc(file=sys.stdout)
        sys.exit()

#Derives the Penman Top Term (topmiddle_term*topright_term) + topleft_term
def Penman_topTerm(Penman_topLeft_np, Penman_topMiddle_np, Penman_topRight_np):

    try:

        #Multiply topmiddle_term*topright_term
        bracket_np = np.multiply(Penman_topMiddle_np, Penman_topRight_np)
        del Penman_topMiddle_np
        del Penman_topRight_np

        #Final Calc: topmiddle_term*topright_term) + topleft_term
        Penman_topTerm_np = np.add(bracket_np, Penman_topLeft_np)
        del bracket_np
        del Penman_topLeft_np

        return Penman_topTerm_np

    except:
        messageTime = timeFun()
        print ("Error Function 'Penman_topTerm' - " + messageTime)
        traceback.print_exc(file=sys.stdout)
        sys.exit()

#Derives the Penman Bottom Right Term: (1 + wind_correction) * gamma
# Wind Correction = 0.34 * u2 (i.e. wind speed)  - wind speed being set at the constant 2 mph value
def  Penman_bottomRightTerm():

    try:

        # Derive the default 2 mph wind speed array
        u2_np = raster2array(soilAWS)
        u2_np[u2_np > -100000] = 2.0

        #Derive the wind correction value (0.34 * u2)
        #Create array with 0.34
        pt34_np = u2_np
        #Create Raster with value 2 every where
        pt34_np[pt34_np > -100000] = 0.34

        #Derived wind correction value
        windCorretion_np = np.multiply(pt34_np, u2_np)
        del pt34_np
        del u2_np

        #Create array with 1.0
        One_np = windCorretion_np
        #Create Raster with value 2 every where
        One_np[One_np > -100000] = 1.0

        #Derive (1 + wind_correction)
        one_windCorrection_np = np.add(One_np, windCorretion_np)
        del One_np
        del windCorretion_np

        # Derive atmospheric pressure
        atmos_pressure_np = calc_atmospheric_pressure(elevation)
        # Derive Gamma
        gamma_np = calc_gamma(atmos_pressure_np)
        del atmos_pressure_np

        #Derive (1 + wind_correction) * gamma
        penman_bottomRightTerm_np = np.multiply(one_windCorrection_np, gamma_np)
        del one_windCorrection_np
        del gamma_np

        return penman_bottomRightTerm_np

    except:
        messageTime = timeFun()
        print ("Error Function 'Penman_bottomRightTerm' - " + messageTime)
        traceback.print_exc(file=sys.stdout)
        sys.exit()


#Derive overall Bottom term: delta + gamma *(1 + wind_correction)
def  Penman_bottomTerm(year, month, penman_bottomRightTerm_np):

    try:
        # Derive Delta
        out_Delta = calc_Delta(year, month)
        delta_np = raster2array(out_Delta)

        penman_bottomTerm_Initial = np.multiply(delta_np, penman_bottomRightTerm_np)
        del delta_np
        del penman_bottomRightTerm_np

        #Set any Eto values less than zero to zero
        penman_bottomTerm_np = np.where(penman_bottomTerm_Initial < 0, 0, penman_bottomTerm_Initial)
        del penman_bottomTerm_Initial

        return penman_bottomTerm_np

    except:
        messageTime = timeFun()
        print ("Error Function 'Penman_bottomTerm' - " + messageTime)
        traceback.print_exc(file=sys.stdout)
        sys.exit()

#Derive overall Penman-Monteith ET Equation:
def Penman_FullTerm(Penman_topTerm_np, penman_bottomTerm_np):

    try:

        penman_Eto_np = np.divide(Penman_topTerm_np, penman_bottomTerm_np)
        del Penman_topTerm_np
        del penman_bottomTerm_np

        return penman_Eto_np

    except:
        messageTime = timeFun()
        print ("Error Function 'Penman_FullTerm' - " + messageTime)
        traceback.print_exc(file=sys.stdout)
        sys.exit()


#Function Calculated the Mean Temperature Array using the TMIN and TMAX inputs
def calc_TMean(year, month):
        #Get the Correct Monthly Tmax dataset'
        out_Path = funPathName_dataset(tmaxDir, "\\*MonthlyAvg_", year, month, "*.nc")
        datasetGlob = glob.glob(out_Path)
        #Create the Numpy Array'
        tmax_np = raster2array(datasetGlob[0])


        #Get the Correct Monthly Tmin dataset'
        out_Path = funPathName_dataset(tminDir, "\\*MonthlyAvg_", year, month, "*.nc")
        datasetGlob = glob.glob(out_Path)
        #Create the Numpy Array'
        tmin_np = raster2array(datasetGlob[0])

        #Add Tmax and Tmin
        addMaxMin_NP = np.add(tmax_np, tmin_np)
        del tmax_np
        del tmin_np

        #Array value 2
        np2 = raster2array(datasetGlob[0])
        #Create Raster with value 0.408 every where
        np2[np2 > -999] = 2.0


        #Derive the Mean Temp Array
        meanTemp_NP = np.divide(addMaxMin_NP, np2)
        del np2
        del addMaxMin_NP

        return meanTemp_NP



#Function evaluates if the year,month value has climatic data available
def checkNextMonth(year, month):

    if year == endYear: #Last Year, check if the month value is the December value after which (i.e Jan of next Year) no climatic data

        if month == "12":

            outNextMonth = "No"
        else:
            outNextMonth = "Yes"

    else:

        outNextMonth = "Yes"

    return outNextMonth


def calc_Delta(year, month): #Debug QC Complete - 20191230 - KRS
    #Slope of the vapor pressure curve
    # t is AVERAGE air temperature in degrees C
    # Equation 13 in FAO doc (http://www.fao.org/docrep/X0490E/x0490e06.htm#TopOfPage)
##    tmax = float(tmax);tmin=float(tmin)
##    t = (tmax + tmin)/2
##    bracket_term = (17.27*t)/(t+237.3)
##    right_term = 0.6108 * np.exp(bracket_term)
##    top_term = 4098*right_term
##    bottom_term = (t+237.3)**2
##    D = top_term/bottom_term
##    return D


    dirPath_Name = tminDir + "\\*monavg_" + str(year) + month + "*.tif"  #Directory Path and wildcard syntax
    tmin_NC = glob.glob(dirPath_Name)

    #Create the tmin array
    tmin_np = raster2array(tmin_NC[0])

    dirPath_Name = tmaxDir + "\\*monavg_" + str(year) + month + "*.tif"  #Directory Path and wildcard syntax
    tmax_NC = glob.glob(dirPath_Name)

    #Create the srad array
    tmax_np = raster2array(tmax_NC[0])

    #Calculate the average temp
    avgTemp_np = calc_avgTemp(tmin_np, tmax_np)

    #Calculate the (17.27*t)/(t+237.3)
    ras17pt27_NP = raster2array(tmin_NC[0])

    #Create Raster with value 17.27 every where
    ras17pt27_NP[ras17pt27_NP > -999] = 17.27

    #(17.27*t)
    deltaleft_NP = np.multiply(ras17pt27_NP, avgTemp_np)
    del ras17pt27_NP

    ras237pt3_NP = raster2array(tmin_NC[0])
    #Create Raster with value 237.3 every where
    ras237pt3_NP[ras237pt3_NP > -999] = 237.3

    #(t+237.3)
    deltaRight_NP = np.add(avgTemp_np, ras237pt3_NP)

    #(17.27*t)/(t+237.3)
    deltaBracket_NP = np.divide(deltaleft_NP, deltaRight_NP)
    del deltaleft_NP
    del deltaRight_NP

    ######
    #Right Term (0.6108 * np.exp(bracket_term))

    raspt6108_NP = raster2array(tmin_NC[0])

    #Create Raster with value 0.6108 every where
    raspt6108_NP[raspt6108_NP > -999] = 0.6108

    #Create Exp (Delta Bracket)
    expBracket_NP = np.exp(deltaBracket_NP)

    del deltaBracket_NP

    rightTerm_NP = np.multiply(raspt6108_NP, expBracket_NP)

    del raspt6108_NP

    #######
    #Calculate top_term = 4098*right_term

    ras4098_NP = raster2array(tmin_NC[0])

    #Create Raster with value 4098 every where
    ras4098_NP[ras4098_NP > -999] = 4098

    #4098*right_term
    topterm_NP = np.multiply(ras4098_NP, rightTerm_NP)

    del ras4098_NP
    del rightTerm_NP

    ############
    #bottom_term = (t+237.3)**2
    ############

    tempPlus237pt3_NP = np.add(avgTemp_np, ras237pt3_NP)

    del ras237pt3_NP
    del avgTemp_np

    bottom_term_NP = np.power(tempPlus237pt3_NP, 2)

    del tempPlus237pt3_NP

    #########################
    #D = top_term/bottom_term
    #########################

    delta_NP = np.divide(topterm_NP,bottom_term_NP)
    outDelta = outDir + "\\Penman_Delta_" + str(year) + "_" + month + ".tif"

    #Export Array to a Raster
    array2raster(tmin_NC[0],outDelta, delta_NP)
    messageTime = timeFun()
    print("Derived Penman Delta ( for year/month - " + str(year) + "_" + month + " - " + outDelta + " - " + messageTime)

    return outDelta

#Function calculate the average temperature using the Tmax and Tmin' (tmax + tmin)/2) (KRS 20180122 Finished)
def calc_avgTemp(tmin_np, tmax_np):

    try:
        addTminTmax_NP = np.add(tmin_np, tmax_np)
        del tmin_np
        del tmax_np

        divide_2_NP = addTminTmax_NP
        #Create Raster with value 2 every where
        divide_2_NP[divide_2_NP > -999] = 2

        #Derive the tavg
        avgTemp_np = np.divide(addTminTmax_NP, divide_2_NP)

        del addTminTmax_NP
        del divide_2_NP

        return avgTemp_np

    except:
        messageTime = timeFun()
        print ("Error 'calc_avgTemp' function - " + messageTime)
        traceback.print_exc(file=sys.stdout)
        sys.exit()

#Derive monthly Soil Heat Flux Density (G - (MJ/m2/day)) using equations 43 when (Tmonth i+1 is known (i.e. next monthly average temp is available)
#Gmonth, i = 0.07 (Tmonth, i+1 - Tmonth, i-1) (43)
def calc_G_nextMonthKnown(year, month):

    try:
        monthList = ["10","11","12","01","02","03","04","05","06","07","08","09"]

        #####################
        #Calculate Tmonth,i+1 (i.e. Average temp of next Month)
        monthIndex = monthList.index(month)

        #Define monthly index, is September restart at beginning of index
        if monthIndex == 11:
            monthIndex_plus1 = 0

        else:
            monthIndex_plus1 = monthIndex + 1

        #Define the Month + 1 value (i.e the plus one month value)
        month_iplus1 = monthList[monthIndex_plus1]

        #Define the Year + 1 value (i.e the Year plus 1 month value.  If 'month' = 12 this will be 'year' + 1, else 'year')
        if year == 12:
            year_iplus1 = year + 1
        else:

            year_iplus1 = year

        dirPath_Name = tminDir + "\\*monavg_" + str(year_iplus1) + month_iplus1 + "*.tif"  #Directory Path and wildcard syntx for the srad NC File'
        tmin_NC = glob.glob(dirPath_Name)

        #Create the tmin array
        tmin_np = raster2array(tmin_NC[0])

        dirPath_Name = tmaxDir + "\\*monavg_" + str(year_iplus1) + month_iplus1 + "*.tif"  #Directory Path and wildcard syntx for the srad NC File'
        tmax_NC = glob.glob(dirPath_Name)

        #Create the tmax array
        tmax_np = raster2array(tmax_NC[0])

        Tmonth_iplus1_np = calc_avgTemp(tmin_np, tmax_np)
        del tmin_np
        del tmax_np
        #####################

        #####################
        #Calculate Tmonth,i-1 (i.e. Average temp of previous Month)
        monthIndex = monthList.index(month)

        #Define monthly index, is October restart at end of List (i.e September
        if monthIndex == 10:
            monthIndex_minus1 = 11

        else:
            monthIndex_minus1 = monthIndex - 1

        #Define the Month - 1 value (i.e the previous month value)
        month_iminus1 = monthList[monthIndex_minus1]

        #Define the Year + 1 value (i.e the Year plus 1 month value.  If 'month' = 12 this will be 'year' + 1, else 'year')
        if year == "01":
            year_iminus1 = year - 1
        else:
            year_iminus1 = year


        dirPath_Name = tminDir + "\\*monavg_" + str(year_iminus1) + month_iminus1 + "*.tif"  #Directory Path and wildcard syntx for the srad NC File'
        tmin_NC = glob.glob(dirPath_Name)

        #Create the tmin array
        tmin_np = raster2array(tmin_NC[0])


        dirPath_Name = tmaxDir + "\\*monavg_" + str(year_iminus1) + month_iminus1 + "*.tif"  #Directory Path and wildcard syntx for the srad NC File'
        tmax_NC = glob.glob(dirPath_Name)

        #Create the tmax array
        tmax_np = raster2array(tmax_NC[0])

        Tmonth_iminus_np = calc_avgTemp(tmin_np, tmax_np)
        del tmin_np
        del tmax_np
        #####################

        #Calc - Tmonth_iplus1_np - Tmonth_iminus_np
        right_Side_np = np.subtract(Tmonth_iplus1_np, Tmonth_iminus_np)
        del Tmonth_iplus1_np
        del Tmonth_iminus_np

        #Derive the 0.07 array
        pt07_np = right_Side_np
        pt07_np[pt07_np > -1000000] = 0.07

        #Derived 0.07 x (Tmonth_iplus1_np - Tmonth_iminus_np)

        G_np = np.multiply(pt07_np, right_Side_np)
        del pt07_np
        del right_Side_np


        return G_np

    except:
        messageTime = timeFun()
        print ("Error 'calc_G_nextMonthKnown' function - " + messageTime)
        traceback.print_exc(file=sys.stdout)
        sys.exit()

#Derive monthly Soil Heat Flux Density (G - (MJ/m2/day)) using equations 44 when (Tmonth i+1 is Unknown (i.e. next monthly average temp is NOT available)
#Gmonth, i = 0.14 (Tmonth, i - Tmonth, i-1) (44)
def calc_G_nextMonthUnknown(year, month):

    monthList = ["10","11","12","01","02","03","04","05","06","07","08","09"]

    #####################
    #Calculate Tmonth,i (i.e. the Current Month)

    dirPath_Name = tmin + "\\*monavg_" + str(year) + month + "*.tif"  #Directory Path and wildcard syntx for the srad NC File'
    tmin_NC = glob.glob(dirPath_Name)

    #Create the tmin array
    tmin_np = raster2array(tmin_NC[0])


    dirPath_Name = tmax + "\\*monavg_" + str(year) + month + "*.tif"  #Directory Path and wildcard syntx for the srad NC File'
    tmax_NC = glob.glob(dirPath_Name)

    #Create the tmax array
    tmax_np = raster2array(tmax_NC[0])

    Tmonth_i_np = calc_avgTemp(tmin_np, tmax_np)
    del tmin_np
    del tmax_np
    #####################

    #####################
    #Calculate Tmonth,i-1 (i.e. Average temp of previous Month)
    monthIndex = monthList.index(month)

    #Define monthly index, is October restart at end of List (i.e September
    if monthIndex == 10:
        monthIndex_minus1 = 11

    else:
        monthIndex_minus1 = monthIndex - 1

    #Define the Month - 1 value (i.e the previous month value)
    month_iminus1 = monthList[monthIndex_minus1]

    #Define the Year + 1 value (i.e the Year plus 1 month value.  If 'month' = 12 this will be 'year' + 1, else 'year')
    if year == "01":
        year_iminus1 = year - 1
    else:
        year_iminus1 = year

    dirPath_Name = tmin + "\\*monavg_" + str(year_iminus1) + month_iminus1 + "*.tif"  #Directory Path and wildcard syntx for the srad NC File'
    tmin_NC = glob.glob(dirPath_Name)

    #Create the tmin array
    tmin_np = raster2array(tmin_NC[0])


    dirPath_Name = tmax + "\\*monavg_" + str(year_iminus1) + month_iminus1 + "*.tif"  #Directory Path and wildcard syntx for the srad NC File'
    tmax_NC = glob.glob(dirPath_Name)

    #Create the tmax array
    tmax_np = raster2array(tmax_NC[0])

    Tmonth_iminus_np = calc_avgTemp(tmin_np, tmax_np)
    del tmin_np
    del tmax_np
    #####################

    #Calc - Tmonth_i_np - Tmonth_iminus_np
    right_Side_np = np.subtract(Tmonth_i_np, Tmonth_iminus_np)
    del Tmonth_iplus1_np
    del Tmonth_iminus_np

    #Derive the 0.14 array
    pt14_np = right_Side_np
    pt14_np[pt14_np > -1000000] = 0.14

    #Derived 0.14 x (Tmonth_i - Tmonth_iminus_np)

    G_np = np.multiply(pt14_np, right_Side_np)
    del pt14_np
    del right_Side_np

    return G_np

def calc_Ra(inverse_rel_distance, sunset_hour_angle_NP, latitude, month): #Completed 20180706
    #Ra = extra-terrestrial radiation in MJ/m2/day. Equation 21 of Ch3 FAO doc.
    # Latitude (j) in radians. Positive for northern hemisphere and negative for southern hemisphere.
    # Sunset hour angle (Ws) in radians. Solar declination (d) in radians.
##    Gsc = .0820 # Solar constant : MJ/m^2/day
##    first_term = (float((24*60))/pi) * Gsc #37.586
##    first_half_bracket_term = (np.sin(latitude) * np.sin(solar_declination)) * sunset_hour_angle
##    second_half_bracket_term = (np.cos(latitude) * np.cos(solar_declination) * np.sin(sunset_hour_angle))
##    full_bracket_term = first_half_bracket_term + second_half_bracket_term
##    Ra = first_term * full_bracket_term * inverse_rel_distance
##    return Ra

    #Create Raster with value 0.0820 every where - Solar constant : MJ/m^2/day
    gsc_NP = raster2array(latitude)
    gsc_NP[gsc_NP > -999] = 0.0820

    #Create Raster with value 1440 every where (i.e 24 * 60)
    np1440zeropt0 = raster2array(latitude)
    np1440zeropt0[np1440zeropt0 > -999] = 1440.0

    #1440 / Pi
    np1440_divPI = np.divide(np1440zeropt0, np.pi)

    del np1440zeropt0

    #Finish first term Calculation
    Ra_FirstTerm_NP = np.multiply(np1440_divPI, gsc_NP)

    del np1440_divPI
    del gsc_NP

    ##################################
    # first_half_bracket_term = (np.sin(latitude) * np.sin(solar_declination)) * sunset_hour_angle
    latitude_NP = raster2array(latitude)

    #Derive the Latitude in Radians
    latitudeRadian_NP = np.radians(latitude_NP)

    #Derive the Latitude in Radians * Sin
    latSin_NP = np.sin(latitudeRadian_NP)

    #Calculate the montly solar declination via the Penman Approach
    monthSolarDec = calc_solar_declination_Penman(month)

    #Create the Numpy raster Raster with the Monthly Solar Declinaton value
    solarDec_Monthly_NP = raster2array(latitude)
    solarDec_Monthly_NP[solarDec_Monthly_NP > -999] = monthSolarDec

    #Create the Numpy raster Raster with the Monthly Solar Declinaton value * Sin
    solarDec_Sin_NP = np.sin(solarDec_Monthly_NP)

    #(np.sin(latitude) * np.sin(solar_declination))
    SinLat_SinSolarDec_NP = np.multiply(latSin_NP, solarDec_Sin_NP)
    del  solarDec_Sin_NP

    #Multiple the Sunset_hour_angle
    firstHalfBracket_term_NP = np.multiply(SinLat_SinSolarDec_NP, sunset_hour_angle_NP)
    del SinLat_SinSolarDec_NP
    del latSin_NP


    ################
    #Second Half Bracket Term - (np.cos(latitude) * np.cos(solar_declination) * np.sin(sunset_hour_angle))

    latCos_NP = np.sin(latitudeRadian_NP)
    del latitudeRadian_NP


    #Create the Numpy raster Raster with the Monthly Solar Declinaton value * cos
    solarDec_Cos_NP = np.cos(solarDec_Monthly_NP)
    del solarDec_Monthly_NP

    #Sin(Sunset_hour_angle)
    sinSunSet_Hour_Angle_NP = np.sin(sunset_hour_angle_NP)
    del sunset_hour_angle_NP

    #Multiply the Cos(Latitude) * Cos(Solar_Declination)
    cosLat_cosSolarDec_NP = np.multiply(solarDec_Cos_NP, sinSunSet_Hour_Angle_NP)
    del solarDec_Cos_NP
    del sinSunSet_Hour_Angle_NP

    #Second Half Bracket Term
    secondHalfBracket_term_NP = np.multiply(latCos_NP, cosLat_cosSolarDec_NP)
    del cosLat_cosSolarDec_NP


    ###Full Bracket Term
    fullBracket_term_NP = np.add(firstHalfBracket_term_NP, secondHalfBracket_term_NP)
    del firstHalfBracket_term_NP
    del secondHalfBracket_term_NP


    Ra_Left_Side_NP = np.multiply(Ra_FirstTerm_NP, fullBracket_term_NP)
    del Ra_FirstTerm_NP
    del fullBracket_term_NP

    Ra_NP = np.multiply(Ra_Left_Side_NP, inverse_rel_distance)
    del Ra_Left_Side_NP

    return Ra_NP

    #Function to derive Rnl: net long-wave radiation
def calc_Rnl(tmaxDir,tminDir,Rs_np,Ra_np, year, month): #
    #Rnl = net long-wave radiation in MJ/m2/day. Equation 39 Ch3 FAO doc.
    #Ea = actual vapor pressure (Kpa). Rs = Solar radiation in MJ/m2/day as calc by equation 35.
    #Rso = clear sky radiation in MJ/m2/day as calculated by equation 37.
##    if Rs == 'null' or Rso == 'null':
##        Rs = 1
##        Rso = 1
##    relative_shortwave_radiation = Rs/Rso
##    if relative_shortwave_radiation > 1 : relative_shortwave_radiation = 1
##    tmax = tmax + 273.16;tmin = tmin + 273.16 # Convert to degrees Kelvin
##    tmax = tmax**4;tmin=tmin**4
##    left_bracket_term = (tmax+tmin)/2;left_bracket_term = left_bracket_term * .000000004903 # Stefan-Boltzmann constant
##    middle_term = 0.34 - (.14 * np.sqrt(Ea))
##    right_term = (1.35*relative_shortwave_radiation) - 0.35
##    Rnl = left_bracket_term * middle_term * right_term
##    return Rnl


    #Create the Rs Raster if null (i.e. -3.40282347e+38, KRS can never get nan function to work?
    Rs_np_Null_1 = np.where(Rs_np<-1000000, 1, Rs_np)
    del Rs_np

    #Calculate the Clear-sky solar radiation (Rso) - Even with daymat sRad I believe this still needs to be calculated. - KRS?
    Rso_np = calc_Rso(elevation,Ra_np)

    #Create the Rso Raster if null (i.e. -3.40282347e+38,k KRS can never get nan function to work?
    Rso_np_Null_1 = np.where(Rso_np<-1000000, 1, Rso_np)
    del Rso_np

    #Rs/Rs0
    relative_shortwave_radiation_np = np.divide(Rs_np_Null_1, Rso_np_Null_1)
    del Rs_np_Null_1
    del Rso_np_Null_1


    #Set Relative Shortwave Radiation to 1 if > 1.
    relative_shortwave_radiation_np[relative_shortwave_radiation_np > 1] = 1


    'Get the Correct Monthly Tmax dataset'
    out_Path = funPathName_dataset(tmaxDir, "\\*monavg_", year, month, "*.tif")
    datasetGlob = glob.glob(out_Path)
    'Create the Numpy Array'
    tmax_np = raster2array(datasetGlob[0])

    #Create a Kelvin NP array
    kelvin_np = raster2array(datasetGlob[0])
    kelvin_np[kelvin_np > -1000000] = 273.16


    #Tmax in Kelvin
    tmax_kelvin_np = np.add(tmax_np, kelvin_np)
    del tmax_np

    #Tmin in Kelvin
    #Directory Path and wildcard syntx for tmin dataset
    out_Path = funPathName_dataset(tminDir, "\\*monavg_", year, month, "*.tif")
    datasetGlob = glob.glob(out_Path)
    'Create the Numpy Array'
    tmin_np = raster2array(datasetGlob[0])


    #Tmin in Kelvin
    tmin_kelvin_np = np.add(tmin_np, kelvin_np)
    del kelvin_np
    del tmin_np


    #Tmax Kelvin raised to the power of 4
    tmax_power4_np = np.power(tmax_kelvin_np, 4)
    del tmax_kelvin_np

    #Tmin Kelvin raised to the power of 4
    tmin_power4_np = np.power(tmin_kelvin_np, 4)
    del tmin_kelvin_np

    left_bracket_term_np = np.add(tmax_power4_np, tmin_power4_np)
    del tmax_power4_np
    del tmin_power4_np

    np_Val2 = raster2array(datasetGlob[0])
    np_Val2[np_Val2 > -1000000] = 2.0


    left_bracket_term_div2_np = np.divide(left_bracket_term_np, np_Val2)
    del left_bracket_term_np
    del np_Val2

    #Create the Stefan-Boltzmann array
    stefan_Boltz_np = raster2array(datasetGlob[0])
    stefan_Boltz_np[stefan_Boltz_np > -1000000] = 0.000000004903


    left_bracket_termFinal = np.multiply(left_bracket_term_div2_np, stefan_Boltz_np) # Stefan-Boltzmann constant
    del left_bracket_term_div2_np
    del stefan_Boltz_np

     #Create a 0.34 Array
    p34_np = raster2array(datasetGlob[0])
    p34_np[p34_np > -1000000] = 0.34


    #Create a 0.14 Array
    p14_np = raster2array(datasetGlob[0])
    p14_np[p14_np > -1000000] = 0.14


    #Calculate the vapour pressure array in unit Kpa.  Daymet native vp data set is in Pa.
    out_Kpa_NP = calc_vp_kpa(month, year)


    #Sqroot the VP kpa array
    vp_kpa_sqrt_NP = np.sqrt(out_Kpa_NP)
    del out_Kpa_NP

    #(.14 * np.sqrt(Ea))
    middleRight_NP = np.multiply(p14_np, vp_kpa_sqrt_NP)

    #0.34 - (.14 * np.sqrt(Ea))
    middleTerm_NP = np.subtract(p34_np, middleRight_NP)

    #Convert sRad to MJ/m2/day -  See url https://daac.ornl.gov/DAYMET/guides/Daymet_mosaics.html  for formula to convert Daily total radion (MJ/m2/day)
    sRad_np = calc_sRad_MJM2Day(month, year)

    #Create a 1.35 Array
    p1pt35_np = raster2array(datasetGlob[0])
    p1pt35_np[p1pt35_np > -1000000] = 1.35

    #Right Term Right Side (1.35 * sRad (MJ/M2/day))
    rightTerm_Right_np = np.multiply(p1pt35_np, sRad_np)
    del sRad_np
    del p1pt35_np

    #Create a 0.35 Array
    pt35_np = raster2array(datasetGlob[0])
    pt35_np[pt35_np > -1000000] = 0.35


    #Full Right Term (1.35*relative_shortwave_radiation) - 0.35
    rightTermNP = np.subtract(rightTerm_Right_np, pt35_np)
    del rightTerm_Right_np
    del pt35_np

    #Multple the Left Bracket, Middle Term and Right Term
    Rnl_Left_Middle_np = np.multiply(left_bracket_termFinal, middleTerm_NP)
    del left_bracket_termFinal
    del middleTerm_NP

    #left_bracket_term * middle_term * right_term
    Rnl_np = np.multiply(Rnl_Left_Middle_np, rightTermNP)
    del Rnl_Left_Middle_np
    del rightTermNP

    return Rnl_np

#Function calculates the Daily total radiation (MJ/m2/day) using the following equation: ((srad (W/m2) * dayl (s/day)) / 1,000,000);Code Debug Complete 20200102 KRS
def calc_sRad_MJM2Day(month, year):
    #Directory Path and wildcard syntx for the srad tif file'
    dirPath_Name = sRad + "\\*MonthlyAvg_" + str(year) + month + "*.tif"
    srad_NC = glob.glob(dirPath_Name)

    #Create the srad array
    srad_np = raster2array(srad_NC[0])

    #Directory Path and wildcard syntx for the dayl NC File' - Using Standard 2010 15th of month for DayLength - Should derive average daylength monthly rasters for all years, but haven't
    #as of 20190102 - KRS
    dirPath_Name = dayl + "\\*Average_dayl_*" + month + ".tif"
    dayl_tif = glob.glob(dirPath_Name)

    #Create the 1,000,000
    dayl_np = raster2array(dayl_tif[0])

    #Create an 1,000,000 Array
    Array_1Mill_np = raster2array(dayl_tif[0])
    Array_1Mill_np[Array_1Mill_np > -1000000] = 1000000.0

    #srad * dayl
    srad_dayl_np = np.multiply(srad_np, dayl_np)
    del srad_np
    del dayl_np

    #final calc
    shortWaveRad_MJM2Day_np = np.divide(srad_dayl_np, Array_1Mill_np)
    del Array_1Mill_np
    del srad_dayl_np


    print ("Successfully calculated the Short Wave Radiation Conversion to 'MJ/m2/day' - function 'calc_ShortWaveRad_MJM2Day")
    return shortWaveRad_MJM2Day_np

#Function caculates Gamma
def calc_gamma(atmos_pressure_np):#Initial Derived 20180724
##    Gamma is the psychrometric constant used for Penman_Montieth Eto
##    gamma = 0.665 * .001 * atmospheric_pressure

    #Create Array with 0.665 every where
    pt665_np = atmos_pressure_np
    pt665_np[pt665_np > -1000000] = 0.665


    #Create Array with 0.001 every where
    pt001_np = atmos_pressure_np
    pt001_np[pt001_np > -1000000] = 0.001

    #Derive: 0.665 * .001
    pt001_x_pt665_np = np.multiply(pt665_np, pt001_np)
    del pt665_np
    del pt001_np

    #Derive Gamma: 0.665 * .001 * atmospheric_pressure
    gamma_np = np.multiply(pt001_x_pt665_np, atmos_pressure_np)

    messageTime = timeFun()
    print ("Successfully calculated the Gamma constant -'calc_gamma' - " + messageTime)

    return gamma_np

#Function to derive atmospheric pressure (
def calc_atmospheric_pressure(elevation): #Initial Development 20180724

##    tr = .0065*elevation
##    top = 293-tr
##    inside = top/293
##    right = inside**5.26
##    atmos_pressure = 101.3*right

    #Create Elevation Array
    elevation_np = raster2array(elevation)

    #Create Array with 0.0065 every where
    pt0065_np = elevation_np
    pt0065_np[pt0065_np > -1000000] = 0.0065

    #Derive: .0065*elevation
    tr_np = np.multiply(pt0065_np,elevation_np)
    del pt0065_np
    del elevation_np

    #Create Array with 293.0 every where
    Array_293_np = tr_np
    Array_293_np[Array_293_np > -1000000] = 293.0

    #Derive: 293-(.0065*elevation)
    top_np = np.subtract(Array_293_np, tr_np)
    del tr_np

    #Derived: (293-(.0065*elevation)) / 293
    inside_np = np.divide(top_np, Array_293_np)
    del top_np
    del Array_293_np

    #Create Array with 5.26 every where
    Array_5pt26_np = inside_np
    Array_5pt26_np[Array_5pt26_np > -1000000] = 5.26

    #Derive: ((293-(.0065*elevation)) / 293)^5.26
    right_np = np.power(inside_np, Array_5pt26_np)

    del Array_5pt26_np

    #Create Array with 101.3 every where
    Array_101pt3_np = inside_np
    Array_101pt3_np[Array_101pt3_np > -1000000] = 101.3
    del inside_np

    #Derive: 101.3*(((293-(.0065*elevation)) / 293)^5.26)
    atmos_pressure_np = np.multiply(Array_101pt3_np, right_np)
    del Array_101pt3_np
    del right_np

    return atmos_pressure_np

def calc_saturation_vapor_pressure(temp_NP): #This is being used to derive the Ea (actual vapour pressure) for arid regions when humidity data is not available.  Recommendation
# is to assume dewpoint is 2 degrees below Tmin.
    # t = degrees C, equation 11 in FAO doc
    # e(T) = 0.6108exp[(17.27* T)/ (T + 237.3)]


##    bracket_term = (17.27*t)/(t+237.3)
##    right_term = np.exp(bracket_term)
##    saturation_vapor_pressure = 0.6108 * right_term
##    return saturation_vapor_pressure #kPa

    try:
        #Array 17.27
        Array17pt27 = temp_NP
        Array17pt27[Array17pt27 > -1000000] = 17.27

        #17.27 * meanTemp
        Array17pt27_x_meanTemp_NP = np.multiply(Array17pt27, temp_NP)
        del Array17pt27

        #Array 237.3
        Array237pt3 = temp_NP
        Array237pt3[Array237pt3  > -1000000] = 237.3

        #237.3 + meanTemp
        Array237pt_plus_meanTemp_NP = np.add(Array237pt3, temp_NP)
        del Array237pt3
        del temp_NP


        #Bracket Term (17.27*t)/(t+237.3)
        bracket_term_np = np.divide(Array17pt27_x_meanTemp_NP, Array237pt_plus_meanTemp_NP)
        del Array17pt27_x_meanTemp_NP
        del Array237pt_plus_meanTemp_NP

        #Calculate the exponential of the Right side of Sat Vap Pressure Equation
        right_term_np = np.exp(bracket_term_np)

        #Array 0.6108
        Arraypt6108 = right_term_np
        Arraypt6108[Arraypt6108  > -1000000] = 0.6108

        #Devired: saturation_vapor_pressure = 0.6108 * right_term
        Es_np = np.multiply(Arraypt6108, bracket_term_np)
        del Arraypt6108
        del bracket_term_np

        return Es_np #kpa

    except:
        messageTime = timeFun()
        print ("Error Function 'calc_saturation_vapor_pressure_Ea' - " + messageTime)
        traceback.print_exc(file=sys.stdout)
        sys.exit()


def calc_Es(month, year): #Derived 20180803
    #Equation 12 in FAO doc
    # This is saturation vapor pressure for Tmean
##    tmax=float(tmax);tmin=float(tmin)
##    e_tmax = calc_saturation_vapor_pressure(tmax)
##    e_tmin = calc_saturation_vapor_pressure(tmin)
##    Es = (e_tmax + e_tmin)/2
##    return Es #kPa

    'Derive the SVP at TMAX'
    dirPath_Name = tmaxDir + "\\*monavg_" + str(year) + month + "*.tif"  #Directory Path and wildcard syntx
    tmax_NC = glob.glob(dirPath_Name)
    tmax_np = raster2array(tmax_NC[0])
    Es_tmax_np = calc_saturation_vapor_pressure(tmax_np)
    del tmax_np

    'Derive the SVP at TMIN'
    dirPath_Name = tminDir + "\\*monavg_" + str(year) + month + "*.tif"  #Directory Path and wildcard syntx
    tmin_NC = glob.glob(dirPath_Name)
    tmin_np = raster2array(tmin_NC[0])
    Es_tmin_np = calc_saturation_vapor_pressure(tmin_np)
    del tmin_np

    #'Sum Es_tmin' and 'Es_tmax
    Es_tmin_Es_tmax_np = np.add(Es_tmax_np, Es_tmin_np)
    del Es_tmax_np
    del Es_tmin_np

    #Derive the division array
    np_2 = Es_tmin_Es_tmax_np
    np_2[np_2 > -1000000] = 2.0

    #Derive Es = (e_tmax + e_tmin)/2
    Es_np = np.divide(Es_tmin_Es_tmax_np, np_2)
    del Es_tmin_Es_tmax_np
    del np_2

    return Es_np

#Step 11 - Actual vapor pressure (ea) derived with relative humidity data
#Derive Ea:Step 11- Calc Penmann Step by Step. Ea = (e(Tmin)[RHmax/100] + e(Tmax)[RHmin/100])/2
def calc_Ea(month, year):
    try:

        ###Derive Relative Humdity RH = vp from daymet / SVP
        ##rh_np = calc_Rh(month,year)

        ######################################
        #Derive Top Left : e(Tmin)[RHmax/100])

        #Derived Relative Humdity at Tmax - RHmax';QC Code Debug Complete 20200103 - KRS
        rhTmax_np = calc_RhTmax(month, year)

        #Create Array with value of 100
        Array100_np = rhTmax_np
        Array100_np[Array100_np > -1000000] = 100.0

        rhmax_div100_np = np.divide(rhTmax_np, Array100_np)
        del rhTmax_np
        del Array100_np

        #Derive the eTMIN'
        dirPath_Name = tminDir + "\\*monavg_" + str(year) + month + "*.tif"  #Directory Path and wildcard syntx
        tmin_NC = glob.glob(dirPath_Name)
        tmin_np = raster2array(tmin_NC[0])
        Etmin_np = calc_saturation_vapor_pressure(tmin_np)
        del tmin_np

        #Derive: etmin * (RHmax/100)
        topLeft_np = np.multiply(Etmin_np, rhmax_div100_np)
        del Etmin_np
        del rhmax_div100_np

        ########################################
        #Derive Top Right 'e(Tmax)[RHmin/100])

        #Derived Relative Humdity at Tmin - RHmin'
        rhTmin_np = calc_RhTmin(month, year)

        #Create Array with value of 100
        Array100_np = rhTmin_np
        Array100_np[Array100_np > -1000000] = 100.0

        rhmin_div100_np = np.divide(rhTmin_np, Array100_np)
        del rhTmin_np
        del Array100_np

        #Derive eTMax'
        dirPath_Name = tmaxDir + "\\*monavg_" + str(year) + month + "*.tif"  #Directory Path and wildcard syntax
        tmax_NC = glob.glob(dirPath_Name)
        tmax_np = raster2array(tmax_NC[0])
        Etmax_np = calc_saturation_vapor_pressure(tmax_np)
        del tmax_np

        topRight_np = np.multiply(Etmax_np, rhmin_div100_np)
        del Etmax_np
        del rhmin_div100_np

        #####################
        #Derive Full Top: (e(Tmin)[RHmax/100] + e(Tmax)[RHmin/100])
        fullTop_np = np.add(topLeft_np, topRight_np)
        del topLeft_np


        ################################
        # Divide by Create Array with value of 2.0
        Array2_np = topRight_np
        Array2_np[Array2_np > -1000000] = 2.0
        del topRight_np

        Ea_np = np.divide(fullTop_np, Array2_np)
        del fullTop_np
        del Array2_np

        return Ea_np

    except:
        messageTime = timeFun()
        print ("Error calc_Ea function - " + messageTime)
        traceback.print_exc(file=sys.stdout)
        sys.exit()


#Derive svp for Humdity Calculation at Tmax - Following  Thoma Equation Excel Spreadsheet (P9)
#SVP =610.7*10^(7.5*Tmax/(237.3+Tmax)))Tmax temps from a single day.
def calc_svpTmax_forHumdity (month, year):

    try:

        #1.Define the Tmax dataset value'
        dirPath_Name = tmaxDir + "\\*monavg_" + str(year) + month + "*.tif"  #Directory Path and wildcard syntx
        tmax_NC = glob.glob(dirPath_Name)
        tmax_np = raster2array(tmax_NC[0])

        #Create a 7.5 Array
        Array_7pt5_np = tmax_np
        Array_7pt5_np[Array_7pt5_np > -1000000] = 7.5

        #Derive (7.5 * Tmax)
        Array_7pt5_right_np = np.multiply(Array_7pt5_np, tmax_np)
        del Array_7pt5_np

        #2.Create a 237.5 Array
        Array_237pt5_np = tmax_np
        Array_237pt5_np[Array_237pt5_np > -1000000] = 237.5

        #Derive (237.5 + TMax)
        Array_237pt5_Tmax_np = np.add(Array_237pt5_np, tmax_np)
        del Array_237pt5_np

        #3.Derive (7.5 * Tmax)/(237.5 + Tmax)
        topRight_np = np.divide(Array_7pt5_right_np, Array_237pt5_Tmax_np)
        del Array_7pt5_right_np
        del Array_237pt5_Tmax_np
        del tmax_np

        #4 Derive 10^(7.5 * Tmax)/(237.5 + Tmax)
        Array10_np = topRight_np
        Array10_np[Array10_np > -1000000] = 10.0

        rs_raised10_np = np.power(Array10_np, topRight_np)
        del Array10_np
        del topRight_np

        #5 Derive: 610.7 * 10^(7.5 * Tmax)/(237.5 + Tmax)
        Array610pt7_np = rs_raised10_np
        Array610pt7_np[Array610pt7_np > -1000000] = 610.7

        svpTmax_np = np.multiply(Array610pt7_np, rs_raised10_np)
        del Array610pt7_np
        del rs_raised10_np

        return svpTmax_np

    except:
        messageTime = timeFun()
        print ("Error calc_svpTmax_forHumdity function - " + messageTime)
        traceback.print_exc(file=sys.stdout)
        sys.exit()


#Derive svp for Humdity Calculation at Tmin - Following  Thoma Equation Excel Spreadsheet (P9)
#SVP =610.7*10^(7.5*Tmin/(237.3+Tmin)))Tmin temps from a single day.
def calc_svpTmin_forHumdity (month, year):

    try:

        #1.Define the Tmin dataset value'
        dirPath_Name = tminDir + "\\*monavg_" + str(year) + month + "*.tif"  #Directory Path and wildcard syntx
        tmin_NC = glob.glob(dirPath_Name)
        tmin_np = raster2array(tmin_NC[0])

        #Create a 7.5 Array
        Array_7pt5_np = tmin_np
        Array_7pt5_np[Array_7pt5_np > -1000000] = 7.5

        #Derive (7.5 * Tmin)
        Array_7pt5_right_np = np.multiply(Array_7pt5_np, tmin_np)
        del Array_7pt5_np

        #2.Create a 237.5 Array
        Array_237pt5_np = tmin_np
        Array_237pt5_np[Array_237pt5_np > -1000000] = 237.5

        #Derive (237.5 + TMin)
        Array_237pt5_Tmin_np = np.add(Array_237pt5_np, tmin_np)
        del Array_237pt5_np

        #3.Derive (7.5 * Tmin)/(237.5 + Tmin)
        topRight_np = np.divide(Array_7pt5_right_np, Array_237pt5_Tmin_np)
        del Array_7pt5_right_np
        del Array_237pt5_Tmin_np
        del tmin_np

        #4 Derive 10^(7.5 * Tmin)/(237.5 + Tmin)
        Array10_np = topRight_np
        Array10_np[Array10_np > -1000000] = 10.0

        rs_raised10_np = np.power(Array10_np, topRight_np)
        del Array10_np
        del topRight_np

        #5 Derive: 610.7 * 10^(7.5 * Tmin)/(237.5 + Tmin)
        Array610pt7_np = rs_raised10_np
        Array610pt7_np[Array610pt7_np > -1000000] = 610.7

        svpTmin_np = np.multiply(Array610pt7_np, rs_raised10_np)
        del Array610pt7_np
        del rs_raised10_np

        return svpTmin_np

    except:
        messageTime = timeFun()
        print ("Error calc_svpTmin_forHumdity function - " + messageTime)
        traceback.print_exc(file=sys.stdout)
        sys.exit()

#Function: Derives Relative Humidity at the TMax temperature'
#Relative Humdity RH = vp from daymet / SVP
#vp: Daymat Vapour Pressure / 1000 = kpa'
def calc_RhTmax(month, year):

    try:

        #Derive svp for Humdity at Tmax' - Following Thoma Penman Excel Equation (P9); QC Code Debug Complete 20200103 - KRS
        svpTmax_np = calc_svpTmax_forHumdity(month, year)

        #Daymet VP (Water Vapor Pressure (PA) converted to (KPA); QC Code Debug Complete 20200103 - KRS
        vp_kpa_np = calc_vp_kpa(month, year)

        rhTmax_np = np.divide(vp_kpa_np, svpTmax_np)
        del vp_kpa_np
        del svpTmax_np

        return rhTmax_np

    except:
        messageTime = timeFun()
        print ("Error calc_RhTmax function - " + messageTime)
        traceback.print_exc(file=sys.stdout)
        sys.exit()

#Function: Derives Relative Humidity at the TMin temperature'
#Relative Humdity RH = vp from daymet / SVP
#vp: Daymet Vapour Pressure / 1000 = kpa'
def calc_RhTmin(month, year):

    try:
        #Derive svp for Humdity at Tmin' - Following Thoma Penman Excel Equation (P9);QC Code Debug Complete 20200103 - KRS
        svpTmin_np = calc_svpTmin_forHumdity(month, year)

        #Daymet VP (Water Vapor Pressure (PA) converted to (KPA)
        vp_kpa_np = calc_vp_kpa(month, year)

        rhTmin_np = np.divide(vp_kpa_np, svpTmin_np)
        del vp_kpa_np
        del svpTmin_np

        return rhTmin_np

    except:
        messageTime = timeFun()
        print ("Error calc_RhTmin function - " + messageTime)
        traceback.print_exc(file=sys.stdout)
        sys.exit()

#Function calculates the Water Vapour Pressure from Daymet (Pa) to unit (Kpa). Code Debug 20200102 - KRS
def calc_vp_kpa(month, year):

    try:

        dirPath_Name = vpDir + "\\*monavg_" + str(year) + month + "*.tif"  #Directory Path and wildcard syntx for the Vapour Pressure NC File'
        vp_NC = glob.glob(dirPath_Name)

        vp_np = raster2array(vp_NC[0])

        #Create a 1000.0 Array
        Array_1000_np = raster2array(vp_NC[0])
        Array_1000_np[Array_1000_np > -1000000] = 1000.0

        #Derive the Vp array in unit Kpa
        vp_kpa_np = np.divide(vp_np, Array_1000_np)
        del vp_np
        del Array_1000_np

        return vp_kpa_np


    except:
        messageTime = timeFun()
        print ("Error calc_vp_kpa function - " + messageTime)
        traceback.print_exc(file=sys.stdout)
        sys.exit()

#Function define the dataset Path for the variable of interest
#inDir - Directory with the variable datasets
#prefix - wild card syntax for file name prefix
#year - year being processed
#month - month being processed
#suffix - wild card syntax for file name suffix (e.g "*.nc", "*.tif"
def funPathName_dataset(inDir, prefix, year, month, suffix):

    outPath = inDir + prefix + str(year) + month + suffix

    return outPath


# Calculate the Net Radiation (Rn) - The net radiation (Rn) is the difference between the incoming net shortwave radiation (Rns)
# and the outgoing net longwave radiation (Rnl):
def calc_Rn(Rnl_np,Rs_np): #Completed 20180719
    # Equation 40 of ch3 FAO doc.
    # Using estimate of Rns from equation 38 :> Rns = (1-a)*Rs. a is default set to 0.25 unless a regression has been done.
    #Rns = 0.75* Rs
    #Rn = Rns - Rnl
    #return Rn

    #Create Array with 0.75
    pt75_np = Rs_np
    pt75_np[pt75_np > -1000000] = 0.75

    #Rns = 0.75* Rs
    Rns_np = np.multiply(pt75_np, Rs_np)
    del pt75_np

    #Rn = Rns - Rnl
    Rn_np = np.subtract(Rns_np,Rnl_np)
    del Rns_np
    del Rnl_np

    return Rn_np


def calc_Rs(Ra_NP, year, month, N_np): # Equation 35 - Completed 20180706 - I believe this is the equivalent of the Daymet sRad data product so
    # the calculation is not needed if using Daymet - KRS
    # Ra = extra-terrestrial radiation as calc by equation 21 in MJ/m2/day.
    # Rs = MJ/m2/day
    # n = actual duration of sunshine (hours)
    # N = maximum possible duration of sunshine (hours)
##    a = 0.25 # Regression constant expressing fraction of extra-terrestrial radiation reaching the earth on overcast days
##    b = 0.5 # a + b = fraction of extra-terrestrial radiation reaching earth on clear days.
##    # These default values were taken from FAO Ch3 page 23.
##    ratio = float(n/N)
##    bracket_term = (ratio * b) + a
##    Rs = bracket_term * Ra
##    return Rs

    dirPath_Name = dayl + "\\*MonthlyAvg_" + str(year) + month + "*.nc"  'Directory Path and wildcard syntx for the Daylength NC File'
    daylength_NC = glob.glob(dirPath_Name)

    n_np = raster2array(daylength_NC[0])

    #Create float type array of the Daylength raster
    n_np_float = np.float(n_np)
    del n_np

    #Create float type array of maximum possible duration of sunshine
    N_np_float = np.float(N_np)
    del N_np

    # These default values were taken from FAO Ch3 page 23.
    a = 0.25 # Regression constant expressing fraction of extra-terrestrial radiation reaching the earth on overcast days
    b = 0.5 # a + b = fraction of extra-terrestrial radiation reaching earth on clear days.


    #Create Array with the a cloudy day component
    a_np = raster2array(daylength_NC)

    a_np[a_np > -999] = a


    #Create Array with the b component
    b_np = raster2array(daylength_NC)
    b_np[b_np > -999] = b

    ratio_np = np.divide(n_np_float, N_np_float)
    del n_np_float
    del N_np_float

    leftBracket_np = Numpy.Multipy(ratio_np, b_np)
    del b_np

    fullBracket_np = Numpy.Add(leftBracket_np, a_np)
    del a_np
    del leftBracket_np

    #Final Rs array'
    Rs_np = np.Multiply(fullBracket_np, Ra_NP)
    del fullBracket_np
    #del Ra_NP

    return Rs_np

    #Clear-sky solar radiation (Rso)
def calc_Rso(elevation,Ra_np): #Completed 20180706; Debug Code Complete 20200102
    # Equation 37 in ch3 of FAO doc.
    # Ra as calc from equation 21.
    # Elevation in meters
    #elevation = float(elevation)
    #correction_term = (.00002 * elevation) + .75
    #Rso = Ra * correction_term
    #return Rso

    elevation_np = raster2array(elevation)

    np_pt00002 = raster2array(elevation)
    np_pt00002[np_pt00002 > -100000] = 0.00002

    cor_term_left_np = np.multiply(elevation_np, np_pt00002)
    del elevation_np
    del np_pt00002

    np_pt75 = raster2array(elevation)
    np_pt75[np_pt75 > -100000] = 0.75


    cor_term_Full_np = np.add(cor_term_left_np, np_pt75)
    del cor_term_left_np
    del np_pt75

    Rso_np = np.multiply(Ra_np, cor_term_Full_np)

    return Rso_np

# Calc Solar Declination for mid monthly value used in Penman ET Calculation
def calc_solar_declination_Penman(month):
##    doy = float(doy)
##    bracket_term = (((2*pi)/365) * doy) - 1.39
##    retval = .409 * np.sin(bracket_term)
##    return retval # radians


    doy = dayYearMidMonth(month)
    bracket_term = (((2*np.pi)/365) * doy) - 1.39
    retval = .409 * np.sin(bracket_term)
    return retval

def calc_daylength(sunset_hour_angle_NP): #equation 34 Maximu Daylight Hours
    #N = (24/pi)*sunset_hour_angle

    leftSideVal = (24/np.pi)
    N_np = np.multiply(sunset_hour_angle_NP,leftSideVal)
    return N_np



def calc_sunset_hour_angle(latitude, month): #
    #Both Latitude and Solar Declination need to be in radians

    #Convert Latitude Raster to Numpy Array
    latitude_NP = raster2array(latitude)

    #Derive the Latitude in Radians
    latitudeRadian_NP = np.radians(latitude_NP)
    del latitude_NP

    #############################
    #Derive the Solar Declination
    out_Solar_Declination = calc_solar_declination_Penman(month)

    #Create the solar_delcination_NP array
    solar_declination_NP = raster2array(latitude)
    solar_declination_NP[solar_declination_NP > -999] = out_Solar_Declination
    ############################

    bracket_term = np.tan(latitudeRadian_NP) * -1 * np.tan(solar_declination_NP)

    del latitudeRadian_NP
    del solar_declination_NP

    sunset_hour_angle_NP = np.arccos(bracket_term)
    return sunset_hour_angle_NP #radians
def calc_inverse_rel_distance(month): #Using the Mid Month Day value due to monthly calculation in place of daily

    midMonthDay = dayYearMidMonth(month)
    doy = float(midMonthDay)

    bracket_term = ((2*np.pi)/365) * doy
    retval = (.033 * np.cos(bracket_term)) + 1
    return retval #radians

def calc_Ea_with_humidity_data(tmax, tmin, RHmean):#Function is only used if their is humidity data - Daymet doesn't have humidity data- Not being used.
##    #Equation 19 of chap3 in FAO doc
##    #RHmean must be a %. It is reduced to decimal below.
##    RHmean = float(RHmean)
##    E_tmax = calc_saturation_vapor_pressure(tmax)
##    E_tmin = calc_saturation_vapor_pressure(tmin)
##    bracket_term = (E_tmax + E_tmin)/2
##    left_term = RHmean / 100
##    Ea = left_term * bracket_term
##    return Ea

    out_Path = funPathName_dataset(tmax, "\\*MonthlyAvg_", year, month, "*.nc")
    datasetGlob = glob.glob(out_Path)
    'Create the Numpy Array'
    tmax_np = raster2array(datasetGlob[0])
    E_tmax = satVapourPressure(tmax_np, month, year)


    out_Path = funPathName_dataset(tmin, "\\*MonthlyAvg_", year, month, "*.nc")
    datasetGlob = glob.glob(out_Path)
    'Create the Numpy Array'
    tmin_np = raster2array(datasetGlob[0])
    E_tmin = satVapourPressure(tmin, month, year)

    #(E_tmax + E_tmin)
    add_Etmin_Etmax_NP = np.add(E_tmax, E_tmin)
    del E_tmax
    del E_tmin

    #Create array with value 2.0
    np2 = raster2array(datasetGlob[0])
    np2[np2 > -1000000] = 2.0


    #bracket_term = (E_tmax + E_tmin)/2
    braket_term_NP = np.divide(add_Etmin_Etmax_NP,np2)
    del add_Etmin_Etmax_NP
    del np2

    ################## - Functionality for deriving Ea with humidty data has not been developed KRS 20180712
    RHmean = float(RHmean)


    left_term = RHmean / 100
    Ea = left_term * bracket_term
    return Ea


if __name__ == '__main__':

    # Analyses routine ---------------------------------------------------------
    main()
