'''
-------------------------------------------------------------------------------
Tool Name:  Generalize Shared Features
Source Name: GeneralizeSharedFeatures.py
Version: ArcGIS 10.3
Author: ESRI

Performs the selected generalization operations (simplify and smooth) on the
main feature class. If feature classes are selected as topology feature classes,
features from these feature classes that share a boundary with the main feature
class will also be generalized to maintain coincidence.
-------------------------------------------------------------------------------
'''

import arcpy
import common
import productionscripting
import datetime
from collections import defaultdict

def temp_fds():
    """ Create a feature dataset (fds) for storing output results"""
    temp = arcpy.env.scratchGDB
    main_fc = arcpy.GetParameterAsText(0)
    desc = arcpy.Describe(main_fc)
    spat_ref = desc.spatialReference

    now = datetime.datetime.now()
    time_str = now.strftime("%H%M%S")
    unique = "GenShareFDS_" + time_str

    out_fds = temp + "\\" + unique
    if arcpy.Exists(out_fds):

        out_sr = arcpy.Describe(out_fds).spatialReference
        if out_sr != spat_ref:
            arcpy.AddMessage("Ouput FDS exists and will be deleted")
            arcpy.Delete_management(out_fds)
    else:
        arcpy.AddMessage("Creating output FDS")
        arcpy.CreateFeatureDataset_management(temp, unique, spat_ref)

    arcpy.AddMessage("out fds " + out_fds)
    return out_fds

def update_geometries(dissolve, orig_field, topo_feat_class, update_query):
    dissolve_dict = {}
    dissolve_ids = []
##    arcpy.AddMessage(" ... Building dictionary")
    with arcpy.da.SearchCursor(dissolve, [orig_field, 'SHAPE@']) as diss_cur:
        for diss_row in diss_cur:
            dissolve_dict[str(diss_row[0])] = diss_row[1]
    #Replace the geometries in the input feature class
##    arcpy.AddMessage(topo_feat_class)

    with arcpy.da.UpdateCursor(topo_feat_class, ['oid@', 'SHAPE@'], update_query) as cursor:
##        arcpy.AddMessage("Start Update")
        for row in cursor:
            obj_id = row[0]
            if str(obj_id) in dissolve_dict:
                arcpy.AddMessage(" ... Updating geometry for " + str(obj_id))
    ##            if str(obj_id) in dissolve_ids:
                all_geos = dissolve_dict[str(obj_id)]
                if all_geos:
                    row[1] = all_geos
                    cursor.updateRow(row)

    return topo_feat_class

def finalize_dissolve(main_fc_union, main_fc, clean_list, time_str, unionOids, dissolve_fc_name, fidField):

    #fidField = "FID_" + common.get_unqualified_name(main_fc)
    main_fc_dissolve = arcpy.Dissolve_management(main_fc_union, dissolve_fc_name, fidField)
    clean_list.append(main_fc_dissolve)

    desc = arcpy.Describe(main_fc_dissolve)

    arcpy.AddMessage("Final dissolve........")
    for oid in list(unionOids.keys()):
        #arcpy.AddMessage("Final dissolve........" + str(oid))
        if len(unionOids[oid])> 0:
            with arcpy.da.UpdateCursor(main_fc_dissolve, ['OID@','SHAPE@'], '"{0}"={1}'.format(desc.OIDFieldName, oid)) as cursor:
                for row in cursor:
                    for row1 in arcpy.da.SearchCursor(main_fc_union, ['OID@','SHAPE@'], 'OBJECTID IN ({})'.format(','.join(map(str, unionOids[oid])))):
                        #arcpy.AddMessage("Final dissolve........" + str(oid) + " *** " + str(row1[0]))
                        shape = row[1].union(row1[1])
                        row[1] = shape
                        cursor.updateRow(row)

    arcpy.AddMessage("Updating input features...")
    desc = arcpy.Describe(main_fc)
    for row1 in arcpy.da.SearchCursor(main_fc_dissolve, [fidField,'SHAPE@']):
        with arcpy.da.UpdateCursor(main_fc, ['OID@','SHAPE@'], '"{0}"={1}'.format(desc.OIDFieldName, row1[0])) as cursor:
            for row2 in cursor:
                row2[1] = row1[1]
                cursor.updateRow(row2)
    return

