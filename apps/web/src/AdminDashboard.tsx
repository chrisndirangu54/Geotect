import {useEffect,useMemo,useState} from "react";
import {KeyRound,Settings,BrainCircuit,Users,ShieldCheck,ScrollText,RefreshCw,Trash2,Save,LogIn,LogOut,Plug} from "lucide-react";
import {configured,loginGoogle,logout,watchAuth} from "./firebase";
import {adminFetch} from "./adminApi";

type Tab="overview"|"models"|"keys"|"settings"|"users"|"integrations"|"audit";
export default function AdminDashboard({api,onClose}:{api:string;onClose:()=>void}){
 const [authUser,setAuthUser]=useState<any>(null);const [me,setMe]=useState<any>(null);const [tab,setTab]=useState<Tab>("overview");
 const [data,setData]=useState<any>(null);const [error,setError]=useState("");const [busy,setBusy]=useState(false);

 useEffect(()=>watchAuth(u=>{setAuthUser(u);setMe(null);setData(null);if(u)adminFetch(api,"/api/v1/admin/me").then(setMe).catch(e=>setError(e.message))}),[api]);
 async function load(t:Tab=tab){setBusy(true);setError("");try{
   const path=t==="overview"?"/api/v1/admin/overview":t==="models"?"/api/v1/admin/models":t==="keys"?"/api/v1/admin/secrets":t==="settings"?"/api/v1/admin/settings":t==="users"?"/api/v1/admin/users":t==="integrations"?"/api/v1/integrations/catalog":"/api/v1/admin/audit?limit=100";
   setData(await adminFetch(api,path));
 }catch(e:any){setError(e.message)}finally{setBusy(false)}}
 useEffect(()=>{if(me?.role==="super_admin")load(tab)},[tab,me?.role]);

 if(!configured)return <AdminShell onClose={onClose}><div className="adminGate"><ShieldCheck/><h2>Admin configuration required</h2><p>Add the Firebase web variables from <code>.env.example</code> before the secure admin console can sign in.</p></div></AdminShell>;
 if(!authUser)return <AdminShell onClose={onClose}><div className="adminGate"><ShieldCheck/><h2>GeoTect Super Admin</h2><p>Sign in with the verified super-admin account to access security-sensitive controls.</p><button onClick={()=>loginGoogle().catch(e=>setError(e.message))}><LogIn/>Sign in with Google</button>{error&&<em>{error}</em>}</div></AdminShell>;
 if(!me)return <AdminShell onClose={onClose}><div className="adminGate"><RefreshCw className="spin"/><p>Verifying administrator privileges…</p>{error&&<em>{error}</em>}</div></AdminShell>;
 if(me.role!=="super_admin")return <AdminShell onClose={onClose}><div className="adminGate"><ShieldCheck/><h2>Access denied</h2><p>{me.email} is authenticated but does not have super-admin privileges.</p><button onClick={logout}><LogOut/>Sign out</button></div></AdminShell>;

 return <AdminShell onClose={onClose}>
  <div className="adminLayout">
   <aside className="adminNav">
    <div className="adminIdentity"><ShieldCheck/><div><b>Super Admin</b><small>{me.email}</small></div></div>
    {([["overview",ShieldCheck,"Overview"],["models",BrainCircuit,"Models"],["keys",KeyRound,"API Keys"],["settings",Settings,"Settings"],["users",Users,"Users & Roles"],["integrations",Plug,"Integrations"],["audit",ScrollText,"Audit Log"]] as any[]).map(([id,Icon,label])=><button key={id} className={tab===id?"activeAdminTab":""} onClick={()=>setTab(id)}><Icon/>{label}</button>)}
    <button className="adminSignout" onClick={logout}><LogOut/>Sign out</button>
   </aside>
   <section className="adminContent">
    <div className="adminContentHeader"><div><small>SECURE CONTROL PLANE</small><h2>{tab[0].toUpperCase()+tab.slice(1)}</h2></div><button onClick={()=>load()} disabled={busy}><RefreshCw className={busy?"spin":""}/>Refresh</button></div>
    {error&&<div className="adminError">{error}</div>}
    {busy&&data==null?<div className="adminLoading">Loading…</div>:<AdminTab api={api} tab={tab} data={data} refresh={()=>load()}/>}
   </section>
  </div>
 </AdminShell>
}

