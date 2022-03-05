'''
-------------------------------------------------------------------------------
 Tool Name:  Delete Polygon And Extend Lines
 Source Name: DeletePolygonAndExtendLines.py
 Version: ArcGIS 10.3
 Author: ESRI

 Polygon features that are smaller than the specified area and connected to 2
 or more line features will be deleted and the lines will be extended to meet
 at the center of the polygon.

-------------------------------------------------------------------------------
'''

#import os
import arcpy
import common
import productionscripting
import arcpyproduction.generalization as gen

class LicenseError(Exception):
    """Function for capturing errors with extension licenses"""
    pass

def find_poly_multiple_intersections(polygon, line):
    """ determines which polygons intersect multiple lines"""
    duplist = []

    # generate Near Table of polygons that touch lines
    near = arcpy.GenerateNearTable_analysis(polygon, line, "PolyNearTable", "0 Meters",
                                    "NO_LOCATION","NO_ANGLE","ALL","0")

##    arcpy.AddMessage("near cnt " + str(int(arcpy.GetCount_management(near)[0])))
    #Get a list of all the OIDs of polygons that touch lines
    poly_ids = [row[0] for row in arcpy.da.SearchCursor(near, "IN_FID")]

    #Determine which of these polygons touch more than one line
    duplist = [str(x) for i, x in enumerate(poly_ids) if poly_ids.count(x) > 1]

    #Get a list with each value listed once
    dupset = set(duplist)

##    arcpy.AddMessage(str(len(dupset)))
    # Now get a dictionary of all the Poly id and line id matches
    dupdict = {}

    # order the records in the table by the polygon ids
    sql = "ORDER BY IN_FID ASC"
    in_id = 0
    line_ids = []
    # loop through all the records
    with arcpy.da.SearchCursor(near, ["IN_FID", "NEAR_FID"], sql_clause = (None, sql)) as cursor:
        for row in cursor:
            #get the polygon and line ids
            poly_id = row[0]
            line_id = row[1]
            #if the polygon id is not the same as the previous id,
            if in_id != 0 and in_id != poly_id:
                #add the array of line ids to the dictionary and clear array
                dupdict[str(in_id)] = line_ids
                line_ids = []
            #add the line ID to the array and get the poly id
            line_ids.append(str(line_id))
            in_id = poly_id

    #When done with the loop, add the final polyid and line array to the dict
    dupdict[str(in_id)] = line_ids

    return dupset, dupdict

def extend_polyline_to_point(layer, extension_pt, spatial_ref, ids):
    """
       Extends a polyline's closest endpoint to a point
       Input:
          layer - feature layer - should be a selection set
          extension_pt - arcpy.PointGemetry() object
       Returns:
          None
    """
    try:
        array = arcpy.Array()
        query = ""
        where = "OBJECTID = "
        where += " OR OBJECTID = ".join(ids)

        with arcpy.da.UpdateCursor(layer, ["SHAPE@", "oid@"], where) as rows:
            for row in rows:
                line_geom = row[0]
                first_point = line_geom.firstPoint
                last_point = line_geom.lastPoint
                if extension_pt.distanceTo(first_point) > extension_pt.distanceTo(last_point):
                    for part in row[0]:
                        for pnt in part:
                            array.add(pnt)
                        break
                    array.add(extension_pt.centroid)
                else:
                    array.add(extension_pt.centroid)
                    for part in row[0]:
                        for pnt in part:
                            array.add(pnt)
                        break
                polyline = arcpy.Polyline(array, spatial_ref)
                array.removeAll()
                row[0] = polyline
                rows.updateRow(row)
                del row
                del first_point
                del last_point
                del line_geom

        return True
    except Exception, exc:
        arcpy.AddError(str(exc.message))
        return False


def create_delete_layer(input_polygon, delete_oids):
    """Returns a feature layer with a selection set of features to delete """
    desc = arcpy.Describe(input_polygon)
    oid_delimited = desc.oidFieldName
    del_lyr = arcpy.MakeFeatureLayer_management(desc.catalogPath, "delete_lyr")


    query = "OBJECTID = "
    query += " OR OBJECTID = ".join(delete_oids)

