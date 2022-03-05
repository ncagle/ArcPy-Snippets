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
	#start/finish = dt.now().time()
	# Returns string of total seconds elapsed between start and finish markers
	date = dt.now().date()
	dt_finish = dt.combine(date, finish)
	dt_start = dt.combine(date, start)
	time_delta = dt_finish - dt_start
	time_elapsed = str(time_delta.total_seconds())
	return time_elapsed
start = dt.now().time()
arcpy.MultipartToSinglepart_management(in_class, out_class)
finish = dt.now().time()


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