function AdminTab({api,tab,data,refresh}:{api:string;tab:Tab;data:any;refresh:()=>void}){
 if(tab==="overview")return <Overview data={data}/>;
 if(tab==="models")return <Models api={api} rows={data||[]} refresh={refresh}/>;
 if(tab==="keys")return <Secrets api={api} rows={data||[]} refresh={refresh}/>;
 if(tab==="settings")return <SettingsTab api={api} rows={data||[]} refresh={refresh}/>;
 if(tab==="users")return <UsersTab api={api} rows={data||[]} refresh={refresh}/>;
 if(tab==="integrations")return <IntegrationsTab api={api} catalog={data||{}}/>;
 return <Audit rows={data||[]}/>;
}
function Overview({data}:{data:any}){if(!data)return null;return <><div className="adminCards">{Object.entries(data.counts||{}).map(([k,v])=><div className="adminCard" key={k}><span>{k.replace(/_/g," ")}</span><b>{String(v)}</b></div>)}</div><div className="securityBox"><h3>Security posture</h3><p><b>Role:</b> {data.role}</p><p><b>Encrypted secrets:</b> {data.security?.secrets_encrypted?"Enabled":"Disabled"}</p><p><b>Bootstrap super admin:</b> {data.security?.bootstrap_super_admin}</p><p><b>Permissions:</b> {data.permissions?.join(", ")}</p></div></>}
function Models({api,rows,refresh}:{api:string;rows:any[];refresh:()=>void}){const [task,setTask]=useState("assistant"),[provider,setProvider]=useState("openai"),[model,setModel]=useState("gpt-5.6"),[params,setParams]=useState('{"temperature":0.2}');
 async function save(){await adminFetch(api,`/api/v1/admin/models/${encodeURIComponent(task)}`,{method:"PUT",body:JSON.stringify({provider,model,parameters:JSON.parse(params),enabled:true})});refresh()}
 return <><div className="adminForm grid4"><input value={task} onChange={e=>setTask(e.target.value)} placeholder="Task"/><input value={provider} onChange={e=>setProvider(e.target.value)} placeholder="Provider"/><input value={model} onChange={e=>setModel(e.target.value)} placeholder="Model"/><button onClick={save}><Save/>Save model</button><textarea value={params} onChange={e=>setParams(e.target.value)} /></div><DataTable rows={rows} columns={["task","provider","model","enabled","updated_by","updated_at"]}/></>}
function Secrets({api,rows,refresh}:{api:string;rows:any[];refresh:()=>void}){const [provider,setProvider]=useState("openai"),[name,setName]=useState("api_key"),[value,setValue]=useState("");
 async function save(){await adminFetch(api,`/api/v1/admin/secrets/${encodeURIComponent(provider)}/${encodeURIComponent(name)}`,{method:"PUT",body:JSON.stringify({value,enabled:true})});setValue("");refresh()}
 async function del(id:number){await adminFetch(api,`/api/v1/admin/secrets/${id}`,{method:"DELETE"});refresh()}
 return <><div className="adminForm"><input value={provider} onChange={e=>setProvider(e.target.value)} placeholder="Provider"/><input value={name} onChange={e=>setName(e.target.value)} placeholder="Key name"/><input type="password" value={value} onChange={e=>setValue(e.target.value)} placeholder="Secret value"/><button onClick={save} disabled={value.length<4}><KeyRound/>Encrypt & save</button></div><div className="secretRows">{rows.map(r=><div key={r.id}><div><b>{r.provider} / {r.name}</b><small>{r.value} · updated by {r.updated_by}</small></div><button className="dangerButton" onClick={()=>del(r.id)}><Trash2/></button></div>)}</div><p className="adminHint">Stored secrets are encrypted server-side and are never returned to the browser after submission.</p></>}
function SettingsTab({api,rows,refresh}:{api:string;rows:any[];refresh:()=>void}){const [key,setKey]=useState("ui.theme"),[value,setValue]=useState('{"mode":"dark"}');
 async function save(){await adminFetch(api,`/api/v1/admin/settings/${encodeURIComponent(key)}`,{method:"PUT",body:JSON.stringify({value:JSON.parse(value)})});refresh()}
 return <><div className="adminForm"><input value={key} onChange={e=>setKey(e.target.value)} placeholder="Setting key"/><textarea value={value} onChange={e=>setValue(e.target.value)}/><button onClick={save}><Save/>Save setting</button></div><DataTable rows={rows} columns={["key","value","updated_by","updated_at"]}/></>}
