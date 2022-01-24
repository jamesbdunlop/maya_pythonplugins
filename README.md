# maya_pythonplugins

skinTo:
----------
Is a util for xferring skinning from one mesh to another 
```
args:
:param maxInfluences: is the number of max influences on the source
:param byUVSpace: if you want to xFer using UV maps or not
:param uvSpace: The uvSpace flag indicates that the weight transfer should occur in UV space, based on the source
                 and destination UV sets specified.
:param surfaceAssociation: The surfaceAssociation flag controls how the weights are transferred between the
                        surfaces: "closestPoint", "rayCast", or "closestComponent". The default is closestComponen

Usage:
cmds.skinTo(maxNumInfluences=2, buv=True, sa="closestComponent", uv1='map1', uv2='map2')
```

resetSkinCluster:
----------------
Is a util for resetting the skin if you have moved joints due to refitting a character.

```
cmds.resetSkinCluster()
```

saveSkinWeights:
----------------
An om2 skinweight saver that works pretty fast
```
:param fp: Path including filename.ext as a string
:param szw: Store any weights that are 0 in value? Bool
Usage:
    fp="C:/temp/agathaV01.json"
    cmds.jbdSaveWeights(fp=fp, szw=False)
```

loadSkinWeights:
----------------
For use with the saveSkinweights data, loads the skinWeights back onto the selected meshes.
```
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

Usage:
fp="C:/temp/agathaV01.json"
# Verts no nameCheck
cmds.jbdLoadWeights(fp=fp, ns="", sv=True, nc=True)
# Verts nameCheck
cmds.jbdLoadWeights(fp=fp, ns="", sv=True, nc=False)
# Full load mesh sel
cmds.jbdLoadWeights(fp=fp, ns="", sv=False, nc=False)
```