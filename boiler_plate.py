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



########################################################################
########################################################################



import arcpy
import os


########################################################################
class FeatureClass(object):
	"""FeatureClass object"""

	#----------------------------------------------------------------------
	def __init__(self,path):
		"""Constructor for FeatureClass"""
		gdb_attributes_dict = {'fc_path': arcpy.Describe(path).catalogPath,
							   'fc_name': arcpy.Describe(path).file.split(".")[-1],
							   'shape_type': arcpy.Describe(path).shapeType, # Polygon, Polyline, Point, Multipoint, MultiPatch
							   'shape_field': arcpy.Describe(path).shapeFieldName,
							   'length_field': arcpy.Describe(path).lengthFieldName,
							   'area_field': arcpy.Describe(path).areaFieldName,
							   'oid_field': arcpy.Describe(path).OIDFieldName,
							   'has_spatial_index': arcpy.Describe(path).hasSpatialIndex
							   }

		out_fields = [self.oid_field, self.length_field, self.area_field, self.shape_field] # List Geometry and OID fields to be removed
		# Construct sanitized list of field names
		field_list = [field.name for field in arcpy.ListFields(path) if field.type not in ['Geometry'] and not any(substring in field.name for substring in out_fields)]
		# Add OID@ token to index[-2] and Shape@ geometry token to index[-1]
		field_list.append('OID@')
		field_list.append('SHAPE@')

		for k,v in gdb_attributes_dict.iteritems():
			setattr(self, k, v)

		setattr(self,'TDS',os.path.dirname(self.fc_path))
		setattr(self,'fields',field_list)
		setattr(self,'fc_features',Features(self.fc_path,self.fields))

	#----------------------------------------------------------------------
	def __str__(self):
		return self.baseName

"""FeatureClass.shape_type"""
	u'Polyline'
"""FeatureClass.fc_name"""
	u'HydrographyCrv'
"""FeatureClass.has_spatial_index"""
	True
"""FeatureClass.oid_field"""
	u'objectid'
"""FeatureClass.shape_field"""
	u'shape'
"""FeatureClass.fc_path"""
	u'T:\\GEOINT\\FEATURE DATA\\Hexagon 250-251\\hexagon250_e04a_surge2.sde\\hexagon250_e04a_surge2.sde.TDS\\hexagon250_e04a_surge2.sde.HydrographyCrv'
"""FeatureClass.area_field"""
	u''
"""FeatureClass.length_field"""
	u'st_length(shape)'

"""FeatureClass.TDS"""
	u'T:\\GEOINT\\FEATURE DATA\\Hexagon 250-251\\hexagon250_e04a_surge2.sde\\hexagon250_e04a_surge2.sde.TDS'

"""FeatureClass.fields"""
	[u'f_code', u'fcsubtype', u'aoo', u'ara', u'atc', u'bh141_slta', u'bh141_sltb', u'bmc', u'bmc2', u'bmc3', u'caa', u'cda', u'cwt', u'dev', u'dft', u'dfu', u'dim', u'fcs', u'hgs', u'hgt', u'ldc', u'lmc', u'loc', u'lzn', u'mcc', u'mcc2', u'mcc3', u'nvs', u'oth', u'pcf', u'pwa', u'rle', u'sbb', u'spt', u'thi', u'tid', u'trs', u'trs2', u'trs3', u'ufi', u'voi', u'wcc', u'wd3', u'wid', u'wmt', u'woc', u'wrt', u'zi004_rcg', u'zi005_fna', u'zi005_nfn', u'zi006_mem', u'zi020_ge4', u'zi024_hyp', u'zi024_scc', u'zi024_ywq', u'zi026_ctuc', u'zi026_ctul', u'zi026_ctuu', u'zvh', u'aha', u'zi001_srt', u'zi001_sdv', u'zi001_sdp', u'zi001_sps', u'zi001_vsc', u'zi001_vsd', u'zi001_vsn', u'ccn', u'cdr', u'zsax_rs0', u'zsax_rx0', u'zsax_rx3', u'zsax_rx4', u'globalid', u'version', u'zzhex1', u'zzhex2', u'zzhex3', u'created_user', u'created_date', u'last_edited_user', u'last_edited_date', 'OID@', 'SHAPE@']



########################################################################
class Features:
	"""Feature objects in FeatureClass object"""

	#----------------------------------------------------------------------
	def __init__(self,path,fields):
		"""Constructor for Features"""
		self.path = path
		self.fields = fields
		self.features = [feature for feature in arcpy.da.SearchCursor(self.path,self.fields)]
		self.attribute_table = [{self.fields[feat.index(v)]:v for v in feat} for feat in self.features]

"""Features.path"""
	u'C:\\ArcTutor\\Editing\\Zion.gdb\\Springs'
"""Features.fields"""
	[u'OBJECTID', u'Shape', u'ComID', u'FDate', u'Resolution', u'GNIS_ID', u'GNIS_Name', u'ReachCode', u'FType', u'FCode']
