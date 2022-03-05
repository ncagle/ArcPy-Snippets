"""
Script Created: K Sundeen, 5/2015
Description: Script outputs a *.csv file delimited by ";" that for each feature dataset in
an SDE database, and the output describes the SDE feature classes, attributes of each feature class,
count of features within each feature class, feature class type, domains accessed by each attribute
in each feature class (if present), and lists any subtypes associated with each feature class.
"""

# 1. Import modules 
import arcpy, os
from datetime import datetime


# defines the output logfile for recording geoprocessing messages
# converts the datetime.now() into strings to be accessed & added the end of logfile; updated by KSundeen 10-19-2015
i = datetime.now()
todaysDatetime = i.strftime("Feature counts as of %m/%d/%Y %H:%M:%S")

# 2. Establish workspace connection to SDE Database while Arcmap is open
arcpy.env.workspace = r"Database Connections\cihl-gisdat-01_sde_current_gisuser.sde"
myDir = arcpy.env.workspace

# 3. Acess domain in workspace
domains = arcpy.da.ListDomains(arcpy.env.workspace)

# 4. List dataset(s) in workspace
#ds = ['sde.SDE.SteamSystem']
#ds = arcpy.ListDatasets(feature_type='feature') # WILL ACCESS ALL FEATURE DATASETS
#ds = ['sde.SDE.Water_Distribution_Network', 'sde.SDE.Water_Distribution_Features']   # LIST OF SPECIFIC FEATURE CLASSES IN WATER UTILITIES
#ds = ['sde.SDE.StormSewerFeatures', 'sde.SDE.StormSewerNetwork']   # LIST OF SPECIFIC FEATURE CLASSES IN STORM UTILITIES
#ds = ['sde.SDE.Maintenance']    # DATASET FOR MAINTENANCE FEATURE CLASSES
#ds = ['sde.SDE.SanitarySewerFeatures', 'sde.SDE.SanitarySewerNetwork']  #
ds = ['sde.SDE.Gas']

# 5. Create object for ouput file to store exported data
metadataKeywordList = ['Gas', 'GPS', 'Maintenance', 'SantitarySewer', 'StormwaterSewer', 'Water', 'Steam']
keyword = metadataKeywordList[0]
outFile = open(r"S:\GIS_Public\GIS_Data\Metadata\UtilitiesMetadata\SDE_GIS_" + keyword + r"_DatasetAttributes_DomainsInRows.csv", 'w')

# 6. Set field header names that will be printed in output file: FeatureDataset; FeatureClass; FeatureCount; FeatureType; ShapeType; FieldName; FieldType; FieldDomain; FieldLenth; FieldPrecision...etc
fieldHeaders = ';FieldName;FieldType;FieldLenth;FieldPrecision;FieldDomain;DomainType;DomainValues'

outFile.write('FeatureDataset;FeatureClass;FeatureType;ShapeType;NumberOfFeatures;'
              + fieldHeaders + '\n' + todaysDatetime + '\n')    # WILL WRITE FIELD HEADERS TO FIRST LINE

# 7. Set counter to establish the # of feature classes in the dataset (ds)
# while the counter index (i) is less than the total feature classes in the dataset, then run through script...
i=0
while i < len(ds):
    if ds[i] is not None: 

    ## OPEN A NEW FILE TO WRITE; ALL COLUMNS ARE SEPARATED BY ';'
    ## ITERATES THROUGH EACH SDE FEATURE DATASET & PRINTS FEATURE CLASSES
        print 'Dataset:', ds[i]   

# 8. For each feature class in the dataset list, count the # features, describe the properties, and write the properties in output file                      
        for fc in arcpy.ListFeatureClasses(feature_dataset=ds[i]):
            
            print 'Feature Class:', fc
            ## ITERATING THROUGH ALL FEATURE CLASSESS & REPORTING THE FEATURE COUNT
            featureCount = arcpy.GetCount_management(fc)
            #if featureCount is not None:  
            
            ## WRITE TO THE CSV FILE: DS NAME; FC NAME; FEATURE COUNT; & FEATURE ATTRIBUTES
            ###### FEATURE ATTRIBUTES (FIELD NAME, ALIAS, TYPE, DOMAINS ASSOCIATED WITH FIELD, LENGTH, PRECISION)

            properties = arcpy.Describe(fc)
            fields = arcpy.ListFields(fc)
            
            ## WRITE TO OUTFILE NAME OF DATASET & FEATURE CLASS
            outFile.write('\n'
                          + str(ds[i]) + ';'
                          + str(fc) + ';'
                          + str(properties.featureType) + ';'
                          + str(properties.shapeType) + ';'
                          + str(featureCount)
                          )
            
            # for all fields in each fc, then write out the field attributes...
            for field in fields:                      
                outFile.write('\n;;;;; ATTRIBUTE->;'
                              + '{0}'.format(field.name) + ';'
                              #+ '{0}'.format(field.aliasName) + ';' # a quick comparison of alias names showed they are generally the same
                              + '{0}'.format(field.type) + ';'
                              + '{0}'.format(field.length) + ';'
                              + '{0}'.format(field.precision)+ ';'
                              #+ '{0}'.format(field.domain)
                              )


