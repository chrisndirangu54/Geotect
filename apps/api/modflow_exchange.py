from __future__ import annotations
import os,tempfile,shutil
from pathlib import Path

def _flopy():
    try:import flopy;return flopy
    except Exception as exc:raise RuntimeError("FloPy is required for MODFLOW interchange") from exc

def build_mf6_groundwater(spec:dict,workspace:str|None=None)->dict:
    flopy=_flopy();ws=workspace or tempfile.mkdtemp(prefix="geotect-mf6-")
    sim_name=str(spec.get("simulation_name","geotect"))
    nlay=int(spec.get("nlay",1));nrow=int(spec.get("nrow",20));ncol=int(spec.get("ncol",20))
    delr=float(spec.get("delr",10));delc=float(spec.get("delc",10));top=float(spec.get("top",100));botm=spec.get("botm",[0]*nlay)
    k=spec.get("k",1e-5);left=float(spec.get("left_head",100));right=float(spec.get("right_head",90))
    sim=flopy.mf6.MFSimulation(sim_name=sim_name,sim_ws=ws,exe_name=str(spec.get("exe_name","mf6")))
    flopy.mf6.ModflowTdis(sim,time_units="DAYS",nper=1,perioddata=[(1.0,1,1.0)])
    flopy.mf6.ModflowIms(sim,print_option="SUMMARY",complexity="SIMPLE")
    gwf=flopy.mf6.ModflowGwf(sim,modelname=sim_name,save_flows=True)
    flopy.mf6.ModflowGwfdis(gwf,nlay=nlay,nrow=nrow,ncol=ncol,delr=delr,delc=delc,top=top,botm=botm)
    flopy.mf6.ModflowGwfic(gwf,strt=(left+right)/2)
    flopy.mf6.ModflowGwfnpf(gwf,icelltype=1,k=k,save_specific_discharge=True)
    chd=[]
    for lay in range(nlay):
        for row in range(nrow):
            chd.append(((lay,row,0),left));chd.append(((lay,row,ncol-1),right))
    flopy.mf6.ModflowGwfchd(gwf,stress_period_data=chd,save_flows=True)
    flopy.mf6.ModflowGwfoc(gwf,head_filerecord=f"{sim_name}.hds",budget_filerecord=f"{sim_name}.cbc",saverecord=[("HEAD","ALL"),("BUDGET","ALL")])
    sim.write_simulation()
    return {"workspace":ws,"simulation_name":sim_name,"namefile":str(Path(ws)/"mfsim.nam"),"model_name":sim_name,"status":"written"}

def run_mf6(spec:dict)->dict:
    created=build_mf6_groundwater(spec)
    flopy=_flopy();sim=flopy.mf6.MFSimulation.load(sim_ws=created["workspace"],exe_name=str(spec.get("exe_name","mf6")))
    ok,buff=sim.run_simulation(silent=True,report=True)
    out={**created,"success":bool(ok),"stdout_tail":list(buff)[-30:]}
    if ok:
        gwf=sim.get_model(created["model_name"])
        try:
            heads=gwf.output.head().get_data()
            out["head_shape"]=list(heads.shape);out["head_min"]=float(heads.min());out["head_max"]=float(heads.max())
        except Exception as exc:out["result_warning"]=str(exc)
    return out

def inspect_mf6(workspace:str)->dict:
    flopy=_flopy();sim=flopy.mf6.MFSimulation.load(sim_ws=workspace)
    return {"simulation_name":sim.name,"models":list(sim.model_names),"workspace":workspace}
