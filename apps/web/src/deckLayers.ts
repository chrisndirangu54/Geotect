import {ScatterplotLayer,PathLayer} from "@deck.gl/layers";
import type {ScenePayload} from "./types";

/** Reusable deck.gl representations for dense analytical overlays.
 * Cesium remains the authoritative globe/CAD camera; these layers are intended
 * for synchronized 2D/section views and future Cesium camera bridging.
 */
export function buildAnalyticalLayers(scene:ScenePayload){
 return [
  new ScatterplotLayer({
   id:"geotect-sensors",data:scene.sensors,
   getPosition:(d:any)=>[d.position.lon,d.position.lat,d.position.elevation_m],
   getRadius:18,radiusUnits:"meters",pickable:true,
   getFillColor:(d:any)=>d.status==="critical"?[220,65,65,210]:d.status==="warning"?[230,160,60,210]:[70,220,140,210]
  }),
  new PathLayer({
   id:"geotect-infrastructure",data:scene.infrastructure,
   getPath:(d:any)=>d.positions.map((p:any)=>[p.lon,p.lat,p.elevation_m]),
   getWidth:4,widthUnits:"pixels",getColor:[70,200,220,220],pickable:true
  })
 ];
}
