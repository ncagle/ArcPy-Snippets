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
populated = lambda x: x is not None and str(x).strip() != '' and x is not -999999
fc_fields = ['foobar', 'SHAPE@']
with arcpy.da.SearchCursor(fc, fc_fields) as scursor:
	for row in scursor:
		if row[-1] is None:
			pass # NULL Geometry
		if not populated(row[0]):
			pass # Field is NULL, empty string, or default value



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


#### Update DVOF sourcedates to first of the month for stupid caci bullshit
import arcpy
from datetime import datetime
with arcpy.da.UpdateCursor(dvof_file, ['SOURCEDT']) as dvof:
	for row in dvof:
		date_field = str(row[0])
		feat_date = datetime.strptime(date_field, "%m/%d/%Y")
		dumb_feat_date = feat_date.replace(day=1)
		row[0] = dumb_feat_date
		dvof.updateRow(row)


def add_row_tuple(add_row, index, val): # Adds new index in row tuple with specified value
	# Reminder: The length of the row tuple has to match the target cursor to be applied
	#for add_row in cursor:
	##add_row = add_row_tuple(add_row, index, value)
	##icursor.insertRow(add_row)
	add_row = list(add_row)
	place = int((abs(index)-1) * (index/abs(index)))
	add_row.insert(place, val)
	return tuple(add_row)

def update_row_tuple(edit_row, index, val): # Update a specific row field inside a cursor tuple
	# Usually used for updating geometry before copying the row
	# For short tuples, slicing and concatenation is faster
	# But performance of long tuples is more consistently efficient with list conversion
	#for edit_row in cursor:
	##edit_row = update_row_tuple(edit_row, index, value)
	##icursor.insertRow(edit_row)
	edit_row = list(edit_row)
	edit_row[index] = val
	return tuple(edit_row)

def remove_row_tuple(rem_row, index): # Remove specified index from row tuple
	# Reminder: The length of the row tuple has to match the target cursor to be applied
	#for rem_row in cursor:
	##rem_row = remove_row_tuple(rem_row, index, value)
	##icursor.insertRow(rem_row)
	rem_row = list(rem_row)
	rem_row.pop(index)
	return tuple(rem_row)


def make_field_list(dsc): # Construct a list of proper feature class fields
	# Sanitizes Geometry fields to work on File Geodatabases or SDE Connections
	#field_list = make_field_list(describe_obj)
	fields = dsc.fields # List of all fc fields
	out_fields = [dsc.OIDFieldName, dsc.lengthFieldName, dsc.areaFieldName, 'shape', 'area', 'length', 'global'] # List Geometry and OID fields to be removed
	# Construct sanitized list of field names
	field_list = [field.name for field in fields if field.type not in ['Geometry'] and not any(substring in field.name.lower() for substring in out_fields if substring)]
	# Add ufi field to index[-3], OID@ token to index[-2], and Shape@ geometry token to index[-1]
	field_list.append('OID@')
	field_list.append('SHAPE@')
	return field_list


def copy_fc(source, target, *args, **kwargs): #(s_f)ields, (s_q)uery, (t_f)ields, (t_q)uery
	# copy_fc(source_var, target_var, s_f=s_fields, s_q=s_query, t_f=t_fields, t_q=t_query)
    s_fields = kwargs.get('s_f', "'*'") # Default s_fields variable will be '*' for all fields
    s_query = kwargs.get('s_q', "''") #### Redo the query variables. They don't work if left empty
    t_fields = kwargs.get('t_f', "'*'") # Default t_fields variable will be '*' for all fields
    t_query = kwargs.get('t_q', "''") #### Redo the query variables. They don't work if left empty

	with arcpy.da.SearchCursor(source, s_fields) as scursor: #, s_query) as scursor:
		with arcpy.da.InsertCursor(target, t_fields) as icursor: #, t_query) as icursor:
			for row in scursor:
				icursor.insertRow(row)


