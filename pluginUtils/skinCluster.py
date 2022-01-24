#  Copyright (c) 2020.  James B Dunlop
import logging

import maya.api.OpenMaya as om2
import maya.cmds as cmds

import pluginUtils.skinCluster as mPlugUtils_skin
import pluginUtils.plugs as mPlugUtils_plugs

logging.basicConfig()
logger = logging.getLogger(__name__)


def iterForSkinCluster(node):
    """
    :param node: MObject for the source connection
    :return: MObject
    """
    if node.apiType() == om2.MFn.kSkinClusterFilter:
        return om2.MObjectHandle(node)

    iterDg = om2.MItDependencyGraph(
        node, om2.MItDependencyGraph.kDownstream, om2.MItDependencyGraph.kPlugLevel
    )
    while not iterDg.isDone():
        currentItem = iterDg.currentNode()
        if currentItem.hasFn(om2.MFn.kSkinClusterFilter):
            return om2.MObjectHandle(currentItem)

        iterDg.next()


def findSkinCluster(mesh):
    """
    Find a skinCluster attached to the kMesh or kNurbsCurve

    @:param mesh: `MObjectHandle`. Not the shape! Use the transform!
    :return: `MObjectHandle`
    """
    if not mesh.isValid():
        logger.warning("Destination mesh MObject is no longer valid!")
        return

    dagPath = om2.MDagPath()
    geo = dagPath.getAPathTo(mesh.object())

    ## Does it have a valid number of shapes?
    if geo.numberOfShapesDirectlyBelow() != 0:
        ## Fetch the shape of the geo now.
        shapeMobj = geo.extendToShape().node()
        mFn_shape = om2.MFnDependencyNode(shapeMobj)
        apiType = shapeMobj.apiType()
        if apiType == om2.MFn.kMesh:
            ## Look at the inMesh attr for the source
            inMesh_attr = mFn_shape.attribute("inMesh")
        elif apiType == om2.MFn.kNurbsCurve:
            inMesh_attr = mFn_shape.attribute("create")
        else:
            logger.warning(
                "This type of om2.MFn node is not supported! int: {}".format(apiType)
            )
            return

        inMesh_plug = om2.MPlug(shapeMobj, inMesh_attr)
        getSource = inMesh_plug.source().node()

        ## Now use the iterForSkinCluster() function to find the skinCluster in the connected network.
        skinClusterNode_MObjH = iterForSkinCluster(getSource)

        if skinClusterNode_MObjH is not None:
            return skinClusterNode_MObjH


def findInfluences(skinClusterMobjH=None):
    """
    returns all the valid influences from the .matrix attribute on the skinCluster node.

    :param mesh: MObjectHandle for the skinCluster. Using the handles here may be playing it a little too safe. But meh.
    :return: MObject
    """
    if not skinClusterMobjH.isValid():
        logger.warning("Skincluster is no longer valid! Did it get deleted?")
        return

    skClsMFnDep = om2.MFnDependencyNode(skinClusterMobjH.object())
    mtxAttr = skClsMFnDep.attribute("matrix")
    matrixPlug = om2.MPlug(skinClusterMobjH.object(), mtxAttr)

    ## Get a list of all the valid connected indices in the matrix array now.
    indices = matrixPlug.getExistingArrayAttributeIndices()
    influences = []
    for idx in indices:
        name = om2.MFnDependencyNode(
            matrixPlug.elementByLogicalIndex(idx).source().node()
        ).absoluteName()
        influences.append(str(om2.MNamespace.stripNamespaceFromName(name)))

    return influences


def fetchSkinWeights(geo=None, skipZeroWeights=True):
    """
    If you send in a list of geo, we'll use that. Else we assume we're working off selected.

    :param geoList: MSelectionList of geo to itr
    :param skipZeroWeights: if you want to avoid saving all 0.0 weight data
    :return: dict
    """
    weightData = {}
    for x in range(geo.length()):
        geoMObjH = om2.MObjectHandle(geo.getDependNode(x))
        geoName = om2.MNamespace.stripNamespaceFromName(
            om2.MFnDependencyNode(geoMObjH.object()).name()
        )
        skinClusterMObjH = findSkinCluster(geoMObjH)
        if skinClusterMObjH is None:
            logger.warning("Skipping {} has no skinCluster!".format(geoName))
            continue

        skName = str(
            om2.MNamespace.stripNamespaceFromName(
                om2.MFnDependencyNode(skinClusterMObjH.object()).name()
            )
        )

        influences = findInfluences(skinClusterMObjH)
        ## Add the data to the dict
        weightData[geoName] = {}
        weightData[geoName][skName] = {}
        weightData[geoName][skName]["influences"] = influences
        weightData[geoName][skName]["maxInf"] = cmds.skinCluster(
            skName, q=True, maximumInfluences=True
        )
        weightData[geoName][skName]["weights"] = {}

        ## Fetch the weights now
        weightPlug = mPlugUtils_plugs.findPlugOnNode(skinClusterMObjH, "weightList")
        matrixPlug = mPlugUtils_plugs.findPlugOnNode(skinClusterMObjH, "matrix")
        if weightPlug.isNull or matrixPlug.isNull:
            logger.warning(".weightList or .matrix plug not found on skinCluster!")
            return

        weightCount = weightPlug.getExistingArrayAttributeIndices()
        for x in range(len(weightCount)):
            # .weightList[x]
            p = weightPlug.elementByLogicalIndex(weightCount[x])
            # .weights
            c = p.child(0)

            ## Now fetch the list of idx numbers that should relate to the inf [23, 66, 99]
            w = c.getExistingArrayAttributeIndices()

            ## For each idx we're going to build a tuple (idx, infName, weightVal)
            weightList = list()
            for i in range(len(w)):
                childPlug = c.elementByLogicalIndex(w[i])
                weightValue = mPlugUtils_plugs.getMPlugValue(childPlug)
                infName = om2.MNamespace.stripNamespaceFromName(
                    om2.MFnDagNode(
                        matrixPlug.elementByLogicalIndex(w[i]).source().node()
                    ).name()
                )

                if skipZeroWeights and weightValue == 0.0:
                    continue

                idx = w[i]
                weightList.append((idx, weightValue, infName))

            weightData[geoName][skName]["weights"][str(x)] = weightList

    return weightData