"""Features.features[0:3]"""
	[(228, (305711.4726999998, 4156967.8816), 33034429, datetime.datetime(2002, 2, 6, 0, 0), 2, None, None, None, 458, 45800),
	(229, (305315.84750000015, 4156801.4681), 33034431, datetime.datetime(2002, 2, 6, 0, 0), 2, None, None, None, 458, 45800),
	(230, (305697.4517000001, 4156837.429199999), 33034433, datetime.datetime(2002, 2, 6, 0, 0), 2, None, None, None, 458, 45800)]
"""Features.attribute_table[0:3]"""
	[{u'ComID': 33034429,
		u'FCode': 45800,
		u'FDate': datetime.datetime(2002, 2, 6, 0, 0),
		u'FType': 458,
		u'GNIS_ID': None,
		u'OBJECTID': 228,
		u'Resolution': 2,
		u'Shape': (305711.4726999998, 4156967.8816)
		},
	 {u'ComID': 33034431,
		u'FCode': 45800,
		u'FDate': datetime.datetime(2002, 2, 6, 0, 0),
		u'FType': 458,
		u'GNIS_ID': None,
		u'OBJECTID': 229,
		u'Resolution': 2,
		u'Shape': (305315.84750000015, 4156801.4681)
		},
	 {u'ComID': 33034433,
		u'FCode': 45800,
		u'FDate': datetime.datetime(2002, 2, 6, 0, 0),
		u'FType': 458,
		u'GNIS_ID': None,
		u'OBJECTID': 230,
		u'Resolution': 2,
		u'Shape': (305697.4517000001, 4156837.429199999)
		}
	]



########################################################################
class Geodatabase(object):
    """Geodatabase object"""
    _path = None

    #----------------------------------------------------------------------
    def __init__(self,path,initialize=False):

        self.path = path
        if initialize:
            self.__init()

    #----------------------------------------------------------------------
    def __init(self):
        """populates advanced gdb properties"""
        path = self.path
        arcpy.env.workspace = self.path

        gdb_attributes_dict = {'name': arcpy.Describe(path).name,
                               'workspace_type': arcpy.Describe(path).workspaceType,
							   'workspace_ID': arcpy.Describe(path).workspaceFactoryProgID,
                               'connection_properties': arcpy.Describe(path).connectionProperties,
                               'connection_string': arcpy.Describe(path).connectionString,
                               'feature_class_list': arcpy.ListFeatureClasses(),
                               'feature_class_full_paths': [os.path.join(self.path,fc)
                                                           for fc in arcpy.ListFeatureClasses()]}

		# Change ArcPy's unreadable workspaceFactoryProgID output to something useful
		# AccessWorkspaceFactory, FileGDBWorkspaceFactory, InMemoryWorkspaceFactory, SdeWorkspaceFactory, or Shapefile
		gdb_attributes_dict['workspace_ID'] = gdb_attributes_dict['workspace_ID'].split('.')[1] if gdb_attributes_dict['workspace_ID'] else 'Shapefile'

        for k,v in gdb_attributes_dict.iteritems():
            setattr(self, k, v)

"""name"""
"""workspace_type"""
	'FileSystem' # coverage, shapefile, in_memory workspaces
	'LocalDatabase' # file or personal GDBs
	'RemoteDatabase' # remote connection GDBs (i.e. enterprise)
"""workspace_ID"""
	'AccessWorkspaceFactory' # Personal geodatabase
    'FileGDBWorkspaceFactory' # File geodatabase
    'InMemoryWorkspaceFactory' # In-memory workspace
    'SdeWorkspaceFactory' # Enterprise geodatabase
    'Shapefile' # Technically could be Coverage, CAD, VPF, or another format but is likely a shp with our data
"""connection_properties"""
	# Describe().connectionProperties is a property set. The connection properties for an enterprise geodatabase workspace will vary depending on the type of enterprise database being used. Possible properties include the following:
	'authentication_mode' # Credential authentication mode of the connection, either OSA or DBMS.
	'database' # Database connected to.
	'historical_name' # The historical marker name of the historical version connected to.
	'historical_timestamp' # A date time that represents a moment timestamp in the historical version connected to.
	'is_geodatabase' # String. Returns true if the database has been enabled to support a geodatabase; otherwise, it's false.
	'instance' # Instance connected to.
	'server' # Enterprise server name connected to.
	'user' # Connected user.
	'version' # The transaction version name of the transactional version connected to.
	'branch' # The branch version name of the branch version connected to.
"""connection_string"""
	# The connection string being used in conjunction with the enterprise database type. For any other workspace type, returns an empty string.
"""feature_class_list"""
	['Springs',
	'Tracts',
	'Trails',
	'Roads']
