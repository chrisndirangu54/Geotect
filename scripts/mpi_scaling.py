#!/usr/bin/env python3
import argparse,json,time,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"apps"/"api"))
from parallel_backends import mpi_partition

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--elements",type=int,default=100000);ap.add_argument("--repeats",type=int,default=3);ap.add_argument("--out",default="mpi-scaling.json");args=ap.parse_args()
    try:
        from mpi4py import MPI
        comm=MPI.COMM_WORLD;rank=comm.Get_rank();size=comm.Get_size()
    except Exception:
        comm=None;rank=0;size=1
    part=mpi_partition(args.elements);samples=[]
    import numpy as np
    for _ in range(args.repeats):
        t=time.perf_counter();n=part["count"];x=np.linspace(0,1,max(n,1));local=float(np.sum(np.sin(x)*np.cos(x)));elapsed=time.perf_counter()-t
        wall=comm.allreduce(elapsed,op=MPI.MAX) if comm else elapsed
        samples.append(wall)
    rec={"ranks":size,"elements":args.elements,"local_elements":part["count"],"wall_seconds":samples,"best_seconds":min(samples),"throughput_elements_s":args.elements/min(samples)}
    if rank==0:
        Path(args.out).write_text(json.dumps(rec,indent=2));print(json.dumps(rec))
if __name__=="__main__":main()
