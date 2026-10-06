from __future__ import annotations
import math

def cut_fill(existing:list[list[float]],design:list[list[float]],cell_area_m2:float)->dict:
    if len(existing)!=len(design) or any(len(a)!=len(b) for a,b in zip(existing,design)):raise ValueError("grids must match")
    cut=fill=0.0
    for er,dr in zip(existing,design):
        for e,d in zip(er,dr):
            dv=(float(d)-float(e))*cell_area_m2
            if dv>=0:fill+=dv
            else:cut-=dv
    return {"cut_m3":cut,"fill_m3":fill,"net_fill_m3":fill-cut,"method":"grid-cell cut/fill"}

def bench_geometry(height_m:float,width_m:float,face_angle_deg:float,bench_count:int)->dict:
    run=height_m/max(math.tan(math.radians(face_angle_deg)),1e-9)
    total_height=height_m*bench_count;total_run=bench_count*run+(bench_count-1)*width_m
    overall_angle=math.degrees(math.atan2(total_height,total_run))
    return {"total_height_m":total_height,"total_run_m":total_run,"overall_slope_angle_deg":overall_angle,"bench_count":bench_count}

def convergence(baseline_diameter_m:float,current_diameter_m:float)->dict:
    closure=baseline_diameter_m-current_diameter_m
    return {"closure_m":closure,"closure_mm":closure*1000,"strain_percent":100*closure/max(baseline_diameter_m,1e-9)}