def get_local(out_path, dsc): # Gets the clean feature class name and its local path in the target GDB
	#local_fc_path, clean_fc_name = get_local(output_path, describe_obj)
	# dsc.file        = hexagon250_e04a_surge2.sde.AeronauticCrv
	# split(".")     = [hexagon250_e04a_surge2, sde, AeronauticCrv]
	# split(".")[-1] = AeronauticCrv
	fc_name = dsc.file.split(".")[-1] # AeronauticCrv
	local_fc = os.path.join(out_path, "TDS", fc_name) # C:\Projects\njcagle\finishing\E04A\hexagon250_e04a_surge2_2022Mar28_1608.gdb\TDS\AeronauticCrv
	return local_fc, fc_name


# Get name of input database for either SDE or file GDB to construct output variables
gdb_name_raw = re.findall(r"[\w']+", os.path.basename(os.path.split(TDS)[0]))[0]


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



def fractinull(shp, fc_name, oid): # Checks for NULL geometry
	# If geometry is NULL, output the feature class and OID and continue to next feature
	#fractinull(geometry_obj, fc_name, oid)
	ohdeargod = False
	if shp is None:
		ohdeargod = True
		write("{0} feature OID: {1} found with NULL geometry. Skipping transfer.".format(fc_name, oid))
	return ohdeargod


def fractinull(shp, fc_name, oid): # Checks for NULL geometry
	# If geometry is NULL, output the feature class and OID and continue to next feature
	#fractinull(geometry_obj, fc_name, oid)
	if shp is None:
		write("{0} feature OID: {1} found with NULL geometry. Skipping transfer.".format(fc_name, oid))
		continue


# Ouputs which fields in which row in a feature class have NULL values as well as a total count. Does this by making list of NULL fields for each row
count_nulls = 0
with arcpy.da.SearchCursor(fc, '*') as scursor:
    for i, srow in enumerate(scursor):
        null_fields = [name for name, value in zip(scursor.fields, srow) if value is None]
        if null_fields:
            print 'found NULLs in row {}: {}'.format(i + 1, ', '.join(null_fields)) # found NULLs in row 35: plt2, version
            count_nulls += len(null_fields)
print('{} total NULL values'.format(count_nulls)) # 110 total NULL values


# Lists fields in feature class that have NULL values or ones that don't have NULL values. Can specify field_type
def get_fields(in_fc,only_field_type="String",not_null=True):
	'''returns list of field names of specified data type and contain at least one not NULL value'''
	if not not_null:
		all_fields = [field.name for field in arcpy.ListFields(in_fc,field_type=only_field_type)]
		return all_fields
	else:
		all_fields = [field.name for field in arcpy.ListFields(in_fc,field_type=only_field_type) if field.isNullable != "False"]
		#getting a dict {field name : [list of all values]}
		fields_dict = {field: list(set([feature[all_fields.index(field)] for feature in arcpy.da.SearchCursor(in_fc,all_fields)])) for field in all_fields}
	null_fields = [k for k,v in fields_dict.iteritems() if v == [None]]
	not_null_fields = list(set(all_fields).symmetric_difference(set(null_fields)))
	return null_fields
# null_fields = get_fields('TransportationGroundCurves', 'long', True)
# null_fields.sort()
# print(null_fields)
# [u'lc1', u'ffn', u'nos', u'loc']


