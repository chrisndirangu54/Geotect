import {useEffect,useMemo,useState} from "react";
import {BrainCircuit,Building2,ShieldAlert,Pickaxe,HardHat,Route,Leaf,Activity,Microscope,Plug,Play,Clock3,Save,ChevronRight,X} from "lucide-react";
import {adminFetch} from "./adminApi";
import {configured,loginGoogle,watchAuth} from "./firebase";

type Tab="copilot"|"design"|"investigation"|"modules"|"timeline"|"jobs"|"plugins";
const moduleIcons:any={tailings_dam:ShieldAlert,highway_cut:Route,building_foundation:Building2,open_pit:Pickaxe,underground_mine:Pickaxe,tunnel:HardHat,corridor:Route,esg:Leaf,emergency:ShieldAlert};

export default function PlatformHub({api,onClose}:{api:string;onClose:()=>void}){
 const [user,setUser]=useState<any>(null);const [tab,setTab]=useState<Tab>("copilot");const [orgs,setOrgs]=useState<any[]>([]);const [orgId,setOrgId]=useState("");const [error,setError]=useState("");
 useEffect(()=>watchAuth(setUser),[]);
 useEffect(()=>{if(user)adminFetch(api,"/api/v1/platform/organizations").then((x:any[])=>{setOrgs(x);if(x[0])setOrgId(x[0].id)}).catch(e=>setError(e.message))},[user,api]);
 async function createOrg(){const x=await adminFetch(api,"/api/v1/platform/organizations",{method:"POST",body:JSON.stringify({name:"GeoTect Workspace",plan:"pro"})});setOrgs([...orgs,x]);setOrgId(x.id)}
 if(!configured)return <Shell onClose={onClose}><Gate title="Firebase required" body="Configure Firebase to use authenticated platform capabilities."/></Shell>;
 if(!user)return <Shell onClose={onClose}><Gate title="Sign in to GeoTect Platform" body="Platform workflows, compute jobs and enterprise data are authenticated."><button onClick={()=>loginGoogle().catch(e=>setError(e.message))}>Sign in with Google</button>{error&&<em>{error}</em>}</Gate></Shell>;
 return <Shell onClose={onClose}>
  <div className="platformLayout">
   <aside className="platformNav">
    <div className="platformBrand"><Activity/><div><b>GeoTect Platform</b><small>Ground Engineering OS</small></div></div>
    {([["copilot",BrainCircuit,"AI CAD Copilot"],["design",HardHat,"Design Lab"],["investigation",Microscope,"Investigation"],["modules",Building2,"Domain Modules"],["timeline",Clock3,"4D Twin"],["jobs",Play,"Compute Jobs"],["plugins",Plug,"Plugins"]] as any[]).map(([id,I,l])=><button key={id} className={tab===id?"activePlatformTab":""} onClick={()=>setTab(id)}><I/>{l}</button>)}
    <div className="orgPicker"><span>Organization</span>{orgs.length?<select value={orgId} onChange={e=>setOrgId(e.target.value)}>{orgs.map(o=><option key={o.id} value={o.id}>{o.name}</option>)}</select>:<button onClick={createOrg}>Create workspace</button>}</div>
   </aside>
   <main className="platformContent">
    {tab==="copilot"&&<Copilot api={api}/>}
    {tab==="design"&&<DesignLab api={api}/>}
    {tab==="investigation"&&<Investigation api={api}/>}
    {tab==="modules"&&<Modules api={api}/>}
    {tab==="timeline"&&<Timeline api={api} orgId={orgId}/>}
    {tab==="jobs"&&<Jobs api={api} orgId={orgId}/>}
    {tab==="plugins"&&<Plugins api={api}/>}
   </main>
  </div>
 </Shell>
}

function Copilot({api}:{api:string}){const [text,setText]=useState("draw a tunnel 40 m below terrain following the selected alignment");const [out,setOut]=useState<any>(null);
 async function run(){setOut(await adminFetch(api,"/api/v1/platform/copilot/command",{method:"POST",body:JSON.stringify({text})}))}
 return <Panel title="AI CAD Copilot" sub="Natural-language commands are converted into permission-gated engineering actions."><textarea className="platformPrompt" value={text} onChange={e=>setText(e.target.value)}/><button onClick={run}><BrainCircuit/>Plan command</button><Json x={out}/></Panel>}

function DesignLab({api}:{api:string}){const [tool,setTool]=useState("bearing_capacity");const [out,setOut]=useState<any>(null);const defaults:any={bearing_capacity:{width_m:2,depth_m:1,gamma_kn_m3:18,cohesion_kpa:5,friction_deg:30},settlement:{load_kpa:150,width_m:2,young_mpa:25,poisson:.3},retaining_wall:{height_m:5,gamma_kn_m3:18,friction_deg:30,surcharge_kpa:10},pile_capacity:{diameter_m:.6,length_m:15,unit_shaft_kpa:35,unit_base_kpa:1500},liquefaction:{csr:.18,crr:.24,msf:1}};const [raw,setRaw]=useState(JSON.stringify(defaults[tool],null,2));
 useEffect(()=>setRaw(JSON.stringify(defaults[tool],null,2)),[tool]);
 async function run(){setOut(await adminFetch(api,"/api/v1/platform/design/"+tool,{method:"POST",body:JSON.stringify(JSON.parse(raw))}))}
 return <Panel title="Engineering Design Lab" sub="Transparent screening calculations with method metadata."><select value={tool} onChange={e=>setTool(e.target.value)}>{Object.keys(defaults).map(x=><option key={x}>{x}</option>)}</select><textarea className="platformCode" value={raw} onChange={e=>setRaw(e.target.value)}/><button onClick={run}><Play/>Run calculation</button><Json x={out}/></Panel>}

