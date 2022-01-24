#  Copyright (c) 2020.  James B Dunlop
import logging

import maya.api.OpenMaya as om2

from pluginUtils import types as mpu_types

logger = logging.getLogger(__name__)


# <editor-fold desc="Find Plug functions">

def findPlugOnNode(node, plugName):
    """
    :param node: MObjectHandle
    :return: MPlug
    """
    if not node.isValid():
        raise Exception("Node is no longer valid!")

    mFn = om2.MFnDependencyNode(node.object())
    # Hate a try expect, but want a clean empty plug returned if we can't find the name on the node.
    try:
        plug = mFn.findPlug(plugName, False)
    except RuntimeError:
        plug = om2.MPlug()

    return plug


def getPlugFromAttributeName(node, attributeName):
    """
    :param node: `MObjectHandle`
    :param attributeName: `str` Name
    :return: `MPlug`
    """
    if not node.isValid():
        raise Exception("Node is no longer valid!")

    mFn = om2.MFnDependencyNode(node.object())
    attr = mFn.attribute(attributeName)
    if not om2.MObjectHandle(attr).isValid():
        raise Exception("Attribute {} is not valid!".format(attributeName))

    plug = om2.MPlug(node.object(), attr)

    return plug
# </editor-fold>


# <editor-fold desc="Get Plug functions">


def getMPlugValue(mplug):
    # type: (MPlug) -> any
    if not om2.MObjectHandle(mplug.node()).isValid():
        return

    pAttribute = mplug.attribute()
    apiType = pAttribute.apiType()
    # Float Groups - rotate, translate, scale; Com2pounds
    if apiType in [
        om2.MFn.kAttribute3Double,
        om2.MFn.kAttribute3Float,
        om2.MFn.kCompoundAttribute,
    ]:
        result = []
        if mplug.isCompound:
            for c in range(mplug.numChildren()):
                result.append(getMPlugValue(mplug.child(c)))
            return result

    # Distance
    elif apiType in [om2.MFn.kDoubleLinearAttribute, om2.MFn.kFloatLinearAttribute]:
        return mplug.asMDistance().asCentimeters()

    # Angle
    elif apiType in [om2.MFn.kDoubleAngleAttribute, om2.MFn.kFloatAngleAttribute]:
        return mplug.asMAngle().asDegrees()

    # TYPED
    elif apiType == om2.MFn.kTypedAttribute:
        pType = om2.MFnTypedAttribute(pAttribute).attrType()
        # Matrix
        if pType == om2.MFnData.kMatrix:
            return om2.MFnMatrixData(mplug.asMObject()).matrix()
        # String
        elif pType == om2.MFnData.kString:
            return mplug.asString()

    # MATRIX
    elif apiType == om2.MFn.kMatrixAttribute:
        return om2.MFnMatrixData(mplug.asMObject()).matrix()

    # NUMBERS
    elif apiType == om2.MFn.kNumericAttribute:
        pType = om2.MFnNumericAttribute(pAttribute).numericType()
        if pType == om2.MFnNumericData.kBoolean:
            return mplug.asBool()
        elif pType in [
            om2.MFnNumericData.kShort,
            om2.MFnNumericData.kInt,
            om2.MFnNumericData.kLong,
            om2.MFnNumericData.kByte,
        ]:
            return mplug.asInt()
        elif pType in [
            om2.MFnNumericData.kFloat,
            om2.MFnNumericData.kDouble,
            om2.MFnNumericData.kAddr,
        ]:
            return mplug.asDouble()

    # Enum
    elif apiType == om2.MFn.kEnumAttribute:
        return mplug.asInt()