def combine_and_generalize(fcs, generalize_operations, clean_list, main_name, out_dataset, merge_pts):
    """ Function that combines all the input lines into one feature class
    and generalizes the lines.  Function takes in the cartographic partitions
    environment and will loop through each partition if partition layer was
    chosen. """

    arcpy.env.workspace = out_dataset
    arcpy.env.overwriteOutput = 1
    simple_tolerance = arcpy.GetParameterAsText(2)
    smooth_tolerance = arcpy.GetParameterAsText(3)
    simple_algorithm = arcpy.GetParameterAsText(5)
    smooth_algorithm = arcpy.GetParameterAsText(6)

    partitions = arcpy.env.cartographicPartitions
    now = datetime.datetime.now()
    time_str = now.strftime("%H%M%S")
    other = "not_simplified_lines_" + time_str
    if arcpy.Exists(other):
        arcpy.Delete_management(other)
##    arcpy.AddMessage("Getting partitions " + str(partitions))

    process_lyrs = []
    generalize_fcs = []


    total_parts = 1
    if partitions:
        total_parts = int(arcpy.GetCount_management(partitions)[0])
        part_ids = [str(row[0]) for row in arcpy.da.SearchCursor(partitions, "OID@")]
        partition_name = common.get_unqualified_name(partitions)
        for fclass in fcs:

            name = common.get_unqualified_name(fclass)

            now = datetime.datetime.now()
            time_str = now.strftime("%H%M%S")
            split_name = name + "_splitByPart_" + time_str
            arcpy.AddMessage(" ... Splitting " +  name + " by partition")
            split_lines = arcpy.Identity_analysis(fclass, partitions, split_name, "ONLY_FID")
            split_lines = split_name
            split_layer = arcpy.MakeFeatureLayer_management(split_lines, split_name + "_lyr")
            process_lyrs.append(split_layer)
##            clean_list.append(split_lines)
    else:
        process_lyrs = fcs

    part_cnt = 0

    while part_cnt < total_parts:

        if total_parts == 1:
            combine_fcs = process_lyrs
        else:
            combine_fcs = []
            part = part_ids[part_cnt]
            query = "FID_" + partition_name + " = " + part
##            arcpy.AddMessage(query)
            for layer in process_lyrs:
                arcpy.SelectLayerByAttribute_management(layer, "NEW_SELECTION", query)
                combine_fcs.append(layer)

        part_cnt += 1
        arcpy.AddMessage("Processing partition " + str(part_cnt) + " of " + str(total_parts))
        now = datetime.datetime.now()
        time_str = now.strftime("%H%M%S")
        arcpy.AddMessage("  ... Combining lines " )

        out_lines = arcpy.FeatureToLine_management(combine_fcs, "generalize_lines_" + time_str, "#", "ATTRIBUTES")
        out_layer = arcpy.MakeFeatureLayer_management(out_lines, "out_layer")
##        clean_list.append(out_lines)

        if int(arcpy.GetCount_management(out_lines)[0]) >= 1:

            now = datetime.datetime.now()
            time_str = now.strftime("%H%M%S")
            arcpy.AddMessage("  ... Cleaning lines ")
            arcpy.RepairGeometry_management(out_lines)

            #Select only those lines relating to the main fc
            #Select only those lines relating to the main fc
            fields = arcpy.ListFields(out_lines, "*"+ main_name + "*")
            if fields:
                main_field = fields[0].name
                query = main_field + " <> -1"
            else:
                raise Exception("Unable to determine output field that stores"
                + "information about " + str(main_name))


            # arcpy.AddMessage(main_field)
##            arcpy.AddMessage(query)


            output = arcpy.SelectLayerByAttribute_management(out_layer, "NEW_SELECTION", query)
            arcpy.AddMessage("  ... " + str(int(arcpy.GetCount_management(output)[0])) + " lines to generalize")

            switch_selection = arcpy.MakeFeatureLayer_management(out_lines, "switch_selection", main_field + " = -1")
            barriers_fc = "barriers_fc_" + time_str
            arcpy.CopyFeatures_management(switch_selection, barriers_fc)
            clean_list.append(barriers_fc)

            barrier_pts = "barrier_pts_" + time_str
            arcpy.FeatureVerticesToPoints_management(barriers_fc, barrier_pts)
            clean_list.append(barrier_pts)

            barrier_lyr = arcpy.MakeFeatureLayer_management(barrier_pts)
            barrier_lyr_select = arcpy.SelectLayerByLocation_management(barrier_lyr, "INTERSECT", output)

            arcpy.DeleteFeatures_management(barrier_lyr_select)

            barriers_fc = barrier_pts
            barriers_fc += ";"+str(merge_pts)

            for operation in generalize_operations:
                operation = operation.strip()
                operation = operation.upper()
                if operation == "SIMPLIFY":
                #if simplication tolerance provided, run simplify
                    arcpy.AddMessage("  ... Simplifying lines")
                    now = datetime.datetime.now()
                    time_str = now.strftime("%H%M%S")
