#  Copyright (c) 2020.  James B Dunlop
import sys
import time

import maya.api.OpenMaya as om2
import maya.cmds as cmds

from pluginUtils import skinCluster as u_skinCluster

kPluginCmdName = "resetSkinCluster"


class ResetSkinCluster(om2.MPxCommand):
    myDGMod = om2.MDGModifier()

    def __init__(self):
        om2.MPxCommand.__init__(self)

    def resolve(self):
        ## Resolve the selection and return the skinClusters for the doIt
        skinClusters = om2.MSelectionList()

        if cmds.ls(sl=True):
            geo = om2.MGlobal.getActiveSelectionList()
            for x in range(geo.length()):
                skCls = u_skinCluster.findSkinCluster(
                    mesh=om2.MObjectHandle(geo.getDependNode(x))
                )
                if skCls is not None:
                    skinClusters.add(skCls.object())

        return skinClusters

    def doIt(self, args):
        # Invoked once when the command is run. If the actions need to be redone Maya will call the redoIt() method
        ## Resolve the selection
        skinClusters = self.resolve()
        if skinClusters.length() == 0:
            self.displayInfo("You must have a valid selection of skinned geometry!")
            return

        ## Iter through all the skinclusters in the MSelectionList
        for x in range(skinClusters.length()):
            start = time.time()
            ## Get the dependNode and then the attributes of interest on the skinCluster
            ## Convert those attributes to MPlugs
            skClsMFnDep = om2.MFnDependencyNode(skinClusters.getDependNode(x))
            bindPrePlug = skClsMFnDep.findPlug("bindPreMatrix", False)
            matrixPlug = skClsMFnDep.findPlug("matrix", False)

            ## Find the bindPose node and get it's name
            dagPoseMObj = skClsMFnDep.findPlug("bindPose", False).source().node()
            dagPoseName = om2.MFnDependencyNode(dagPoseMObj).absoluteName()

            ## Get a list of all the valid connected indices in the matrix array now.
            indices = matrixPlug.getExistingArrayAttributeIndices()
            influences = []
            for idx in indices:
                ## Get the inverseMatrix plug from the source and put that into the bindPreMatrix
                connectedMObj = matrixPlug.elementByLogicalIndex(idx).source().node()
                worldInverseMatrixMFn = om2.MFnDependencyNode(connectedMObj)
                inverseMtxPlug = worldInverseMatrixMFn.findPlug(
                    "worldInverseMatrix", False
                )
                InvMtx_matrixAsMObj = inverseMtxPlug.elementByLogicalIndex(
                    0
                ).asMObject()

                ## Store this in the myDGMod for exec after we have run through all the indices.
                self.myDGMod.newPlugValue(
                    bindPrePlug.elementByLogicalIndex(idx), InvMtx_matrixAsMObj
                )

                ## And store the influence on the way through for the bindPose reset
                nodeMobj = matrixPlug.elementByLogicalIndex(idx).source().node()
                inf = om2.MFnDependencyNode(nodeMobj)
                if not inf.hasUniqueName():
                    infName = om2.MDagPath.getAPathTo(nodeMobj).fullPathName()
                else:
                    infName = inf.absoluteName()

                influences.append(infName)

            ## Set all of the bindPreMatrix now.
            self.myDGMod.doIt()

            #################################################
            ## Now make sure the bindPose is fixed up or resetBindPose will fail.
            ## Don't know the om2 equiv of this! grrr
            cmds.dagPose(influences, reset=True, n=dagPoseName)

            self.displayInfo(
                "Reset: {} in {} secs.".format(skClsMFnDep.name(), time.time() - start)
            )

    def undoIt(self):
        self.myDGMod.undoIt()

    def redoIt(self):
        self.myDGMod.doIt()

    def isUndoable(self):
        return True

    @staticmethod
    def cmdCreator():
        return ResetSkinCluster()


def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass


def initializePlugin(mobject):
    mplugin = om2.MFnPlugin(mobject, vendor="jamesdunlop", version="0.0.2", apiVersion="Any")
    try:
        mplugin.registerCommand(kPluginCmdName, ResetSkinCluster.cmdCreator)
        sys.stderr.write("Successfully registered command: {} from {}\n".format(kPluginCmdName, mplugin.loadPath()))
    except:
        sys.stderr.write("Failed to register command: {}\n".format(kPluginCmdName))
        raise


def uninitializePlugin(mobject):
    mplugin = om2.MFnPlugin(mobject)
    try:
        mplugin.deregisterCommand(kPluginCmdName)
        sys.stderr.write(
            "Successfully unregistered command: {}\n".format(kPluginCmdName)
        )
    except:
        sys.stderr.write("Failed to unregistered command: {}\n".format(kPluginCmdName))
