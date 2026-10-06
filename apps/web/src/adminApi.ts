import {idToken} from "./firebase";
export async function adminFetch(api:string,path:string,options:RequestInit={}){
 const token=await idToken();
 if(!token)throw new Error("Sign in required");
 const headers=new Headers(options.headers||{});
 headers.set("Authorization",`Bearer ${token}`);
 if(options.body && !(options.body instanceof FormData))headers.set("Content-Type","application/json");
 const r=await fetch(api+path,{...options,headers});
 if(!r.ok){let message=`${r.status} ${r.statusText}`;try{const j=await r.json();message=j.detail||message}catch{}throw new Error(message)}
 return r.status===204?null:r.json();
}