##                    arcpy.AddMessage("      ... " + time_str)
                    out_name = "simplify_" + str(part_cnt) + "_" + time_str

                    """Note for bug 789 - this will only work with 10.6.1 or higher.
                    do not use in_barriers with Simplify or Smooth on older versions"""
                    output = arcpy.SimplifyLine_cartography(output, out_name,
                                simple_algorithm, simple_tolerance, "RESOLVE_ERRORS",
                                "NO_KEEP", "CHECK", barriers_fc)
                    arcpy.RepairGeometry_management(output)
                    now = datetime.datetime.now()
                    time_str = now.strftime("%H%M%S")
##                    arcpy.AddMessage("      ... " + time_str)

                #if smooth tolerance provided, run smooth
                elif operation == "SMOOTH":
                    arcpy.AddMessage("  ... Smoothing lines")
                    now = datetime.datetime.now()
                    time_str = now.strftime("%H%M%S")
##                    arcpy.AddMessage("      ... " + time_str)
                    out_name = "smooth_" + str(part_cnt) + "_" + time_str

                    output = arcpy.SmoothLine_cartography(output, out_name, smooth_algorithm,
                                smooth_tolerance, "FIXED_CLOSED_ENDPOINT",
                                "FLAG_ERRORS", barriers_fc)
                    arcpy.RepairGeometry_management(output)
                    now = datetime.datetime.now()
                    time_str = now.strftime("%H%M%S")
##                    arcpy.AddMessage("      ... " + time_str)
                else:
                    arcpy.AddWarning("Unknown generalization operation " + operation)


##                clean_list.append(output)


            arcpy.SelectLayerByAttribute_management(out_layer, "SWITCH_SELECTION")
            if arcpy.Exists(other):
                arcpy.Append_management(out_layer, other, "NO_TEST")
            else:
                arcpy.CopyFeatures_management(out_layer, other)

            generalize_fcs.append(output)

        else:
            arcpy.AddMessage("  ... No features in partition to generalize")



    #determine final set of generalized lines...
    if part_cnt == 1:
        final_output = arcpy.Describe(output).catalogPath
        now = datetime.datetime.now()
        time_str = now.strftime("%H%M%S")
        other = arcpy.CopyFeatures_management(out_layer, "not_simplified" + time_str + "_lines")
##        clean_list.append(other)
##        arcpy.AddMessage(final_output)

    else:
        final_output = arcpy.Describe(output).catalogPath
##        arcpy.AddMessage(final_output)
        generalize_fcs.remove(output)
        arcpy.Append_management(generalize_fcs, final_output, "NO_TEST")


    return final_output, clean_list, other, main_field

def process_fc(in_fc, fcs, fc_paths, point_fcs, out_names, clean_list, out_dataset):
    """prep features classes and convert to line if necessary"""
##    arcpy.AddMessage(in_fc)
    arcpy.env.workspace = out_dataset
    name = common.get_unqualified_name(in_fc)
    desc = arcpy.Describe(str(in_fc))
    arcpy.AddMessage(" ... Prepping " + name)
    in_path = desc.catalogPath
    if not arcpy.Exists(in_path):
        in_path = productionscripting.generalization.GetWorkspace(in_fc) + "\\" + desc.catalogPath
        if not arcpy.Exists(in_path):
            arcpy.AddError("Cannot deteremine full path of input layer")

    now = datetime.datetime.now()
    time_str = now.strftime("%H%M%S")
    unique = name + "_" + time_str
    out_name = unique + "_temp"

    if int(arcpy.GetCount_management(in_fc)[0]) >= 1:

        if desc.shapeType == "Polygon":


##            in_single = unique + "_SinglePart"
##            point_out_single = unique + "single_points"
##            temp_poly = unique + "poly2feature"

            point_out = unique + "center_points"
            out =  unique + "_temp"

##            in_single = "in_memory\\" + unique + "_SinglePart"
            now = datetime.datetime.now()
            time_str = now.strftime("%H%M%S")
            in_single = "SinglePart" + unique + time_str
            point_out_single = "in_memory\\" +unique + "single_points"
            temp_poly = "in_memory\\" +unique + "poly2feature"


            #deteremine original results for feature to polygon on layer
            arcpy.AddMessage("    ... Convert to single part")
            arcpy.MultipartToSinglepart_management(in_fc, in_single)
            blah = arcpy.CopyFeatures_management(in_single, unique + "_copy")
            arcpy.RepairGeometry_management(in_single)
            field = "FID_" + name
            arcpy.AddField_management(in_single, field)
            arcpy.CalculateField_management(in_single, field, '!ORIG_FID!', 'PYTHON')
            arcpy.FeatureToPoint_management(in_single, point_out_single, "INSIDE")
            arcpy.AddMessage("    ... Determine inside - outside")
            arcpy.FeatureToPolygon_management(in_single, temp_poly, "", "ATTRIBUTES", point_out_single)


            #Create the center point