function UsersTab({api,rows,refresh}:{api:string;rows:any[];refresh:()=>void}){async function patch(uid:string,p:any){await adminFetch(api,`/api/v1/admin/users/${encodeURIComponent(uid)}`,{method:"PATCH",body:JSON.stringify(p)});refresh()}
 return <div className="userRows">{rows.map(r=><div key={r.uid}><div><b>{r.email}</b><small>{r.role} · {r.disabled?"disabled":"active"}</small></div><select value={r.role} onChange={e=>patch(r.uid,{role:e.target.value})}><option>user</option><option>admin</option><option>super_admin</option></select><button onClick={()=>patch(r.uid,{disabled:!r.disabled})}>{r.disabled?"Enable":"Disable"}</button></div>)}</div>}
function Audit({rows}:{rows:any[]}){return <DataTable rows={rows} columns={["created_at","actor_email","action","target","detail"]}/>}
function DataTable({rows,columns}:{rows:any[];columns:string[]}){return <div className="adminTable"><table><thead><tr>{columns.map(c=><th key={c}>{c}</th>)}</tr></thead><tbody>{rows.map((r,i)=><tr key={i}>{columns.map(c=><td key={c}>{typeof r[c]==="object"?JSON.stringify(r[c]):String(r[c]??"")}</td>)}</tr>)}</tbody></table></div>}
function AdminShell({children,onClose}:{children:any;onClose:()=>void}){return <div className="adminOverlay"><div className="adminWindow"><button className="adminClose" onClick={onClose}>×</button>{children}</div></div>}

function IntegrationsTab({api,catalog}:{api:string;catalog:any}){
 const [orgs,setOrgs]=useState<any[]>([]);const [orgId,setOrgId]=useState("");const [rows,setRows]=useState<any[]>([]);
 const [provider,setProvider]=useState("esri_arcgis"),[name,setName]=useState("ArcGIS"),[baseUrl,setBaseUrl]=useState("");
 const [created,setCreated]=useState<any>(null);const [err,setErr]=useState("");
 useEffect(()=>{adminFetch(api,"/api/v1/platform/organizations").then((x:any[])=>{setOrgs(x);if(x[0])setOrgId(x[0].id)})},[api]);
 async function load(id=orgId){if(id)setRows(await adminFetch(api,"/api/v1/integrations/connections?org_id="+encodeURIComponent(id)))}
 useEffect(()=>{load()},[orgId]);
 async function create(){setErr("");try{const x=await adminFetch(api,"/api/v1/integrations/connections",{method:"POST",body:JSON.stringify({org_id:orgId,provider,name,base_url:baseUrl||undefined,config:{}})});setCreated(x);await load()}catch(e:any){setErr(e.message)}}
 return <div>
  <div className="securityBox"><h3>Integration Hub</h3><p>Cloud REST connectors use encrypted credentials from API Keys. Desktop products use one-time bridge tokens and local bridge agents.</p></div>
  <div className="adminForm grid4">
   <select value={orgId} onChange={e=>setOrgId(e.target.value)}>{orgs.map(o=><option key={o.id} value={o.id}>{o.name}</option>)}</select>
   <select value={provider} onChange={e=>{setProvider(e.target.value);setName(e.target.value)}}>{Object.keys(catalog).map(k=><option key={k}>{k}</option>)}</select>
   <input value={baseUrl} onChange={e=>setBaseUrl(e.target.value)} placeholder="HTTPS base URL (REST connectors)"/>
   <button onClick={create} disabled={!orgId}><Plug/>Add connector</button>
  </div>
  {err&&<div className="adminError">{err}</div>}
  {created?.bridge_token&&<div className="securityBox"><h3>Bridge token — copy now</h3><p>This token is shown once and only its hash is retained.</p><code>{created.bridge_token}</code></div>}
  <div className="moduleGrid">{Object.entries(catalog).map(([k,v]:any)=><div className="moduleCard" key={k}><Plug/><b>{k.replace(/_/g," ")}</b><small>{v.mode} · {v.auth?.join(", ")}</small><p>{v.capabilities?.join(", ")}</p></div>)}</div>
  <h3>Configured connections</h3><DataTable rows={rows} columns={["provider","name","mode","base_url","enabled","updated_at"]}/>
 </div>
}