# 9. Access the domains in the SDE GIS database       
# Listing Domains
                # IF DOMAIN FIELD EXISTS (where the item in the domain list is <0),
                # THEN WRITE THE DOMAIN AND ITS CODE VALUES IN NEXT LINE
                # ACCESSES ALL DOMAINS IN GDB & PRINTS TO CONSOLE
                for domain in domains: 
                    if '{0}'.format(field.domain) == '{0}'.format(domain.name):
                        # IF THE DOMAIN IN THE FIELD MATCHES A DOMAIN IN THE SDE, IT PRINTS THE VALUES
                        outFile.write('{0}'.format(domain.name))
                        if domain.domainType == 'CodedValue':
                            coded_values = domain.codedValues
                            outFile.write(';IsCodedValueDomain;')
                            for val, desc in coded_values.iteritems():
                                outFile.write('{0} : {1}'.format(val, desc) + ' | ')
                        elif domain.domainType == 'Range':
                            outFile.write(';IsRangeDomain;')
                            outFile.write('Min: {0}'.format(domain.range[0]) + ' | ')
                            outFile.write('Max: {0}'.format(domain.range[1]) + ' | ')
                        else: print('No Domain')

# 10. Access the subtypes used in each of the iterated feature classes
# Listing Subtypes, separated by "|" and listed in rows
            # list subtypes in feature class
            subtypes = arcpy.da.ListSubtypes(fc)
            print 'SUBTYPES:', subtypes

            outFile.write('\n\n;;;;;;(SubtypeFieldName=SubtypeDefaultValue | SubtypeDomainName)') # print subtype code and code's description, printed with enough
                        # spaces so I can format the "feature attribute/subtype definition" after the name
            
            # for subtype code and subtype dictionary, iterate through each subtype...
            for stcode, stdict in subtypes.iteritems():
                
                
                # for each subtype key iterate through the subtype dictionary's keys...
                for stkey in stdict.iterkeys():
                    #print 'STCODE:', stcode
                    #print 'STDICT:', stdict

                    # only print field attribute names once...eventually
                    # print restuls in one line (row) instead of in separate columns
                    
                    # if subtype key value is 'Name' and 'FieldValues' then ...
                    if stkey == 'Name': # grabs the dictionary's key of "SubtypeField", which is the subtypes attribute field
                        outFile.write('\n;;;;;;FeatureClassSubtype: (SubtypeCode={0}/SubtypeName={1})'.format(stcode, stdict[stkey]))    # print subtype code and code's description, printed with enough
                        # spaces so I can format the "feature attribute/subtype definition" after the name
                        print 'done with "SubtypeField"'
                        
                    if stkey == 'FieldValues':  
                        fields = stdict[stkey]

                        # iterates through each subtype dictionary & writes subtype name (field) and it's default values [index0] in the list of values (fieldvals)
                        for field, fieldvals in fields.iteritems():
                            outFile.write(' | ({0}={1}'.format(field, fieldvals[0])) # AttributeName{0}=DefaultValue{1}
                            
                            if not fieldvals[1] is None: #grabs the domain if the object at index [1] contains a domain object
                                outFile.write(' | FieldDomain: {0})'.format(fieldvals[1].name)) # to make result print out in same row use ";" otherwise use a newline character to make many rows '/n'
                            else: outFile.write(')') # to make result print out in same row use ";" otherwise use a newline character to make many rows '/n'

                            #print 'done with ',stdict[stkey],'field' # prints to console all dictionary items and their keys
                        outFile.write(")") # to make result print out in same row use ";" otherwise use a newline character to make many rows '/n'
                    #else: print 'other fields excluded are', stkey, 'fields'




    else: print 'something went wrong in the if conditional statement'


    i+=1  # ITERATES TO THE NEXT FEATURE DATASET TO DESCRIBE FEATURE CLASSES & ATTRIBUTES

#11. When script is complete print this    
print '\n script completed\n'

# 12. Delete the object holding the variable for the output file "outFile"
del outFile


## SEE RESOURCE FOR MORE NOTES ON FORMATTING PYTHON OUTPUT: http://www.python-course.eu/python3_formatted_output.php

"""
The Subtype Dictionary is structured as below:
  Subtype Code: 10; Dictionary:
    {
        'Default': False,
        'Name': u'Sleeve', #<--this is the subtype name in the code
        'SubtypeField': u'Subtype',
        'FieldValues':
            {u'FacilityID': (None, None),
             u'LocationDescription': (None, None),
             u'AdministrativeArea': (u'CITY', <Workspace Domain object object at 0x1D1FF240>),
             u'Elevation': (None, None),
             u'InstallDate': (None, None),
             u'Material': (u'CI', <Workspace Domain object object at 0x1D1FFB70>),
             u'XCoord_GPS': (None, None),
             u'Rotation': (None, None),
             u'Diameter2': (6, <Workspace Domain object object at 0x1D1FF1A0>),
             u'Diameter3': (0, <Workspace Domain object object at 0x1D1FFB60>),
             u'Diameter1': (6, <Workspace Domain object object at 0x1D1FF320>),
             u'WaterType': (u'Potable', <Workspace Domain object object at 0x1D5298A0>),
             u'GISOBJID': (None, None),
             u'OBJECTID': (None, None),
             u'Enabled': (1, <Workspace Domain object object at 0x1D1FF2A0>),
             u'Subtype': (10, None),
             u'JointType': (u'MJ', <Workspace Domain object object at 0x1D1FF8F0>),
             u'Date_GPS': (None, None),
             u'OperationalArea': (u'LS', <Workspace Domain object object at 0x1D1FF290>),
             u'YCoord_GPS': (None, None),
             u'WorkorderID': (None, None),
             u'AncillaryRole': (None, None),
             u'Shape': (None, None),
             u'Diameter4': (0, <Workspace Domain object object at 0x06D53730>),
             u'UDI': (None, None),
             u'LifecycleStatus': (u'ACT', <Workspace Domain object object at 0x06D53BF0>)
             }
        }
    """
