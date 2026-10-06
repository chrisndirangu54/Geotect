from __future__ import annotations
import json
def export_geojson(features:list[dict])->dict:
    out=[]
    for f in features:
        pts=f.get("positions",[]);geom=f.get("geometry")
        coords=[[p["lon"],p["lat"],p.get("elevation_m",0)] for p in pts]
        gt="Point" if geom=="point" else "LineString" if geom=="polyline" else "Polygon"
        gc=coords[0] if gt=="Point" and coords else [coords] if gt=="Polygon" else coords
        out.append({"type":"Feature","id":f.get("id"),"geometry":{"type":gt,"coordinates":gc},"properties":{k:v for k,v in f.items() if k not in {"positions","geometry"}}})
    return {"type":"FeatureCollection","features":out}

def export_landxml_alignment(name:str,points:list[dict])->str:
    pnts="".join(f'<P id="{i+1}">{p["lat"]} {p["lon"]} {p.get("elevation_m",0)}</P>' for i,p in enumerate(points))
    return f'<?xml version="1.0"?><LandXML version="1.2"><CgPoints>{pnts}</CgPoints><Alignments><Alignment name="{name}"/></Alignments></LandXML>'

def ifc_manifest(objects:list[dict])->dict:
    return {"schema":"IFC4-alignment-manifest","objects":[{"external_id":o.get("id"),"type":o.get("kind",o.get("asset_type","IfcProxy")),"name":o.get("name"),"properties":o.get("properties",{})} for o in objects],
            "note":"Manifest maps GeoTect semantics for downstream IFC writer/converter."}
