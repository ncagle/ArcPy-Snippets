### Walk SDE and count features in feature classes
import arcpy
import os
from arcpy import AddMessage as write

# Set workspace
SDE = r"T:\Database Connections\reference_for_stuff.sde"
arcpy.env.workspace = SDE
feature_classes = []

walk = arcpy.da.Walk(SDE, datatype="FeatureClass", type="All")
write("Starting..")
for dirpath, dirnames, filenames in walk:
	for filename in filenames:
		write(filename)
		filepath = os.path.join(dirpath, filename)
		feature_classes.append(filepath)
		count = int(arcpy.GetCount_management(filename).getOutput(0))
		write('{0} has {1} records'.format(filename, count))‍‍‍‍‍‍‍‍‍‍‍‍‍‍‍‍‍‍



### Append feature classes using cursors
fc = r"C:\input.gdb\newRoads"
fc_out = r"C:\out.gdb\Roads"
#Collect all fields except the Geometry field
dsc = arcpy.Describe(fc)
fields = dsc.fields
out_fields = [dsc.OIDFieldName, dsc.lengthFieldName, dsc.areaFieldName] # List of field names for OID, length, and area
# Create list of field names that aren't Geometry or in out_fields
field_list = [field.name for field in fields if field.type not in ['Geometry'] and field.name not in out_fields]
field_list[:] = [x for x in field_list if 'Shape' not in x and 'shape' not in x] # Make sure to clean the list for all possible geometry standards including ST_Geometry
field_list[:] = [x for x in field_list if 'area' not in x and 'length' not in x]
field_list.append("SHAPE@") # add the full Geometry object
# Nested Search/Insert cursors for input/output feature classes to copy all rows with specified fields and geometry
with arcpy.da.SearchCursor(fc, field_list) as scursor:
	with arcpy.da.InsertCursor(fc_out, field_list) as icursor:
		for row in scursor:
			icursor.insertRow(row)



# Finds empty fields and NULL geometry.
populated = lambda x: x is not None and str(x).strip() != ''
fc_fields = ['foobar', 'SHAPE@']
with arcpy.da.SearchCursor(fc, fc_fields) as scursor:
	for row in scursor:
		if row[-1] is None:
			pass # NULL Geometry
		if not populated(row[0]):
			pass # Field is NULL or empty

# Remove Nones from a list
cleaned_list = list(filter(None, filenames))