def getMPlugType(mplug):
    # type: (MPlug) -> int
    if not om2.MObjectHandle(mplug.node()).isValid():
        return

    pAttribute = mplug.attribute()
    apiType = pAttribute.apiType()

    # Float Groups - rotate, translate, scale; Com2pounds
    if apiType in [
        om2.MFn.kAttribute3Double,
        om2.MFn.kAttribute3Float,
        om2.MFn.kCompoundAttribute,
    ]:
        result = []
        if mplug.isCompound:
            for c in range(mplug.numChildren()):
                result.append(getMPlugType(mplug.child(c)))
            return result

    # Distance
    elif apiType in [om2.MFn.kDoubleLinearAttribute, om2.MFn.kFloatLinearAttribute]:
        return mpu_types.FLOAT

    # Angle
    elif apiType in [om2.MFn.kDoubleAngleAttribute, om2.MFn.kFloatAngleAttribute]:
        return mpu_types.FLOAT

    # TYPED
    elif apiType == om2.MFn.kTypedAttribute:
        pType = om2.MFnTypedAttribute(pAttribute).attrType()
        # Matrix
        if pType == om2.MFnData.kMatrix:
            return mpu_types.MATRIXF44
        # String
        elif pType == om2.MFnData.kString:
            return mpu_types.STRING

    # MATRIX
    elif apiType == om2.MFn.kMatrixAttribute:
        return mpu_types.MATRIXF44

    # NUMBERS
    elif apiType == om2.MFn.kNumericAttribute:
        pType = om2.MFnNumericAttribute(pAttribute).numericType()
        if pType == om2.MFnNumericData.kBoolean:
            return mpu_types.BOOL

        elif pType in [
            om2.MFnNumericData.kShort,
            om2.MFnNumericData.kInt,
            om2.MFnNumericData.kLong,
            om2.MFnNumericData.kByte,
        ]:
            return mpu_types.INT

        elif pType in [
            om2.MFnNumericData.kFloat,
            om2.MFnNumericData.kDouble,
            om2.MFnNumericData.kAddr,
        ]:
            return mpu_types.DOUBLE

    # Enum
    elif apiType == om2.MFn.kEnumAttribute:
        return mpu_types.INT

    elif apiType == om2.MFn.kMessageAttribute:
        return mpu_types.MESSAGE


def getMPlugFromLongName(nodeLongName, plugName):
    # type: (str, str) -> om2.MPlug
    if isinstance(plugName, list):
        plugName = plugName[0]

    mSel = om2.MSelectionList()
    try:
        mSel.add(str(nodeLongName))
        mObj = mSel.getDependNode(0)
        mFn = om2.MFnDependencyNode(mObj)
        mplug = mFn.findPlug(plugName, False)
    except RuntimeError:
        logger.error("Failed to add to MSelectionList. %s does not exist!" % nodeLongName)
        mplug = om2.MPlug()

    return mplug


def getMPlugElementFromLongName(nodeLongName, plugName, index, useLogicalIndex=True):
    # type: (str, str, int, bool) -> om2.MPlug
    parentPlug = getMPlugFromLongName(nodeLongName, plugName)
    if parentPlug.isArray():
        mplug = getMPlugArrayElement(parentPlug, index, useLogicalIndex=useLogicalIndex)

        return mplug


def getMPlugArrayElement(mplug, index, useLogicalIndex=True):
    # type: (om2.MPlug, int, bool) -> om2.MPlug
    if useLogicalIndex:
        mplug = mplug.elementyByLogicalIndex(index)
    else:
        mplug = mplug.elementByPhysicalIndex(index)

    return mplug


def getMPlugChildFromLongName(nodeLongName, plugName, index):
    # type: (str, str, int) -> om2.MPlug
    parentPlug = getMPlugFromLongName(nodeLongName, plugName)
    if parentPlug.isCompound:
        mplug = parentPlug.child(index)

        return mplug

# </editor-fold>


# <editor-fold desc="Set Plug functions">
def setMPlugValue(mplug, value):
    plugType = getMPlugType(mplug)
    status = False
    if plugType == "message":
        return

    pAttribute = mplug.attribute()
    apiType = pAttribute.apiType()
    if apiType in [om2.MFn.kAttribute3Double, om2.MFn.kAttribute3Float, om2.MFn.kCompoundAttribute]:
        if mplug.isCompound:
            for x in range(mplug.numChildren()):
                if not mplug.child(x).isConnected:
                    mplug.child(x).setFloat(value[x])

    elif plugType == mpu_types.FLOAT:
        mplug.setFloat(value)
        status = True

    elif plugType == mpu_types.MATRIXF44:
        pass
        # mplug.setMatrix(value)
        # status = True

    elif plugType == mpu_types.INT:
        mplug.setInt(value)
        status = True

    elif plugType == mpu_types.BOOL:
        mplug.setBool(value)
        status = True

    elif plugType == mpu_types.DOUBLE:
        mplug.setDouble(value)
        status = True

    return status
# </editor-fold>


# <editor-fold desc="Index Plug functions (for arrays and compounds)">
def isMPlugIndexed(mPlug):
    isElement = mPlug.isElement
    isChild = mPlug.isChild
    isIndexed = any((isElement, isChild))
    logger.debug("mPlug: %s isIndexed: %s" % (mPlug.name(), isIndexed))

    return isIndexed


