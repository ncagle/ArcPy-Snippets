'''
-------------------------------------------------------------------------------
Tool Name:  Remove Cutbacks
Source Name: RemoveCutbacks.py
Version: ArcGIS 10.5
Author: ESRI

Remove cutbacks from polyline or polygon features.
-------------------------------------------------------------------------------
'''

import math
import os
import arcpy
#import arcpyproduction.generalization as gen
import productionscripting
#import common
class LicenseError(Exception):
    """Function for capturing errors with extension licenses"""
    pass


def convert_cutbacks_list_to_dict(cutbacks_list):
    '''private function to convert cutbacks list'''
    cutbacks_oid_list = []
    cutbacks_dict = {}

    for oid, part_num, idx_num in cutbacks_list:
        if oid not in cutbacks_oid_list:
            cutbacks_oid_list.append(oid)

        key = "{0}:{1}:{2}".format(oid, part_num, idx_num)
        cutbacks_dict[key] = True

    return (cutbacks_oid_list, cutbacks_dict)


def remove_cutbacks(in_features, cutbacks_list):
    '''remove cutbacks'''

    cutbacks_oid_list = []
    cutbacks_dict = {}
    (cutbacks_oid_list, cutbacks_dict) = convert_cutbacks_list_to_dict(cutbacks_list)

    desc = arcpy.Describe(in_features)
    shape_type = ""
    if hasattr(desc, "ShapeType"):
        shape_type = desc.ShapeType
    else:
        return

    spat_ref = desc.spatialReference
    hasZ = desc.hasZ
    hasM = desc.hasM
    oid_field_name = desc.OIDFieldName

    # loop through cutback points, update geometry
    # note: polygon rings will auto close
    for oid in cutbacks_oid_list:
        with arcpy.da.UpdateCursor(in_features, ["OID@", "SHAPE@"], '"{0}"={1}'.format(oid_field_name, oid)) as update_cursor:
            for row in update_cursor:
                geom = row[1]

                parts_array = arcpy.Array()
                for part_num, part in enumerate(geom):
                    points_array = arcpy.Array()
                    for idx_num, point in enumerate(part):
                        key = "{0}:{1}:{2}".format(oid, part_num, idx_num)
                        if not cutbacks_dict.has_key(key):
                            points_array.add(point)
                    parts_array.add(points_array)
                    # points_array.removeAll

                new_geom = None
                if shape_type == "Polyline":
                    new_geom = arcpy.Polyline(parts_array, spat_ref, hasZ, hasM)
                elif shape_type == "Polygon":
                    new_geom = arcpy.Polygon(parts_array, spat_ref, hasZ, hasM)
                else:
                    new_geom = geom

                #update geometry
                row[1] = new_geom
                update_cursor.updateRow(row)

                parts_array.removeAll()


def log_cutbacks(cutback_points_log, output_fc):
    ''' record cutbacks to an output point feature class'''
    # loop through cutback points log, record to output point feature class
    with arcpy.da.InsertCursor(output_fc, ["ORIGFID", "ANGLE", "DESCRIPTION", "SHAPE@XY"]) as pt_cursor:
        for origfid, angle, pt_xy in cutback_points_log:
            pt_cursor.insertRow((origfid, angle, "Cutback", pt_xy))


def log_points_snapped_to_features(points_snapped_to_features, output_fc):
    '''save those points that were skipped to an output point feature class.
    These points were skipped because they snapped to other features.
    '''
    # loop through list, log point to output point feature class
    with arcpy.da.InsertCursor(output_fc, ["ORIGFID", "ANGLE", "DESCRIPTION", "SHAPE@XY"]) as ptCursor:
        for origfid, angle, pt_xy in points_snapped_to_features:
            ptCursor.insertRow((origfid, angle, "Ignored as it snaps to other feature(s).", pt_xy))


def create_cutbacks_feature_class(output_fc, spat_ref):
    '''create output cutbacks point feature class'''

    #out_path = os.path.dirname(output_fc)
    out_name = os.path.basename(output_fc) + "_temp"
    has_m = "DISABLED"
    has_z = "DISABLED"

    # create in_memory first, as an work around for "error 000464"
    # "error 000464: Cannot get exclusive schema lock.  Either being edited or
    # in use by another application."
    im_fc = arcpy.CreateFeatureclass_management("in_memory", out_name, "POINT", "", has_m, has_z, spat_ref, arcpy.env.configKeyword)
    #arcpy.CreateFeatureclass_management(out_path, out_name, "POINT", "",
    #has_m, has_z, spat_ref, arcpy.env.configKeyword)

    # add "ORIGID", "ANGLE", and "DESCRIPTION" columns
    arcpy.AddField_management(im_fc, "ORIGFID", "LONG")
    arcpy.AddField_management(im_fc, "ANGLE", "DOUBLE")
    arcpy.AddField_management(im_fc, "DESCRIPTION", "TEXT", "", "", 255)

    output_fc = arcpy.CopyFeatures_management(im_fc, output_fc)
    arcpy.Delete_management(im_fc)

    return output_fc