##            arcpy.FeatureToPoint_management(in_single, point_out, "INSIDE")
            arcpy.FeatureToPoint_management(temp_poly, point_out, "INSIDE")
            arcpy.AddMessage("    ... Convert to line")
            arcpy.PolygonToLine_management(blah, out, "IGNORE_NEIGHBORS")

            fcs.append(out_name)
            fc_paths[out_name] = in_path

            point_fcs[out_name] = point_out

            out_names[name] = out_name
            clean_list.extend((in_single, out, point_out, point_out_single, temp_poly))

        else:

##                arcpy.RepairGeometry_management(in_fc)

            fcs.append(str(in_fc))
            fc_paths[name] = in_path
            out_names[name] = name
    else:
        arcpy.AddMessage("    ... No features were found for processing")



    return fcs, fc_paths, point_fcs, out_names, clean_list




def main():
    """ Main fucntion for beginning generalization and rebuilding geometries"""
    try:
        #Check for license level
        license = arcpy.SetProduct('arcinfo')
        serverlicense = arcpy.SetProduct('arcserver')
        if license == 'AlreadyInitialized' or serverlicense == 'AlreadyInitialized' or serverlicense == 'CheckedOut':
            clean_list = []

            main_fc = arcpy.GetParameterAsText(0)
            generalize_operations = arcpy.GetParameterAsText(1).split("_")
            simple_tolerance = arcpy.GetParameterAsText(2)
            smooth_tolerance = arcpy.GetParameterAsText(3)
            topology_fcs = arcpy.GetParameter(4)
##            topowksp = arcpy.GetParameterAsText(4)
            check_operations = arcpy.GetParameterAsText(1)



##            maincheck = productionscripting.generalization.GetWorkspace(main_fc)
##            topocheck = productionscripting.generalization.GetWorkspace(topowksp)
            data_wksp = productionscripting.generalization.GetWorkspace(main_fc)
            out_dataset = temp_fds()
            clean_list.append(out_dataset)


            session = productionscripting.generalization.IsBeingEdited(main_fc)
            if session == 0:

                topo_name_dict = {}
                topo_name_orignal_dict = {}
                #topology_fcs.insert(0, main_fc)
                desc = arcpy.Describe(main_fc)
                is_versioned = desc.IsVersioned
                can_version = desc.canVersion
                inputShapeType = desc.shapeType

                if simple_tolerance >= smooth_tolerance:
                    max_tolerance = simple_tolerance
                else:
                    max_tolerance = smooth_tolerance
##                arcpy.AddMessage("tol start" + str(max_tolerance))
                units_split = max_tolerance.split(" ")
                val = float(units_split[0]) * 4
                units_split[0] = val
                max_tolerance = ''
                for value in units_split:
                    max_tolerance += (str(value) + " ")

