'''
-------------------------------------------------------------------------------
Tool Name:  Remove Self Intersections
Source Name: RemoveSelfIntersections.py
Version: ArcGIS 10.4.1
Author: ESRI

Removes self-intersecting portions of features beyond their vertices of intersection
in an input line or polygon feature class.

-------------------------------------------------------------------------------
'''

import arcpy
import arcpyproduction.generalization as gen
import productionscripting
import os

from operator import itemgetter
from itertools import groupby


'''
Identify the end loops which may need to be excluded from the self intersections
'''
def identifyEndLoops( segment_features, compareField ):

    vertices = arcpy.FeatureVerticesToPoints_management(segment_features,"vertices","BOTH_ENDS")

    intersection_points = arcpy.FindIdentical_management("vertices","intersection_points",["SHAPE",compareField],output_record_option="ONLY_DUPLICATES")

    # Populate [seqId, featId] dictionary to identify end loop vertices
    idDict = {}
    with arcpy.da.SearchCursor(intersection_points, ["FEAT_SEQ", "IN_FID"]) as cursor:
        for row in cursor:
            seqId  = row[0]
            featId = row[1]
            if seqId in idDict:
                idDict[seqId].append(featId)
            else:
                idDict[seqId] = [featId]

    endLoopPoints = [item for item in idDict.values() if len(item) == 3]

    # Populate [vertexId,segmentId] dictionary to identify segment ids from set of vertices
    flatList = [item for subList in endLoopPoints for item in subList]
    verWhereClause = createWhereClauseFromIDList(flatList)

    segDict = {}
    with arcpy.da.SearchCursor(vertices, ["OID@", "ORIG_FID"],verWhereClause) as cursor:
        for row in cursor:
            vertexId  = row[0]
            segmentId = row[1]
            segDict[vertexId] = segmentId

    # Identify end loop segment ids
    endLoopDict = {}
    for item in endLoopPoints:
        for vertexId in item:
            if vertexId not in segDict:
                continue
            segId = segDict[vertexId]

            if segId in endLoopDict:
                endLoopDict[segId] += 1
            else:
                endLoopDict[segId] = 1

    endSegmentIds = [item[0] for item in endLoopDict.items() if item[1] > 1]
    return endSegmentIds