##    arcpy.AddMessage(query)

    arcpy.SelectLayerByAttribute_management(del_lyr, "NEW_SELECTION", query)

    selection_count = int(arcpy.GetCount_management(del_lyr)[0])
    arcpy.AddMessage("Selected " + str(selection_count) + " features to delete")

    return del_lyr

def check_layer_count(layer):
    if int(arcpy.GetCount_management(layer)[0]) == 0:
        desc = arcpy.Describe(layer)
        if desc.dataType == "FeatureLayer":
            layer = desc.featureClass.catalogPath
    return layer

def main():
    """ main driver of program """
    try:
        #Check for license level
        license = arcpy.SetProduct('arcinfo')
        serverlicense = arcpy.SetProduct('arcserver')
        if license == 'AlreadyInitialized' or serverlicense == 'AlreadyInitialized' or serverlicense == 'CheckedOut' or license == 'CheckedOut':
            input_line_fc = check_layer_count(arcpy.GetParameterAsText(0))
            input_line = arcpy.MakeFeatureLayer_management(input_line_fc, "input_line")
            input_poly_fc = check_layer_count(arcpy.GetParameterAsText(1))
            input_polygon = arcpy.MakeFeatureLayer_management(input_poly_fc, "input_poly")
            edit = arcpy.da.Editor(productionscripting.generalization.GetWorkspace(input_line_fc))
            session = productionscripting.generalization.IsBeingEdited(input_line_fc)
            desc = arcpy.Describe(input_line_fc)
            isVersioned = desc.IsVersioned
            canVersion = desc.canVersion


            #convert minimum area value to comparable value in data units.
            minimum_area = gen.ConvertArealUnits(arcpy.GetParameterAsText(2), input_polygon)

            del_features = ""
            compare_list = arcpy.GetParameterAsText(3)
            check_areal = arcpy.GetParameterAsText(2)
            if float(check_areal.split(" ")[0]) <= 0:
                arcpy.AddError("Minimum area must be above 0.")
            else:
                all_input = [input_line, input_polygon]


                compare_fcs = []
                for item in compare_list.split(";"):
                    item = item.strip("'")
                    arcpy.AddMessage(item)
                    compare_fcs.append(item)

                arcpy.AddMessage(compare_fcs)
                #Return warning message if data is not projected
                common.check_projection(input_polygon)
                if (common.check_matching_workspace(all_input)):

                    delete_oids = []

                    # Set the workspace
                    arcpy.env.workspace = arcpy.env.scratchGDB
                    arcpy.env.overwriteOutput = True



                    #Get properties from the input feature class
                    desc = arcpy.Describe(input_polygon)

                    spatial_ref = desc.spatialReference



                    # Create query for features smaller than minimum size
                    query = ""
                    if minimum_area and minimum_area >= 0:
                        query = "{0} <= {1}".format(desc.areaFieldName, minimum_area)


