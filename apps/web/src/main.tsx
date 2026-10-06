import React,{useCallback,useEffect,useMemo,useState} from "react";
import {createRoot} from "react-dom/client";
import {Activity,Box,Database,Layers3,Mountain,Radio,ShieldAlert,Waves} from "lucide-react";
import Workspace3D from "./Workspace3D";
import DemUpload,{type DemMesh} from "./DemUpload";
import CadToolbar,{type CadMode} from "./CadToolbar";
import SectionView from "./SectionView";
import FeatureInspector from "./FeatureInspector";
import ComputePanel from "./ComputePanel";
import {useHistory} from "./useHistory";
import type {CadFeature,ScenePayload} from "./types";
import "./styles.css";

const API=import.meta.env.VITE_API_URL||"http://localhost:8000";

function App(){
 const [scene,setScene]=useState<ScenePayload|null>(null);const [demMesh,setDemMesh]=useState<DemMesh|null>(null);
 const [status,setStatus]=useState("connecting");const [slope,setSlope]=useState(32);const [rain,setRain]=useState(80);const [risk,setRisk]=useState<any>(null);
 const [layer,setLayer]=useState("All layers");const [mode,setMode]=useState<CadMode>("select");const [clipping,setClipping]=useState(false);
 const features=useHistory<CadFeature[]>([]);const [projectId,setProjectId]=useState<string|null>(()=>localStorage.getItem("geotect_project_id"));const [saveState,setSaveState]=useState("Unsaved");
 const [section,setSection]=useState<any>(null);const [correlations,setCorrelations]=useState<any>(null);const [selectedId,setSelectedId]=useState<string|null>(null);
 const selectedFeature=useMemo(()=>features.value.find(f=>f.id===selectedId)||null,[features.value,selectedId]);

 useEffect(()=>{(async()=>{try{
   const demo=await fetch(`${API}/api/v1/workspace/demo`).then(r=>r.json());
   if(projectId){const r=await fetch(`${API}/api/v1/cad/projects/${projectId}`);if(r.ok){const p=await r.json();const restored=p.scene as ScenePayload;setScene(restored);features.set(restored.cad_features||[]);setSaveState(`Restored v${p.version}`)}else{setScene(demo);features.set(demo.cad_features||[])}}
   else{setScene(demo);features.set(demo.cad_features||[])}
   setStatus("online");
 }catch{setStatus("offline")}})()},[]);

 const addFeature=useCallback((f:CadFeature)=>{features.set(current=>[...current,f]);setSelectedId(f.id);setSaveState("Modified");if(f.kind==="section"&&scene){fetch(`${API}/api/v1/cad/sections/fence`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({line:f.positions,boreholes:scene.boreholes})}).then(r=>r.json()).then(setSection)}},[scene,features.set]);
 const updateFeature=useCallback((f:CadFeature)=>{features.set(current=>current.map(x=>x.id===f.id?f:x));setSaveState("Modified")},[features.set]);
 const deleteFeature=useCallback((id:string)=>{features.set(current=>current.filter(x=>x.id!==id));setSelectedId(null);setSaveState("Modified")},[features.set]);

 async function run(){const r=await fetch(`${API}/api/v1/risk/slope`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({slope_deg:slope,friction_angle_deg:28,cohesion_kpa:8,unit_weight_kn_m3:18,failure_depth_m:3,saturation:.7,rainfall_24h_mm:rain})});setRisk(await r.json())}
 async function save(){
  if(!scene)return;setSaveState("Saving…");const snapshot={...scene,cad_features:features.value};
  try{
   if(!projectId){const r=await fetch(`${API}/api/v1/cad/projects`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:"GeoTect Engineering Project",crs:scene.crs,scene:snapshot})});const p=await r.json();setProjectId(p.id);localStorage.setItem("geotect_project_id",p.id);setSaveState(`Saved v${p.version}`)}
   else{const r=await fetch(`${API}/api/v1/cad/projects/${projectId}/versions`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({scene:snapshot,message:`CAD version ${new Date().toISOString()}`})});const p=await r.json();setSaveState(`Saved v${p.version}`)}
  }catch{setSaveState("Save failed")}
 }
 async function correlate(){if(!scene)return;const r=await fetch(`${API}/api/v1/cad/boreholes/correlate`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({boreholes:scene.boreholes})});setCorrelations(await r.json())}

 return <div className="shell">
  <aside><div className="brand"><div className="mark">G</div><div><b>GeoTect</b><span>Earth Intelligence CAD</span></div></div>
   <nav><a className="active"><Box/>3D CAD</a><a><Mountain/>Terrain / DEM</a><a><Layers3/>Geology</a><a><Waves/>Geophysics</a><a><Radio/>IoT Sensors</a><a><Database/>Data Twin</a><a><ShieldAlert/>Simulation & Risk</a></nav>
   <div className="status"><span className={status}/>{status.toUpperCase()} · {saveState}</div></aside>
  <main><header><div><small>GEOTECT / COMPUTATIONAL DIGITAL TWIN</small><h1>3D Geotechnical CAD Workspace</h1></div>
   <div className="headerActions"><DemUpload api={API} onMesh={setDemMesh}/><select value={layer} onChange={e=>setLayer(e.target.value)}><option>All layers</option><option>Measured only</option><option>Geophysics</option><option>Infrastructure</option></select><button onClick={()=>setClipping(v=>!v)}>{clipping?"Disable":"Enable"} clip</button><button onClick={correlate}>Correlate BH</button><button onClick={run}>Run risk</button></div></header>
   <CadToolbar mode={mode} setMode={setMode} undo={features.undo} redo={features.redo} canUndo={features.canUndo} canRedo={features.canRedo} onSave={save}/>
   <section className="metrics"><Card label="CAD features" value={features.value.length} note="authored geometry"/><Card label="24h rainfall" value={`${rain} mm`} note="climate input"/><Card label="Factor of safety" value={risk?.factor_of_safety_screening??"—"} note="screening model"/><Card label="Risk state" value={risk?.risk_band?.toUpperCase()??"UNSET"} note={risk?`score ${risk.risk_score}`:"Run model"}/></section>
   <section className="workspace"><Workspace3D scene={scene} demMesh={demMesh} features={features.value} mode={mode} onAddFeature={addFeature} clipping={clipping} onSelectFeatureId={setSelectedId}/><div className="panel">
    <h3>Live model controls</h3><label>Slope <strong>{slope}°</strong><input type="range" min="1" max="60" value={slope} onChange={e=>setSlope(+e.target.value)}/></label><label>Rainfall (24h) <strong>{rain} mm</strong><input type="range" min="0" max="250" value={rain} onChange={e=>setRain(+e.target.value)}/></label><button onClick={run}>Evaluate slope</button>
    {risk&&<div className="result"><span>Risk</span><b>{risk.risk_band}</b><p>FoS {risk.factor_of_safety_screening} · score {risk.risk_score}</p></div>}
    {demMesh&&<div className="result"><span>Terrain mesh</span><b>{demMesh.vertices.length.toLocaleString()} vertices</b><p>{demMesh.min_elevation_m?.toFixed(1)}–{demMesh.max_elevation_m?.toFixed(1)} m</p></div>}
    {correlations&&<div className="result"><span>Borehole correlation</span><b>{correlations.correlations.length} suggested ties</b><p>Human verification required</p></div>}
    <h3>Feature inspector</h3><FeatureInspector feature={selectedFeature} onUpdate={updateFeature} onDelete={deleteFeature}/>
    <h3>Spatial layers</h3><div className="layerList">{scene&&<><p><i/>Boreholes <b>{scene.boreholes.length}</b></p><p><i/>Sensors <b>{scene.sensors.length}</b></p><p><i/>Bodies <b>{scene.bodies.length}</b></p><p><i/>Authored CAD <b>{features.value.length}</b></p></>}</div>
    <div className="scientificNote"><Activity/><p><b>CAD is computational.</b> New features retain 3D coordinates and enter versioned project state; sections and correlations derive from the same objects.</p></div>
   </div></section>
   <SectionView data={section}/>
   <ComputePanel api={API}/>
  </main></div>
}
function Card({label,value,note}:{label:string,value:any,note:string}){return <div className="card"><span>{label}</span><b>{value}</b><small>{note}</small></div>}
createRoot(document.getElementById("root")!).render(<App/>);
