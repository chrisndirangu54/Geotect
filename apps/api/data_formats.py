from __future__ import annotations
from pathlib import Path
import json

def write_geoparquet(records:list[dict],path:str)->dict:
    try:
        import pyarrow as pa,pyarrow.parquet as pq
    except Exception as exc:raise RuntimeError("pyarrow is required for GeoParquet export") from exc
    rows=[]
    for r in records:
        row=dict(r);geom=row.pop("geometry",None);row["geometry_json"]=json.dumps(geom) if geom is not None else None;rows.append(row)
    table=pa.Table.from_pylist(rows);meta=dict(table.schema.metadata or {});meta[b"geo"]=json.dumps({"version":"1.1.0","primary_column":"geometry_json",
      "columns":{"geometry_json":{"encoding":"GeoJSON","geometry_types":[]}}}).encode()
    table=table.replace_schema_metadata(meta);pq.write_table(table,path)
    return {"path":path,"rows":len(records),"format":"GeoParquet"}

def write_zarr(array,path:str,name:str="data",attrs:dict|None=None)->dict:
    try:
        import zarr,numpy as np
    except Exception as exc:raise RuntimeError("zarr and numpy are required") from exc
    a=np.asarray(array);root=zarr.open_group(path,mode="w");root.create_array(name,data=a,chunks="auto");root.attrs.update(attrs or {})
    return {"path":path,"name":name,"shape":list(a.shape),"dtype":str(a.dtype),"format":"Zarr"}

def inspect_copc(path:str)->dict:
    import laspy
    with laspy.CopcReader.open(path) as reader:
        h=reader.header
        return {"point_count":int(h.point_count),"mins":list(map(float,h.mins)),"maxs":list(map(float,h.maxs)),
          "scales":list(map(float,h.scales)),"offsets":list(map(float,h.offsets)),"format":"COPC"}

def e57_exchange_manifest(scans:list[dict])->dict:
    return {"format":"ASTM E2807/E57-compatible exchange manifest","scans":scans,
      "note":"Binary E57 parsing/writing is delegated to an installed E57 library or scanner vendor bridge."}
