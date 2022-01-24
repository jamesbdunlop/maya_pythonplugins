#  Copyright (c) 2020.  James B Dunlop
###################################################################################
# The imports and defining the plugin name
import sys
import time

import maya.api.OpenMaya as om2
import maya.cmds as cmds

try:
    import simplejson as sjson
except ImportError:
    print("saveSkinWeights: simplejson not found!")

from pluginUtils import skinCluster as u_skinCluster

kPluginCmdName = "saveSkinWeights"


class SaveSkinWeights(om2.MPxCommand):
    def __init__(self):
        om2.MPxCommand.__init__(self)
        self.filepath = None
        self.skipZeroWeights = True

        if not self.hasSyntax():
            self.syntaxCreator()

    def resolve(self):
        if not cmds.ls(sl=True):
            self.displayError("You must have a valid selection of skinned geometry!")
            return None

        ## Resolve the selection and return the skinClusters for the doIt
        geo = om2.MSelectionList()
        for eachGeo in cmds.ls(sl=True):
            geo.add(eachGeo)

        return geo

    def doIt(self, args):
        """
        :param fp: Path including filename.ext as a string
        :param szw: Store any weights that are 0 in value? Bool
        USage:
            fp="C:/temp/agathaV01.json"
            cmds.jbdSaveWeights(fp=fp, szw=False)
        """
        self.parseArgs(args)
        geoList = self.resolve()
        if geoList is None:
            return

        start = time.time()
        data = u_skinCluster.fetchSkinWeights(
            geo=geoList, skipZeroWeights=self.skipZeroWeights
        )
        if data:
            with open(self.filepath, "w") as outfile:
                outfile.write(sjson.dumps(data))

            self.displayInfo(
                "Time to export skinWeights: {}".format(time.time() - start)
            )
            return

        self.displayError("Nothing to export. Skipping.")

    def isUndoable(self):
        return False

    def parseArgs(self, args):
        # look into MArgList
        # om2.MArgList.
        argData = om2.MArgParser(self.syntax, args)
        if argData.isFlagSet("fp"):
            self.filepath = argData.flagArgumentString("fp", 0)
        if argData.isFlagSet("szw"):
            self.skipZeroWeights = argData.flagArgumentBool("szw", 0)

    def syntaxCreator(self):
        self.syntax = om2.MSyntax()
        self.syntax.enableQuery = True
        self.syntax.setMaxObjects(2)
        self.syntax.addFlag("fp", "filepath", om2.MSyntax.kString)
        self.syntax.addFlag("szw", "skipZeroWeights", om2.MSyntax.kBoolean)

    @staticmethod
    def cmdCreator():
        return SaveSkinWeights()


###################################################################################
# The code to setup maya to know about the command, how to initialize(setup) and Uninitialize(teardown) the plugin in the
# current maya session
def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass


# Initialize the script plug-in
def initializePlugin(mobject):
    mplugin = om2.MFnPlugin(mobject, vendor="jamesd", version="0.0.1", apiVersion="Any")
    try:
        mplugin.registerCommand(kPluginCmdName, SaveSkinWeights.cmdCreator)
        sys.stderr.write(
            "Successfully registered command: {} from {}\n".format(
                kPluginCmdName, mplugin.loadPath()
            )
        )
    except:
        sys.stderr.write("Failed to register command: %s\n" % kPluginCmdName)
        raise


# Uninitialize the script plug-in
def uninitializePlugin(mobject):
    mplugin = om2.MFnPlugin(mobject)
    try:
        mplugin.deregisterCommand(kPluginCmdName)
        sys.stderr.write(
            "Successfully unregistered command: {} from {}\n".format(
                kPluginCmdName, mplugin.loadPath()
            )
        )
    except:
        sys.stderr.write("Failed to unregister command: %s\n" % kPluginCmdName)
