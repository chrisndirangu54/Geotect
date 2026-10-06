import type {CadFeature,ConfidenceState} from "./types";
export default function FeatureInspector({feature,onUpdate,onDelete}:{feature:CadFeature|null;onUpdate:(f:CadFeature)=>void;onDelete:(id:string)=>void}){
 if(!feature)return <div className="inspectorEmpty">Select an authored CAD object to edit it.</div>;
 const set=(patch:Partial<CadFeature>)=>onUpdate({...feature,...patch});
 const props=(patch:Record<string,any>)=>onUpdate({...feature,properties:{...feature.properties,...patch}});
 return <div className="featureInspector">
  <div className="inspectorTitle"><b>{feature.kind.toUpperCase()}</b><span>{feature.id.slice(0,18)}…</span></div>
  <label>Name<input value={feature.name} onChange={e=>set({name:e.target.value})}/></label>
  <label>Data state<select value={feature.state} onChange={e=>set({state:e.target.value as ConfidenceState})}><option value="measured">Measured</option><option value="interpreted">Interpreted</option><option value="predicted">Predicted</option></select></label>
  <label>Confidence <strong>{Math.round(feature.confidence*100)}%</strong><input type="range" min="0" max="1" step=".01" value={feature.confidence} onChange={e=>set({confidence:+e.target.value})}/></label>
  {feature.geometry==="polygon"&&<label>Extrusion base (m)<input type="number" value={Number(feature.properties.extruded_to_m??0)} onChange={e=>props({extruded_to_m:+e.target.value})}/></label>}
  <div className="elevationButtons"><button onClick={()=>set({positions:feature.positions.map(p=>({...p,elevation_m:p.elevation_m+1}))})}>+1 m Z</button><button onClick={()=>set({positions:feature.positions.map(p=>({...p,elevation_m:p.elevation_m-1}))})}>−1 m Z</button></div>
  <p>{feature.positions.length} vertices · {feature.geometry}</p>
  <button className="dangerButton" onClick={()=>onDelete(feature.id)}>Delete feature</button>
 </div>
}
