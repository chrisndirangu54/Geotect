#!/usr/bin/env python3
import json,time,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"apps"/"api"))
import numpy as np
from parallel_backends import cuda_cst_stiffness_batch
from verification_campaigns import compare_cpu_gpu

def main():
    n=2000
    nodes=np.zeros((n,3,2));nodes[:,0]=[0,0];nodes[:,1]=[1,0];nodes[:,2]=[0,1]
    E=30000.;nu=.3;lam=E*nu/((1+nu)*(1-2*nu));mu=E/(2*(1+nu));D=np.array([[lam+2*mu,lam,0],[lam,lam+2*mu,0],[0,0,mu]])
    t=time.perf_counter();Kcpu=[]
    for _ in range(n):
        A=.5;b=np.array([-1,1,0]);c=np.array([-1,0,1]);B=np.zeros((3,6))
        for i in range(3):B[0,2*i]=b[i];B[1,2*i+1]=c[i];B[2,2*i]=c[i];B[2,2*i+1]=b[i]
        Kcpu.append(B.T@D@B*A)
    cpu_s=time.perf_counter()-t;Kcpu=np.asarray(Kcpu)
    out={"elements":n,"cpu_seconds":cpu_s}
    try:
        t=time.perf_counter();Kgpu,_=cuda_cst_stiffness_batch(nodes,E,nu);gpu_s=time.perf_counter()-t
        out.update({"gpu_available":True,"gpu_seconds":gpu_s,"speedup":cpu_s/gpu_s,"accuracy":compare_cpu_gpu(Kcpu,Kgpu)})
    except Exception as e:
        out.update({"gpu_available":False,"gpu_error":str(e)})
    Path("gpu-cpu-matrix.json").write_text(json.dumps(out,indent=2));print(json.dumps(out))
if __name__=="__main__":main()