def writeresults(tool_name): # If tool fails, get messages and output error report before endind process
	write("\n\n***Failed to run {0}.***\n".format(tool_name))
	messages = ap.GetMessages(0)
	warnings = ap.GetMessages(1)
	errors = ap.GetMessages(2)
	write("GP Tool Outputs:")
	write("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
	write(messages)
	write("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
	if len(warnings) > 0:
		write("Tool Warnings:")
		write("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
		write(warnings)
		write("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
	if len(errors) > 0:
		write("Error Report:")
		write("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
		write(errors)
		write("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
	write('                       ______\n                    .-"      "-.\n                   /            \\\n       _          |              |          _\n      ( \\         |,  .-.  .-.  ,|         / )\n       > "=._     | )(__/  \\__)( |     _.=" <\n      (_/"=._"=._ |/     /\\     \\| _.="_.="\\_)\n             "=._ (_     ^^     _)"_.="\n                 "=\\__|IIIIII|__/="\n                _.="| \\IIIIII/ |"=._\n      _     _.="_.="\\          /"=._"=._     _\n     ( \\_.="_.="     `--------`     "=._"=._/ )\n      > _.="                            "=._ <\n     (_/                                    \\_)\n')
	write("Please rerun the tool, but uncheck the {0} tool option. Either the feature class is too big or something else has gone wrong.".format(tool_name))
	write("Exiting tool.\n")
	sys.exit(0)
	#print(u'                 uuuuuuu\n             uu$$$$$$$$$$$uu\n          uu$$$$$$$$$$$$$$$$$uu\n         u$$$$$$$$$$$$$$$$$$$$$u\n        u$$$$$$$$$$$$$$$$$$$$$$$u\n       u$$$$$$$$$$$$$$$$$$$$$$$$$u\n       u$$$$$$$$$$$$$$$$$$$$$$$$$u\n       u$$$$$$"   "$$$"   "$$$$$$u\n       "$$$$"      u$u       $$$$"\n        $$$u       u$u       u$$$\n        $$$u      u$$$u      u$$$\n         "$$$$uu$$$   $$$uu$$$$"\n          "$$$$$$$"   "$$$$$$$"\n            u$$$$$$$u$$$$$$$u\n             u$"|¨|¨|¨|¨|"$u\n  uuu        $$u|¯|¯|¯|¯|u$$       uuu\n u$$$$        $$$$$u$u$u$$$       u$$$$\n  $$$$$uu      "$$$$$$$$$"     uu$$$$$$\nu$$$$$$$$$$$uu    """""    uuuu$$$$$$$$$$\n$$$$"""$$$$$$$$$$uuu   uu$$$$$$$$$"""$$$"\n """      ""$$$$$$$$$$$uu ""$"""\n           uuuu ""$$$$$$$$$$uuu\n  u$$$uuu$$$$$$$$$uu ""$$$$$$$$$$$uuu$$$\n  $$$$$$$$$$""""           ""$$$$$$$$$$$"\n   "$$$$$"                      ""$$$$""\n     $$$"                         $$$$"')



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


import sys
import subprocess
subprocess.check_call([sys.executable, '-m', 'pip', 'install',
'playsound'])
import playsound
playsound("MyPath\\MySound.mp3")


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




import os

def cut_geometry(to_cut, cutter):
    """
    Cut a feature by a line, splitting it into its separate geometries.
    :param to_cut: The feature to cut.
    :param cutter: The polylines to cut the feature by.
    :return: The feature with the split geometry added to it.
    """
    arcpy.AddField_management(to_cut, "SOURCE_OID", "LONG")
    geometries = []
    polygon = None

    edit = arcpy.da.Editor(os.path.dirname(to_cut))
    edit.startEditing(False, False)

    insert_cursor = arcpy.da.InsertCursor(to_cut, ["SHAPE@", "SOURCE_OID"])

    with arcpy.da.SearchCursor(cutter, "SHAPE@") as lines:
        for line in lines:
            with arcpy.da.UpdateCursor(to_cut, ["SHAPE@", "OID@", "SOURCE_OID"]) as polygons:
                for polygon in polygons:
                    if line[0].disjoint(polygon[0]) == False:
                        if polygon[2] == None:
                            id = polygon[1]
                        # Remove previous geom if additional cuts are needed for intersecting lines
                        if len(geometries) > 1:
                            del geometries[0]
                        geometries.append([polygon[0].cut(line[0]), id])
                        polygons.deleteRow()
                for geometryList in geometries:
                    for geometry in geometryList[0]:
                        if geometry.area > 0:
                            insert_cursor.insertRow([geometry, geometryList[1]])

    edit.stopEditing(True)


cut_geometry(r"PATH_TO_POLY", r"PATH_TO_LINES")



### Example of getting parameters in .pyt python toolbox as opposed to arcpy.GetParameterAsText(0) in python script tools
# def get_Parameter_Info(self):
#     # Define parameter definitions
#     param0 = arcpy._Parameter(
#         displayName="Input workspace",
#         name="workspace",
#         datatype="DEWorkspace",
#         parameterType="Required",
#         direction="Input")
#     param1 = arcpy._Parameter(
#         displayName="Input classified raster",
#         name="input_raster",
#         datatype="GPRasterLayer",
#         parameterType="Required",
#         direction="Input")
#     param2 = arcpy._Parameter(
#         displayName="Input features",
#         name="input_features",
#         datatype="GPFeatureLayer",
#         parameterType="Required",
#         direction="Input")
#
#
#     params = [param0, param1, param2]
#
#     return params
#
#
# toggled inputs are set to optional but throw error if not filled in
# if self.params[2].value == True:
#     self.params[3].enabled = 1
#     self.params[3].setIDMessage("ERROR", 735, self.params[3].displayName)
#     self.params[4].enabled = 0
#     self.params[4].clearMessage()
# else:
#     self.params[3].enabled = 0
#     self.params[3].clearMessage()
#     self.params[4].enabled = 1
#     self.params[4].setIDMessage("ERROR", 735, self.params[4].displayName)
#
#
# def _execute_(self, parameters, messages):
#     # The source code of the tool.
#     # Define some paths/variables
#     outWorkspace = parameters[0].valueAsText
#     arcpy.env.workspace = outWorkspace
#     output_location = parameters[0].valueAsText
#     input_raster = parameters[1].valueAsText
#     input_features = parameters[2].valueAsText



arcpy.env.workspace = r'T:\GEOINT\FEATURE DATA\Hexagon 250-251\SDE_Connections\hexagon250_h12b_radahn_north.sde\hexagon250_h12b_radahn_north.sde.TDS'

def make_field_list(dsc): # Construct a list of proper feature class fields
	# Sanitizes Geometry fields to work on File Geodatabases or SDE Connections
	#field_list = make_field_list(describe_obj)
	fields = dsc.fields # List of all fc fields
	out_fields = [dsc.OIDFieldName, dsc.lengthFieldName, dsc.areaFieldName, 'shape', 'area', 'length', 'global'] # List Geometry and OID fields to be removed
	# Construct sanitized list of field names
	field_list = [field.name for field in fields if field.type not in ['Geometry'] and not any(substring in field.name.lower() for substring in out_fields if substring)]
	# Add ufi field to index[-3], OID@ token to index[-2], and Shape@ geometry token to index[-1]
	field_list.append('OID@')
	field_list.append('SHAPE@')
	return field_list

ag_local_dsc = arcpy.Describe("AgricultureSurfaces_local")
field_list = make_field_list(ag_local_dsc)
field_list.remove(u'created_user')
field_list.remove(u'created_date')
field_list.remove(u'last_edited_user')
field_list.remove(u'last_edited_date')

def copy_fc(source, target, *args, **kwargs): #(s_f)ields, (s_q)uery, (t_f)ields, (t_q)uery
	# copy_fc(source_var, target_var, s_f=s_fields, s_q=s_query, t_f=t_fields, t_q=t_query)
    s_fields = kwargs.get('s_f', "'*'") # Default s_fields variable will be '*' for all fields
    #s_query = kwargs.get('s_q', "''")
    t_fields = kwargs.get('t_f', "'*'") # Default t_fields variable will be '*' for all fields
    #t_query = kwargs.get('t_q', "''")

	with arcpy.da.SearchCursor(source, s_fields) as scursor:
		with arcpy.da.InsertCursor(target, t_fields) as icursor:
			for row in scursor:
				icursor.insertRow(row)

copy_fc("AgricultureSurfaces_local", r"sde\AgricultureSurfaces", s_f=field_list, t_f=field_list)
