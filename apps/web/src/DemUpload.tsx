import {useState} from "react";

export type DemMesh={vertices:number[][];indices:number[];min_elevation_m:number|null;max_elevation_m:number|null;representation:string};

export default function DemUpload({api,onMesh}:{api:string;onMesh:(mesh:DemMesh)=>void}){
 const [name,setName]=useState("No DEM loaded");const [busy,setBusy]=useState(false);
 async function upload(file:File){
   setBusy(true);setName(file.name);
   const body=new FormData();body.append("file",file);
   try{
    const r=await fetch(`${api}/api/v1/datasets/geotiff/mesh`,{method:"POST",body});
    if(!r.ok) throw new Error(await r.text());
    onMesh(await r.json());
   }catch(e){setName(`DEM error: ${String(e)}`)}finally{setBusy(false)}
 }
 return <label className="uploadButton">{busy?"Meshing DEM…":"Load GeoTIFF DEM"}
   <input type="file" accept=".tif,.tiff" onChange={e=>e.target.files?.[0]&&upload(e.target.files[0])}/>
   <small>{name}</small>
 </label>
}