'''
Given the shapeType (tool allows only Polyline or Polygon) and inputFeatures, return the set of
features that self-intersect.
'''
def identifySelfIntersections(shapeType, inputFeatures, maxRemovalLength, endPointRemoval, onlyCheckErrors, outputTable):

    intersectingFeatures = None
    comparisonFieldName = None

    # arcpy.AddMessage("Features in <inputFeatures>: " + str(arcpy.GetCount_management(inputFeatures)[0]))

    segments = arcpy.FeatureToLine_management(inputFeatures, "segments")
    arcpy.AddMessage("Creating line segments from input features...")
    # arcpy.AddMessage("Features in <segments>: " + str(arcpy.GetCount_management(segments)[0]))

    if not endPointRemoval:
        fcName = arcpy.Describe(inputFeatures).name
        cmpField = constructComparisonFieldName(fcName)

        endLoopSegments = identifyEndLoops(segments,cmpField)

        segList = []
        with arcpy.da.SearchCursor(segments, ["OID@"]) as cursor:
            for row in cursor:
                segId = row[0]
                if segId in endLoopSegments:
                    continue
                segList.append(segId)

        segWhereClause = createWhereClauseFromIDList(segList)
        # arcpy.AddMessage("Segment's Where Clause: " + str(segWhereClause))

        arcpy.AddMessage("Finding end-point segments...")
        segLayer = arcpy.MakeFeatureLayer_management(segments, "segLayer")
        arcpy.SelectLayerByAttribute_management(segLayer, "#", segWhereClause)

    else:
        segLayer = arcpy.MakeFeatureLayer_management(segments, "segLayer")
        arcpy.SelectLayerByAttribute_management(segLayer, "#", "")

    vertices = arcpy.FeatureVerticesToPoints_management(segLayer, "vertices", "BOTH_ENDS")
    # arcpy.AddMessage("Features in <vertices>: " + str(arcpy.GetCount_management(vertices)[0]))

    if shapeType == "Polyline":
        identical = arcpy.FindIdentical_management(vertices, "identical", ["SHAPE", "ORIG_FID"], output_record_option="ONLY_DUPLICATES")
        # arcpy.AddMessage("Rows in <identical> (polyline): " + str(arcpy.GetCount_management(identical)[0]))
    elif shapeType == "Polygon":
        fcName = arcpy.Describe(inputFeatures).name
        comparisonFieldName = constructComparisonFieldName(fcName)
        identical = arcpy.FindIdentical_management(vertices, "identical", ["SHAPE", comparisonFieldName], output_record_option="ONLY_DUPLICATES")
        # arcpy.AddMessage("Rows in <identical> (polygon): " + str(arcpy.GetCount_management(identical)[0]))

    rowList = []
    with arcpy.da.SearchCursor(identical, ["FEAT_SEQ", "IN_FID"]) as cursor:
        for row in cursor:
            rowList.append(row)

    # create dictionary containing with key = FEAT_SEQ value and value = list of IN_FIDs with that FEAT_SEQ
    idDict = {}
    for entry in rowList:
        if idDict.has_key(entry[0]):
            idDict[entry[0]].append(entry[1])
        else:
            idDict[entry[0]] = [entry[1]]

    # get list of ORIG_FID in vertices from OBJECTIDs in idDict
    listOfIDLists = idDict.values()
    # arcpy.AddMessage("List of Lists: ")
    # arcpy.AddMessage(listOfIDLists)

    if shapeType == "Polygon":
        # remove sublists with 2 or fewer items
        listCopy = listOfIDLists[:]
        # iterate over copy of list since it is being modified
        for sublist in listCopy:
            if len(sublist) < 3:
                listOfIDLists.remove(sublist)

        # arcpy.AddMessage("Modified (polygon) List of Lists: ")
        # arcpy.AddMessage(listOfIDLists)

    flatList = [item for sublist in listOfIDLists for item in sublist]
    # arcpy.AddMessage("Flattened List: ")
    # arcpy.AddMessage(flatList)

    finalOIDList = []
    with arcpy.da.SearchCursor(vertices, ["OBJECTID", "ORIG_FID"]) as vCursor:
        for vRow in vCursor:
            if vRow[0] in flatList:
                finalOIDList.append(vRow[1])

    # arcpy.AddMessage("Final OID List: ")
    # arcpy.AddMessage(finalOIDList)

    uniqueOIDs = list(set(finalOIDList))
    # arcpy.AddMessage("Unique OIDs: ")
    # arcpy.AddMessage(uniqueOIDs)

    whereClause = createWhereClauseFromIDList(uniqueOIDs)
    # arcpy.AddMessage("ID's Where Clause: " + str(whereClause))

    segments_layer = arcpy.MakeFeatureLayer_management(segments, "segments_layer")
    # segDesc = arcpy.Describe(segments_layer)

    if shapeType == "Polyline":

        if maxRemovalLength != -1:
            whereClause = addMaxRemovalLengthToWhereClause(segments, maxRemovalLength, whereClause)
            # arcpy.AddMessage("Adjusted where clause: " + str(whereClause))
        arcpy.SelectLayerByAttribute_management(segments_layer, "#", whereClause)

        arcpy.AddMessage("Calculating self-intersections...")
        if onlyCheckErrors:
            arcpy.FeatureClassToFeatureClass_conversion(segments_layer, os.path.dirname(outputTable), os.path.basename(outputTable))
            intersectionsCount = arcpy.GetCount_management(segments_layer)[0]
            arcpy.AddMessage("{0} self-intersections were identified and recorded to {1}".format(str(intersectionsCount), outputTable))

        # clear selection on input layer for Erase
        arcpy.SelectLayerByAttribute_management(inputFeatures, "CLEAR_SELECTION")
        intersectingPolylines = arcpy.Erase_analysis(inputFeatures, segments_layer, "erase")
        # arcpy.AddMessage("Polyline Features in <erase>: " + str(arcpy.GetCount_management(intersectingPolylines)[0]))
        return intersectingPolylines

    elif shapeType == "Polygon":
        # #1. Remove segment IDs of segments with vertices at different locations
        with arcpy.da.SearchCursor(segments, ["OID@", "SHAPE@"]) as closedLoopCursor:
            closedLoopIDList = [row[0] for row in closedLoopCursor if row[1].firstPoint.X == row[1].lastPoint.X and row[1].firstPoint.Y == row[1].lastPoint.Y]

        # arcpy.AddMessage("Closed Loop list: " + str(closedLoopIDList))

        intersectedIDList = list(set(uniqueOIDs).intersection(closedLoopIDList))
        # arcpy.AddMessage("Intersected ID list: " + str(intersectedIDList))

        newWhereClause = createWhereClauseFromIDList(intersectedIDList)
        # arcpy.AddMessage("New Where Clause: " + str(newWhereClause))

        # #2. Select smallest segment with same FID_<input>
        segList = []
        with arcpy.da.SearchCursor(segments, ["OID@", comparisonFieldName, "SHAPE@LENGTH"], newWhereClause) as segmentCursor:
            for row in segmentCursor:
                segList.append(row)

        # arcpy.AddMessage("Segment list: " + str(segList))

        groups = {}
        segList.sort(key=itemgetter(1))
        for k, v in groupby(segList, itemgetter(1)):
            groups[k] = list(v)

        # arcpy.AddMessage("Groups: " + str(groups))

        polygonIDList = []
        for g in groups.values():
            generator = (x for x in g)
            minVal = min(x[2] for x in g)
            # arcpy.AddMessage("Minimum value = " + str(minVal))
            minTuple = min(generator, key = itemgetter(2))
            # arcpy.AddMessage("Minimum tuple = " + str(minTuple))
            polygonIDList.append(minTuple[0])

        filteredWhereClause = createWhereClauseFromIDList(polygonIDList)
        # arcpy.AddMessage("Updated polygon where clause: " + filteredWhereClause)

        if maxRemovalLength != -1:
            filteredWhereClause = addMaxRemovalLengthToWhereClause(segments, maxRemovalLength, filteredWhereClause)
            # arcpy.AddMessage("Adjusted MRL where clause: " + str(filteredWhereClause))

        # #3. Convert those segments to polygons
        arcpy.SelectLayerByAttribute_management(segments_layer, "#", filteredWhereClause)

        arcpy.AddMessage("Calculating self-intersections...")
        if onlyCheckErrors:
            arcpy.FeatureClassToFeatureClass_conversion(segments_layer, os.path.dirname(outputTable), os.path.basename(outputTable))
            intersectionsCount = arcpy.GetCount_management(segments_layer)[0]
            arcpy.AddMessage("{0} self-intersections were identified and recorded to {1}".format(str(intersectionsCount), outputTable))

        splitPolygons = arcpy.FeatureToPolygon_management(segments_layer, "split_polygons")
        # arcpy.AddMessage("Features in <split_polygons> after: " + str(arcpy.GetCount_management(splitPolygons)[0]))
        polygons_layer = arcpy.MakeFeatureLayer_management(splitPolygons, "polygons_layer")

        # #4. Erase using new polygons as erase_features
        # clear selection on input layer for Erase
        arcpy.SelectLayerByAttribute_management(inputFeatures, "CLEAR_SELECTION")
        intersectingPolygons = arcpy.Erase_analysis(inputFeatures, polygons_layer, "erase")
        # arcpy.AddMessage("Polygon Features in <erase>: " + str(arcpy.GetCount_management(intersectingPolygons)[0]))
        return intersectingPolygons


