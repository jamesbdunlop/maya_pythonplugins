#  Copyright (c) 2020.  James B Dunlop
import sys
import time

import maya.api.OpenMaya as om2
import maya.cmds as cmds

from pluginUtils import skinCluster as u_skinCluster

kPluginCmdName = "skinTo"
"""
usage:
cmds.skinTo(maxNumInfluences=2, buv=True, sa="closestComponent", uv1='map1', uv2='map2')
"""


class SkinTo(om2.MPxCommand):
    default_MaxInf = 4
    default_byUVSpace = False
    default_uvSpace = ["map1", "map1"]
    default_surfaceAssociation = "closestComponent"

    def __init__(self):
        om2.MPxCommand.__init__(self)
        self.maxInfluences = SkinTo.default_MaxInf
        self.byUVSpace = SkinTo.default_byUVSpace
        self.uvSpace = SkinTo.default_uvSpace
        self.surfaceAssociation = SkinTo.default_surfaceAssociation
        if not self.hasSyntax():
            self.syntaxCreator()

    def doIt(self, args):
        """
        Supports: kMesh and kNurbsCurve
        Use this to copy the skin weights from one mesh to another.
        Note: You don't need to have an existing skinCluster on the mesh you want to transfer to. It will bind for you.

        @:param maxInfluences: is the number of max influences on the source
        @:param byUVSpace: if you want to xFer using UV maps or not
        @:param uvSpace: The uvSpace flag indicates that the weight transfer should occur in UV space, based on the source
                         and destination UV sets specified.
        @:param surfaceAssociation: The surfaceAssociation flag controls how the weights are transferred between the
                                surfaces: "closestPoint", "rayCast", or "closestComponent". The default is closestComponent.
        """
        self.parseArgs(args)
        self.displayInfo("maxInfluences: {}".format(self.maxInfluences))
        self.displayInfo("byUVSpace: {}".format(self.byUVSpace))
        self.displayInfo("surfaceAssociation: {}".format(self.surfaceAssociation))
        self.displayInfo("uvSpace: {}".format(self.uvSpace))

        start = time.time()
        mySel = om2.MSelectionList()
        for eachMesh in cmds.ls(sl=True, long=True):
            mySel.add(eachMesh)

        ## Bail out if bad selection
        if mySel.length() < 2:
            self.displayError(
                "You must select a source mesh then ## of destination meshes!"
            )
            return

        # Find the skinCluster and the influences we need to bind.
        sourceMObj = mySel.getDependNode(0)
        sourceMObjH = om2.MObjectHandle(sourceMObj)
        sourceMFnDep = om2.MFnDependencyNode(sourceMObj)
        sourceSkCls = u_skinCluster.findSkinCluster(sourceMObjH)
        if sourceSkCls is None:
            self.displayInfo(
                "No valid skinCluster could be found on {}".format(sourceMFnDep.name())
            )
            return

        bindInfluences = u_skinCluster.findInfluences(sourceSkCls)

        ## Now bind each mesh to these influences
        for x in range(mySel.length()):
            ## Skip source mesh
            if x == 0:
                continue
            destMObj = mySel.getDependNode(x)
            destMObjH = om2.MObjectHandle(destMObj)
            destMFnDep = om2.MFnDependencyNode(destMObj)
            skCls = u_skinCluster.findSkinCluster(destMObjH)
            if skCls is not None:
                self.displayInfo(
                    "Found a skinCluster on {}. Skipping bind!".format(
                        destMFnDep.name()
                    )
                )
            else:
                ## Here we have to use CMDS to create the darn skinCluster and xfer!
                ## Note happy mixing cmds and om2 but short of writing a full om2 bind I'm sticking to this for now.
                cmds.skinCluster(
                    bindInfluences + [destMFnDep.name()],
                    name="{}_skCls".format(destMFnDep.name()),
                    before=True,
                    maximumInfluences=self.maxInfluences,
                )

            ## Now copy the weights over
            srcSkCls_MFnDep = om2.MFnDependencyNode(sourceSkCls.object())
            if self.byUVSpace:
                cmds.copySkinWeights(
                    sourceSkin=srcSkCls_MFnDep.name(),
                    destinationSkin="{}_skCls".format(destMFnDep.name()),
                    sa=self.surfaceAssociation,
                    noMirror=True,
                    ia=["closestJoint", "label",],
                    uvSpace=self.uvSpace,
                )
            else:
                cmds.copySkinWeights(
                    sourceSkin=srcSkCls_MFnDep.name(),
                    destinationSkin="{}_skCls".format(destMFnDep.name()),
                    sa=self.surfaceAssociation,
                    noMirror=True,
                    ia=["closestJoint", "label",],
                )

            self.displayInfo(
                "SkinTo complete! Time taken: {}secs".format(time.time() - start)
            )

    def isUndoable(self):
        return False

    def parseArgs(self, args):
        # Create an argument parser object
        # Used with a def syntaxCreator() function but for now this is a kFailure regardless of approach.
        argData = om2.MArgParser(self.syntax, args)
        self.displayInfo("PARSE: {}".format(argData.isFlagSet("max")))

        # Check if each flag is set, and store it's value
        if argData.isFlagSet("max"):
            self.maxInfluences = argData.flagArgumentInt("max", 0)
        if argData.isFlagSet("buv"):
            self.byUVSpace = argData.flagArgumentBool("buv", 0)
        if argData.isFlagSet("sa"):
            self.surfaceAssociation = argData.flagArgumentString("sa", 0)
        if argData.isFlagSet("uv1"):
            self.uvSpace[0] = argData.flagArgumentString("uv1", 0)
        if argData.isFlagSet("uv2"):
            self.uvSpace[1] = argData.flagArgumentString("uv2", 0)

    @staticmethod
    def cmdCreator():
        return SkinTo()

    def syntaxCreator(self):
        self.syntax = om2.MSyntax()
        self.syntax.enableQuery = True
        self.syntax.setMaxObjects(4)
        self.syntax.addFlag("max", "maxNumInfluences", om2.MSyntax.kDouble)
        self.syntax.addFlag("buv", "byUVSpace", om2.MSyntax.kBoolean)
        self.syntax.addFlag("sa", "surfaceAssociation", om2.MSyntax.kString)
        self.syntax.addFlag("uv1", "UVSpace1", om2.MSyntax.kString)
        self.syntax.addFlag("uv2", "UVSpace2", om2.MSyntax.kString)


def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass


def initializePlugin(mobject):
    mplugin = om2.MFnPlugin(
        mobject, vendor="jamesdunlop", version="0.0.2", apiVersion="Any"
    )
    try:
        mplugin.registerCommand(name=kPluginCmdName, createCmdFunc=SkinTo.cmdCreator)
        sys.stderr.write(
            "Successfully registered command: {} from {}\n".format(
                kPluginCmdName, mplugin.loadPath()
            )
        )
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
        sys.stderr.write("Failed to unregister command: {}\n".format(kPluginCmdName))
