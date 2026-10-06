import {useState} from "react";
export default function ComputePanel({api}:{api:string}){
 const [output,setOutput]=useState<any>(null);const [busy,setBusy]=useState("");
 async function post(path:string,payload:any,label:string){setBusy(label);try{const r=await fetch(api+path,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});setOutput(await r.json())}finally{setBusy("")}}
 async function tile(file:File){setBusy("LAS tiling");try{const body=new FormData();body.append("file",file);const r=await fetch(api+"/api/v1/datasets/las/tiles",{method:"POST",body});if(!r.ok)throw new Error(await r.text());const blob=await r.blob();const url=URL.createObjectURL(blob);const a=document.createElement("a");a.href=url;a.download="geotect-las-tiles.zip";a.click();URL.revokeObjectURL(url);setOutput({status:"LAS/LAZ tiled",download:"geotect-las-tiles.zip"})}catch(e){setOutput({error:String(e)})}finally{setBusy("")}}
 return <section className="computePanel"><div className="sectionHeader"><b>Computational Geoscience</b><span>{busy||"Ready"}</span></div>
  <div className="computeButtons">
   <button onClick={()=>post("/api/v1/geophysics/ert/invert",{sensitivity:[[1,0,0],[0,1,0],[0,0,1],[.5,.5,0],[0,.5,.5]],apparent_resistivity:[80,140,260,105,190],regularization:.4,iterations:6},"ERT inversion")}>Run ERT inversion</button>
   <button onClick={()=>post("/api/v1/geophysics/seismic/reconstruct",{traces:[{x:0,y:0,dt_s:.002,samples:[0,.2,1,.1,0]},{x:20,y:0,dt_s:.002,samples:[0,.1,.7,.3,0]},{x:0,y:20,dt_s:.002,samples:[0,.3,.8,.1,0]},{x:20,y:20,dt_s:.002,samples:[0,.2,.9,.2,0]}],nx:8,ny:8,velocity_m_s:1800},"Seismic reconstruction")}>Reconstruct seismic</button>
   <button onClick={()=>post("/api/v1/groundwater/pde",{nx:24,ny:14,dx_m:5,dy_m:5,k:0.00001,left_head_m:100,right_head_m:88},"Groundwater PDE")}>Solve groundwater PDE</button>
   <button onClick={()=>post("/api/v1/simulation/fem/elastic",{width_m:60,height_m:30,nx:18,ny:10,young_pa:5e8,poisson:.3,density_kg_m3:1900,top_pressure_pa:30000},"FEM")}>Run elastic FEM</button>
   <label className="uploadButton">Tile LAS/LAZ<input type="file" accept=".las,.laz" onChange={e=>e.target.files?.[0]&&tile(e.target.files[0])}/></label>
  </div>
  {output&&<pre className="computeOutput">{JSON.stringify(output,null,2).slice(0,12000)}</pre>}
 </section>
}
