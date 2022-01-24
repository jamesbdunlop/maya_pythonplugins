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
    print("loadSkinWeights: simplejson not found!")
from pluginUtils import skinCluster as u_skinCluster
from pluginUtils import plugs as u_plugs

kPluginCmdName = "loadSkinWeights"


class LoadSkinWeights(om2.MPxCommand):
    def __init__(self):
        om2.MPxCommand.__init__(self)
        self.filepath = None
        self.namespace = ""
        self.selectedVerts = False
        self.forceNameCheck = False

        if not self.hasSyntax():
            self.syntaxCreator()

    def resolve(self):
        geoList = None
        curSel = cmds.ls(sl=True)
        ids = []
        if not curSel:
            self.displayError(
                "You must have a valid mesh or vtx selection to load weights!!"
            )
            return ids, geoList

        if self.selectedVerts:
            if ".vtx" not in curSel[0]:
                self.displayError("sv=True. You must have a valid vertex selection!")
                return ids, geoList

            ids = [
                int(v.split(".vtx[")[-1].replace("]", ""))
                for v in cmds.ls(sl=True, fl=True)
            ]
            geoList = [cmds.ls(sl=True)[0].split(".")[0]]
        else:
            if ".vtx" in curSel[0]:
                self.displayError("sv=False. You must have a valid geo selection!")
                return ids, geoList
            geoList = curSel

        return ids, geoList

    def doIt(self, args):
        """
        :param fp: `str` path to the json including the fileName.json
        :param ns: `str` namespace for the influences if there is one, as saving strips namespaces from the joints
        :param sv: `bool` load to selected verts or not?
        :param nc: `bool` scan the skCls.matrix array to find the idx by inf name.

        It's important to note the following:
        If you've got an existing mesh and you're loading the weights back on it, the weightList logical indices should
        match the matrix logical indicies and you won't need to set the nameCheck to true.
        If you've rebound since saving you should prob force a name check to make sure
        that any logical indicies that may now be differrent(but match an id in the json) can be resolved by influence names.
        This will practically double the time to load skinWeights though.
        USage:
            fp="C:/temp/agathaV01.json"
            # Verts no nameCheck
            cmds.jbdLoadWeights(fp=fp, ns="", sv=True, nc=True)
            # Verts nameCheck
            cmds.jbdLoadWeights(fp=fp, ns="", sv=True, nc=False)
            # Full load mesh sel
            cmds.jbdLoadWeights(fp=fp, ns="", sv=False, nc=False)
        """
        self.parseArgs(args)

        ids, geoList = self.resolve()
        if geoList is None:
            return

        start = time.time()
        with open(self.filepath) as infile:
            data = sjson.load(infile)
        self.displayInfo("Time to load json: {}".format(time.time() - start))

        for geoName, skData in data.items():
            if geoList is not None and geoName not in geoList:
                continue

            self.displayInfo("Setting weights for geoName: {}".format(geoName))

            selList = om2.MSelectionList()
            selList.add(geoName)

            geoMObjH = om2.MObjectHandle(selList.getDependNode(0))
            # Do we have a skinCluster on this geo??
            skinClusterMObjH = u_skinCluster.findSkinCluster(geoMObjH)

            # if not lets make one now from the influence list!
            for skCLS, weightData in skData.items():
                if skinClusterMObjH is None:
                    self.displayInfo(
                        "No skinCluster found for {}! Attempting to make one now..".format(
                            geoName
                        )
                    )
                    influences = [
                        "{}:{}".format(self.namespace, j)
                        for j in weightData["influences"]
                    ]
                    maxInf = weightData["maxInf"]
                    cmds.skinCluster(
                        influences + [geoName],
                        frontOfChain=False,
                        n=skCLS,
                        maximumInfluences=maxInf,
                    )

                ## Now proceed as we should have a valid skinCluster
                selList.add(skCLS)
                skinClusterMObjH = om2.MObjectHandle(selList.getDependNode(1))

                weights = weightData["weights"]
                weightPlug = u_plugs.findPlugOnNode(skinClusterMObjH, "weightList")
                matrixPlug = u_plugs.findPlugOnNode(skinClusterMObjH, "matrix")
                if weightPlug.isNull or matrixPlug.isNull:
                    self.displayWarning(
                        ".weightList or .matrix plug not found on skinCluster!"
                    )
                    return

                if self.forceNameCheck:
                    # Cache the current matrix locigal indices influence names
                    self.matrixCacheById = {}
                    self.matrixCacheByName = {}
                    for i in matrixPlug.getExistingArrayAttributeIndices():
                        skInfName = om2.MNamespace.stripNamespaceFromName(
                            om2.MFnDagNode(
                                matrixPlug.elementByLogicalIndex(i).source().node()
                            ).name()
                        )
                        self.matrixCacheById[i] = skInfName
                        self.matrixCacheByName[skInfName] = i

                for idx, weightList in weights.items():
                    if self.selectedVerts and int(idx) not in ids:
                        continue

                    p = weightPlug.elementByLogicalIndex(int(idx))
                    c = p.child(0)

                    ## Set ALL existing array indices to 0
                    existing = c.getExistingArrayAttributeIndices()
                    for x in range(len(existing)):
                        c.elementByLogicalIndex(existing[x]).setFloat(0)

                    ## Now set the saved weights
                    for eachWeight in weightList:
                        id = eachWeight[0]
                        val = eachWeight[1]
                        inf = eachWeight[2]

                        # Sel verts and we're merging weights we might have clashing logical indices so we check against inf names
                        if self.forceNameCheck:
                            if self.matrixCacheById[id] != inf:
                                if inf in self.matrixCacheByName.keys():
                                    id = self.matrixCacheByName[inf]
                                else:
                                    continue

                        c.elementByLogicalIndex(id).setFloat(val)

        self.displayInfo(
            "Success: Time to load skinWeights: {}".format(time.time() - start)
        )

    def isUndoable(self):
        return False

    def parseArgs(self, args):
        argData = om2.MArgParser(self.syntax, args)

        if argData.isFlagSet("fp"):
            self.filepath = argData.flagArgumentString("fp", 0)
        if argData.isFlagSet("ns"):
            self.namespace = argData.flagArgumentString("ns", 0)
        if argData.isFlagSet("sv"):
            self.selectedVerts = argData.flagArgumentBool("sv", 0)
        if argData.isFlagSet("nc"):
            self.forceNameCheck = argData.flagArgumentBool("nc", 0)

    def syntaxCreator(self):
        self.syntax = om2.MSyntax()
        self.syntax.enableQuery = True
        self.syntax.setMaxObjects(2)
        self.syntax.addFlag("fp", "filepath", om2.MSyntax.kString)
        self.syntax.addFlag("ns", "namespace", om2.MSyntax.kString)
        self.syntax.addFlag("sv", "selectedVerts", om2.MSyntax.kBoolean)
        self.syntax.addFlag("nc", "forceNameCheck", om2.MSyntax.kBoolean)

    @staticmethod
    def cmdCreator():
        return LoadSkinWeights()


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
    mplugin = om2.MFnPlugin(
        mobject, vendor="jamesd", version="0.0.21", apiVersion="Any"
    )
    try:
        mplugin.registerCommand(kPluginCmdName, LoadSkinWeights.cmdCreator)
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