'''
Replace the geometries of the originalInputFeatures feature class with the corresponding geometries
from the newIntersectingFeatures feature class.
'''
def replaceIntersectingFeatures(originalInputFeatures, newIntersectingFeatures):

    # Step 1: delete original features in originalInputFeatures
    arcpy.DeleteFeatures_management(originalInputFeatures)
    # arcpy.AddMessage("Deleted features. # features in original layer = " + str(arcpy.GetCount_management(originalInputFeatures)[0]))

    # Step 2: copy intersecting features into originalInputFeatures
    intersectFeatureLayer = arcpy.MakeFeatureLayer_management(newIntersectingFeatures, "intersectFL")
    # arcpy.Append_management([newIntersectingFeatures], originalInputFeatures, "TEST")
    inputFeaturesDesc = arcpy.Describe(originalInputFeatures)
    # arcpy.AddMessage("Input Features File Path = " + inputFeaturesDesc.path)
    # arcpy.AddMessage("Input Features File Name = " + inputFeaturesDesc.file)
    inputFCFullPath = os.path.join(inputFeaturesDesc.path, inputFeaturesDesc.file)
    arcpy.Append_management(intersectFeatureLayer, inputFCFullPath)


def constructComparisonFieldName(inputFCName):

    # Make sure table name is unqualifed
    tableName = inputFCName.split('.')[-1]

    fieldName = "FID_{0}".format(tableName)
    return fieldName

