# Import arcpy and required modules
import arcpy, DMScriptingTools, os, sys, time, traceback

# Set arcpy environment variables
arcpy.env.overwriteOutput = True

# Get environment variables
defmapHome = DMScriptingTools.getEnvVar("DEFMAPHOME")

# Get installed version string
version = ""
temp = defmapHome.split("EsriDefenseMapping")
version = temp[1]

# Create logging object
loggingDir = DMScriptingTools.getEnvVar("APPDATA") + os.sep + "ESRI" + os.sep + version + os.sep + "Workstation" + os.sep + "Logs"
logger = DMScriptingTools.Logger(loggingDir, "SplitFeatures.txt")

# Script arguments...
logger.log("******************************************************")
logger.log("Listing script arguments...")
selectedCells = sys.argv[1]
logger.log("Selected Cells: " + selectedCells)
selectedCells = selectedCells.split(";")
jobConnection = sys.argv[2]
logger.log("Job Connection: " + jobConnection)
schemaName = sys.argv[3]
logger.log("Schema Name: " + schemaName)
extractionGrid = sys.argv[4]
logger.log("Extraction Grid: " + extractionGrid)
gridAttribute = sys.argv[5]
logger.log("Grid Attribute: " + gridAttribute)

# Check out any necessary licenses
logger.log("******************************************************")
logger.log("Checking out licenses...")
extensionList = ["Defense"]
for extension in extensionList:
    retVal = arcpy.CheckOutExtension(extension)
    if retVal != "CheckedOut":
        logger.log("Could not get extension: " + extension + "; return code: " + retVal)
    else:
        logger.log("Got extension: " + extension)

# Load required toolboxes
logger.log("******************************************************")
logger.log("Loading toolboxes...")
arcpy.ImportToolbox(defmapHome + os.sep + "ArcToolbox" + os.sep + "Toolboxes" + os.sep + "Defense Mapping Tools.tbx", "defense")

success = False

try:
    logger.log("******************************************************")
    logger.log("Beginning step processing...")

    # Get list of layers for feature classes in datasets and stand alone feature classes to be split
    arcpy.env.workspace = jobConnection
    datasetList = arcpy.ListDatasets('*{}*'.format(schemaName), "Feature")
    featureClassList = arcpy.ListFeatureClasses('*{}*'.format(schemaName))
    featuresToSplit = ""
    if len(datasetList) > 0:
        for dataset in datasetList:
            featureClasses = arcpy.ListFeatureClasses("", "ALL", dataset)
            for f in featureClasses:
                desc = arcpy.Describe(f)
                if desc.featureType == "Simple" and (desc.shapeType == "Polyline" or desc.shapeType == "Polygon") :
                    featuresToSplit = featuresToSplit + desc.catalogPath + ";"
    if len(featureClassList) > 0:
        for f in featureClassList:
            desc = arcpy.Describe(f)
            if desc.featureType == "Simple" and (desc.shapeType == "Polyline" or desc.shapeType == "Polygon"):
                featuresToSplit = featuresToSplit + desc.catalogPath + ";"
    if featuresToSplit[len(featuresToSplit)-1] == ";":
        featuresToSplit = featuresToSplit[:-1]

    # Create AOI layer
    aoiLyr = arcpy.management.MakeFeatureLayer(extractionGrid, "extractionGrid")

    for s in selectedCells:
        logger.log("Processing selected cell: " + s)
        # Get AOI selection
        arcpy.management.SelectLayerByAttribute(aoiLyr, "NEW_SELECTION", gridAttribute + " = '" + s + "'")
        logger.log("Splitting layers...")
        arcpy.defense.SplitFeatures(aoiLyr, featuresToSplit, "USE_TARGET_Z")

    # Finish
    logger.log("******************************************************")
    logger.log("Cleaning up layers and temporary items...")
    arcpy.Delete_management(aoiLyr)
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
    if success == True:
        sys.exit(1)
    else:
        sys.exit(0)
