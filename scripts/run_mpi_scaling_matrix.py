#!/usr/bin/env python3
import argparse,json,subprocess,shutil
from pathlib import Path
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--ranks",default="2,4,8,16,32");ap.add_argument("--elements",type=int,default=200000);ap.add_argument("--out",default="mpi-scaling-matrix.json");args=ap.parse_args()
    mpiexec=shutil.which("mpiexec") or shutil.which("mpirun")
    if not mpiexec:raise SystemExit("mpiexec/mpirun not found")
    rows=[];base=None
    for n in [int(x) for x in args.ranks.split(",")]:
        tmp=f".mpi-{n}.json"
        subprocess.check_call([mpiexec,"-n",str(n),"python","scripts/mpi_scaling.py","--elements",str(args.elements),"--out",tmp])
        rec=json.loads(Path(tmp).read_text());Path(tmp).unlink(missing_ok=True)
        if base is None:base=rec["best_seconds"]*n
        rec["speedup"]=base/rec["best_seconds"];rec["parallel_efficiency"]=rec["speedup"]/n;rows.append(rec)
    Path(args.out).write_text(json.dumps({"runs":rows},indent=2));print(json.dumps({"runs":rows}))
if __name__=="__main__":main()