def fetchIndexedPlugData(mplug, plgData=None):
    # type: (om2.MPlug, list) -> list
    """
    builds a list of the hrc of the plug. the last is the list is the first plug in the hrc.
    eg:
        plgData = [[False, True, u'cvs[0]', 0], [True, False, u'jd_hermiteArrayCrv1.cvs', None]]
        plgData = [isElement, isChild, plugName, plgIdx], [isElement, isChild, plugName, plgIdx]]
    """
    logger.debug("Iter Ascendants: \t\t%s" % mplug.name())
    if plgData is None:
        plgData = list()

    isIndexedMPlug = isMPlugIndexed(mplug)
    currentPlug = [None] * 4
    parentPlug = None

    if isIndexedMPlug and mplug.isElement:
        logger.debug("\t\t\t\t\t\t\t\tISELEMENT!")
        partialName = mplug.partialName(False, False, False, False, True, True)
        currentPlug[3] = mplug.logicalIndex()
        logger.debug("\t\t\t\t\t\t\t\tarrayIndex: %s" % mplug.logicalIndex())

    elif isIndexedMPlug and mplug.isChild:
        logger.debug("\t\t\t\t\t\t\t\tISCHILD!")
        partialName = mplug.partialName(False, False, False, False, True, True)
        parentPlug = mplug.parent()
        for x in range(parentPlug.numChildren()):
            if parentPlug.child(x) == mplug:
                logger.debug("\t\t\t\t\t\t\t\tchildIndex: %s" % x)
                currentPlug[3] = x
                break

    else:
        logger.debug("\t\t\t\t\t\t\t\tISFIRST!")
        partialName = mplug.partialName(False, False, False, False, True, True)

    # And because maya is  DICK and can still leave a [0] in the name.. lets split if we find one.. grrr
    if "." in partialName:
        partialName = partialName.split(".")[-1]

    if "[" in partialName:
        partialName = partialName.split("[")[0]

    currentPlug[0] = mplug.isElement
    currentPlug[1] = mplug.isChild
    currentPlug[2] = partialName

    logger.debug("\t\t\t\t\t\t\t\tcurrentPlug: %s" % currentPlug)
    plgData.append(currentPlug)
    if parentPlug is None:
        logger.debug("\t\t\t\t\t\t\t\tPLUG IS NEITHER ELEMENT OR CHILD.")
        logger.debug("\t\t\t\t\t\t\t\tPLGDATA: %s" % plgData)
        logger.debug("###########")
        return plgData

    # Now keep going up the line cause we want the full path to the connected plug which might be a
    # compound.child(0).array(0) etc
    return fetchIndexedPlugData(parentPlug, plgData)


def fetchMPlugFromConnectionData(nodeLongName, plugData):
    copyPlugData = plugData[:]
    mPlug = None

    logger.debug("-----------fetchMPlugFromConnectionData-------------")
    logger.debug("\t--copyPlugData: %s" % copyPlugData)
    while copyPlugData:
        plgIsElement, plgIsChild, plgPlugName, plgIndex = copyPlugData[-1]
        logger.debug("\t%-- s %s %s %s" % (plgIsElement, plgIsChild, plgPlugName, plgIndex))

        if mPlug is None:
            mPlug = getMPlugFromLongName(nodeLongName, plgPlugName)
            if plgIsElement:
                mPlug = mPlug.elementByLogicalIndex(plgIndex)
            elif plgIsChild:
                mPlug = mPlug.child(plgIndex)
            logger.debug("\tFound starting plug: %s" % (mPlug.name()))

        elif plgIsElement:
            logger.debug("\t\t%s IsElement" % (plgPlugName))
            logger.debug("\t\tparentPlug: %s" % (mPlug.name()))
            mPlug = mPlug.elementByLogicalIndex(plgIndex)
            logger.debug("\t\tnewPlug: %s" % (mPlug.name()))

        elif plgIsChild:
            logger.debug("\t\t%s IsChild" % (plgPlugName))
            logger.debug("\t\tparentPlug: %s" % (mPlug.name()))
            mPlug = mPlug.child(plgIndex)
            logger.debug("\t\tnewPlug: %s" % (mPlug.name()))

        copyPlugData.pop()

    if mPlug is None:
        raise Exception("Unable to find MPlug from plugData: %s!" % plugData)

    logger.debug("FINAL PLUG %s" % mPlug.name())
    return mPlug
# </editor-fold>
