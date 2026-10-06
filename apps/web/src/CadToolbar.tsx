import {MousePointer2,GitBranch,Layers3,CircleDot,Route,Box,TrainFront,Shovel,Slice, Ruler,Undo2,Redo2,Save} from "lucide-react";
import type {CadKind} from "./types";
export type CadMode="select"|CadKind;

const tools:{mode:CadMode;label:string;Icon:any}[]=[
 {mode:"select",label:"Select",Icon:MousePointer2},{mode:"fault",label:"Fault",Icon:GitBranch},
 {mode:"stratum",label:"Stratum",Icon:Layers3},{mode:"borehole",label:"Borehole",Icon:CircleDot},
 {mode:"road",label:"Road",Icon:Route},{mode:"foundation",label:"Foundation",Icon:Box},
 {mode:"tunnel",label:"Tunnel",Icon:TrainFront},{mode:"excavation",label:"Excavation",Icon:Shovel},
 {mode:"section",label:"Section",Icon:Slice},{mode:"measurement",label:"Measure",Icon:Ruler}
];
export default function CadToolbar({mode,setMode,undo,redo,canUndo,canRedo,onSave}:{mode:CadMode;setMode:(m:CadMode)=>void;undo:()=>void;redo:()=>void;canUndo:boolean;canRedo:boolean;onSave:()=>void}){
 return <div className="cadToolbar">
  {tools.map(({mode:m,label,Icon})=><button key={m} className={mode===m?"tool activeTool":"tool"} title={label} onClick={()=>setMode(m)}><Icon/><span>{label}</span></button>)}
  <div className="toolSep"/>
  <button className="tool" disabled={!canUndo} onClick={undo}><Undo2/><span>Undo</span></button>
  <button className="tool" disabled={!canRedo} onClick={redo}><Redo2/><span>Redo</span></button>
  <button className="tool" onClick={onSave}><Save/><span>Version</span></button>
 </div>
}