def calculate_angle(tri_pt0, tri_pt1, tri_pt2):
    '''calcuate the angle formed by three points'''

    # calculate the angle
    ang1 = math.atan2((tri_pt0.Y - tri_pt1.Y), (tri_pt0.X - tri_pt1.X))
    ang2 = math.atan2((tri_pt2.Y - tri_pt1.Y), (tri_pt2.X - tri_pt1.X))
    ang = math.degrees(abs(ang2 - ang1))
    if ang > 180:
        ang = 360 - ang

    return ang

def main():
    """ Main function logic"""

    ALMOST_ZERO_VALUE = 1E-09     # small value used to check if angle is close to zero

    try:
        license = arcpy.arcpy.SetProduct('arcinfo')
        serverlicense = arcpy.arcpy.SetProduct('arcserver')
        if license in ('AlreadyInitialized', 'CheckedOut') or serverlicense in ('AlreadyInitialized', 'CheckedOut'):

            #arcpy.env.overwriteOutput = True
            #arcpy.env.addOutputToMap=False

            # get parameters
            in_features = arcpy.GetParameterAsText(0)
            min_angle = float(arcpy.GetParameterAsText(1))
            removal_method = arcpy.GetParameterAsText(2)
            is_check_for_errors_only = (arcpy.GetParameterAsText(3).lower() == "true")
            is_ignore_pts_snapped = (arcpy.GetParameterAsText(4).lower() == "true") #  "ignore points snapped to features"
            output_points_fc = arcpy.GetParameterAsText(5)

            # removal method (optional) default to value "SEQUENTIAL"
            if removal_method is None:
                removal_method = "SEQUENTIAL"
            elif removal_method == '' or removal_method == '#':
                removal_method = "SEQUENTIAL"

            # validate whether in_isCheckForErrorsOnly and
            # in_isIgnorePointsSnappedToFeatures are valid.
            # "If check for errors is enabled, then unselect and disable this
            # option "ignore points snapped for features"
            if is_check_for_errors_only:
                is_ignore_pts_snapped = False

            shape_type = ""
            desc = arcpy.Describe(in_features)
            if hasattr(desc, "ShapeType"):
                shape_type = desc.ShapeType
            if shape_type != "Polygon" and shape_type != "Polyline":
                arcpy.AddError("Invalid input feature class. The input feature class must be either Polygon or Polyline.")
                return

            in_feature_class = desc.catalogPath
            spat_ref = desc.spatialReference
            arcpy.env.outputCoordinateSystem = spat_ref
            # hasZ = desc.hasZ
            # hasM = desc.hasM
            # oid_field_name = desc.OIDFieldName
            is_versioned = desc.isVersioned
            can_version = desc.canVersion

            ## check out Production Mapping extension
            #if arcpy.CheckExtension("Foundation"):
            #    status=arcpy.CheckOutExtension("Foundation")
            #else:
            #    raise LicenseError("[Production Mapping] license not
            #    available.")

            # fix for Bug 91411, 91377, and 91376
            #Note: commented out to avoid PM license error during debug
            wksp = productionscripting.generalization.GetWorkspace(in_features)
            is_being_edited = productionscripting.generalization.IsBeingEdited(in_features)
            #note: uncomment when debugging
            #wksp = common.get_workspace(in_features)
            wksp_type = arcpy.Describe(wksp).workspaceType
            edit = arcpy.da.Editor(wksp)
            #is_being_edited = edit.isEditing


            # when check for errors only, store cutback points in the output
            # points feature class
            # when ignore points snapped to features, store the ignored points
            # in the output points feature class
            if is_check_for_errors_only or is_ignore_pts_snapped:
                if output_points_fc is None:
                    arcpy.AddError("Output feature class parameter is not provided.")
                    return
                elif arcpy.Exists(output_points_fc):
                    arcpy.Delete_management(output_points_fc)

                # create a point feature class
                create_cutbacks_feature_class(output_points_fc, spat_ref)

            # fix for #91479.
            # get feature class from feature layer, and use it for check for
            # the reasons that in ArcMap:
            #     1.  in_features could be just a selection set made by user
            #     2.  in_features could be a feature layer with definition
            #     query, thus only a subset of the feature class
            temp_layer = "temp_feat_layer"
            if is_ignore_pts_snapped:
                arcpy.MakeFeatureLayer_management(in_feature_class, temp_layer)
                #arcpy.MakeFeatureLayer_management(in_features, temp_layer)

            # -- detect cutbacks ---
            tri_pt = []                        # three points used to calculate angle
            points_to_log = []                 # cutback points to record to table, when "check for errors
                                               # only" option is selected
            points_snapped_to_features = []    # cutback points ignored due to snapped to features
            points_to_remove = []              # cutback points to remove
            points_to_remove_count = 0         # the count used for reporting.  different from
                                               # "len(points_to_remove)" due to the closing point of polygon ring(s)
            with arcpy.da.SearchCursor(in_features, ["OID@", "SHAPE@"]) as read_cursor:
                for row in read_cursor:
                    # check geometry for cutbacks
                    geom = row[1]
                    if geom is None:
                        continue

                    # at least 2 vetice for polyline, at least 4 vertice for
                    # polygon
                    # (starting point and ending point counts as 2 items, even
                    # though they are at the same location)
                    min_vert_count = 4 if shape_type == "Polygon" else 2

                    for partNum, part in enumerate(geom):
                        del tri_pt[:]        #reset array

                        # skip if removing a vertex will cause empty/invalid
                        # geometry
                        if len(part) <= min_vert_count:
                            continue

                        if shape_type == "Polygon":
                            # need to test the first/last vertex for polygon
                            part.add(None)

                        ring_starting_point_index = 0
                        second_point = None
                        for indexNum, point in enumerate(part):
                            is_cutback = False

                            if point is not None:
                                if shape_type == 'Polygon':
                                    if indexNum == ring_starting_point_index + 1:
                                        second_point = point

                                tri_pt.append(point)
                                if len(tri_pt) < 3:
                                    continue

                                # if reaching 3 points, then calculate the
                                # angle
                                ang = calculate_angle(tri_pt[0], tri_pt[1], tri_pt[2])
                                if ang < min_angle:
                                    is_cutback = True
                                    if is_check_for_errors_only:
                                        points_to_log.append((row[0], ang, tri_pt[1]))
                                    else:
                                        # check if the angle is close to 0 (or
                                        # 360) degrees, aka vertex falls back
                                        # forth on the line.
                                        # if it does, then skip and add a
                                        # warning message
                                        if ang < ALMOST_ZERO_VALUE:
                                            is_cutback = False
                                            arcpy.AddWarning("Skipped point (FeatureID: {0}, Part {1}, Vetex: {2}) because it has an angle close to 0 or 360 degree.".format(row[0], partNum, indexNum - 1))

                                        # further check if it touches other
                                        # feature(s).
                                        # if it does, then skip the point and
                                        # log in output table/fc
                                        elif is_ignore_pts_snapped:
                                            # if geometry is a polygon, use Boundary Touches
                                            # to keep cutback if touches edge of
                                            # another polygon (not inside)
                                            if shape_type == "Polygon":
                                                arcpy.SelectLayerByLocation_management(temp_layer, 'BOUNDARY_TOUCHES', arcpy.PointGeometry(tri_pt[1], spat_ref), "", "NEW_SELECTION")
                                            #if geometry is a like, use Intersect
                                            # as boundary touches would only flag
                                            # if cutback touches the end of another line
                                            elif shape_type == "Polyline":
                                                arcpy.SelectLayerByLocation_management(temp_layer, 'INTERSECT', arcpy.PointGeometry(tri_pt[1], spat_ref), "", "NEW_SELECTION")
