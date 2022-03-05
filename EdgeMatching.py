# Import arcpy and required modules
import arcpy, DMScriptingTools, getpass, glob, os, shutil, sys, time, traceback, uuid

# Set arcpy environment variables
arcpy.env.overwriteOutput = True

# Get environment workspace
envWorkspace = arcpy.env.workspace

# Get environment variables
arcgisHome = DMScriptingTools.getEnvVar("DEFMAPARCGISHOME")
defmapHome = DMScriptingTools.getEnvVar("DEFMAPHOME")

# Get installed version string
version = ""
temp = defmapHome.split("EsriDefenseMapping")
version = temp[1]

# Create logging object
loggingDir = DMScriptingTools.getEnvVar("APPDATA") + os.sep + "ESRI" + os.sep + version + os.sep + "Workstation" + os.sep + "Logs"
logger = DMScriptingTools.Logger(loggingDir, "CreateOuterEdgeMatchStrip.txt")

# Script arguments
logger.log("******************************************************")
logger.log("Listing script arguments...")
jobID = sys.argv[1]
logger.log("Job ID: " + jobID)
features = sys.argv[2]
logger.log("Input Feature List: " + features)
jobConnection = sys.argv[3]
logger.log("Job Version SDE Connection: " + jobConnection)
jobAOI = sys.argv[4]
logger.log("Job AOI Feature Class: " + jobAOI)
aoiBuffer = sys.argv[5]
logger.log("AOI Buffer: " + aoiBuffer)
targetGDB = sys.argv[6]
logger.log("Target Geodatabase: " + targetGDB)
templateDatabase = sys.argv[7]
logger.log("Template Geodatabase: " + templateDatabase)
schemaName = sys.argv[8]
logger.log("Schema Name: " + schemaName)
gridLookup = sys.argv[9]
logger.log('Grid Lookup: {}'.format(gridLookup))

# Set the necessary product code
logger.log("******************************************************")
logger.log("Setting product code...")
retVal = arcpy.SetProduct("ArcInfo")
if retVal == "CheckedOut" or retVal == "AlreadyInitialized":
    logger.log("Got product successfully.")
else:
    logger.log("Could not get required product license.")

# Check out any necessary licenses
logger.log("******************************************************")
logger.log("Checking out licenses...")
extensionList = ["Foundation"]
for extension in extensionList:
    retVal = arcpy.CheckOutExtension(extension)
    if retVal != "CheckedOut":
        logger.log("Could not get extension: " + extension + "; return code: " + retVal)
    else:
        logger.log("Got extension: " + extension)

# Load required toolboxes
logger.log("******************************************************")
logger.log("Loading toolboxes...")
arcpy.ImportToolbox(arcgisHome + os.sep + "ArcToolbox" + os.sep + "Toolboxes" + os.sep + "Analysis Tools.tbx", "analysis")
arcpy.ImportToolbox(defmapHome + ".." + os.sep + ".." + os.sep + "EsriProductionMapping" + os.sep + version + os.sep + "ArcToolbox" + os.sep + "Toolboxes" + os.sep + "Production Mapping Tools.tbx", "production")

# Create a job-specific temporary/scratch GDB
logger.log("******************************************************")
logger.log("Creating scratch workspace...")
scratchDir = DMScriptingTools.getEnvVar("APPDATA") + os.sep + "ESRI" + os.sep + version + os.sep + "Workstation" + os.sep + "Scratch"
scratchGDB = DMScriptingTools.ScratchGDB(scratchDir, "Temp_" + jobID)
scratchGDBLocation = scratchGDB.gdb()
logger.log("Created temporary GDB")

