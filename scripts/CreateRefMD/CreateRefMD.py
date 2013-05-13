#-------------------------------------------------------------------------------
# Name  	    	: CreateRefMD.py
# ArcGIS Version	: ArcGIS 10.1 sp1
# Script Version	: 20130225
# Name of Company 	: Environmental System Research Institute
# Author        	: ESRI raster solution team
# Date          	: 16-09-2012
# Purpose 	    	: To create referenced Mosaic datasets
# Created	    	: 14-08-2012
# LastUpdated  		: 13-05-2013
# Required Argument 	:
# Optional Argument 	:
# Usage         	: c:\Python27\ArcGIS10.1\python.exe CreateRefMD.py.py CreateMD.xml
# Copyright	    	: (c) ESRI 2012
# License	    	: <your license>
#-------------------------------------------------------------------------------

import arcpy,os,sys
sys.path.append('../SetMDProperties/')

import SetMDProperties
import Base

from xml.dom import minidom

class CreateReferencedMD(Base.Base):

    geodatabase_ext = '.gdb'
    srs = ''
    pixel_type = ''

    gdbName = ''
    gdbNameExt = ''
    dic_derive_lst = {}
    dic_ref_info = {}
    rftLocation = ''
    doc = None
    workspace = ''
    gdbPath = ''
    m_numBands = ''
    m_base = None

    def __init__(self, base=None):
        if (base != None):
            self.setLog(base.m_log)
            self.workspace = base.m_workspace
            self.gdbNameExt = base.m_geodatabase
            self.m_MD = base.m_md

        self.m_base = base


    def createReferencedMD(self):
        self.log("Creating reference mosaic datasets:", self.const_general_text)

        for k in self.dic_derive_lst.keys():

            for r in self.dic_derive_lst[k]['ref'].keys():

                try:
                    mdPath = os.path.join(self.gdbPath, r)

                    inMosaic = os.path.join(self.gdbPath, self.dic_derive_lst[k]['key'])
                    refMosaic = os.path.join(self.gdbPath, r)

                    self.log("Creating MD:" + r, self.const_general_text)

                    if not arcpy.Exists(mdPath):
                        try:
                            if (len(self.dic_ref_info) > 0):

                                in_dataset = self.m_base.getInternalPropValue(self.dic_ref_info, 'in_dataset')
                                _p, _f = os.path.split(in_dataset)
                                if (_p == '' and _f != ''):
                                    in_dataset = os.path.join(self.gdbPath, _f)

                                arcpy.CreateReferencedMosaicDataset_management(\
                                in_dataset,\
                                refMosaic,\
                                self.srs,\
                                self.m_numBands,\
                                self.pixel_type,\
                                self.m_base.getInternalPropValue(self.dic_ref_info, 'where_clause'),\
                                self.m_base.getInternalPropValue(self.dic_ref_info, 'in_template_dataset'),\
                                self.m_base.getInternalPropValue(self.dic_ref_info, 'extent'),\
                                self.m_base.getInternalPropValue(self.dic_ref_info, 'select_using_features'),\
                                self.m_base.getInternalPropValue(self.dic_ref_info, 'lod_field'),\
                                self.m_base.getInternalPropValue(self.dic_ref_info, 'minPS_field>'),\
                                self.m_base.getInternalPropValue(self.dic_ref_info, 'maxPS_field>'),\
                                self.m_base.getInternalPropValue(self.dic_ref_info, 'pixelSize'),\
                                self.m_base.getInternalPropValue(self.dic_ref_info, 'build_boundary')\
                                )
                            else:
                                arcpy.CreateReferencedMosaicDataset_management(inMosaic, refMosaic, self.srs, "", self.pixel_type, "", "", "", "", "", "", "", "","NO_BOUNDARY")
                        except:
                            self.log("\tFailed to create refrence MD  " + r, self.const_warning_text)
                            self.log(arcpy.GetMessages(), self.const_warning_text)

                    first_time = True
                    for fnc in self.dic_derive_lst[k]['ref'][r]:
                            self.log("\t\tAdding raster function: " + r + '->' + os.path.basename(fnc), self.const_general_text)
                            try:
                                arcpy.EditRasterFunction_management(refMosaic, \
                                                "EDIT_MOSAIC_DATASET", "REPLACE" if first_time else "INSERT", \
                                                fnc)
                                first_time = False
                            except:
                                self.log("\t\t\tFailed to add raster function  " + fnc, self.const_warning_text)
                                self.log(arcpy.GetMessages(), self.const_warning_text)
                except:
                    self.log("Failed to create/edit raster function reference mosaic dataset: " + r, self.const_critical_text)
                    self.log(arcpy.GetMessages(), self.const_critical_text)
                    return False

        return True


    def setMDProperties(self, config):

        setMDProps = SetMDProperties.SetMDProperties()
        if (setMDProps.init(config) == False):
            return False

        for k in self.dic_derive_lst.keys():
            for r in self.dic_derive_lst[k]['ref'].keys():
                    mdPath = os.path.join(self.gdbPath, r)
                    refMosaic = os.path.join(self.gdbPath, r)
                    setMDProps.setMDProperties(refMosaic)

        return True


    def init(self, config):

        try:
            self.doc = minidom.parse(config)
        except:
            self.log("Error: reading input config file:" + config + "\nQuitting...", self.const_critical_text)
            return False


        #workspace/location on filesystem where the .gdb is created.
        if (self.workspace == ''):
            self.workspace = self.m_base.getAbsPath(self.prefixFolderPath(self.getXMLNodeValue(self.doc, "WorkspacePath"), self.const_workspace_path_))
        if (self.gdbNameExt == ''):
            self.gdbNameExt =  self.getXMLNodeValue(self.doc, "Geodatabase")
        const_len_ext = 4
        if (self.gdbNameExt[-const_len_ext:].lower() != self.geodatabase_ext):
            self.gdbNameExt += '.gdb'


        self.gdbName = self.gdbNameExt[:len(self.gdbNameExt) - const_len_ext]       #.gdb

        self.gdbPath = os.path.join(self.workspace, self.gdbNameExt)

        self.srs = self.getXMLNodeValue(self.doc, "SRS")         #workspace/location on filesystem where the .gdb is created.
        self.pixel_type =  self.getXMLNodeValue(self.doc, "pixel_type")

        self.m_numBands  = self.getXMLNodeValue(self.doc, "num_bands")

        Nodelist = self.doc.getElementsByTagName("MosaicDataset")
        if (Nodelist.length == 0):
            self.log("Error: MosaicDatasets node not found! Invalid schema.", self.const_critical_text)
            return False

        dListEmpty = len(self.dic_derive_lst) == 0
        refMD = self.m_MD
        dName = ''

        try:
            for node in Nodelist[0].childNodes:
                  node =  node.nextSibling
                  if (node != None and node.nodeType == minidom.Node.ELEMENT_NODE):

                        if (node.nodeName == 'Name'):
                            try:
                                if (refMD == ''):
                                    refMD = node.firstChild.nodeValue
                            except:
                                Error = True


                        elif (node.nodeName == 'CreateReferencedMosaicDataset'):

                            for node in node.childNodes:
                                if (node != None and node.nodeType == minidom.Node.ELEMENT_NODE):
                                    nodeName = node.nodeName.lower()
                                    if (node.childNodes.length > 0):
                                        if (self.dic_ref_info.has_key(nodeName) == False):
                                            if (nodeName.lower() == 'in_dataset'):
                                                in_dataset = node.firstChild.nodeValue
                                                self.dic_derive_lst[in_dataset] = { 'ref' : {}}
                                                functions = []
                                                self.dic_derive_lst[in_dataset]['ref'][refMD] = functions
                                                self.dic_derive_lst[in_dataset]['key']  = in_dataset

                                            self.dic_ref_info[nodeName] = node.firstChild.nodeValue


                        elif(node.nodeName == 'AddRasters'):

                            rasterType = rasterTypeEnabled  = False

                            if (len(refMD) == 0):
                                self.log("Error: <MosaicDataset/Name> should be defined first.", self.const_critical_text)
                                return False

                            for node in node.childNodes:
                                if (node != None and node.nodeType == minidom.Node.ELEMENT_NODE):
                                #keyFound = False
                                    nodeName = node.nodeName.lower()

                                    if (nodeName == 'addraster'):
                                        for node in node.childNodes:
                                            if (node != None and node.nodeType == minidom.Node.ELEMENT_NODE):
                                                nodeName = node.nodeName.lower()

                                                if (nodeName == 'sources'):

                                                    for node in node.childNodes:
                                                        if (node.nodeName.lower() == 'data_path'):
                                                            try:
                                                                dNameVal = self.m_base.getAbsPath(node.firstChild.nodeValue)
                                                                dName = dNameVal.upper()

                                                                arydNameVal = dNameVal.split(';')
                                                                arydName = dName.split(';')

                                                                maxRange = len(arydName)
                                                                for indx in range(0, maxRange):
                                                                    _file = arydName[indx].strip()
                                                                    if (_file == ''):
                                                                        continue

                                                                    _p, _f = os.path.split(_file)
                                                                    if (_p == ''):
                                                                        arydNameVal[indx] = os.path.join(self.gdbPath, _f)
                                                                        _file = arydNameVal[indx].upper()

                                                                    if (dListEmpty or self.dic_derive_lst.has_key(_file) == False):
                                                                            self.dic_derive_lst[_file] = { 'ref' : {}}
                                                                            dListEmpty = False

                                                                    prev_indx  = self.dic_derive_lst[_file]['ref'].has_key(refMD)

                                                                    if (prev_indx == False):
                                                                        functions = []
                                                                        self.dic_derive_lst[_file]['ref'][refMD] = functions

                                                                    self.dic_derive_lst[_file]['key'] = arydNameVal[indx]
                                                            except:
                                                                    Error = True


                        elif(node.nodeName == 'Functions'):
                            if (refMD == '' and dName == ''):
                                self.log("Warning/Internal: refMD/dName empty!", self.const_warning_text)
                                break;

                            for node in node.childNodes:
                                if (node.nodeName == 'function_path'):
                                    if (node.childNodes.length > 0):
                                        rftNode = self.m_base.getAbsPath(node.firstChild.nodeValue.strip())
                                        if (len(rftNode) != 0):
                                            rft =  self.prefixFolderPath(rftNode, self.const_raster_function_templates_path_)
                                            if (os.path.exists(rft) == False):
                                                    rft = rftNode
                                            for md in self.dic_derive_lst.keys():
                                                self.dic_derive_lst[md]['ref'][refMD].append(rft)


        except:
            self.log("Error: reading MosaicDataset nodes.", self.const_critical_text)
            return False


        return True