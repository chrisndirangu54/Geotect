import {useEffect,useRef,useState} from "react";
import {
 Viewer,Cartesian2,Cartesian3,Cartographic,Color,Entity,PolylineGlowMaterialProperty,HeightReference,
 Math as CesiumMath,Primitive,GeometryInstance,Geometry,GeometryAttribute,ComponentDatatype,
 PrimitiveType,PerInstanceColorAppearance,ColorGeometryInstanceAttribute,BoundingSphere,
 ScreenSpaceEventHandler,ScreenSpaceEventType,EllipsoidGeodesic,ClippingPlaneCollection,ClippingPlane
} from "cesium";
import "cesium/Build/Cesium/Widgets/widgets.css";
import type {CadFeature,Point3D,ScenePayload} from "./types";
import type {DemMesh} from "./DemUpload";
import type {CadMode} from "./CadToolbar";

const stateColor={measured:Color.LIME,interpreted:Color.GOLD,predicted:Color.CORNFLOWERBLUE};
const lineKinds=new Set(["fault","road","tunnel","section","measurement"]);
const polygonKinds=new Set(["stratum","foundation","excavation"]);

function pickPoint(viewer:Viewer,screen:Cartesian2):Point3D|null{
 let c:Cartesian3|undefined;
 if(viewer.scene.pickPositionSupported){try{c=viewer.scene.pickPosition(screen)}catch{}}
 if(!c){const ray=viewer.camera.getPickRay(screen);if(ray)c=viewer.scene.globe.pick(ray,viewer.scene)}
 if(!c)c=viewer.camera.pickEllipsoid(screen,viewer.scene.globe.ellipsoid);
 if(!c)return null;
 const q=Cartographic.fromCartesian(c);
 return {lon:CesiumMath.toDegrees(q.longitude),lat:CesiumMath.toDegrees(q.latitude),elevation_m:q.height};
}
function distance3d(a:Point3D,b:Point3D){
 const ca=Cartographic.fromDegrees(a.lon,a.lat,a.elevation_m),cb=Cartographic.fromDegrees(b.lon,b.lat,b.elevation_m);
 const surface=new EllipsoidGeodesic(ca,cb).surfaceDistance;
 return Math.hypot(surface,b.elevation_m-a.elevation_m);
}

