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
from quadratic_up_fem import solve_quadratic_up_2d
from updated_lagrangian_fem import solve_updated_lagrangian_2d
from strength_reduction import strength_reduction_search
from cyclic_materials import cyclic_series,newmark_beta_sdof
from contact_surfaces import SurfaceContactState,coulomb_surface_contact
from parallel_backends import execution_capabilities,petsc_available
from verification_dashboard import release_verification,render_html

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


@router.post("/quadratic-up")
async def quadratic_up(payload:dict,user:dict=Depends(require_permission("jobs.execute"))):
    try:return solve_quadratic_up_2d(**payload)
    except Exception as exc:raise HTTPException(422,str(exc))

@router.post("/updated-lagrangian")
async def updated_lagrangian(payload:dict,user:dict=Depends(require_permission("jobs.execute"))):
    try:return solve_updated_lagrangian_2d(**payload)
    except Exception as exc:raise HTTPException(422,str(exc))

@router.post("/strength-reduction")
async def strength_reduction(payload:dict,user:dict=Depends(require_permission("jobs.execute"))):
    try:return strength_reduction_search(payload.get("base",{}),float(payload.get("min_factor",1)),float(payload.get("max_factor",5)),
      float(payload.get("tolerance",.02)),int(payload.get("max_iter",12)),payload.get("displacement_limit_m"))
    except Exception as exc:raise HTTPException(422,str(exc))

@router.post("/cyclic/material")
async def cyclic_material(payload:dict,user:dict=Depends(current_user)):
    try:return cyclic_series(payload.get("strains",[]),float(payload["gmax_kpa"]),float(payload["gamma_ref"]))
    except Exception as exc:raise HTTPException(422,str(exc))

@router.post("/dynamic/sdof")
async def dynamic_sdof(payload:dict,user:dict=Depends(current_user)):
    try:return newmark_beta_sdof(payload.get("accel_m_s2",[]),float(payload["dt_s"]),float(payload["mass"]),float(payload["stiffness"]),
      float(payload.get("damping_ratio",.05)),float(payload.get("beta",.25)),float(payload.get("gamma",.5)))
    except Exception as exc:raise HTTPException(422,str(exc))

@router.post("/contact3d/test")
async def contact3d(payload:dict,user:dict=Depends(current_user)):
    try:
        st=SurfaceContactState(**payload.get("state",{}))
        return coulomb_surface_contact(payload["point"],payload.get("displacement",[0,0,0]),payload["triangle"],st,
          float(payload.get("normal_stiffness_kpa_m",1e6)),float(payload.get("shear_stiffness_kpa_m",1e5)),
          float(payload.get("friction_deg",30)),float(payload.get("cohesion_kpa",0)))
    except Exception as exc:raise HTTPException(422,str(exc))

@router.get("/execution-capabilities")
async def execution(user:dict=Depends(current_user)):return execution_capabilities()

@router.get("/verification/report")
async def verification_report(user:dict=Depends(current_user)):return release_verification()

@router.get("/verification/dashboard")
async def verification_dashboard(user:dict=Depends(current_user)):
    from fastapi.responses import HTMLResponse
    return HTMLResponse(render_html(release_verification()))
