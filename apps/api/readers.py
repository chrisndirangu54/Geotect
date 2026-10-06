from __future__ import annotations
from pathlib import Path

def read_geotiff(path: str) -> dict:
    import rasterio
    with rasterio.open(path) as src:
        b=src.bounds
        return {"format":"GeoTIFF","crs":str(src.crs),"width":src.width,"height":src.height,
                "bounds":{"left":b.left,"bottom":b.bottom,"right":b.right,"top":b.top},
                "count":src.count,"dtype":str(src.dtypes[0]),"nodata":src.nodata}

def read_las(path: str) -> dict:
    import laspy
    las=laspy.read(path)
    h=las.header
    return {"format":"LAS/LAZ","point_count":int(h.point_count),"version":str(h.version),
            "mins":[float(v) for v in h.mins],"maxs":[float(v) for v in h.maxs],
            "scales":[float(v) for v in h.scales]}

def read_segy(path: str) -> dict:
    from obspy import read
    st=read(path,format="SEGY",headonly=True)
    return {"format":"SEG-Y","trace_count":len(st),"sampling_rate_hz":float(st[0].stats.sampling_rate) if st else None,
            "npts":int(st[0].stats.npts) if st else 0}

READERS={".tif":read_geotiff,".tiff":read_geotiff,".las":read_las,".laz":read_las,".sgy":read_segy,".segy":read_segy}

def inspect_dataset(path: str) -> dict:
    suffix=Path(path).suffix.lower()
    if suffix not in READERS: raise ValueError(f"Unsupported scientific format: {suffix}")
    return READERS[suffix](path)