def createWhereClauseFromIDList(idList):

    if len(idList) > 0:
        whereClause = "OBJECTID IN "
        oidStrings = ",".join([str(item) for item in idList])
        whereClause += "("
        whereClause += oidStrings
        whereClause += ")"
    else:
        whereClause = ""

    return whereClause

def addMaxRemovalLengthToWhereClause(segments, convertedLength, whereClause):

    if whereClause != "":
        where = whereClause + " AND "
    else:
        where = ""

    segShapeField = arcpy.Describe(segments).lengthFieldName
    where += str(segShapeField) + " < " + str(convertedLength)
    return where

def main():
    try:
        license = arcpy.SetProduct("arcinfo")
        serverlicense = arcpy.SetProduct("arcserver")

        if license == "AlreadyInitialized" or serverlicense == "AlreadyInitialized" or serverlicense == "CheckedOut" or license == "CheckedOut":
            inputFeatures     = arcpy.GetParameterAsText(0)
            maxRemovalLength  = arcpy.GetParameterAsText(1)
            removeAtEndPoint  = arcpy.GetParameter(2)
            checkErrorsOnly   = arcpy.GetParameter(3)
            tableLocation     = arcpy.GetParameterAsText(4)

            inputFeatureLayer = arcpy.MakeFeatureLayer_management(inputFeatures,'inputfeatures_lyr')

            desc = arcpy.Describe(inputFeatureLayer)
            inputShapeType = desc.shapeType

            ## check out Production Mapping extension
            #if arcpy.CheckExtension("Foundation"):
            #    status=arcpy.CheckOutExtension("Foundation")

            # editor = arcpy.da.Editor(productionscripting.generalization.GetWorkspace(inputFeatureLayer))
            # isBeingEdited = productionscripting.generalization.IsBeingEdited(inputFeatureLayer)

            # isVersioned = desc.IsVersioned
            # canVersion = desc.canVersion

            # arcpy.AddMessage("Is Versioned? " + str(isVersioned))
            # arcpy.AddMessage("Can Version? " + str(canVersion))
            # arcpy.AddMessage("Is Being Edited? " + str(isBeingEdited))

            # check if the tool needs to start editing and operation
            # begin edit block
            # start_edit_operation = (not isBeingEdited) and ((canVersion and isVersioned) or not canVersion)
            # arcpy.AddMessage("Tool needs to start editing? " + str(start_edit_operation))
            # if start_edit_operation == True:
                # editor.startEditing(False, True)
                # editor.startOperation()

            arcpy.env.overwriteOutput = 1
            arcpy.env.workspace = arcpy.env.scratchGDB

            convertedRemovalLength = -1
            if maxRemovalLength != '':
                convertedRemovalLength = gen.ConvertLinearUnits(maxRemovalLength, inputFeatureLayer)
                # arcpy.AddMessage("Max Removal Length = " + str(convertedRemovalLength))
                if convertedRemovalLength < 0:
                    arcpy.AddError("Maximum Removal Length may not be a negative value.")
                    return

            if int(arcpy.GetCount_management(inputFeatureLayer)[0]) > 0:
                features = identifySelfIntersections(inputShapeType, inputFeatureLayer, convertedRemovalLength, removeAtEndPoint, checkErrorsOnly, tableLocation)
            else:
                # 312 appears to be the wrong error message
                # arcpy.AddIDMessage("Error", 312, inputFeatureLayer)
                arcpy.AddWarning("There are no features in the input layer.")
                return

            if not checkErrorsOnly:
                replaceIntersectingFeatures(inputFeatureLayer, features)
                arcpy.RepairBadGeometry_production(inputFeatureLayer)

            # end edit block
            # stop operation and editing if we started them in this tool
            # if start_edit_operation == True:
                # editor.stopOperation()
                # editor.stopEditing(True)

        else:
            arcpy.AddIDMessage("Error", 626, "[Remove Self Intersections]")
            arcpy.AddError("Tool requires an Advanced license.")


    except arcpy.ExecuteError:
        arcpy.AddError("ArcPy Error Message: {0}".format(arcpy.GetMessages(2)))
    except Exception, exc:
        arcpy.AddError(str(exc.message))
    finally:
        clean_list = ["segments", "vertices", "identical", "erase", "segments_layer","inputfeatures_lyr"]
        # clean_list = []
        for item in clean_list:
            if arcpy.Exists(item):
                arcpy.Delete_management(item)
        arcpy.RefreshActiveView()

if __name__ == '__main__':
    main()
