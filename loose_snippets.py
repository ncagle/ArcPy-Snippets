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



def write_info(name, var): # Write information for given variable
	#write_info('var_name', var)
	write("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
	write("Debug info for {0}:".format(name))
	write("   Variable Type: {0}".format(type(var)))
	if type(var) is str or type(var) is unicode:
		write("   Assigned Value: '{0}'".format(var))
	else:
		write("   Assigned Value: {0}".format(var))
	write("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")



def runtime(start, finish): # Time a process or code block
	# Add a start and finish variable markers surrounding the code to be timed
	#from datetime import datetime as dt
	#start/finish = dt.now()
	# Returns string of formatted elapsed time between start and finish markers
	time_delta = (finish - start).total_seconds()
	h = int(time_delta/(60*60))
	m = int((time_delta%(60*60))/60)
	s = time_delta%60.
	time_elapsed = "{}:{:>02}:{:>05.4f}".format(h, m, s) # 00:00:00.0000
	return time_elapsed



def get_count(fc_layer): # Returns feature count
    results = int(ap.GetCount_management(fc_layer).getOutput(0))
    return results



def update_row_tuple(irow, index, val): # Update a specific row field inside an insert cursor
	# Usually used for updating geometry before copying the row
	# For short tuples, slicing and concatenation is faster
	# But performance of long tuples is more consistently efficient with list conversion
	#geometry_obj = SHAPE@.method()
	#irow = update_row_tuple(irow, -1, geometry_obj)
	#icursor.insertRow(irow)
	edit_row = list(irow)
	edit_row[index] = val
	return tuple(edit_row)



def make_field_list(dsc): # Construct a list of proper feature class fields
	# Sanitizes Geometry fields to work on File Geodatabases or SDE Connections
	#field_list = make_field_list(describe_obj)
	fields = dsc.fields # List of all fc fields
	out_fields = [dsc.OIDFieldName, dsc.lengthFieldName, dsc.areaFieldName] # List Geometry and OID fields to be removed
	# Construct sanitized list of field names
	field_list = [field.name for field in fields if field.type not in ['Geometry'] and field.name not in out_fields]
	# Further cleaning to account for other possible geometry standards including ST_Geometry
	field_list[:] = [x for x in field_list if 'Shape' not in x and 'shape' not in x and 'Area' not in x and 'area' not in x and 'Length' not in x and 'length' not in x]
	# Add OID@ token to index[-2] and Shape@ geometry token to index[-1]
	field_list.append('OID@')
	field_list.append('SHAPE@')
	return field_list



def get_local(out_path, dsc): # Gets the clean feature class name and its local path in the target GDB
	#local_fc_path, clean_fc_name = get_local(output_path, describe_obj)
	# dsc.file        = hexagon250_e04a_surge2.sde.AeronauticCrv
	# split(".")     = [hexagon250_e04a_surge2, sde, AeronauticCrv]
	# split(".")[-1] = AeronauticCrv
	fc_name = dsc.file.split(".")[-1] # AeronauticCrv
	local_fc = os.path.join(out_path, "TDS", fc_name) # C:\Projects\njcagle\finishing\E04A\hexagon250_e04a_surge2_2022Mar28_1608.gdb\TDS\AeronauticCrv
	return local_fc, fc_name



def make_gdb_schema(TDS, xml_out, out_folder, gdb_name, out_path): # Creates a new file GDB with an empty schema identical to the source
	# Works to replicate schema from SDE
	# TDS - Path to source TDS with schema to replicate       # "T:\GEOINT\FEATURE DATA\hexagon250_e04a_surge.sde\hexagon250_e04a_surge2.sde.TDS"
	# xml_out - Output path for schema xml file               # "C:\Projects\njcagle\finishing\E04A\hexagon250_e04a_surge_schema.xml"
	# out_folder - Folder path where new GDB will be created  # "C:\Projects\njcagle\finishing\E04A"
	# gdb_name - Name of GDB to be created                    # "hexagon250_e04a_surge_2022Mar29_1923"
	# out_path - Path of newly created GDB                    # "C:\Projects\njcagle\finishing\E04A\hexagon250_e04a_surge_2022Mar29_1923.gdb"
	start_schema = dt.now()
	write("Exporting XML workspace")
	arcpy.ExportXMLWorkspaceDocument_management(TDS, xml_out, "SCHEMA_ONLY", "BINARY", "METADATA")
	write("Creating File GDB")
	arcpy.CreateFileGDB_management(out_folder, gdb_name, "CURRENT")
	write("Importing XML workspace")
	arcpy.ImportXMLWorkspaceDocument_management(out_path, xml_out, "SCHEMA_ONLY")
	write("Local blank GDB with schema successfully created")
	os.remove(xml_out)
	finish_schema = dt.now()
	write("Time to create local GDB with schema: {0}".format(runtime(start_schema,finish_schema)))



################################################################################




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




################################################################################




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
