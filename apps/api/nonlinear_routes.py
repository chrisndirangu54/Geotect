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
from up3d_fem import solve_up3d_tet
from hex8_up_fem import solve_up3d_hex
from materials3d import AnisotropicCriticalState,LiquefactionSandStyle
from nonlocal_softening import regularized_strength
from fracture_remesh import remesh_contact_surfaces
from thm_coupling import solve_thm_1d
from petsc_dmplex import create_distributed_box
from gpu_constitutive import cuda_mohr_coulomb_batch

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


@router.post("/up3d/tet")
async def up3d_tet(payload:dict,user:dict=Depends(require_permission("jobs.execute"))):
    try:return solve_up3d_tet(**payload)
    except Exception as exc:raise HTTPException(422,str(exc))

@router.post("/up3d/hex")
async def up3d_hex(payload:dict,user:dict=Depends(require_permission("jobs.execute"))):
    try:return solve_up3d_hex(**payload)
    except Exception as exc:raise HTTPException(422,str(exc))

@router.post("/materials3d/liquefaction-style")
async def liquefaction_style(payload:dict,user:dict=Depends(current_user)):
    try:
        m=LiquefactionSandStyle(**payload.get("parameters",{}));s=m.initial()
        import numpy as np
        history=[]
        for deps in payload.get("strain_increments",[]):
            s,_,meta=m.integrate(s,np.asarray(deps,dtype=float),float(payload.get("effective_mean_kpa",100)))
            history.append({"state":{"stress":s.stress.tolist(),"eqp":s.eqp,"ru":s.pore_pressure_ratio,"fabric":s.fabric.tolist() if s.fabric is not None else None},"meta":meta})
        return {"history":history,"model":"PM4Sand/UBCSAND-style research formulation","equivalence_claim":False}
    except Exception as exc:raise HTTPException(422,str(exc))

@router.post("/materials3d/critical-state")
async def critical_state(payload:dict,user:dict=Depends(current_user)):
    try:
        import numpy as np
        m=AnisotropicCriticalState(**payload.get("parameters",{}));s=m.initial();hist=[]
        for deps in payload.get("strain_increments",[]):
            s,_,meta=m.integrate(s,np.asarray(deps,dtype=float));hist.append({"stress":s.stress.tolist(),"eqp":s.eqp,"hardening":s.hardening,"meta":meta})
        return {"history":hist,"model":"anisotropic critical-state research formulation"}
    except Exception as exc:raise HTTPException(422,str(exc))

@router.post("/regularization/nonlocal")
async def nonlocal_regularization(payload:dict,user:dict=Depends(current_user)):
    try:return regularized_strength(**payload)
    except Exception as exc:raise HTTPException(422,str(exc))

@router.post("/fracture/remesh")
async def fracture_remesh(payload:dict,user:dict=Depends(current_user)):
    try:return remesh_contact_surfaces(payload["nodes"],payload["triangles"],payload["damage"],float(payload.get("threshold",.8)))
    except Exception as exc:raise HTTPException(422,str(exc))

@router.post("/thm/1d")
async def thm(payload:dict,user:dict=Depends(require_permission("jobs.execute"))):
    try:return solve_thm_1d(**payload)
    except Exception as exc:raise HTTPException(422,str(exc))

@router.get("/petsc/dmplex")
async def dmplex_info(user:dict=Depends(current_user)):
    try:
        dm,meta=create_distributed_box();dm.destroy();return meta
    except Exception as exc:return {"available":False,"reason":str(exc)}

@router.post("/gpu/constitutive")
async def gpu_constitutive(payload:dict,user:dict=Depends(require_permission("jobs.execute"))):
    try:
        s,y,f=cuda_mohr_coulomb_batch(payload["stress"],payload["deps"],float(payload["E_kpa"]),float(payload["nu"]),float(payload["cohesion_kpa"]),float(payload["friction_deg"]))
        return {"stress":s.tolist(),"yielded":y.tolist(),"yield_function":f.tolist()}
    except Exception as exc:raise HTTPException(422,str(exc))


from opensees_reference import available as opensees_available,pm4sand_simple_shear,manzari_dafalias_brick,sanisand_ms_brick
from petsc_fieldsplit import solve_fieldsplit_schur
from cuda_global_assembly import assemble_cuda_coo,cuda_assemble_and_solve
from dynamic_up3d import solve_dynamic_up3d_hex
from phase_field_fracture import solve_phase_field_2d,xfem_heaviside_enrichment
from thm3d_fem import solve_thm3d_tet
from experimental_validation import dataset_catalog,validate_channels,shake_table_objective

@router.get("/reference/opensees")
async def reference_opensees(user:dict=Depends(current_user)): return opensees_available()

@router.post("/reference/pm4sand")
async def reference_pm4sand(payload:dict,user:dict=Depends(require_permission("jobs.execute"))):
    try:return pm4sand_simple_shear(payload.get("parameters",{}),payload.get("strain_history",[]),float(payload.get("dt",.01)))
    except Exception as exc:raise HTTPException(422,str(exc))

