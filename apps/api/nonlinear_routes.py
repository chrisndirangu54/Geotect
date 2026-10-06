from __future__ import annotations
from fastapi import APIRouter,Depends,HTTPException
from auth import current_user,require_permission
from elastoplastic_fem import solve_elastoplastic_2d,staged_excavation,adaptive_mesh_cycle,solve_adaptive_elastoplastic
from biot_solver import solve_biot_1d
from richards_solver import solve_richards_1d
from solver_benchmarks import suite,compare_reference
from coupled_up_fem import solve_monolithic_up_2d
from interface_elements import InterfaceState,coulomb_interface_response
from continuation_benchmarks import snap_through_scalar
from convergence_studies import full_matrix

router=APIRouter(prefix="/api/v1/nonlinear",tags=["nonlinear-fem"])

@router.post("/fem")
async def fem(payload:dict,user:dict=Depends(require_permission("jobs.execute"))):
    try:return solve_elastoplastic_2d(**payload)
    except Exception as exc:raise HTTPException(422,str(exc))

@router.post("/staged")
async def staged(payload:dict,user:dict=Depends(require_permission("jobs.execute"))):
    try:return staged_excavation(payload.get("base",{}),payload.get("stages",[]))
    except Exception as exc:raise HTTPException(422,str(exc))

@router.post("/adaptive")
async def adaptive(payload:dict,user:dict=Depends(current_user)):
    try:return adaptive_mesh_cycle(payload["result"],float(payload.get("max_fraction",.2)))
    except Exception as exc:raise HTTPException(422,str(exc))

@router.post("/biot-1d")
async def biot(payload:dict,user:dict=Depends(require_permission("jobs.execute"))):
    try:return solve_biot_1d(**payload)
    except Exception as exc:raise HTTPException(422,str(exc))

@router.post("/richards-1d")
async def richards(payload:dict,user:dict=Depends(require_permission("jobs.execute"))):
    try:return solve_richards_1d(**payload)
    except Exception as exc:raise HTTPException(422,str(exc))

@router.get("/benchmarks")
async def benchmarks(user:dict=Depends(current_user)):return suite()

@router.post("/benchmarks/compare")
async def benchmark_compare(payload:dict,user:dict=Depends(current_user)):
    return compare_reference(payload.get("result",{}),payload.get("reference",{}),payload.get("tolerances"))


@router.post("/monolithic-up")
async def monolithic_up(payload:dict,user:dict=Depends(require_permission("jobs.execute"))):
    try:return solve_monolithic_up_2d(**payload)
    except Exception as exc:raise HTTPException(422,str(exc))

@router.post("/adaptive-solve")
async def adaptive_solve(payload:dict,user:dict=Depends(require_permission("jobs.execute"))):
    try:return solve_adaptive_elastoplastic(payload.get("base",{}),int(payload.get("cycles",2)),float(payload.get("refine_fraction",.2)))
    except Exception as exc:raise HTTPException(422,str(exc))

@router.post("/interface/test")
async def interface_test(payload:dict,user:dict=Depends(current_user)):
    st=InterfaceState(**payload.get("state",{}))
    ns,K,info=coulomb_interface_response(payload.get("relative_disp_m",[0,0]),st,float(payload.get("normal_stiffness_kpa_m",1e6)),
      float(payload.get("shear_stiffness_kpa_m",1e5)),float(payload.get("friction_deg",30)),float(payload.get("cohesion_kpa",0)),float(payload.get("dilation_deg",0)))
    return {"state":ns.__dict__,"tangent":K.tolist(),"info":info}

@router.get("/continuation/snap-through")
async def continuation(user:dict=Depends(current_user)):return snap_through_scalar()

@router.get("/convergence")
async def convergence(user:dict=Depends(current_user)):return full_matrix()
