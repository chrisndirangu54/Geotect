import {useCallback,useState} from "react";
export function useHistory<T>(initial:T){
 const [past,setPast]=useState<T[]>([]);const [present,setPresent]=useState<T>(initial);const [future,setFuture]=useState<T[]>([]);
 const set=useCallback((next:T|((x:T)=>T))=>{setPresent(current=>{const value=typeof next==="function"?(next as (x:T)=>T)(current):next;setPast(p=>[...p,current].slice(-100));setFuture([]);return value})},[]);
 const undo=useCallback(()=>setPast(p=>{if(!p.length)return p;const previous=p[p.length-1];setPresent(current=>{setFuture(f=>[current,...f]);return previous});return p.slice(0,-1)}),[]);
 const redo=useCallback(()=>setFuture(f=>{if(!f.length)return f;const next=f[0];setPresent(current=>{setPast(p=>[...p,current]);return next});return f.slice(1)}),[]);
 return {value:present,set,undo,redo,canUndo:past.length>0,canRedo:future.length>0};
}