##                                            arcpy.AddMessage("selection cnt " + str(arcpy.GetCount_management(temp_layer)[0] ))
                                            if int(arcpy.GetCount_management(temp_layer)[0]) > 1:
##                                                arcpy.AddMessage("Point Touches")
                                                is_cutback = False
                                                points_snapped_to_features.append((row[0], ang, tri_pt[1]))

                                        if is_cutback:
                                            points_to_remove.append((row[0], partNum, indexNum - 1))
                                            points_to_remove_count += 1

                                #pop the middle point for remove method option
                                #"SEQUENTIAL", when a cutback vertex was found.
                                #Thus it shall not be used to next point.
                                #otherwise, pop the first point, if "ALL", or
                                #if the middle point is not a Cutback point.
                                tri_pt.pop(1 if (is_cutback and removal_method == "SEQUENTIAL") else 0)

                            else:
                                if shape_type == "Polygon":
                                    # interior ring coming up.
                                    # for polygon, necessary to run a cutback
                                    # test for the closing point in a ring (aka
                                    # the 1st and last)
                                    tri_pt.append(second_point)
                                    if len(tri_pt) < 3:
                                        continue

                                    ang = calculate_angle(tri_pt[0], tri_pt[1], tri_pt[2])
                                    if ang < min_angle:
                                        is_cutback = True

                                        if is_check_for_errors_only:
                                            points_to_log.append((row[0], ang, tri_pt[1]))
                                        else:
                                            if ang < ALMOST_ZERO_VALUE:
                                                is_cutback = False
                                                arcpy.AddWarning("Skipped point (FeatureID: {0}, Part: {1}, Vetex: {2}) because it has an angle close to 0 or 360 degree.".format(row[0], partNum, indexNum - 1))
                                            elif is_ignore_pts_snapped:
                                                arcpy.SelectLayerByLocation_management(temp_layer, 'BOUNDARY_TOUCHES', arcpy.PointGeometry(tri_pt[1], spat_ref), "", "NEW_SELECTION")
                                                if arcpy.GetCount_management(temp_layer)[0] > 1:
                                                    is_cutback = False
                                                    points_snapped_to_features.append((row[0], ang, tri_pt[1]))

                                            if is_cutback:
                                                # need to remove the closing
                                                # point (aka, in ArcPy, the 1st
                                                # and the last points in
                                                # current ring.  )
                                                points_to_remove.append((row[0], partNum, ring_starting_point_index))
                                                points_to_remove.append((row[0], partNum, indexNum - 1))
                                                points_to_remove_count += 1      # note: closing points count as only 1 point in reporting

                                    ring_starting_point_index = indexNum + 1

                                # reset point array
                                del tri_pt[:]

            #search cursor ends ->
            del temp_layer


            # check if the tool needs to start editing and operation
            start_editing_operation = (not is_being_edited) and ((can_version and is_versioned) or not can_version)

            #arcpy.AddMessage('Being Edited:{}, CanVersion:{}, Versioned:{}'.format(is_being_edited,can_version,is_versioned))

            #if start_editing_operation == True:
            #    edit.startEditing(False, True)
            #    edit.stopOperation()

            if wksp_type == "RemoteDatabase":
                edit.startEditing(False, True)
                edit.startOperation()
            else:
                if start_editing_operation == True:
                    edit.startEditing(False,True)
                    edit.startOperation()

            if is_check_for_errors_only:
                # log cutbacks to output point feature class
                log_cutbacks(points_to_log, output_points_fc)
                arcpy.AddMessage("{0} cutbacks were identified and recorded to {1}.".format(len(points_to_log), output_points_fc))
            else:
                if is_ignore_pts_snapped:
                    log_points_snapped_to_features(points_snapped_to_features, output_points_fc)
                    arcpy.AddMessage("{0} cutbacks were ignored and recorded to {1}.".format(len(points_snapped_to_features), output_points_fc))

                # remove cutbacks
                remove_cutbacks(in_features, points_to_remove)
                arcpy.AddMessage("{0} cutbacks were identified and deleted.".format(points_to_remove_count))


            if wksp_type == "RemoteDatabase":
                edit.stopOperation()
                if is_being_edited == False:
                    edit.stopEditing(True)
            else:
                if start_editing_operation == True:
                    edit.stopOperation()
                    edit.stopEditing(True)


            #stop operation and editing if we started them in this tool
            #if start_editing_operation == True:
            #   edit.stopOperation()
            #   edit.stopEditing(True)

            # run RepairGeometry on feature class for file geodatabase and
            # shapefile only.  skip for enterprise gdb
            if (wksp_type == "FileSystem" or wksp_type == "LocalDatabase"):
                #arcpy.RepairGeometry_management(in_features, "KEEP_NULL")
                arcpy.RepairGeometry_management(in_features)


    except arcpy.ExecuteError:
        arcpy.AddError("ArcPy Error Message: {0}".format(arcpy.GetMessages(2)))
        print ("ArcPy Error Message: {0}".format(arcpy.GetMessages(2)))
    except LicenseError:
        arcpy.AddError("Production Mapping license is unavailable")
    except Exception, exc:
        arcpy.AddError(str(exc.message))
        print(str(exc.message))
    finally:
        #arcpy.CheckInExtension("Foundation")
        arcpy.RefreshActiveView()


if __name__ == "__main__":
    main()