##                arcpy.AddMessage("tol " + str(max_tolerance))
                fcs = []
                point_fcs = {}
                fc_paths = {}
                out_names = {}

                match = common.check_matching_workspace(topology_fcs)
                common.check_projection(main_fc)
            ##    match = True
                #Set enviornments to override outputs and define temp workspace
                arcpy.env.workspace = out_dataset
                arcpy.env.overwriteOutput = 1

                if check_operations == 'SMOOTH' and float(smooth_tolerance.split(" ")[0]) <= 0:
                    arcpy.AddError("Smooth tolerance must be greater than 0.")
                elif check_operations == 'SIMPLIFY' and float(simple_tolerance.split(" ")[0]) <= 0:
                    arcpy.AddError("Simplify tolerance must be greater than 0.")
                elif (check_operations != 'SIMPLIFY' and check_operations != 'SMOOTH' and
                    (float(simple_tolerance.split(" ")[0]) <= 0 or float(smooth_tolerance.split(" ")[0]) <= 0)):
                    arcpy.AddError("Simplify and Smooth tolerance must be greater than 0.")
                else:

                    if int(arcpy.GetCount_management(main_fc)[0]) >= 1 and match:

                        now = datetime.datetime.now()
                        time_str = now.strftime("%H%M%S")

                        oids = {}
                        unionOids = defaultdict(list)

                        main_name = common.get_unqualified_name(main_fc)
                        topo_name_orignal_dict[main_fc] = main_name

                        main_fc_union_name = main_name
                        topology_fcs_lookup = {}
                        unionOids_dict = {}#defaultdict(dict(list))

                        if inputShapeType == 'Polygon':

                            main_fc_union_name = "main_fc_union" + time_str
                            main_fc_union = arcpy.Union_analysis(main_fc, main_fc_union_name, "ONLY_FID")
                            clean_list.append(main_fc_union)

                            with arcpy.da.UpdateCursor(main_fc_union, ['OID@', 'SHAPE@TRUECENTROID', 'FID_'+ main_name]) as cursor:
                                for row in cursor:
                                    if row[1] not in oids:
                                        oids[row[1]]=row[0]
                                    else:
                                        unionOids[row[2]].append(oids[row[1]])
                                        cursor.deleteRow()

                            unionOids_dict[main_fc] = unionOids
                            main_lyr = arcpy.MakeFeatureLayer_management(main_fc)

                            for topo_fc in topology_fcs:
                                oids = {}
                                unionOids = defaultdict(list)

                                topo_fc_name = common.get_unqualified_name(topo_fc)

                                topo_name_orignal_dict[topo_fc] = topo_fc_name
                                topo_fc_union_name = topo_fc_name + "_union_" + time_str

                                topo_lyr = arcpy.MakeFeatureLayer_management(topo_fc)

                                desc = arcpy.Describe(topo_lyr)
                                if desc.shapeType == 'Polygon':
                                    topo_lyr_select = arcpy.SelectLayerByLocation_management(topo_lyr, "INTERSECT", main_lyr)


                                    topo_fc_union = arcpy.Union_analysis(topo_lyr_select, topo_fc_union_name, "ONLY_FID")

                                    clean_list.append(topo_fc_union)

                                    with arcpy.da.UpdateCursor(topo_fc_union, ['OID@', 'SHAPE@TRUECENTROID', 'FID_'+ topo_fc_name]) as cursor:
                                        for row in cursor:
                                            if row[1] not in oids:
                                                oids[row[1]]=row[0]
                                            else:
                                                unionOids[row[2]].append(oids[row[1]])
                                                cursor.deleteRow()

                                    unionOids_dict[topo_fc] = unionOids

                                    topology_fcs_lookup[topo_fc] = topo_fc_union
                        else:
                            main_fc_union = main_fc

                        topology_fcs.insert(0, main_fc_union)





                        arcpy.AddMessage("Determining shared edges...")
                        #determine info for main_fc
                        #main_name = common.get_unqualified_name(main_fc)
    ##                    arcpy.AddMessage(main_name)



                        #split topology fcs
                        for topo_fc in topology_fcs:

                            if topo_fc in topology_fcs_lookup:
                                topo_fc = topology_fcs_lookup[topo_fc]

                            topo_name = common.get_unqualified_name(topo_fc)

##                            arcpy.AddMessage('{} : name {}'.format(topo_fc, topo_name))
                            topo_name_dict[topo_fc] = topo_name
                            topo_fc = arcpy.MakeFeatureLayer_management(topo_fc)

                            fcs, fc_paths, point_fcs, out_names, clean_list = process_fc(topo_fc, fcs, fc_paths, point_fcs, out_names, clean_list, out_dataset)


                        #create a single point feature class from the point_fcs
                        # to use as barriers when generalizing
                        #now = datetime.datetime.now()
                        #time_str = now.strftime("%H%M%S")
                        merge_pts = arcpy.Merge_management(point_fcs.values(), 'all_points_'+ time_str)
                        clean_list.append(merge_pts)

                        #process lines by tile - combine and generalize

                        output, clean_list, other, main_field = combine_and_generalize(fcs, generalize_operations, clean_list, main_fc_union_name, out_dataset, merge_pts)

##                        arcpy.AddMessage("Gen result " + output)



                        #append the lines not smoothed or simplified back into result fc

                        gen_count = int(arcpy.GetCount_management(output)[0])

                        #determine which features need to be rebuilt for each layer
                        arcpy.AddMessage("Determining features to rebuild")
                        rebuild_dict = {}
                        for feat_class in topology_fcs:

                            if feat_class in topology_fcs_lookup:
                                feat_class = topology_fcs_lookup[feat_class]
                            name = None
                            if feat_class in topo_name_dict:
                                name = topo_name_dict[feat_class]
                            feat_class = str(feat_class)
