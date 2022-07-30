# -*- coding: utf-8 -*-
#¸¸.·´¯`·.¸¸.·´¯`·.¸¸
# ║╚╔═╗╝║  │┌┘─└┐│  ▄█▀‾
# ================= #
#    Tool Title     #
# Author 2022-07-12 #
# ================= #

'''
Name: Tool Title
Description: This boiler plate is designed to give a starting point for an ArcPy
			 script based on prevous script tools written by Nat Cagle and John
			 Jackson.
Created by: Nat Cagle
Creation Date: 2022-07-12

╔═════════════════╗
║ Notes and To-Do ║
╚═════════════════╝

## 2 hashtags in the code - recent changes/updates
### 3 hashtags in the code - unique variable or identifier
#### 4 hashtags in the code - things to be updated

## Recent Changes
  - Something that has recently been updated. A dynamic list that is preserved/reset
    in each new version

#### Update Plans
  - Something that still needs to be updated

'''



'''
╔═════════╗
║ Imports ║
╚═════════╝
'''
# ArcPy aliasing
import arcpy as ap
from arcpy import (AddFieldDelimiters as field_delim,
	AddMessage as write,
	MakeFeatureLayer_management as make_lyr,
	MakeTableView_management as make_tbl,
	SelectLayerByAttribute_management as select_by_att,
	SelectLayerByLocation_management as select_by_loc,
	Delete_management as arcdel)
# Collections to organize and simplify
from collections import OrderedDict
from collections import namedtuple
# STOP! Hammer time
from datetime import datetime as dt
import time
# Number bumbers
import csv as cs
import pandas as pd
import numpy as np
import math
import uuid
import re
# System Modules
import os
import sys
import imp
import traceback
import subprocess
#import arc_dict as ad
ad = imp.load_source('arc_dict', r"Q:\Special_Projects\4_Finishing\Post Production Tools & Docs\6_Tools\_dict_source\arc_dict.py")


#----------------------------------------------------------------------
# arc_dict imported as ad contains these dictionaries that can be referenced
# Ex: if fcode_field != str(ad.sub2fcode_dict[fcsubtype_field]): # If the fcode and subtype don't match
#         fcode_field = str(ad.sub2fcode_dict[fcsubtype_field]) # set the fcode to match the subtype
	# fcode_dict
		# { 'AB040' : 'AerationBasin', ...}
	# fcsub_dict
		# { 100010 : 'AerationBasin', ...}
	# sub2fcode_dict
		# {100185 : 'AQ120', ...}
	# fc_fields_og
		# { 'AeronauticCrv' : ['F_CODE','FCSUBTYPE','ZI026_CTUU','Shape','Version'], ...}
	# fc_fields
		# { 'AeronauticCrv' : ['f_code','fcsubtype','zi026_ctuu','shape@','version'], ...}
	# ffn_list_all
		# OrderedDict([('    Public Administration', 808), ...]) # Sorted, formatted, list of tuples that becomes an ordered dictionary
	# ffn_list_caci
		# Same as above but the CACI specific version cz they just have to be different



#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#



'''
╔═══════════════════╗
║ General Functions ║
╚═══════════════════╝
'''
#-----------------------------------
def myfunc1(param1, param2):
	# Do stuff
	pass

#-----------------------------------
def myfunc2(param1, param2):
	# Do other stuff
	pass

def TDS_check(TDS):
	if not ap.Exists(TDS):
		ap.AddError('                       ______\n                    .-"      "-.\n                   /            \\\n       _          |              |          _\n      ( \\         |,  .-.  .-.  ,|         / )\n       > "=._     | )(__/  \\__)( |     _.=" <\n      (_/"=._"=._ |/     /\\     \\| _.="_.="\\_)\n             "=._ (_     ^^     _)"_.="\n                 "=\\__|IIIIII|__/="\n                _.="| \\IIIIII/ |"=._\n      _     _.="_.="\\          /"=._"=._     _\n     ( \\_.="_.="     `--------`     "=._"=._/ )\n      > _.="                            "=._ <\n     (_/                                    \\_)\n')
		ap.AddError("Dataset {0} does not exist.\nPlease double check that the file path is correct.\nExitting tool...\n".format(TDS))
		sys.exit(0)


#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#



'''
╔═══════════════╗
║ Main Function ║
╚═══════════════╝
'''

def main(*argv):
	### [0] TDS - Feature Dataset
	TDS = argv[0]
	TDS_check(TDS) # Check that the provided TDS exists
	# Set the workspace to the TDS feature dataset
	ap.env.workspace = TDS
	ap.env.extent = TDS

	pass



#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#



if __name__=='__main__':
	ap.env.overwriteOutput = True
	argv = tuple(ap.GetParameterAsText(i) for i in range(ap.GetArgumentCount()))
	now = dt.now()
	main(*argv)
	write(dt.now() - now)