export default function Workspace3D({scene,demMesh,features,mode,onAddFeature,clipping,onSelectFeatureId}:{scene:ScenePayload|null;demMesh?:DemMesh|null;features:CadFeature[];mode:CadMode;onAddFeature:(f:CadFeature)=>void;clipping:boolean;onSelectFeatureId:(id:string|null)=>void}){
 const host=useRef<HTMLDivElement>(null);const viewerRef=useRef<Viewer|null>(null);const meshRef=useRef<Primitive|null>(null);const handlerRef=useRef<ScreenSpaceEventHandler|null>(null);
 const draftRef=useRef<Point3D[]>([]);const [selected,setSelected]=useState("Nothing selected");const [draftCount,setDraftCount]=useState(0);

 useEffect(()=>{if(!host.current||viewerRef.current)return;const viewer=new Viewer(host.current,{animation:false,timeline:false,geocoder:false,homeButton:true,baseLayer:false,baseLayerPicker:false,sceneModePicker:true,navigationHelpButton:false,infoBox:true,selectionIndicator:true});viewer.scene.globe.depthTestAgainstTerrain=true;viewerRef.current=viewer;viewer.selectedEntityChanged.addEventListener((e?:Entity)=>{setSelected(e?.name||"Nothing selected");const id=e?.id;onSelectFeatureId(typeof id==="string"&&id.includes("-")?id:null)});return()=>{handlerRef.current?.destroy();viewer.destroy();viewerRef.current=null}},[onSelectFeatureId]);

 useEffect(()=>{const viewer=viewerRef.current;if(!viewer)return;const old=viewer.scene.globe.clippingPlanes;if(old&&!old.isDestroyed())old.destroy();viewer.scene.globe.clippingPlanes=clipping?new ClippingPlaneCollection({planes:[new ClippingPlane(new Cartesian3(1,0,0),0)],edgeWidth:1,edgeColor:Color.WHITE}):undefined as any},[clipping]);

 useEffect(()=>{
  const viewer=viewerRef.current;if(!viewer||!scene)return;viewer.entities.removeAll();
  scene.boreholes.forEach(b=>viewer.entities.add({id:b.id,name:`${b.id} · Borehole`,polyline:{positions:Cartesian3.fromDegreesArrayHeights([b.collar.lon,b.collar.lat,b.collar.elevation_m,b.collar.lon,b.collar.lat,b.collar.elevation_m-b.total_depth_m]),width:7,material:new PolylineGlowMaterialProperty({glowPower:.18,color:Color.WHITE})},description:`Depth: ${b.total_depth_m} m<br/>${b.intervals.map(i=>`${i.from_m}-${i.to_m}m ${i.lithology}`).join("<br/>")}`}));
  scene.sensors.forEach(s=>viewer.entities.add({id:s.id,name:`${s.id} · ${s.type}`,position:Cartesian3.fromDegrees(s.position.lon,s.position.lat,s.position.elevation_m),point:{pixelSize:12,color:s.status==="critical"?Color.RED:s.status==="warning"?Color.ORANGE:Color.LIME,outlineColor:Color.WHITE,outlineWidth:2,heightReference:HeightReference.NONE},label:{text:s.id,font:"12px sans-serif",fillColor:Color.WHITE,pixelOffset:new Cartesian2(0,-18)},description:`${s.value} ${s.unit}`}));
  scene.infrastructure.forEach(x=>viewer.entities.add({id:x.id,name:`${x.name} · ${x.type}`,polyline:{positions:Cartesian3.fromDegreesArrayHeights(x.positions.flatMap(p=>[p.lon,p.lat,p.elevation_m])),width:6,material:Color.CYAN}}));
  scene.bodies.forEach(body=>{if(body.positions.length<3)return;const c=stateColor[body.state].withAlpha(Math.max(.12,Math.min(.55,body.confidence*.5)));viewer.entities.add({id:body.id,name:`${body.name} · ${body.kind}`,polygon:{hierarchy:body.positions.map(p=>Cartesian3.fromDegrees(p.lon,p.lat,p.elevation_m)),material:c,outline:true,outlineColor:stateColor[body.state]}})});
  for(const f of features){
   const positions=Cartesian3.fromDegreesArrayHeights(f.positions.flatMap(p=>[p.lon,p.lat,p.elevation_m]));
   const color=f.kind==="fault"?Color.ORANGERED:f.kind==="measurement"?Color.WHITE:f.kind==="tunnel"?Color.VIOLET:f.state==="interpreted"?Color.GOLD:f.state==="predicted"?Color.CORNFLOWERBLUE:Color.DEEPSKYBLUE;
   if(f.geometry==="point"&&f.positions[0])viewer.entities.add({id:f.id,name:f.name,position:positions[0],point:{pixelSize:11,color},label:{text:f.name,font:"11px sans-serif",pixelOffset:new Cartesian2(0,-16)},description:`State: ${f.state}<br/>Confidence: ${Math.round(f.confidence*100)}%`});
   else if(f.geometry==="polyline")viewer.entities.add({id:f.id,name:f.name,polyline:{positions,width:f.kind==="fault"?5:3,material:color},description:f.properties.length_m?`Length: ${Number(f.properties.length_m).toFixed(2)} m`:""});
   else if(f.geometry==="polygon")viewer.entities.add({id:f.id,name:f.name,polygon:{hierarchy:positions,material:color.withAlpha(.28),outline:true,outlineColor:color,extrudedHeight:typeof f.properties.extruded_to_m==="number"?Number(f.properties.extruded_to_m):undefined},description:`State: ${f.state}<br/>Confidence: ${Math.round(f.confidence*100)}%`});
  }
 },[scene,features]);

 useEffect(()=>{const viewer=viewerRef.current;if(!viewer||!scene)return;viewer.camera.flyTo({destination:Cartesian3.fromDegrees(scene.center.lon,scene.center.lat,scene.center.elevation_m+1800),orientation:{heading:0,pitch:CesiumMath.toRadians(-55),roll:0}})},[scene]);

 useEffect(()=>{const viewer=viewerRef.current;if(!viewer||!demMesh)return;if(meshRef.current)viewer.scene.primitives.remove(meshRef.current);const positions=new Float64Array(demMesh.vertices.length*3);const cart=demMesh.vertices.map(v=>Cartesian3.fromDegrees(v[0],v[1],v[2]));cart.forEach((p,i)=>{positions[i*3]=p.x;positions[i*3+1]=p.y;positions[i*3+2]=p.z});const geometry=new Geometry({attributes:{position:new GeometryAttribute({componentDatatype:ComponentDatatype.DOUBLE,componentsPerAttribute:3,values:positions})},indices:new Uint32Array(demMesh.indices),primitiveType:PrimitiveType.TRIANGLES,boundingSphere:BoundingSphere.fromPoints(cart)});const primitive=new Primitive({geometryInstances:new GeometryInstance({id:"loaded-dem",geometry,attributes:{color:ColorGeometryInstanceAttribute.fromColor(Color.DARKSEAGREEN.withAlpha(.82))}}),appearance:new PerInstanceColorAppearance({flat:true,translucent:true,closed:false}),asynchronous:false});viewer.scene.primitives.add(primitive);meshRef.current=primitive;if(cart.length)viewer.camera.flyToBoundingSphere(BoundingSphere.fromPoints(cart),{duration:1.2})},[demMesh]);

 useEffect(()=>{
  const viewer=viewerRef.current;if(!viewer)return;handlerRef.current?.destroy();draftRef.current=[];setDraftCount(0);
  if(mode==="select")return;
  const handler=new ScreenSpaceEventHandler(viewer.scene.canvas);handlerRef.current=handler;
  const finish=()=>{
   const pts=draftRef.current;if(!pts.length)return;
   const isPoint=mode==="borehole";const isLine=lineKinds.has(mode);const isPoly=polygonKinds.has(mode);
   if((isLine&&pts.length<2)||(isPoly&&pts.length<3))return;
   let length=0;for(let i=1;i<pts.length;i++)length+=distance3d(pts[i-1],pts[i]);
   const avg=pts.reduce((s,p)=>s+p.elevation_m,0)/pts.length;
   const feature:CadFeature={id:`${mode}-${crypto.randomUUID()}`,kind:mode as any,name:`${mode[0].toUpperCase()+mode.slice(1)} ${new Date().toLocaleTimeString()}`,state:"measured",confidence:1,geometry:isPoint?"point":isLine?"polyline":"polygon",positions:[...pts],properties:{length_m:isLine?length:null,extruded_to_m:isPoly?avg-10:null,snap_source:"scene-depth/terrain"}};
   onAddFeature(feature);draftRef.current=[];setDraftCount(0);
  };
  handler.setInputAction((e:any)=>{const p=pickPoint(viewer,e.position);if(!p)return;draftRef.current.push(p);setDraftCount(draftRef.current.length);if(mode==="borehole")finish()},ScreenSpaceEventType.LEFT_CLICK);
  handler.setInputAction(()=>finish(),ScreenSpaceEventType.RIGHT_CLICK);
  return()=>handler.destroy();
 },[mode,onAddFeature]);

 return <div className="cadWrap"><div ref={host} className="cesiumHost"/><div className="cadOverlay"><b>GeoTect 3D CAD · {mode}</b><span>{mode==="select"?selected:`${draftCount} vertices · left-click draw / right-click finish`}</span></div><div className="cadLegend"><span><i className="measured"/>Measured</span><span><i className="interpreted"/>Interpreted</span><span><i className="predicted"/>Predicted</span></div></div>
}
