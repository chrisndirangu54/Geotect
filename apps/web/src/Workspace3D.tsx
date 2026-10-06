import {useEffect,useRef,useState} from "react";
import {
 Viewer,Cartesian2,Cartesian3,Color,Entity,PolylineGlowMaterialProperty,HeightReference,
 Math as CesiumMath,Primitive,GeometryInstance,Geometry,GeometryAttribute,ComponentDatatype,
 PrimitiveType,PerInstanceColorAppearance,ColorGeometryInstanceAttribute,BoundingSphere
} from "cesium";
import "cesium/Build/Cesium/Widgets/widgets.css";
import type {ScenePayload} from "./types";
import type {DemMesh} from "./DemUpload";

const stateColor={measured:Color.LIME,interpreted:Color.GOLD,predicted:Color.CORNFLOWERBLUE};

export default function Workspace3D({scene,demMesh}:{scene:ScenePayload|null;demMesh?:DemMesh|null}){
 const host=useRef<HTMLDivElement>(null);const viewerRef=useRef<Viewer|null>(null);const meshRef=useRef<Primitive|null>(null);
 const [selected,setSelected]=useState("Nothing selected");

 useEffect(()=>{
  if(!host.current||viewerRef.current)return;
  const viewer=new Viewer(host.current,{animation:false,timeline:false,geocoder:false,homeButton:true,baseLayer:false,baseLayerPicker:false,sceneModePicker:true,navigationHelpButton:false,infoBox:true,selectionIndicator:true});
  viewer.scene.globe.depthTestAgainstTerrain=true;viewerRef.current=viewer;
  viewer.selectedEntityChanged.addEventListener((e?:Entity)=>setSelected(e?.name||"Nothing selected"));
  return()=>{viewer.destroy();viewerRef.current=null};
 },[]);

 useEffect(()=>{
  const viewer=viewerRef.current;if(!viewer||!scene)return;viewer.entities.removeAll();
  scene.boreholes.forEach(b=>viewer.entities.add({id:b.id,name:`${b.id} · Borehole`,polyline:{positions:Cartesian3.fromDegreesArrayHeights([b.collar.lon,b.collar.lat,b.collar.elevation_m,b.collar.lon,b.collar.lat,b.collar.elevation_m-b.total_depth_m]),width:7,material:new PolylineGlowMaterialProperty({glowPower:.18,color:Color.WHITE})},description:`Depth: ${b.total_depth_m} m<br/>Intervals: ${b.intervals.map(i=>`${i.from_m}-${i.to_m} m ${i.lithology} (${Math.round(i.confidence*100)}%)`).join("<br/>")}`}));
  scene.sensors.forEach(s=>viewer.entities.add({id:s.id,name:`${s.id} · ${s.type}`,position:Cartesian3.fromDegrees(s.position.lon,s.position.lat,s.position.elevation_m),point:{pixelSize:12,color:s.status==="critical"?Color.RED:s.status==="warning"?Color.ORANGE:Color.LIME,outlineColor:Color.WHITE,outlineWidth:2,heightReference:HeightReference.NONE},label:{text:s.id,font:"12px sans-serif",fillColor:Color.WHITE,pixelOffset:new Cartesian2(0,-18)},description:`${s.value} ${s.unit}<br/>${s.observed_at}`}));
  scene.infrastructure.forEach(x=>viewer.entities.add({id:x.id,name:`${x.name} · ${x.type}`,polyline:{positions:Cartesian3.fromDegreesArrayHeights(x.positions.flatMap(p=>[p.lon,p.lat,p.elevation_m])),width:6,material:Color.CYAN},description:`Criticality: ${Math.round(x.criticality*100)}%`}));
  scene.bodies.forEach(body=>{if(body.positions.length<3)return;const c=stateColor[body.state].withAlpha(Math.max(.12,Math.min(.55,body.confidence*.5)));viewer.entities.add({id:body.id,name:`${body.name} · ${body.kind}`,polygon:{hierarchy:body.positions.map(p=>Cartesian3.fromDegrees(p.lon,p.lat,p.elevation_m)),material:c,outline:true,outlineColor:stateColor[body.state]},description:`State: ${body.state}<br/>Confidence: ${Math.round(body.confidence*100)}%`})});
  viewer.camera.flyTo({destination:Cartesian3.fromDegrees(scene.center.lon,scene.center.lat,scene.center.elevation_m+1800),orientation:{heading:0,pitch:CesiumMath.toRadians(-55),roll:0}});
 },[scene]);

 useEffect(()=>{
   const viewer=viewerRef.current;if(!viewer||!demMesh)return;
   if(meshRef.current)viewer.scene.primitives.remove(meshRef.current);
   const positions=new Float64Array(demMesh.vertices.length*3);
   const cart=demMesh.vertices.map(v=>Cartesian3.fromDegrees(v[0],v[1],v[2]));
   cart.forEach((p,i)=>{positions[i*3]=p.x;positions[i*3+1]=p.y;positions[i*3+2]=p.z});
   const geometry=new Geometry({
     attributes:{position:new GeometryAttribute({componentDatatype:ComponentDatatype.DOUBLE,componentsPerAttribute:3,values:positions})},
     indices:new Uint32Array(demMesh.indices),primitiveType:PrimitiveType.TRIANGLES,
     boundingSphere:BoundingSphere.fromPoints(cart)
   });
   const primitive=new Primitive({geometryInstances:new GeometryInstance({geometry,attributes:{color:ColorGeometryInstanceAttribute.fromColor(Color.DARKSEAGREEN.withAlpha(.82))}}),appearance:new PerInstanceColorAppearance({flat:true,translucent:true,closed:false}),asynchronous:false});
   viewer.scene.primitives.add(primitive);meshRef.current=primitive;
   if(cart.length)viewer.camera.flyToBoundingSphere(BoundingSphere.fromPoints(cart),{duration:1.5});
 },[demMesh]);

 return <div className="cadWrap"><div ref={host} className="cesiumHost"/><div className="cadOverlay"><b>GeoTect 3D CAD</b><span>{selected}</span></div><div className="cadLegend"><span><i className="measured"/>Measured</span><span><i className="interpreted"/>Interpreted</span><span><i className="predicted"/>Predicted</span></div></div>
}
