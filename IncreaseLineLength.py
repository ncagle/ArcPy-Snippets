'''
-------------------------------------------------------------------------------
Tool Name:  Increase Line Length
Source Name: IncreaseLineLength.py
Version: ArcGIS 10.3
Author: ESRI

Selects lines shorter than the specified length and extends them in both
directions until they meet the specified length.

-------------------------------------------------------------------------------
'''
# 1. Get features that meet minimum length criteria
# 2. Get the center point of the line
# 3. Calculate angle of this feature (from center point) with respect to the x-axis
# 4. Calculate the new X,Y point for each end of the line (using center point as base point)
# 5. Create new polyline Geometry
# 6. Use UpdateCursor to update geometry of original line
#-------------------------------------------------------------------------------

import arcpy
import math
import arcpyproduction.generalization as gen
import common
import productionscripting

class LicenseError(Exception):
    """Function for capturing errors with extension licenses"""
    pass

def main():
    """ Main function logic"""
    try:
        # Set the workspace
        arcpy.env.workspace = arcpy.env.scratchGDB
        arcpy.env.overwriteOutput = True

        # Input Params
        input_lines = arcpy.GetParameter(0)
        minimum_length = arcpy.GetParameterAsText(1)
        edit = arcpy.da.Editor(productionscripting.generalization.GetWorkspace(input_lines))
        session = productionscripting.generalization.IsBeingEdited(input_lines)
        desc = arcpy.Describe(input_lines)
        isVersioned = desc.IsVersioned
        canVersion = desc.canVersion
        #Check for common issues with input data
        #Return warning message if data is not projected
        common.check_projection(input_lines)


        desc = arcpy.Describe(input_lines)
        spatial_ref = desc.spatialReference
        length_field = desc.lengthFieldName
        #Check for common issues with input data
        advanced = arcpy.SetProduct('arcinfo')
        standard = arcpy.SetProduct('arceditor')
        serverlicense = arcpy.SetProduct('arcserver')
        if advanced == 'AlreadyInitialized' or serverlicense == 'AlreadyInitialized' or serverlicense == 'CheckedOut' or standard == 'AlreadyInitialized' or standard == 'CheckedOut' or advanced == 'CheckedOut':
            if int(arcpy.GetCount_management(input_lines)[0]) > 0:

                if canVersion == 1:
                    if isVersioned == 1:
                        edit.startEditing(False, True)
                        edit.startOperation()
##                else:
##                    if session == 0:
##                        edit.startEditing(False, True)
##                        edit.startOperation()
                # Get features that meet selection criteria
                convert_units = gen.ConvertLinearUnits(minimum_length, input_lines)
                where_clause = length_field  + "<" +  str(convert_units)
                arcpy.MakeFeatureLayer_management(input_lines, "count", where_clause)
                if arcpy.GetCount_management("count") > 0:
                    with arcpy.da.SearchCursor(input_lines, ("OID@", "SHAPE@", length_field), where_clause) as cursor:
                        for row in cursor:
                            orig_polyline_geometry = row[1]
                            # Get start and end points of line
                            orig_start_point = orig_polyline_geometry.firstPoint
                            orig_end_point = orig_polyline_geometry.lastPoint

                            # Get center X,Y point of line
                            center_point_geo = orig_polyline_geometry.positionAlongLine(0.5, True)
                            center_point = center_point_geo.firstPoint
                            arcpy.AddMessage("Modifying Object ID {2}".format(center_point_geo.firstPoint.X, center_point_geo.firstPoint.Y, row[0]) + '...')

                            # Calculate the angle between this line and x-axix
                            radian = math.atan2((orig_polyline_geometry.lastPoint.Y - orig_polyline_geometry.firstPoint.Y), (orig_polyline_geometry.lastPoint.X - orig_polyline_geometry.firstPoint.X))
                            arcpy.AddMessage("Original Length  = {0} ".format(str(orig_polyline_geometry.length)) + '...')

                            # Calculate element's new height and width
                            # (for half the minimum_length). Make sure
                            #  absolute value of new height and width is used
                            new_wd = math.fabs(convert_units/2 * math.cos(radian))
                            new_ht = math.fabs(convert_units/2 * math.sin(radian))

                            # Calculate the new X,Y
                            # For the first half of line - end point is already
                            # center point of original line
                            # For the second half of line - start point is already
                            # center point of original line
                            start_point = arcpy.Point()
                            end_point = arcpy.Point()

                            if orig_start_point.X > orig_end_point.X:
                                start_point.X = float(center_point.X + new_wd)
                                end_point.X = float(center_point.X - new_wd)
                            else:
                                start_point.X = float(center_point.X - new_wd)
                                end_point.X = float(center_point.X + new_wd)

                            if orig_start_point.Y > orig_end_point.Y:
                                start_point.Y = float(center_point.Y + new_ht)
                                end_point.Y = float(center_point.Y - new_ht)
                            else:
                                start_point.Y = float(center_point.Y - new_ht)
                                end_point.Y = float(center_point.Y + new_ht)

                            # Create new Polyline
                            array = arcpy.Array([start_point, end_point])
                            new_geo = arcpy.Polyline(array, spatial_ref)
                            with arcpy.da.UpdateCursor(input_lines, ("OID@", "SHAPE@"), "OBJECTID=" + str(row[0])) as update_cursor:
                                for update_row in update_cursor:
                                    # Update geometry
                                    update_row = (update_row[0], new_geo)
                                    update_cursor.updateRow(update_row)
                                    arcpy.AddMessage("Updated geometry...")


                    # Set output data
                    arcpy.SetParameter(2, input_lines)
                    if canVersion == 1:
                        if isVersioned == 1:
                            if session == 0:
                                edit.stopOperation()
                                edit.stopEditing(True)
                            else:
                                edit.stopOperation()

##                    else:
##                        if session == 0:
##                            edit.stopOperation()
##                            edit.stopEditing(True)

                else:
                    arcpy.AddIDMessage("INFORMATIVE", 401)
            else:
                arcpy.AddIDMessage("INFORMATIVE", 401)
        else:
            arcpy.AddIDMessage("Error",626, "[Increase Line Length]")
            arcpy.AddError("Tool requires a Standard or Advanced license.")

    except arcpy.ExecuteError:
        arcpy.AddError("ArcPy Error Message: {0}".format(arcpy.GetMessages(2)))
    except LicenseError:
        arcpy.AddError("Production Mapping license is unavailable")
    except Exception, exc:
        arcpy.AddError(str(exc.message))


    finally:
        arcpy.RefreshActiveView()


if __name__ == '__main__':
    main()