@router.post("/reference/manzari-dafalias")
async def reference_manzari(payload:dict,user:dict=Depends(require_permission("jobs.execute"))):
    try:return manzari_dafalias_brick(payload.get("parameters",{}),payload.get("accel"),float(payload.get("dt",.01)))
    except Exception as exc:raise HTTPException(422,str(exc))

@router.post("/reference/sanisand-ms")
async def reference_sanisand(payload:dict,user:dict=Depends(require_permission("jobs.execute"))):
    try:return sanisand_ms_brick(payload.get("parameters",{}),payload.get("accel"),float(payload.get("dt",.01)))
    except Exception as exc:raise HTTPException(422,str(exc))

@router.post("/dynamic/up3d")
async def dynamic_up3d(payload:dict,user:dict=Depends(require_permission("jobs.execute"))):
    try:return solve_dynamic_up3d_hex(**payload)
    except Exception as exc:raise HTTPException(422,str(exc))

@router.post("/fracture/phase-field")
async def phase_field(payload:dict,user:dict=Depends(require_permission("jobs.execute"))):
    try:return solve_phase_field_2d(**payload)
    except Exception as exc:raise HTTPException(422,str(exc))

@router.post("/fracture/xfem-enrichment")
async def xfem(payload:dict,user:dict=Depends(current_user)):
    try:return xfem_heaviside_enrichment(payload["nodes"],payload["crack_point"],payload["crack_normal"])
    except Exception as exc:raise HTTPException(422,str(exc))

@router.post("/thm/3d")
async def thm3d(payload:dict,user:dict=Depends(require_permission("jobs.execute"))):
    try:return solve_thm3d_tet(**payload)
    except Exception as exc:raise HTTPException(422,str(exc))

@router.get("/validation/datasets")
async def validation_datasets(user:dict=Depends(current_user)):return dataset_catalog()

@router.post("/validation/channels")
async def validation_channels(payload:dict,user:dict=Depends(current_user)):
    try:return validate_channels(payload["observed"],payload["simulated"],payload["channel_map"])
    except Exception as exc:raise HTTPException(422,str(exc))

@router.post("/validation/shake-table")
async def validation_shake(payload:dict,user:dict=Depends(current_user)):
    try:return shake_table_objective(payload["observed_accel"],payload["sim_accel"],payload.get("observed_pressure"),payload.get("sim_pressure"))
    except Exception as exc:raise HTTPException(422,str(exc))


from calibration_campaigns import calibrate_liquefaction_style
from verification_campaigns import wave_propagation_benchmark,phase_field_energy_convergence,compare_cpu_gpu
from designsafe_client import DesignSafeClient,published_corral_path,nees_corral_path
from model_registry import get_provider_secret
import tempfile,os

@router.post("/calibration/liquefaction-style")
async def calibrate_liquefaction(payload:dict,user:dict=Depends(require_permission("jobs.execute"))):
    try:return calibrate_liquefaction_style(payload["strain_history"],payload["observed_ru"],payload.get("fixed"),payload.get("bounds"),int(payload.get("seed",42)),int(payload.get("maxiter",50)))
    except Exception as exc:raise HTTPException(422,str(exc))

@router.get("/campaigns/wave-propagation")
async def campaign_wave(user:dict=Depends(current_user)):return wave_propagation_benchmark()

@router.get("/campaigns/phase-field-energy")
async def campaign_phase_field(user:dict=Depends(current_user)):return phase_field_energy_convergence()

@router.get("/designsafe/path/published/{project_id}")
async def designsafe_published_path(project_id:str,user:dict=Depends(current_user)):return {"path":published_corral_path(project_id)}

@router.get("/designsafe/path/nees/{project_id}")
async def designsafe_nees_path(project_id:str,user:dict=Depends(current_user)):return {"path":nees_corral_path(project_id)}

@router.get("/designsafe/files")
async def designsafe_files(system_id:str,path:str="",user:dict=Depends(current_user)):
    token=await get_provider_secret("designsafe","tapis_token")
    if not token:raise HTTPException(400,"DesignSafe Tapis token is not configured in the server secret vault")
    try:return await DesignSafeClient(token).list_files(system_id,path)
    except Exception as exc:raise HTTPException(422,str(exc))

@router.post("/designsafe/download")
async def designsafe_download(payload:dict,user:dict=Depends(require_permission("jobs.execute"))):
    token=await get_provider_secret("designsafe","tapis_token")
    if not token:raise HTTPException(400,"DesignSafe Tapis token is not configured in the server secret vault")
    fd,path=tempfile.mkstemp(prefix="designsafe-",suffix=os.path.splitext(str(payload.get("path","data.bin")))[1]);os.close(fd)
    try:return await DesignSafeClient(token).download(str(payload["system_id"]),str(payload["path"]),path)
    except Exception as exc:
        try:os.unlink(path)
        except OSError:pass
        raise HTTPException(422,str(exc))
