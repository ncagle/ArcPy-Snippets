# Import arcpy and required modules
import arcpy, DMScriptingTools, os, string, sys, traceback

# Get environment variables
defmapHome = DMScriptingTools.getEnvVar("DEFMAPHOME")

# Get installed version string
version = ""
temp = defmapHome.split("EsriDefenseMapping")
version = temp[1]

# Create logging object
loggingDir = DMScriptingTools.getEnvVar("APPDATA") + os.sep + "ESRI" + os.sep + version + os.sep + "Workstation" + os.sep + "Logs"
logger = DMScriptingTools.Logger(loggingDir, "SplitProducitonAOI.txt")

# Script arguments...
logger.log("******************************************************")
logger.log("Listing script arguments...")
job_id = sys.argv[1]
logger.log("Job ID: " + job_id)
rows = sys.argv[2]
logger.log("Number of rows: " + rows)
columns = sys.argv[3]
logger.log("Number of columns: " + columns)
child_count_ext_prop_name = sys.argv[4]
logger.log("Child count extended property: " + child_count_ext_prop_name)
child_list_ext_prop_name = sys.argv[5]
logger.log("Child list extended property: " + child_list_ext_prop_name)
child_count_ext_prop_table = sys.argv[6]
logger.log("Child count extended property table: " + child_count_ext_prop_table)
grid_cell_ids = sys.argv[7]
logger.log("Grid Cell IDs: " + grid_cell_ids)
grid_cell_id_column_name = sys.argv[8]
logger.log("Cell ID Column Name: " + grid_cell_id_column_name)
dataset_srf_fc = sys.argv[9]
logger.log("Dataset Surface Feature Class: " + dataset_srf_fc)
parent_grid_cell_id_column_name = sys.argv[10]
logger.log("Parent Cell ID Column Name: " + parent_grid_cell_id_column_name)
split_dataset_srf_fc = sys.argv[11]
logger.log("Split Dataset Surface Feature Class: " + split_dataset_srf_fc)

# Create scratch workspace
scratch_dir = DMScriptingTools.getEnvVar("APPDATA") + os.sep + "ESRI" + os.sep + version + os.sep + "Workstation" \
              + os.sep + "Scratch"
scratch_gdb = DMScriptingTools.ScratchGDB(scratch_dir, "SplitProductionAOI")
scratch_gdb_location = scratch_gdb.gdb()

try:
    logger.log("******************************************************")
    logger.log("Beginning step processing...")

    # Setting up
    arcpy.env.workspace = scratch_gdb_location
    cell_list = ''

    # Loop through the cells for the job
    grid_cell_id_list = grid_cell_ids.split(";")
    for grid_cell_id in grid_cell_id_list:
        logger.log("Splitting grid cell: " + str(grid_cell_id))
        grid_cell_layer = "GridCellLayer"
        grid_cell_where_clause = grid_cell_id_column_name + " = '" + grid_cell_id + "'"
        with arcpy.da.SearchCursor(dataset_srf_fc, "SHAPE@", grid_cell_where_clause) as grid_cell_cursor:
            for grid_cell_row in grid_cell_cursor:
                grid_cell_geometry = grid_cell_row[0]

                # Building fishnet
                logger.log("Splitting grid cell " + grid_cell_id + " by " + str(rows) + " x " + str(columns))
                fishnet_fc = "Fishnet_" + grid_cell_id
                origin_coord = str(grid_cell_geometry.extent.XMin) + " " + str(grid_cell_geometry.extent.YMin)
                y_axis_coord = str(grid_cell_geometry.extent.XMin) + " " + str(grid_cell_geometry.extent.YMax)
                arcpy.CreateFishnet_management(fishnet_fc, origin_coord, y_axis_coord, "", "", rows, columns, "",
                                               "NO_LABELS", grid_cell_geometry.extent, "POLYGON")

                # Joining attributes
                logger.log("Joining grid cell attributes with split features")
                dataset_srf_layer = "DatasetSrfLayer_" + grid_cell_id
                joined_layer = "JoinedLayer_" + grid_cell_id
                arcpy.MakeFeatureLayer_management(dataset_srf_fc, dataset_srf_layer, grid_cell_where_clause)
                arcpy.SpatialJoin_analysis(fishnet_fc, dataset_srf_layer, joined_layer)

                # Adding parent cell identifier field
                logger.log("Adding parent cell identifier to split features")
                arcpy.AddField_management(joined_layer, parent_grid_cell_id_column_name, "TEXT", 20)

                # Setting cell identifier and parent cell identifier values
                logger.log("Setting the parent cell identifier values")
                arcpy.CalculateField_management(joined_layer, parent_grid_cell_id_column_name, "!"
                                                + grid_cell_id_column_name + "!", "PYTHON_9.3")

                logger.log("Setting the cell identifier values")
                arcpy.CalculateField_management(joined_layer, grid_cell_id_column_name, "!"
                                                + grid_cell_id_column_name + '! + "_" + str(!OBJECTID!)', "PYTHON_9.3")

                # Delete any splits in the current split feature class that have the same parent
                logger.log("Deleting any split features that currently have the same parent id")
                delete_where_clause = parent_grid_cell_id_column_name + " = '" + grid_cell_id + "'"
                delete_layer = "DeleteLayer_" + grid_cell_id
                arcpy.MakeFeatureLayer_management(split_dataset_srf_fc, delete_layer, delete_where_clause)
                arcpy.DeleteFeatures_management(delete_layer)

                # Append new split features
                logger.log("Appending split features to the split dataset surface feature class")
                arcpy.Append_management(joined_layer, split_dataset_srf_fc, "NO_TEST")

                # Update cell list
                logger.log("Updating cell list.")
                split_dataset_where_clause = parent_grid_cell_id_column_name + " = '" + grid_cell_id + "'"
                with arcpy.da.SearchCursor(split_dataset_srf_fc, grid_cell_id_column_name, split_dataset_where_clause) as split_dataset_cursor:
                    for split_dataset_row in split_dataset_cursor:
                        cell_list = '{};{}'.format(cell_list,split_dataset_row[0])

                # Cleanup
                arcpy.Delete_management(dataset_srf_layer)
                arcpy.Delete_management(joined_layer)
                arcpy.Delete_management(delete_layer)

    # Cleanup cell list
    cell_list = cell_list.lstrip(';')

    # Setting child job tracking properties
    number_of_children = int(rows) * int(columns) * len(grid_cell_id_list)
    logger.log("Setting number of children for the job to " + str(number_of_children))
    child_count_ext_prop_layer = "ChildCountExtPropLayer"
    child_count_where_clause = "JOB_ID = " + str(job_id)
    arcpy.MakeTableView_management(child_count_ext_prop_table, child_count_ext_prop_layer, child_count_where_clause)
    arcpy.CalculateField_management(child_count_ext_prop_layer, child_count_ext_prop_name, number_of_children,
                                    "PYTHON_9.3")
    logger.log("Setting cell list to " + cell_list)
    arcpy.CalculateField_management(child_count_ext_prop_layer, child_list_ext_prop_name, "\"" + cell_list + "\"",
                                    "PYTHON_9.3")
    arcpy.Delete_management(child_count_ext_prop_layer)

    # Cleanup
    logger.log("******************************************************")
    logger.log("Cleaning up layers and temporary items...")
    arcpy.Delete_management(scratch_gdb_location)
    del scratch_gdb

    # Finish
    logger.log("******************************************************")
    logger.log("arcpy messages: " + arcpy.GetMessages(1))
    logger.log("Script SUCCEEDED\n")

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
