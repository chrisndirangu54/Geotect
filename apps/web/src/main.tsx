import React,{useEffect,useState} from "react";
import {createRoot} from "react-dom/client";
import {Activity,Box,Database,Layers3,Mountain,Radio,ShieldAlert,Waves} from "lucide-react";
import Workspace3D from "./Workspace3D";
import DemUpload,{type DemMesh} from "./DemUpload";
import type {ScenePayload} from "./types";
import "./styles.css";

const API=import.meta.env.VITE_API_URL||"http://localhost:8000";

function App(){
 const [scene,setScene]=useState<ScenePayload|null>(null);const [demMesh,setDemMesh]=useState<DemMesh|null>(null);
 const [status,setStatus]=useState("connecting");const [slope,setSlope]=useState(32);const [rain,setRain]=useState(80);const [risk,setRisk]=useState<any>(null);
 const [layer,setLayer]=useState("All layers");

 useEffect(()=>{Promise.all([fetch(`${API}/health`).then(r=>r.json()),fetch(`${API}/api/v1/workspace/demo`).then(r=>r.json())]).then(([,s])=>{setScene(s);setStatus("online")}).catch(()=>setStatus("offline"))},[]);
 async function run(){const r=await fetch(`${API}/api/v1/risk/slope`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({slope_deg:slope,friction_angle_deg:28,cohesion_kpa:8,unit_weight_kn_m3:18,failure_depth_m:3,saturation:.7,rainfall_24h_mm:rain})});setRisk(await r.json())}

 return <div className="shell">
  <aside><div className="brand"><div className="mark">G</div><div><b>GeoTect</b><span>Earth Intelligence CAD</span></div></div>
   <nav><a className="active"><Box/>3D CAD</a><a><Mountain/>Terrain / DEM</a><a><Layers3/>Geology</a><a><Waves/>Geophysics</a><a><Radio/>IoT Sensors</a><a><Database/>Data Twin</a><a><ShieldAlert/>Simulation & Risk</a></nav>
   <div className="status"><span className={status}/>{status.toUpperCase()} DIGITAL TWIN</div></aside>
  <main><header><div><small>GEOTECT / DEMO DIGITAL TWIN</small><h1>3D Geotechnical CAD Workspace</h1></div>
   <div className="headerActions"><DemUpload api={API} onMesh={setDemMesh}/><select value={layer} onChange={e=>setLayer(e.target.value)}><option>All layers</option><option>Measured only</option><option>Geophysics</option><option>Infrastructure</option></select><button onClick={run}>Run risk screen</button></div></header>
   <section className="metrics"><Card label="Terrain slope" value={`${slope}°`} note="DEM-derived input"/><Card label="24h rainfall" value={`${rain} mm`} note="Climate input"/><Card label="Factor of safety" value={risk?.factor_of_safety_screening??"—"} note="Screening model"/><Card label="Risk state" value={risk?.risk_band?.toUpperCase()??"UNSET"} note={risk?`score ${risk.risk_score}`:"Run model"}/></section>
   <section className="workspace"><Workspace3D scene={scene} demMesh={demMesh}/><div className="panel">
    <h3>Live model controls</h3><label>Slope <strong>{slope}°</strong><input type="range" min="1" max="60" value={slope} onChange={e=>setSlope(+e.target.value)}/></label><label>Rainfall (24h) <strong>{rain} mm</strong><input type="range" min="0" max="250" value={rain} onChange={e=>setRain(+e.target.value)}/></label><button onClick={run}>Evaluate slope</button>
    {risk&&<div className="result"><span>Risk</span><b>{risk.risk_band}</b><p>FoS {risk.factor_of_safety_screening} · score {risk.risk_score}</p></div>}
    {demMesh&&<div className="result"><span>Terrain mesh</span><b>{demMesh.vertices.length.toLocaleString()} vertices</b><p>{demMesh.min_elevation_m?.toFixed(1)}–{demMesh.max_elevation_m?.toFixed(1)} m</p></div>}
    <h3>Spatial layers</h3><div className="layerList">{scene&&<><p><i/>Boreholes <b>{scene.boreholes.length}</b></p><p><i/>Sensors <b>{scene.sensors.length}</b></p><p><i/>Geophysical/geology bodies <b>{scene.bodies.length}</b></p><p><i/>Infrastructure <b>{scene.infrastructure.length}</b></p></>}</div>
    <div className="scientificNote"><Activity/><p><b>Uncertainty-aware.</b> Measured, interpreted and predicted geometry remain separate data states.</p></div>
   </div></section>
  </main></div>
}
function Card({label,value,note}:{label:string,value:any,note:string}){return <div className="card"><span>{label}</span><b>{value}</b><small>{note}</small></div>}
createRoot(document.getElementById("root")!).render(<App/>);
