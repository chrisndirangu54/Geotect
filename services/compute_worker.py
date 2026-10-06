from __future__ import annotations
import asyncio,traceback
from datetime import datetime,timezone
from sqlalchemy import select
from db import SessionLocal
from platform_models import ComputeJob
from probabilistic import monte_carlo_slope
from design_tools import bearing_capacity,elastic_settlement,retaining_wall,pile_capacity,liquefaction_screening
from investigation import recommend_locations
from groundwater_pde import solve_steady_groundwater
from ert_inversion import invert_ert
from seismic_volume import reconstruct_volume
from advanced_engineering import transient_diffusion,newmark_sliding,consolidation_time,inverse_velocity_failure,coupled_hydro_mechanical
from calibration import calibrate_scalar
from nonlinear_coupled import solve_staggered_hm,benchmark_suite
from elastoplastic_fem import solve_elastoplastic_2d,staged_excavation
from biot_solver import solve_biot_1d
from richards_solver import solve_richards_1d
from solver_benchmarks import suite as nonlinear_benchmark_suite
from coupled_up_fem import solve_monolithic_up_2d
from elastoplastic_fem import solve_adaptive_elastoplastic
from convergence_studies import full_matrix
from quadratic_up_fem import solve_quadratic_up_2d
from updated_lagrangian_fem import solve_updated_lagrangian_2d
from strength_reduction import strength_reduction_search
from verification_dashboard import write_dashboard

HANDLERS={
 "monte_carlo_slope":lambda p:monte_carlo_slope(**p),
 "bearing_capacity":lambda p:bearing_capacity(**p),
 "settlement":lambda p:elastic_settlement(**p),
 "retaining_wall":lambda p:retaining_wall(**p),
 "pile_capacity":lambda p:pile_capacity(**p),
 "liquefaction":lambda p:liquefaction_screening(**p),
 "investigation_recommend":lambda p:recommend_locations(p.get("candidates",[]),p.get("observations",[]),int(p.get("count",5)),float(p.get("min_spacing_m",50))),
 "groundwater_pde":lambda p:solve_steady_groundwater(**p),
 "ert_inversion":lambda p:invert_ert(**p),
 "seismic_reconstruction":lambda p:reconstruct_volume(**p),
 "transient_groundwater":lambda p:transient_diffusion(**p),
 "newmark_sliding":lambda p:newmark_sliding(**p),
 "consolidation":lambda p:consolidation_time(**p),
 "inverse_velocity":lambda p:inverse_velocity_failure(**p),
 "hydro_mechanical":lambda p:coupled_hydro_mechanical(**p),
 "calibrate_scalar":lambda p:calibrate_scalar(**p),
 "nonlinear_hm":lambda p:solve_staggered_hm(**p),
 "solver_benchmarks":lambda p:benchmark_suite(),
 "elastoplastic_fem":lambda p:solve_elastoplastic_2d(**p),
 "staged_elastoplastic":lambda p:staged_excavation(p.get("base",{}),p.get("stages",[])),
 "biot_1d":lambda p:solve_biot_1d(**p),
 "richards_1d":lambda p:solve_richards_1d(**p),
 "nonlinear_benchmarks":lambda p:nonlinear_benchmark_suite(),
 "monolithic_up_2d":lambda p:solve_monolithic_up_2d(**p),
 "adaptive_elastoplastic":lambda p:solve_adaptive_elastoplastic(p.get("base",{}),int(p.get("cycles",2)),float(p.get("refine_fraction",.2))),
 "convergence_matrix":lambda p:full_matrix(),
 "quadratic_up_2d":lambda p:solve_quadratic_up_2d(**p),
 "updated_lagrangian_2d":lambda p:solve_updated_lagrangian_2d(**p),
 "strength_reduction":lambda p:strength_reduction_search(p.get("base",{}),float(p.get("min_factor",1)),float(p.get("max_factor",5)),float(p.get("tolerance",.02)),int(p.get("max_iter",12)),p.get("displacement_limit_m")),
 "verification_dashboard":lambda p:write_dashboard(p.get("output_dir","/tmp/geotect-verification"),p.get("version"),p.get("commit_sha"))
}

async def run_once():
    async with SessionLocal() as s:
        q=await s.execute(select(ComputeJob).where(ComputeJob.status=="queued").order_by(ComputeJob.created_at).limit(1))
        job=q.scalar_one_or_none()
        if not job:return False
        job.status="running";job.progress=.05;job.updated_at=datetime.now(timezone.utc);await s.commit()
        handler=HANDLERS.get(job.job_type)
        if not handler:
            job.status="failed";job.output={"error":f"Unsupported job_type {job.job_type}"};job.progress=1;await s.commit();return True
        try:
            result=await asyncio.to_thread(handler,job.input)
            job.status="completed";job.output=result;job.progress=1
        except Exception as exc:
            job.status="failed";job.output={"error":str(exc),"trace":traceback.format_exc(limit=3)};job.progress=1
        job.updated_at=datetime.now(timezone.utc);await s.commit();return True

async def main():
    while True:
        worked=await run_once()
        if not worked:await asyncio.sleep(2)

if __name__=="__main__":asyncio.run(main())