# Create required functions
#
#
# Function to iterate through feature classes and remove features outside of the AOI
def RemoveUnwantedFeatures(fc, select, count):
    # Make feature layer from current fc
    lyr = "lyr_" + str(count) + time.strftime("%Y%m%d_%H%M%S")
    arcpy.MakeFeatureLayer_management(fc, lyr)
    # Select features to delete
    arcpy.SelectLayerByLocation_management(lyr, "WITHIN", select, "", "NEW_SELECTION")
    # Delete selected features
    featCount = int(arcpy.GetCount_management(lyr).getOutput(0))
    if (featCount > 0):
        arcpy.DeleteFeatures_management(lyr)
    # Delete layer
    arcpy.Delete_management(lyr)
#
# Function to remove topologies
def RemoveTopologies():
    topologyList = arcpy.ListDatasets("*", "Topology")
    for t in topologyList:
        #arcpy.AddMessage("Deleting topology: " + t)
        arcpy.Delete_management(t)

success = False

try:
    logger.log("******************************************************")
    logger.log("Beginning step processing...")

    # Set local temp folder
    userName = getpass.getuser()
    tempFolder = ''
    if 'TEMP' in os.environ:
        tempFolder = os.getenv('TEMP')
    else:
        tempFolder = r'C:\users\{0}\Documents\ArcGIS'.format(userName)
    tempFolder = tempFolder.rstrip('\\')
    logger.log("Local temp folder: " + tempFolder)

    # Set local variables
    aoiBuffer = aoiBuffer.strip()
    tempAOI = scratchGDBLocation + os.sep + "tempAOI"
    outputBuffer = tempAOI + "_BUFFER"
    outputErase = tempAOI + "_ERASE"

    # Select Job ID
    jobAOILyr = arcpy.MakeFeatureLayer_management(jobAOI, "jobAOI_" + time.strftime("%Y%m%d_%H%M%S"), "JOB_ID = " + jobID)
    arcpy.CopyFeatures_management(jobAOILyr, tempAOI)
    arcpy.Delete_management(jobAOILyr)
    logger.log("Job AOI copied for processing.")

    # Buffer user specified value inside cell
    arcpy.Buffer_analysis(tempAOI, outputBuffer, aoiBuffer)

    isInside = 0;
    if aoiBuffer[0] == '-':
        isInside = 1

    if isInside == 1:
        # Erase Buffer from JOB AOI
        # Store erased buffer as selection variable
        arcpy.Erase_analysis(tempAOI, outputBuffer, outputErase)
        select = outputBuffer
        logger.log("Processed inside buffer")
    else:
        # Erase JOB AOI from buffer
        arcpy.Erase_analysis(outputBuffer, tempAOI, outputErase)
        # Store erased JOB AOI as selection variable
        select = tempAOI
        logger.log("Processed outside buffer")

    # Get list of grid feature classes and reference grid information
    gridFeatures = []
    query = "SCHEMA_NAME = '{}'".format(schemaName)
    fields = ['GRID_NAME']
    try:
        with arcpy.da.SearchCursor(gridLookup, fields, query) as cur:
            for row in cur:
                gridFeatures.append(row[0].upper())
    except Exception, e:
        logger.log('{}'.format(e))
        raise Exception ('Error: Unable to search operational grid records.')

    # Build list of items to export
    itemsToExport = ""
    if features.find("#") == -1 and bool(features) == True:
        itemsToExport = features
    else:
        arcpy.env.workspace = jobConnection
        datasetList = arcpy.ListDatasets('*{}*'.format(schemaName), "Feature")
        featureClassList = arcpy.ListFeatureClasses('*{}*'.format(schemaName))
        # Filter grid feature classes from feature class list
        i = 0
        while i < len(featureClassList):
            temp = featureClassList[i].split('.')
            if temp[len(temp) - 1].upper() in gridFeatures:
                del featureClassList[i]
            else:
                i += 1

        if len(datasetList) > 0:
            for s in datasetList:
                items = arcpy.ListFeatureClasses("", "", s)
                for item in items:
                    itemsToExport = itemsToExport + s + os.sep + item + " USE_FILTERS;"
        if len(featureClassList) > 0:
            for s in featureClassList:
                itemsToExport = itemsToExport + s + " USE_FILTERS;"
        if itemsToExport[len(itemsToExport)-1] == ";":
            itemsToExport = itemsToExport[:-1]

    # Extract Data
    extractAOILyr = arcpy.MakeFeatureLayer_management(outputErase, "extractAOILyr_" + time.strftime("%Y%m%d_%H%M%S"))
    arcpy.SelectLayerByAttribute_management(extractAOILyr, "NEW_SELECTION", "(JOB_ID = " + str(jobID) + ")")
    # Create the output FGDB if it does not exist
    tempOutput = tempFolder + os.sep + "Job_" + jobID + ".gdb"
    # Create the temp FGDB
    if os.path.exists(tempOutput):
        shutil.rmtree(tempOutput)
        logger.log("Existing temp replica geodatabase deleted.")
    if not os.path.exists(templateDatabase):
        raise Exception("Error: Source geodatabase not found.")
    else:
        arcpy.management.Copy(templateDatabase, tempOutput)
        logger.log("Template geodatabase copied to temp folder.")

    logger.log("Extracting data...")
    arcpy.ExtractData_production(itemsToExport, tempOutput, "REUSE", "FILTER_BY_GEOMETRY", "INTERSECTS", extractAOILyr)
    logger.log("Data extract completed.")

    # Run RemoveUnwantedFeatures on each feature class in the edgematch (output) DB
    logger.log("Removing features not needed for edgematch strip...")
    arcpy.env.workspace = tempOutput
    # First, remove any topologies from the workspace (for performance reasons)
    RemoveTopologies()
    fcList = arcpy.ListFeatureClasses("*")
    count = 0
    for fc in fcList:
        logger.log("Processing feature class: " + fc)
        RemoveUnwantedFeatures(fc, select, count)
        count = count + 1
    dsList = arcpy.ListDatasets("*")
    for ds in dsList:
        logger.log("Processing dataset: " + ds)
        arcpy.env.workspace = tempOutput + os.sep + ds
        # First, remove any topologies from the dataset (for performance reasons)
        RemoveTopologies()
        fcList = arcpy.ListFeatureClasses("*")
        for fc in fcList:
            arcpy.AddMessage("Processing feature class: " + fc)
            RemoveUnwantedFeatures(fc, select, count)
            count = count + 1

    # Copy fgdb to job artifacts
    logger.log("Moving local fgdb to job directory...")
    if not os.path.exists(targetGDB):
        os.mkdir(targetGDB)
        files = glob.glob(r'{}\*'.format(tempOutput))
        for f in files:
            if os.path.isfile(f) and '.lock' not in f:
                shutil.copyfile(f, r'{0}\{1}'.format(targetGDB, os.path.basename(f)))

    # Finish
    logger.log("******************************************************")
    logger.log("Cleaning up layers and temporary items...")
    arcpy.Delete_management(extractAOILyr)
    arcpy.Delete_management(scratchGDBLocation)
    del scratchGDB
    logger.log("arcpy messages: " + arcpy.GetMessages(1))
    logger.log("Script SUCCEEDED\n")

    success = True

except arcpy.ExecuteError:
    msgs = arcpy.GetMessage(0)
    msgs += arcpy.GetMessages(2)
    arcpy.AddError("arcpy messages: " + msgs)
    logger.log("arcpy messages: " + msgs)
    logger.log("Script FAILED\n")
except:
    tb = sys.exc_info()[2]
    tbinfo = traceback.format_tb(tb)[0]
    pymsg = tbinfo + "\n" + str(sys.exc_type)+ ": " + str(sys.exc_value)
    arcpy.AddError("arcpy messages: " + pymsg)
    logger.log("arcpy messages: " + pymsg)
    logger.log("Script FAILED\n")
finally:
    arcpy.env.workspace = envWorkspace
    if success == True:
        sys.exit(1)
    else:
        sys.exit(0)
