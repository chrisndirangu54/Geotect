export type Point3D={lon:number;lat:number;elevation_m:number};
export type ConfidenceState="measured"|"interpreted"|"predicted";

export type Borehole={
  id:string;collar:Point3D;total_depth_m:number;
  intervals:{from_m:number;to_m:number;lithology:string;confidence:number}[];
};
export type Sensor={
  id:string;type:string;position:Point3D;status:"normal"|"warning"|"critical";
  value:number;unit:string;observed_at:string;
};
export type Infrastructure={
  id:string;type:string;name:string;positions:Point3D[];criticality:number;
};
export type GeoBody={
  id:string;name:string;kind:"geology"|"ert"|"seismic"|"uncertainty"|"groundwater"|"insar";
  state:ConfidenceState;confidence:number;positions:Point3D[];values?:number[];
};
export type ScenePayload={
  site_id:string;crs:string;center:Point3D;
  boreholes:Borehole[];sensors:Sensor[];infrastructure:Infrastructure[];bodies:GeoBody[];
};
