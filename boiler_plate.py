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
							   'hasSpatialIndex': arcpy.Describe(path).hasSpatialIndex
							   }

		out_fields = [self.oid_field, self.length_field, self.area_field, self.shape_field] # List Geometry and OID fields to be removed
		# Construct sanitized list of field names
		field_list = [field.name for field in arcpy.ListFields(path) if field.type not in ['Geometry'] and field.name not in out_fields]
		# Add OID@ token to index[-2] and Shape@ geometry token to index[-1]
		field_list.append('OID@')
		field_list.append('SHAPE@')

        for k,v in gdb_attributes_dict.iteritems():
            setattr(self, k, v)

		setattr(self,'TDS',os.path.dirname(self.fc_path))
		setattr(self,'fields',field_list)
        setattr(self,'fcFeatures',Features(self.fc_path,self.fields))

    #----------------------------------------------------------------------
    def __str__(self):
        return self.baseName

'shape_type': u'Polyline',
'fc_name': u'HydrographyCrv',
'hasSpatialIndex': True,
'oid_field': u'objectid',
'shape_field': u'shape',
'fc_path': u'T:\\GEOINT\\FEATURE DATA\\Hexagon 250-251\\hexagon250_e04a_surge2.sde\\hexagon250_e04a_surge2.sde.TDS\\hexagon250_e04a_surge2.sde.HydrographyCrv',
'area_field': u'',
'length_field': u'st_length(shape)'

'TDS': u'T:\\GEOINT\\FEATURE DATA\\Hexagon 250-251\\hexagon250_e04a_surge2.sde\\hexagon250_e04a_surge2.sde.TDS'

'fields': [u'f_code', u'fcsubtype', u'aoo', u'ara', u'atc', u'bh141_slta', u'bh141_sltb', u'bmc', u'bmc2', u'bmc3', u'caa', u'cda', u'cwt', u'dev', u'dft', u'dfu', u'dim', u'fcs', u'hgs', u'hgt', u'ldc', u'lmc', u'loc', u'lzn', u'mcc', u'mcc2', u'mcc3', u'nvs', u'oth', u'pcf', u'pwa', u'rle', u'sbb', u'spt', u'thi', u'tid', u'trs', u'trs2', u'trs3', u'ufi', u'voi', u'wcc', u'wd3', u'wid', u'wmt', u'woc', u'wrt', u'zi004_rcg', u'zi005_fna', u'zi005_nfn', u'zi006_mem', u'zi020_ge4', u'zi024_hyp', u'zi024_scc', u'zi024_ywq', u'zi026_ctuc', u'zi026_ctul', u'zi026_ctuu', u'zvh', u'aha', u'zi001_srt', u'zi001_sdv', u'zi001_sdp', u'zi001_sps', u'zi001_vsc', u'zi001_vsd', u'zi001_vsn', u'ccn', u'cdr', u'zsax_rs0', u'zsax_rx0', u'zsax_rx3', u'zsax_rx4', u'globalid', u'version', u'zzhex1', u'zzhex2', u'zzhex3', u'created_user', u'created_date', u'last_edited_user', u'last_edited_date', 'OID@', 'SHAPE@']



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

        gdb_attributes_dict = {'name':arcpy.Describe(path).name,
                               'release': arcpy.Describe(path).release,
                               'workspaceType': arcpy.Describe(path).workspaceType,
                               'connectionProperties': arcpy.Describe(path).connectionProperties,
                               'connectionString': arcpy.Describe(path).connectionString,
                               'workspaceFactoryProgID': arcpy.Describe(path).workspaceFactoryProgID,
                               'featureClassesNames': arcpy.ListFeatureClasses(),
                               'featureClassesFullPaths': [os.path.join(self.path,fc)
                                                           for fc in arcpy.ListFeatureClasses()]}

        for k,v in gdb_attributes_dict.iteritems():
            setattr(self, k, v)

    #----------------------------------------------------------------------
    def __str__(self):
        """returns the object as a string"""
        return str({'path':self.path,
                    'release':self.release})
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
    def feature_classes_objects(self):
        """gets a list of feature class objects in the gdb"""
        return [FeatureClass(path) for path in self.featureClassesFullPaths]
    #----------------------------------------------------------------------
    @property
    def feature_class_features(self,fc_name):
        """gets a list of feature objects in the feature class"""
        return [FeatureClass(path) for path in [os.path.join(gdb.path,fc_name)]]