##                            name = common.get_unqualified_name(feat_class)
    ##                        arcpy.AddMessage(name)
                            if name in out_names:
                                out_name = out_names[name]

                                id_field = "FID_" + out_name

    ##                            arcpy.AddMessage(id_field)
                                ids = [str(row[0]) for row in arcpy.da.SearchCursor(output, id_field, main_field + " >= 1")]
                                ids = set(ids)
                                ids = sorted(ids)
                                rebuild_dict[name] = ids
    ##                        arcpy.AddMessage(str(len(ids)))


                        arcpy.Append_management(other, output, "NO_TEST")


                ##        arcpy.AddMessage("output feature class " + str(output))

                        output_layer = arcpy.MakeFeatureLayer_management(output, "output_layer")

                        arcpy.AddMessage(str(gen_count) + " generalized lines")

                        if gen_count > 0:
                            for feat_class in fcs:
                                #based on the temp feature classes determine the matching original
                                #feature class
                                feat_class = str(feat_class)
                                name = common.get_unqualified_name(feat_class)
                                update_query = ""
        ##                        arcpy.AddMessage(name)

                                topo_feat_class = fc_paths[name]
                                orig_name = common.get_unqualified_name(topo_feat_class)
                                out_name = out_names[orig_name]

                                arcpy.AddMessage("Rebuilding " + orig_name + "...")
                                now = datetime.datetime.now()
                                time_str = now.strftime("%H%M%S")
    ##                            arcpy.AddMessage("      ... " + time_str)
                                # If the geometry type of the feature class is a polygon
                                shape_type = arcpy.Describe(topo_feat_class).shapeType
                                if shape_type == "Polygon":

                                    poly_ids = rebuild_dict[orig_name]

                                    if len(poly_ids) >= 1:
                                        join_field = "FID_" + out_name
    ##                                    arcpy.AddMessage(join_field)
                                        dissolve_query = join_field + " >= 1"
                                        arcpy.SelectLayerByAttribute_management(output_layer, "NEW_SELECTION", dissolve_query)
        ##                                dissolve_layer = output_layer
                                        temp_poly_fc = name + "_rebuild" + time_str

                                        orig_pt = point_fcs[name]

                                        arcpy.AddMessage(" ... Creating polygons")
                                        arcpy.FeatureToPolygon_management(output_layer, temp_poly_fc, label_features=orig_pt)
                                        clean_list.append(temp_poly_fc)
                                        # check quality of poly links
                                        orig_ids = [row[0] for row in arcpy.da.SearchCursor(orig_pt, 'ORIG_FID')]

                                        no_match_ids = [] # oids of polygons
                                        pointTopoly = {} # oid of point to oid of polygons
                                        dup_ids = [] # oid of points
                                        match_ids = [] # oid of points
                                        fid_field = 'FID_' + name



                                        with arcpy.da.SearchCursor(temp_poly_fc, ['oid@', 'ORIG_FID']) as cursor:
                                            for row in cursor:
                                                if not row[1] or row[1] == 0:

                                                    no_match_ids.append(row[0])
                                                else:
                                                    match_ids.append(row[1])
                                                    if row[1] in pointTopoly:
                                                        dup_ids.append(row[1])
                                                        cur = pointTopoly[row[1]]
                                                        cur.append(row[0])
                                                        pointTopoly[row[1]] = cur
                                                    else:
                                                        pointTopoly[row[1]] = [row[0]]

                                        # if any points have multiple matches
                                        if len(dup_ids) >= 1:

                                            dup_ids = set(dup_ids)
                                            for dup_id in dup_ids:
                                                no_match_ids.extend(pointTopoly[dup_id])




                                        # if any points do not have a match
                                        no_match_pts = list(set(orig_ids) - set(match_ids))
                                        no_match_pts.extend(list(dup_ids))
    ##                                    arcpy.AddMessage("Orig polygons without matches {}".format(len(no_match_pts)))
                                        if len(no_match_pts) >= 1:

                                            with arcpy.da.UpdateCursor(temp_poly_fc, ['oid@', 'ORIG_FID']) as cursor:
                                                for row in cursor:
                                                    if row[0] in no_match_ids:
                                                        row[1] = 0
                                                        cursor.updateRow(row)

                                            with arcpy.da.UpdateCursor(orig_pt, 'oid@') as cursor:
                                                for row in cursor:
                                                    if row[0] not in no_match_pts:
                                                        cursor.deleteRow()


                                            arcpy.AddMessage(" ... Tie polygons to orig polygons")

                                            temp_poly_lyr = arcpy.MakeFeatureLayer_management(temp_poly_fc, 'tempPolyLyr', 'ORIG_FID = 0')
                                            #get the centerpoints of the polygons
                                            temp_point_fc = name + "_rebuild_pts"
                                            arcpy.FeatureToPoint_management(temp_poly_lyr, temp_point_fc, 'INSIDE')

                                            #Deteremine which original centerpoint the output centerpoints are closest to
                                            orig_pt = point_fcs[name]

    ##                                        arcpy.AddMessage("near")
                                            arcpy.Near_analysis(orig_pt, temp_point_fc)

                                            # if some points don't have a near point
                                            orig_field ="FID_" + orig_name
                                            point_near_dict = {} # poly id to orig pt id

                                            point_poly_dict = {} # orig pt id to orig poly id

    ##                                        arcpy.AddMessage("point near")
                                            with arcpy.da.SearchCursor(orig_pt, ["ORIG_FID", "NEAR_FID"]) as cursor:
                                                for row in cursor:
                                                    point_near_dict[row[1]] = row[0]
    ##                                        arcpy.AddMessage("poly near")
                                            with arcpy.da.SearchCursor(orig_pt, ['oid@', orig_field]) as cursor:
                                                for row in cursor:
                                                    point_poly_dict[row[0]] = row[1]
    ##                                        arcpy.AddMessage("udpate")
                                            with arcpy.da.UpdateCursor(temp_poly_lyr, ['oid@', 'ORIG_FID', orig_field]) as cursor:
                                                for row in cursor:
                                                    if row[0] in point_near_dict:
    ##                                                    arcpy.AddMessage("link poly for {}".format(row[0]))
                                                        pt_id = point_near_dict[row[0]]
                                                        if pt_id in point_poly_dict:
                                                            poly_id = point_poly_dict[pt_id]
    ##                                                        arcpy.AddMessage("orig pt {}, orig poly {}".format(pt_id, poly_id))
                                                            row[1] = pt_id
                                                            row[2] = poly_id
                                                            cursor.updateRow(row)


    ##                                        near_query = "NEAR_FID = -1"
    ##
    ##                                        arcpy.MakeFeatureLayer_management(temp_point_fc, 'no_near', near_query)
    ##                                        if int(arcpy.GetCount_management('no_near')[0]) >= 1:
    ##                                            arcpy.AddMessage(' ... refining polygon matches')
    ##
    ##                                            matched_points = []
    ##                                            arcpy.AddField_management(temp_point_fc, "NEW_NEAR_FID")
    ##                                            with arcpy.da.UpdateCursor(temp_point_fc, ["NEAR_FID", "NEW_NEAR_FID"]) as cursor:
    ##                                                for row in cursor:
    ##                                                    row[1] = row[0]
    ##                                                    cursor.updateRow(row)
    ##                                                    if row[0] != -1:
    ##                                                        matched_points.append(row[0])
    ##
    ##                                            no_match_orig = arcpy.Copy_management(orig_pt, name + "_orig_pts_subset")
    ##
    ##                                            with arcpy.da.UpdateCursor(no_match_orig, 'oid@') as cursor:
    ##                                                for row in cursor:
    ##                                                    if row[0] in matched_points:
    ##                                                        cursor.deleteRow()
    ##                                                        matched_points.remove(row[0])
    ##
    ##                                            arcpy.Near_analysis('no_near', no_match_orig)
    ##
    ##                                            with arcpy.da.UpdateCursor(temp_point_fc, ["NEAR_FID", "NEW_NEAR_FID"]) as cursor:
    ##                                                for row in cursor:
    ##                                                    if row[1] != -1:
    ##                                                        row[0] = row[1]
    ##                                                        cursor.updateRow(row)


                                        #Join the orginal ID back to the polygon feature class
        ##                                arcpy.AddMessage("join field " + join_field)
                                        orig_field ="FID_" + orig_name
    ##                                    arcpy.JoinField_management(temp_poly_fc, "OBJECTID", temp_point_fc, "ORIG_FID", "NEAR_FID")
    ##                                    arcpy.JoinField_management(temp_poly_fc, "NEAR_FID", orig_pt, "OBJECTID", orig_field)
                                        arcpy.AddMessage(" ... Dissolving polygon geometries")
                                        dissolve_geo = arcpy.Dissolve_management(temp_poly_fc, name + "dissolve", orig_field)
                                        arcpy.RepairGeometry_management(dissolve_geo)

                                else:

                                    id_field = "FID_" + name
                                    line_ids = rebuild_dict[name]
                                    query = ""
                                    query = id_field + " IN ("
                                    for id_val in line_ids:
                                        query += (id_val + ", ")
                                    query = query[:-2]
                                    query += ")"
                                    arcpy.AddMessage(" ... Dissolving line geometries")
                                    arcpy.SelectLayerByAttribute_management(output_layer, "NEW_SELECTION", query)
                                    dissolve_geo = arcpy.Dissolve_management(output_layer, "output_line_dissolve", id_field)
                                    arcpy.RepairGeometry_management(dissolve_geo)
                                    orig_field = id_field

                                all_ids = [id_row[0] for id_row in arcpy.da.SearchCursor(topo_feat_class, "oid@")]
                                all_ids = set(all_ids)
                                dissolve_ids = [id_row[0] for id_row in arcpy.da.SearchCursor(dissolve_geo, orig_field)]
                                dissolve_ids = set(dissolve_ids)
                                common_ids = list(set(all_ids).intersection(dissolve_ids))

                                if len(common_ids) >= 1:
                                    update_query = "OBJECTID IN ("
                                    for common_id in common_ids:
                                        update_query += (str(common_id) + ", ")

                                    update_query = update_query[:-2] + ")"

        ##                            arcpy.AddMessage(update_query)

                                    #Start Editing
        ##                            arcpy.AddMessage("Editing Checks - can version: " + str(can_version))
        ##                            arcpy.AddMessage("Editing Checks - is versioned: " + str(is_versioned))
        ##                            arcpy.AddMessage("Editing Checks - editing: " + str(session))

                                    if can_version == 1:
                                        edit = arcpy.da.Editor(data_wksp)
        ##                                arcpy.AddMessage("can version")
                                        if is_versioned == 1:
        ##                                    arcpy.AddMessage("is version")

        ##                                    arcpy.AddMessage("start version edit")
                                            edit.startEditing(False, True)
                                            edit.startOperation()
                                            update_geometries(dissolve_geo, orig_field, topo_feat_class, update_query)
        ##                                    arcpy.AddMessage("stop edit")
                                            edit.stopOperation()
                                            edit.stopEditing(True)

                ##                            else:
                ##                                arcpy.AddMessage("already editing start operation")
                ##                                edit.startOperation()
                                        else:
        ##                                    arcpy.AddMessage("not version")

        ##                                    arcpy.AddMessage("start unversion edit on SDE")
                                            edit.startEditing(False, False)
                                            edit.startOperation()
                                            update_geometries(dissolve_geo, orig_field, topo_feat_class, update_query)
        ##                                    arcpy.AddMessage("stop edit")
                                            edit.stopOperation()
                                            edit.stopEditing(True)
                                        del edit

                    ##              del               else:
                    ##                                arcpy.AddMessage("already editing start operation")
                    ##                                edit.startOperation()
                                    else:
        ##                                arcpy.AddMessage("start unversion edit")
                                        with arcpy.da.Editor(data_wksp) as edit:
                                            update_geometries(dissolve_geo, orig_field, topo_feat_class, update_query)


                                else:
                                    arcpy.AddMessage(" ... Cannot find features to update")

                            if inputShapeType == 'Polygon':
                                finalize_dissolve(main_fc_union, main_fc, clean_list, time_str, unionOids_dict[main_fc], "main_fc_final_dissolve_"+time_str, "FID_" + topo_name_orignal_dict[main_fc])

                                for fc in topology_fcs:
                                    if fc in topology_fcs_lookup:
                                        dissolve_name = topo_name_dict[topology_fcs_lookup[fc]] + "_dissolve_" +time_str
                                        topo_lyr = arcpy.MakeFeatureLayer_management(fc)
                                        finalize_dissolve(topology_fcs_lookup[fc], topo_lyr, clean_list, time_str, unionOids_dict[fc], dissolve_name, "FID_" + topo_name_orignal_dict[fc])

                        else:
                            arcpy.AddWarning("No features were simplified.")
                    else:
                        if not match:
                            arcpy.AddIDMessage("ERROR", 155)
                        else:
                            arcpy.AddIDMessage("INFORMATIVE", 401)

            else:
                arcpy.AddIDMessage("Error", 496, "[Generalize Shared Features]")

        else:
            arcpy.AddIDMessage("Error", 626, "[Generalize Shared Features]")
            arcpy.AddError("Tool requires an Advanced license.")

##    except arcpy.ExecuteError:
##        arcpy.AddError("ArcPy Error Message: {0}".format(arcpy.GetMessages(2)))
##    except Exception, exc:
##        arcpy.AddError(str(exc.message))


    finally:
        arcpy.AddMessage("Removing intermediate data")
        for item in clean_list:
            if arcpy.Exists(item):
                arcpy.Delete_management(item)

if __name__ == '__main__':
    main()