##                    arcpy.AddMessage(query)

                    #Select only those features with area smaller than minimum size
                    arcpy.SelectLayerByAttribute_management(input_polygon, "NEW_SELECTION", query)

        ##            arcpy.AddMessage(str(int(arcpy.GetCount_management(input_polygon)[0])))
        ##            # do initial select determine which polygons may need to be deleted
        ##            # the polygon must intersect at least one line feature
        ##            arcpy.SelectLayerByLocation_management(input_polygon, "INTERSECT", input_line, "", "SUBSET_SELECTION")
                    # generate a list of polygons that touch more than one line
                    poly_ids, dupdict = find_poly_multiple_intersections(input_polygon, input_line)
                    if int(arcpy.GetCount_management(input_line)[0]) > 0 and int(arcpy.GetCount_management(input_polygon)[0]) > 0:

                        if canVersion == 1:
                            if isVersioned == 1:
                                edit.startEditing(False, True)
                                edit.startOperation()
                        else:
                            if session == 0:
                                edit.startEditing(False, True)
                                edit.startOperation()
                        # If at least one feature meets the initial criteria, loop through them
                        if len(poly_ids) > 0:
                            arcpy.AddMessage(str(len(poly_ids))
                                + " polygons intersect lines.  Determining which "
                                + " polygons intersect more than one line...")
                            where = "OBJECTID = "
                            where += " OR OBJECTID = ".join(poly_ids)

                            with arcpy.da.SearchCursor(input_polygon, ["SHAPE@", 'oid@'], where) as rows:
                                for row in rows:

                                    #determine which lines intersect the polygon
            ##                        arcpy.SelectLayerByLocation_management(input_line, "INTERSECT", row[0], "", "NEW_SELECTION")
            ##                        where = "IN_FID = " + str(row[1])

                                    line_ids = dupdict[str(row[1])]

                                    #if more than one line interscts...
                                    if len(line_ids) > 1:
                                        #... get the centerpoint of the polygon
                                        geom_to_merge = arcpy.PointGeometry(row[0].centroid, spatial_ref)
                                        # ... extend the lines to the centerpoint
                                        arcpy.AddMessage("Extending lines that intersect polygon"
                                                        + " with OID " + str(row[1])+ "...")
                                        success = extend_polyline_to_point(input_line, geom_to_merge, spatial_ref, line_ids)
                                        # ... add the polygon to the list of features to delete
                                        if success:
                                            delete_oids.append(str(row[1]))

                                        del geom_to_merge


                            #if features need to be deleted
                            if len(delete_oids) >= 1:
                                arcpy.AddMessage(str(len(delete_oids))
                                                + " features to be deleted...")

                                #Create a feature layer and select the features to delete
                                del_features = create_delete_layer(input_polygon, delete_oids)

                                # If features are selected as comparison features

                                if len(compare_list) > 0:

                                    # If a feature to be deleted is fully touches more than
                                    # one feature from the comparsion feature classes,
                                    # convert the feature to whatever comparsion feature
                                    # shares the longest boundary
                                    arcpy.AddMessage("Converting polygons that intersect"
                                                    + " features from the compare feature"
                                                    + " class.")

                                    gen.ConvertIntersectingPolygons(del_features, compare_fcs)

                                # Finally, delete any features that were not converted
                                #Create a feature layer and select the features to delete
                                if int(arcpy.GetCount_management(del_features)[0]) > 0:
                                    arcpy.AddMessage("Deleting " +
                                            str(int(arcpy.GetCount_management(del_features)[0]))
                                            + " features that were not converted.")
                                    with arcpy.da.UpdateCursor(del_features, ['oid@']) as rows:
                                        for row in rows:
                                            rows.deleteRow()
                                arcpy.SelectLayerByAttribute_management(del_features, "CLEAR_SELECTION")
                            if canVersion == 1:
                                if isVersioned == 1:
                                    if session == 0:
                                        edit.stopOperation()
                                        edit.stopEditing(True)
                                    else:
                                        edit.stopOperation()
                            else:
                                    if session == 0:
                                        edit.stopOperation()
                                        edit.stopEditing(True)


                    else:
                        arcpy.AddIDMessage("INFORMATIVE", 401)
        else:
            arcpy.AddIDMessage("Error",626, "[Delete Polygon and Extend Lines]")
            arcpy.AddError("Tool requires an Advanced license.")

    except arcpy.ExecuteError:
        arcpy.AddError("ArcPy Error Message: {0}".format(arcpy.GetMessages(2)))
    except LicenseError:
        arcpy.AddError("Production Mapping license is unavailable")
    except Exception, exc:
        arcpy.AddError(str(exc.message))


    finally:

        clean_list = ["input_poly", "input_line", "in_memory\\PolyNearTable", "delete_lyr"]
        for item in clean_list:
            if arcpy.Exists(item):
                arcpy.Delete_management(item)

        arcpy.RefreshActiveView()



if __name__ == "__main__":
    arcpy.env.overwriteOutput = True

    main()