"""feature_class_full_paths"""
	[u'C:\\ArcTutor\\Editing\\Zion.gdb\\Springs',
    u'C:\\ArcTutor\\Editing\\Zion.gdb\\Tracts',
    u'C:\\ArcTutor\\Editing\\Zion.gdb\\Trails',
    u'C:\\ArcTutor\\Editing\\Zion.gdb\\Roads']

    #----------------------------------------------------------------------
    # def __str__(self):
    #     """returns the object as a string"""
    #     return str({'path':self.path,
    #                 'release':self.release})
    #----------------------------------------------------------------------
    def __repr__(self):
        """system representation of a class"""
        return str({'name': self.name,
                    'properties': str(self.__dict__)})
    #----------------------------------------------------------------------
    @property
    def path(self):
        return self._path
    #----------------------------------------------------------------------
    @path.setter
    def path(self,path_value):
        if self._path is not None:
            raise ValueError("You shouldn't modify the gdb path!")
        if path_value[-4:] != ".gdb":
            print "Not a valid gdb"
            raise AttributeError("Geodatabase path must end with .gdb")
        self._path = path_value
    #----------------------------------------------------------------------
    @property
    def feature_class_objects(self):
        """gets a list of feature class objects in the gdb"""
        return [FeatureClass(path) for path in self.feature_class_full_paths]

"""feature_class_objects"""
	[<__main__.FeatureClass object at 0x0C6D0A50>,
    <__main__.FeatureClass object at 0x0C3B49F0>,
    <__main__.FeatureClass object at 0x0C6737D0>,
    <__main__.FeatureClass object at 0x0CBC96F0>]

    #----------------------------------------------------------------------
    @property
    def feature_class_features(self,fc_name):
        """gets a list of feature objects in the feature class"""
        return [FeatureClass(path) for path in [os.path.join(gdb.path,fc_name)]]






gdb = Geodatabase(path=r"C:\ArcTutor\Editing\Zion.gdb",initialize=True)

print gdb.featureClassesFullPaths
#[u'C:\\ArcTutor\\Editing\\Zion.gdb\\Springs',
    #u'C:\\ArcTutor\\Editing\\Zion.gdb\\Tracts',
    #u'C:\\ArcTutor\\Editing\\Zion.gdb\\Trails',
    #u'C:\\ArcTutor\\Editing\\Zion.gdb\\Roads']

fcs = gdb.feature_classes_objects
print fcs
#[<__main__.FeatureClass object at 0x0C6D0A50>,
    #<__main__.FeatureClass object at 0x0C3B49F0>,
    #<__main__.FeatureClass object at 0x0C6737D0>,
    #<__main__.FeatureClass object at 0x0CBC96F0>]

print [(fc.fcPath,fc.shapeType) for fc in fcs]
#[(u'C:\\ArcTutor\\Editing\\Zion.gdb\\Springs', u'Point'),
#(u'C:\\ArcTutor\\Editing\\Zion.gdb\\Tracts', u'Polygon'),
#(u'C:\\ArcTutor\\Editing\\Zion.gdb\\Trails', u'Polyline'),
#(u'C:\\ArcTutor\\Editing\\Zion.gdb\\Roads', u'Polyline')]

print [fc.fcPath for fc in fcs if fc.shapeType == 'Polyline']
#[u'C:\\ArcTutor\\Editing\\Zion.gdb\\Trails',
#u'C:\\ArcTutor\\Editing\\Zion.gdb\\Roads',
#u'C:\\ArcTutor\\Editing\\Zion.gdb\\Streams']

springs_fc = [fc.fcFeatures for fc in fcs if fc.baseName == 'Springs'][0]
springs_feats = springs_fc.features

print springs_fc.fields
#[u'OBJECTID', u'Shape', u'ComID', u'FDate', u'Resolution', u'GNIS_ID',
#u'GNIS_Name', u'ReachCode', u'FType', u'FCode']

print springs_feats[0:3]
#[(228, (305711.4726999998, 4156967.8816), 33034429, datetime.datetime(2002, 2, 6, 0, 0), 2, None, None, None, 458, 45800),
#(229, (305315.84750000015, 4156801.4681), 33034431, datetime.datetime(2002, 2, 6, 0, 0), 2, None, None, None, 458, 45800),
#(230, (305697.4517000001, 4156837.429199999), 33034433, datetime.datetime(2002, 2, 6, 0, 0), 2, None, None, None, 458, 45800)]

print springs_fc.attribute_table[0:3]
#[{u'ComID': 33034429,
    #u'FCode': 45800,
    #u'FDate': datetime.datetime(2002, 2, 6, 0, 0),
    #u'FType': 458,
    #u'GNIS_ID': None,
    #u'OBJECTID': 228,
    #u'Resolution': 2,
    #u'Shape': (305711.4726999998, 4156967.8816)},
    #{u'ComID': 33034431,
    #u'FCode': 45800,
    #u'FDate': datetime.datetime(2002, 2, 6, 0, 0),
    #u'FType': 458,
    #u'GNIS_ID': None,
    #u'OBJECTID': 229,
    #u'Resolution': 2,
    #u'Shape': (305315.84750000015, 4156801.4681)},
    #{u'ComID': 33034433,
    #u'FCode': 45800,
    #u'FDate': datetime.datetime(2002, 2, 6, 0, 0),
    #u'FType': 458,
    #u'GNIS_ID': None,
    #u'OBJECTID': 230,
    #u'Resolution': 2,
    #u'Shape': (305697.4517000001, 4156837.429199999)}]