def debug_view(**kwargs): # Input variable to view info in script output
	# Set x_debug = False outside of loop where x is defined
	# Set repeat = False to output for only the first loop or repeat = True to output for every loop
	# Example:
	#foo_debug = False
	#for fc in fc_list:
	#    foo = 'bar'
	#    debug_view(foo=foo,repeat=False)
	#
	#>>> ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	#    Debug info for foo:
	#       Variable Type: <class 'str'>
	#       Assigned Value: 'bar'
	#    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
	arg_list = kwargs.keys() # Python 2: kwargs.keys()  # Python 3: list(kwargs.keys())
	arg_list.remove('repeat')
	while not globals()[arg_list[0] + "_debug"]:
		write("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
		write("Debug info for {0}:".format(arg_list[0]))
		write("   Variable Type: {0}".format(type(kwargs[arg_list[0]])))
		write("   Assigned Value: {0}".format(kwargs[arg_list[0]]))
		write("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
		if not kwargs['repeat']:
			globals()[arg_list[0] + "_debug"] = True
		else:
			return



# Write information for given variable
def write_info(name,var): # write_info('var_name',var)
	write("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
	write("Debug info for {0}:".format(name))
	write("   Variable Type: {0}".format(type(var)))
	write("   Assigned Value: {0}".format(var))
	write("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")



# Time a process
def runtime(start,finish):
	# Add a start and finish variable markers surrounding the code to be timed
	#from datetime import datetime as dt
	#start/finish = dt.now()
	# Returns string of formatted elapsed time between start and finish markers
	time_delta = (finish - start).total_seconds()
	h = int(time_delta/(60*60))
	m = int((time_delta%(60*60))/60)
	s = time_delta%60.
	time_elapsed = "{}:{:>02}:{:>05.5f}".format(h, m, s)
	return time_elapsed



def get_count(fc_layer):
    results = int(ap.GetCount_management(fc_layer).getOutput(0))
    return results



def update_row_tuple(urow, index, val):
	# For short tuples, slicing and concatenation is faster.
	# But performance of long tuples is more consistently efficient with list conversion.
	edit_row = list(urow)
	edit_row[index] = val
	return tuple(edit_row)



def find_dupes(fc, check_field, update_field):
    with arcpy.da.SearchCursor(fc, [check_field]) as scursor:
        values = [srow[0] for srow in scursor]

    with arcpy.da.UpdateCursor(fc, [check_field, update_field]) as ucursor:
        for urow in ucursor:
            if values.count(urow[0]) > 1:
                urow[1] = 'Y'
            else:
                urow[1] = 'N'
            ucursor.updateRow(urow)



def copy_fc(source, target, *args, **kwargs): #(s_f)ields, (s_q)uery, (t_f)ields, (t_q)uery
	# copy_fc(source_var, target_var, s_f=s_fields, s_q=s_query, t_f=t_fields, t_q=t_query)
    s_fields = kwargs.get('s_f', "'*'") # Default s_fields variable will be '*' for all fields
    s_query = kwargs.get('s_q', "''")
    t_fields = kwargs.get('t_f', "'*'") # Default t_fields variable will be '*' for all fields
    t_query = kwargs.get('t_q', "''")

	with arcpy.da.SearchCursor(source, s_fields, s_query) as scursor:
		with arcpy.da.InsertCursor(target, t_fields, t_query) as icursor:
			for row in scursor:
				icursor.insertRow(row)



# Conversion toolset
@gptooldoc('LoadData_production', None)
def LoadData(in_cross_reference=None, in_sources=None, in_target=None, in_dataset_map_defs=None, row_level_errors=None):
    """LoadData_production(in_cross_reference, in_sources;in_sources..., in_target, {in_dataset_map_defs;in_dataset_map_defs...}, {row_level_errors})

        Moves features from one schema to another by loading data from a
        source to a target workspace.  Data mapping rules described in a
        cross-reference database are applied during the load. All Esri Mapping
        and Charting solutions products install a cross-reference database
        that you can use. You can create a cross-reference database using the
        Create Cross-reference tool.Data that matches the schema defined in
        the cross-reference database
        for the source is appended to the target workspace. The cross-
        reference database contains a DatasetMapping table that lists pairs of
        source and target dataset names. Each source and target name pair can
        have a WHERE clause and a subtype. The WHERE clause defines a subset
        of features in the source to append to the target. Subtype identifies
        a subtype in the target feature class into which features are loaded.

     INPUTS:
      in_cross_reference (Workspace):
          The path to a cross-reference database. Cross-reference databases for
          each product specification reside in the <install location>\\SolutionNa
          me\\Desktop10.2\\[ProductName]\\[SpecificationName]\\DataConversion
          directory.
      in_sources (Workspace):
          A list of workspaces that contain the source features to load into the
          target workspace.
      in_target (Workspace):
          The target workspace that contains the schema referenced in the cross-
          reference database. Source features are loaded into this workspace.
      in_dataset_map_defs {String}:
          The source to target feature class mapping list. The format of this
          string is id | SourceDataset | TargetDataset | WhereClause | Subtype.
      row_level_errors {Boolean}:
          Indicates if the tool will log errors that occur while inserting new
          rows into feature classes and tables in the in_target parameter.

          * ROW_LEVEL_ERROR_LOGGING-Log errors that occur during individual row-
          level inserts. This is the default.

          * NO_ROW_LEVEL_ERROR_LOGGING-Do not log errors that occur during
          individual row-level inserts."""
    from arcpy.geoprocessing._base import gp, gp_fixargs
    from arcpy.arcobjects.arcobjectconversion import convertArcObjectToPythonObject
    try:
        retval = convertArcObjectToPythonObject(gp.LoadData_production(*gp_fixargs((in_cross_reference, in_sources, in_target, in_dataset_map_defs, row_level_errors), True)))
        return retval
    except Exception as e:
        raise e



import arcpy
fc_list = [a list of FCs that you want to merge together]
output_fc = r"C:\temp\test.gdb\merge"
for fc in fc_list:
	write("Appending {0} to output feature class".format(fc))
	if fc_list.index(fc) == 0:
		arcpy.CopyFeatures_management(fc, output_fc)
		icursor = arcpy.da.InsertCursor(output_fc, ["SHAPE@","*"])
	else:
		with arcpy.da.SearchCursor(fc, ["SHAPE@","*"]) as scursor:
			for srow in scursor:
				icursor.insertRow(srow)
del icursor



# Gets messages from the ArcGIS tools ran and sends messages to dialog
def writeresults():
    messages = GetMessages(0)
    warnings = GetMessages(1)
    errors = GetMessages(2)
    AddMessage(messages)
    if len(warnings) > 0:
        AddWarning(warnings)
    if len(errors) > 0:
        AddError(errors)
    return



'''
Demonstrates a step progressor by looping through records
on a table. Use a table with 10,000 or so rows - smaller tables
just whiz by.
   1 = table name
   2 = field on the table
'''
import arcpy, time, math
try:
    inTable = arcpy.GetParameterAsText(0)
    inField = 'OID@'

    # Determine number of records in table
    #
    record_count = int(arcpy.GetCount_management(inTable).getOutput(0))
    if record_count == 0:
        raise ValueError("{0} has no records to count".format(inTable))

    arcpy.AddMessage("Number of rows = {0}\n".format(record_count))

    # Method 1: Calculate and use a suitable base 10 increment
    # ===================================

    p = int(math.log10(record_count))
    if not p:
        p = 1
    increment = int(math.pow(10, p - 1))

    arcpy.SetProgressor(
        "step", "Incrementing by {0} on {1}".format(increment, inTable),
        0, record_count, increment)

    beginTime = time.clock()
    with arcpy.da.SearchCursor(inTable, [inField]) as cursor:
        for i, row in enumerate(cursor, 0):
            if (i % increment) == 0:
                arcpy.SetProgressorPosition(i)
            fieldValue = row[0]

    arcpy.SetProgressorPosition(i)
    arcpy.AddMessage("Method 1")
    arcpy.AddMessage("\tIncrement = {0}".format(increment))
    arcpy.AddMessage("\tElapsed time: {0}\n".format(time.clock() - beginTime))

    # Method 2: let's just move in 10 percent increments
    # ===================================
    increment = int(record_count / 10.0)
    arcpy.SetProgressor(
        "step", "Incrementing by {0} on {1}".format(increment, inTable),
        0, record_count, increment)

    beginTime = time.clock()
    with arcpy.da.SearchCursor(inTable, [inField]) as cursor:
        for i, row in enumerate(cursor, 0):
            if (i % increment) == 0:
                arcpy.SetProgressorPosition(i)
            fieldValue = row[0]

    arcpy.SetProgressorPosition(i)
    arcpy.AddMessage("Method 2")
    arcpy.AddMessage("\tIncrement = {0}".format(increment))
    arcpy.AddMessage("\tElapsed time: {0}\n".format(time.clock() - beginTime))

    # Method 3: use increment of 1
    # ===================================
    increment = 1
    arcpy.SetProgressor("step",
                        "Incrementing by 1 on {0}".format(inTable),
                        0, record_count, increment)

    beginTime = time.clock()
    with arcpy.da.SearchCursor(inTable, [inField]) as cursor:
        for row in cursor:
            arcpy.SetProgressorPosition()
            fieldValue = row[0]

    arcpy.SetProgressorPosition(record_count)
    arcpy.ResetProgressor()
    arcpy.AddMessage("Method 3")
    arcpy.AddMessage("\tIncrement = {0}".format(increment))
    arcpy.AddMessage("\tElapsed time: {0}\n".format(time.clock() - beginTime))

    arcpy.AddMessage("Pausing for a moment to allow viewing...")
    time.sleep(2.0)  # Allow viewing of the finished progressor

except Exception as e:
    arcpy.AddError(e[0])



#                           __                    __
#           __       __     \_\  __          __   \_\  __   __       __
#           \_\     /_/        \/_/         /_/      \/_/   \_\     /_/
#         .-.  \.-./  .-.   .-./  .-.   .-./  .-.   .-\   .-.  \.-./  .-.
#        //-\\_//-\\_//-\\_//-\\_//-\\_//-\\_// \\_//-\\_//-\\_//-\\_//-\\
#      __(   '-'   '-'\  '-'   '-'  /'-'   '-'\__'-'   '-'__/'-'   '-'\__
#     /_/))            \__       __/\          \_\       /_/           \_\
#  ___\_//              \_\     /_/  \__
# /_/  ((                             \_\
#       )) __
# __   // /_/
# \_\_((_/___
#      ))  \_\
#      \\
#       )) _
# __   // /_/
# \_\_((
#      \\
#       )) _
# __   // /_/
# \_\_((_/___
#      ))  \_\
#      \\
#       )) _
# __   // /_/
# \_\_((
#      \\
#       )) _
# __   // /_/
# \_\_((_/___
#      ))  \_\                __                    __
#      \\     __       __     \_\  __          __   \_\  __   __       __
#   __  ))    \_\     /_/        \/_/         /_/      \/_/   \_\     /_/
#   \_\_((   .-.  \.-./  .-.   .-./  .-.   .-./  .-.   .-\   .-.  \.-./  .-.
#        \\_//-\\_//-\\_//-\\_//-\\_//-\\_//-\\_// \\_//-\\_//-\\_//-\\_//-\\
#         '-'\__'-'   '-'\  '-'   '-'  /'-'   '-'\__'-'   '-'__/'-'   '-'\__
#             \_\         \__       __/\          \_\       /_/           \_\
#                          \_\     /_/  \__
#                                        \_\




Arcpy Boilerplate

import arcpy as ap
from arcpy import AddMessage as write
from arcpy import AddFieldDelimiters as fieldDelim
import os
import math"
import datetime as dt
import pandas as pd
import numpy as np
import sys



def main(*argv):
	pass


if __name__=='__main__':
	ap.env.overwriteOutput = True
	argv = tuple(ap.GetParameterAsText(i) for i in range(ap.GetArgumentCount()))
	now = dt.datetime.now()
	main(*argv)
	write(dt.datetime.now() - now)
