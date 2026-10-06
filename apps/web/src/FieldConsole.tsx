import {useEffect,useState} from "react";
import {MapPin,Mic,Camera,PackageSearch,RadioTower,RefreshCw,X} from "lucide-react";
import {adminFetch} from "./adminApi";

type OfflineItem={id:string;path:string;body:any;created_at:string};
const KEY="geotect_field_queue";
function loadQueue():OfflineItem[]{try{return JSON.parse(localStorage.getItem(KEY)||"[]")}catch{return []}}
function saveQueue(q:OfflineItem[]){localStorage.setItem(KEY,JSON.stringify(q))}
export default function FieldConsole({api,onClose}:{api:string;onClose:()=>void}){
 const [queue,setQueue]=useState<OfflineItem[]>(loadQueue());const [status,setStatus]=useState(navigator.onLine?"online":"offline");
 const [orgId,setOrgId]=useState("");const [projectId,setProjectId]=useState("");const [note,setNote]=useState("");const [out,setOut]=useState<any>(null);const [position,setPosition]=useState<any>(null);
 useEffect(()=>{const on=()=>setStatus(navigator.onLine?"online":"offline");addEventListener("online",on);addEventListener("offline",on);return()=>{removeEventListener("online",on);removeEventListener("offline",on)}},[]);
 async function submit(path:string,body:any){if(!navigator.onLine){const item={id:crypto.randomUUID(),path,body,created_at:new Date().toISOString()};const q=[...queue,item];setQueue(q);saveQueue(q);setOut({queued_offline:true,id:item.id});return}
  setOut(await adminFetch(api,path,{method:"POST",body:JSON.stringify(body)}))}
 async function flush(){if(!navigator.onLine)return;const remain:OfflineItem[]=[];for(const item of queue){try{await adminFetch(api,item.path,{method:"POST",body:JSON.stringify(item.body)})}catch{remain.push(item)}}setQueue(remain);saveQueue(remain)}
 function geo(){navigator.geolocation?.getCurrentPosition(p=>{const g={type:"Point",coordinates:[p.coords.longitude,p.coords.latitude],accuracy_m:p.coords.accuracy};setPosition(g);setOut(g)})}
 function voice(){const W:any=window as any;const SR=W.SpeechRecognition||W.webkitSpeechRecognition;if(!SR){setOut({error:"Speech recognition is not available in this browser"});return}const rec=new SR();rec.lang="en-US";rec.interimResults=false;rec.onresult=(e:any)=>setNote((n:string)=>(n+" "+e.results[0][0].transcript).trim());rec.onerror=(e:any)=>setOut({speech_error:e.error});rec.start()}
 async function bluetooth(){try{const nav:any=navigator;const device=await nav.bluetooth.requestDevice({acceptAllDevices:true,optionalServices:[]});setOut({bluetooth_device:device.name||device.id})}catch(e:any){setOut({bluetooth_error:e.message})}}
 return <div className="fieldOverlay"><div className="fieldWindow"><button className="fieldClose" onClick={onClose}><X/></button>
  <header><div><small>GEOTECT FIELD</small><h2>Offline Field Console</h2><p>{status.toUpperCase()} · {queue.length} queued records</p></div><button onClick={flush}><RefreshCw/>Sync</button></header>
  <div className="fieldGrid">
   <section><h3>Project context</h3><input placeholder="Organization ID" value={orgId} onChange={e=>setOrgId(e.target.value)}/><input placeholder="Project ID" value={projectId} onChange={e=>setProjectId(e.target.value)}/>
    <textarea placeholder="Field observation / voice transcript" value={note} onChange={e=>setNote(e.target.value)}/>
    <div className="fieldButtons"><button onClick={geo}><MapPin/>GNSS</button><button onClick={voice}><Mic/>Voice</button><button onClick={bluetooth}><RadioTower/>Bluetooth</button><button onClick={()=>submit("/api/v1/operations/field/logs",{org_id:orgId,project_id:projectId,log_type:"observation",content:{note},geometry:position||{}})}>Save log</button></div>
   </section>
   <section><h3>Sample chain of custody</h3><button onClick={()=>submit("/api/v1/operations/samples",{org_id:orgId,project_id:projectId,sample_type:"soil",metadata:{note},location:position||{}})}><PackageSearch/>Create sample + QR/RFID</button>
    <h3>Instrument calibration</h3><button onClick={()=>submit("/api/v1/operations/instruments/calibration",{org_id:orgId,instrument_id:"FIELD-001",instrument_type:"generic",calibrated_at:new Date().toISOString(),calibration_data:{field_check:true}})}><RadioTower/>Record field check</button>
    <h3>Media</h3><label className="uploadButton"><Camera/>Attach photo/video<input type="file" accept="image/*,video/*" capture="environment" onChange={e=>setOut({selected_media:e.target.files?.[0]?.name})}/></label>
   </section>
  </div>{out&&<pre>{JSON.stringify(out,null,2)}</pre>}</div></div>
}
