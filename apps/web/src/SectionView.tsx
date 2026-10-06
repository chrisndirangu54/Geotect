type FenceColumn={id:string;station_m:number;offset_m:number;top_elevation_m:number;intervals:{top_m:number;bottom_m:number;lithology:string;confidence:number}[]};
type Fence={columns:FenceColumn[];length_m:number}|null;
const palette=["#5bb98a","#d5b669","#6fa4d8","#b67bc5","#d9846a","#91a97a"];
export default function SectionView({data}:{data:Fence}){
 if(!data||!data.columns.length)return null;
 const all=data.columns.flatMap(c=>c.intervals.flatMap(i=>[i.top_m,i.bottom_m]));
 const max=Math.max(...all),min=Math.min(...all),range=Math.max(max-min,1);
 const width=1000,height=260,pad=45;
 return <section className="sectionView"><div className="sectionHeader"><b>Geological Fence / Section</b><span>{data.columns.length} boreholes · {data.length_m.toFixed(0)} m trace</span></div>
 <svg viewBox={`0 0 ${width} ${height}`} role="img">
  <line x1={pad} y1={height-pad} x2={width-pad} y2={height-pad} className="axis"/>
  {data.columns.map((c,ci)=>{
   const x=pad+(c.station_m/Math.max(data.length_m,1))*(width-pad*2);
   return <g key={c.id}><line x1={x} x2={x} y1={pad/2} y2={height-pad} className="bhline"/>
    <text x={x+4} y={18} className="svgLabel">{c.id}</text>
    {c.intervals.map((it,i)=>{
      const y=(v:number)=>pad/2+(max-v)/range*(height-pad*1.5);
      const color=palette[Math.abs([...it.lithology].reduce((a,ch)=>a+ch.charCodeAt(0),0))%palette.length];
      return <rect key={i} x={x-9} width={18} y={y(it.top_m)} height={Math.max(2,y(it.bottom_m)-y(it.top_m))} fill={color} opacity={.45+.5*it.confidence}/>;
    })}</g>
  })}
 </svg></section>
}
