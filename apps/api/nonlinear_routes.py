from __future__ import annotations
from fastapi import APIRouter,Depends,HTTPException
from auth import current_user,require_permission
from elastoplastic_fem import solve_elastoplastic_2d,staged_excavation,adaptive_mesh_cycle
from biot_solver import solve_biot_1d
from richards_solver import solve_richards_1d
from solver_benchmarks import suite,compare_reference

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
