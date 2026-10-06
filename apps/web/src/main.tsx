import React, {useEffect, useState} from "react";
import {createRoot} from "react-dom/client";
import {Activity, Layers3, Mountain, Radio, ShieldAlert, Waves} from "lucide-react";
import "./styles.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

type Capability = {terrain:string[];geophysics:string[];geotechnical:string[];iot:string[];risk:string[]};

function App(){
  const [cap,setCap]=useState<Capability|null>(null);
  const [status,setStatus]=useState("connecting");
  const [slope,setSlope]=useState(32);
  const [rain,setRain]=useState(80);
  const [risk,setRisk]=useState<any>(null);

  useEffect(()=>{fetch(`${API}/api/v1/capabilities`).then(r=>r.json()).then(x=>{setCap(x);setStatus("online")}).catch(()=>setStatus("offline"))},[]);

  async function run(){
    const r=await fetch(`${API}/api/v1/risk/slope`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({
      slope_deg:slope,friction_angle_deg:28,cohesion_kpa:8,unit_weight_kn_m3:18,failure_depth_m:3,saturation:.7,rainfall_24h_mm:rain
    })});
    setRisk(await r.json());
  }

  return <div className="shell">
    <aside>
      <div className="brand"><div className="mark">G</div><div><b>GeoTect</b><span>Earth Intelligence</span></div></div>
      <nav>
        <a className="active"><Mountain/>Digital Twin</a><a><Layers3/>Subsurface</a><a><Waves/>Geophysics</a><a><Radio/>Sensors</a><a><ShieldAlert/>Risk</a>
      </nav>
      <div className="status"><span className={status}/>{status.toUpperCase()} API</div>
    </aside>
    <main>
      <header><div><small>PROJECT / DEMO SITE</small><h1>Engineering Digital Twin</h1></div><button onClick={run}>Recalculate risk</button></header>
      <section className="metrics">
        <Card label="Terrain slope" value={`${slope}°`} note="DEM-derived"/>
        <Card label="24h rainfall" value={`${rain} mm`} note="Climate input"/>
        <Card label="Factor of safety" value={risk?.factor_of_safety_screening ?? "—"} note="Screening model"/>
        <Card label="Risk state" value={risk?.risk_band?.toUpperCase() ?? "UNSET"} note={risk ? `score ${risk.risk_score}` : "Run model"}/>
      </section>
      <section className="workspace">
        <div className="scene">
          <div className="sceneTop"><b>3D Site Workspace</b><span>Measured · Interpreted · Predicted</span></div>
          <div className="terrain">
            <div className="ridge r1"/><div className="ridge r2"/><div className="ridge r3"/>
            <div className="borehole b1"><i/><label>BH-01</label></div>
            <div className="borehole b2"><i/><label>BH-02</label></div>
            <div className="sensor s1"><Activity/><label>PZ-04</label></div>
          </div>
          <div className="legend"><span><i className="measured"/>Measured</span><span><i className="interpreted"/>Interpreted</span><span><i className="predicted"/>Predicted</span></div>
        </div>
        <div className="panel">
          <h3>Live screening controls</h3>
          <label>Slope <strong>{slope}°</strong><input type="range" min="1" max="60" value={slope} onChange={e=>setSlope(+e.target.value)}/></label>
          <label>Rainfall (24h) <strong>{rain} mm</strong><input type="range" min="0" max="250" value={rain} onChange={e=>setRain(+e.target.value)}/></label>
          <button onClick={run}>Evaluate slope</button>
          {risk && <div className="result"><span>Risk</span><b>{risk.risk_band}</b><p>FoS {risk.factor_of_safety_screening} · score {risk.risk_score}</p></div>}
          <h3>Connected domains</h3>
          <div className="chips">{cap && [...cap.geophysics,...cap.iot].slice(0,10).map(x=><span key={x}>{x}</span>)}</div>
        </div>
      </section>
    </main>
  </div>
}
function Card({label,value,note}:{label:string,value:any,note:string}){return <div className="card"><span>{label}</span><b>{value}</b><small>{note}</small></div>}
createRoot(document.getElementById("root")!).render(<App/>);
