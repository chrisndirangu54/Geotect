def point_tiles_to_3dtiles(manifest:dict)->dict:
    children=[]
    bounds=manifest.get("bounds",{})
    for tile in manifest.get("tiles",[]):
        mn=tile["min"];mx=tile["max"];cx=[(mn[i]+mx[i])/2 for i in range(3)];half=[max((mx[i]-mn[i])/2,1e-3) for i in range(3)]
        box=[cx[0],cx[1],cx[2],half[0],0,0,0,half[1],0,0,0,half[2]]
        children.append({"boundingVolume":{"box":box},"geometricError":0,"content":{"uri":tile["uri"]},"refine":"ADD","extras":{"points":tile.get("points")}})
    return {"asset":{"version":"1.1","generator":"GeoTect"},"geometricError":1000,"root":{"boundingVolume":{"box":[0,0,0,1,0,0,0,1,0,0,0,1]},"geometricError":1000,"refine":"ADD","children":children},
            "extras":{"source_format":manifest.get("format"),"note":"NPZ tile content requires a renderer/plugin or conversion to PNTS/glTF for standards-complete clients."}}