function Investigation({api}:{api:string}){const [out,setOut]=useState<any>(null);
 const payload={candidates:[{x:0,y:0,uncertainty:.9,importance:1.2},{x:120,y:80,uncertainty:.8,importance:1},{x:240,y:20,uncertainty:.95,importance:1.1},{x:70,y:220,uncertainty:.7,importance:1}],observations:[{x:20,y:20},{x:180,y:50}],count:3,min_spacing_m:50};
 return <Panel title="Autonomous Site Investigation" sub="Ranks the next boreholes, CPTs, ERT lines or sensors using uncertainty and information gain."><button onClick={async()=>setOut(await adminFetch(api,"/api/v1/platform/investigation/recommend",{method:"POST",body:JSON.stringify(payload)}))}><Microscope/>Optimize locations</button><Json x={out}/></Panel>}

function Modules({api}:{api:string}){const [mods,setMods]=useState<any>({});
 useEffect(()=>{adminFetch(api,"/api/v1/platform/templates").then(setMods)},[api]);
 return <Panel title="Domain Modules" sub="Preconfigured layers, risks and workflows for major ground-engineering sectors."><div className="moduleGrid">{Object.entries(mods).map(([k,v]:any)=>{const I=moduleIcons[k]||Building2;return <div className="moduleCard" key={k}><I/><b>{k.replaceAll("_"," ")}</b><small>{(v.layers||[]).slice(0,5).join(" · ")}</small><p>{(v.risks||[]).join(", ")}</p></div>})}</div></Panel>}

function Timeline({api,orgId}:{api:string;orgId:string}){const [events,setEvents]=useState<any[]>([]);const [cursor,setCursor]=useState(100);
 useEffect(()=>{if(orgId)adminFetch(api,`/api/v1/platform/events?org_id=${encodeURIComponent(orgId)}`).then(setEvents)},[api,orgId]);
 const visible=useMemo(()=>events.slice().reverse().slice(0,Math.max(1,Math.ceil(events.length*cursor/100))),[events,cursor]);
 return <Panel title="4D Digital Twin" sub="Replay engineering events, alarms, construction stages and monitoring history."><input type="range" min="1" max="100" value={cursor} onChange={e=>setCursor(+e.target.value)}/><div className="timelineList">{visible.map(e=><div key={e.id}><i className={e.severity}/><div><b>{e.event_type}</b><small>{e.created_at}</small><p>{JSON.stringify(e.payload)}</p></div></div>)}{!events.length&&<span className="emptyState">No timeline events recorded yet.</span>}</div></Panel>}

function Jobs({api,orgId}:{api:string;orgId:string}){const [jobs,setJobs]=useState<any[]>([]);const [kind,setKind]=useState("monte_carlo_slope");
 async function load(){if(orgId)setJobs(await adminFetch(api,`/api/v1/platform/jobs?org_id=${encodeURIComponent(orgId)}`))}
 useEffect(()=>{load()},[orgId]);async function queue(){const inputs:any={monte_carlo_slope:{samples:5000,slope_deg:35,friction_mean:28,friction_sd:2,cohesion_mean_kpa:5,cohesion_sd_kpa:1},groundwater_pde:{nx:30,ny:20,dx_m:5,dy_m:5,k:.00001,left_head_m:100,right_head_m:90}};await adminFetch(api,"/api/v1/platform/jobs",{method:"POST",body:JSON.stringify({org_id:orgId,job_type:kind,input:inputs[kind]||{}})});load()}
 return <Panel title="Remote Compute Jobs" sub="Queue numerical analyses for background CPU/GPU workers."><div className="inlineControls"><select value={kind} onChange={e=>setKind(e.target.value)}><option>monte_carlo_slope</option><option>groundwater_pde</option><option>ert_inversion</option><option>seismic_reconstruction</option></select><button disabled={!orgId} onClick={queue}><Play/>Queue</button><button onClick={load}>Refresh</button></div><div className="jobRows">{jobs.map(j=><div key={j.id}><b>{j.job_type}</b><span>{j.status}</span><progress max="1" value={j.progress}/></div>)}</div></Panel>}

function Plugins({api}:{api:string}){const [rows,setRows]=useState<any[]>([]);useEffect(()=>{adminFetch(api,"/api/v1/platform/plugins").then(setRows)},[api]);
 return <Panel title="Plugin SDK Registry" sub="Register external solvers, instruments, processing services and regional extensions."><div className="moduleGrid">{rows.map(r=><div className="moduleCard" key={r.id}><Plug/><b>{r.name}</b><small>{r.category} · v{r.version}</small><p>{r.capabilities.join(", ")}</p></div>)}{!rows.length&&<span className="emptyState">No external plugins registered yet. Super admins can register them through the platform API.</span>}</div></Panel>}

function Panel({title,sub,children}:{title:string;sub:string;children:any}){return <section className="platformPanel"><header><div><small>GEOTECT PLATFORM</small><h2>{title}</h2><p>{sub}</p></div></header>{children}</section>}
function Json({x}:{x:any}){return x?<pre className="platformOutput">{JSON.stringify(x,null,2)}</pre>:null}
function Gate({title,body,children}:{title:string;body:string;children?:any}){return <div className="platformGate"><Activity/><h2>{title}</h2><p>{body}</p>{children}</div>}
function Shell({children,onClose}:{children:any;onClose:()=>void}){return <div className="platformOverlay"><div className="platformWindow"><button className="platformClose" onClick={onClose}><X/></button>{children}</div></div>}
