from __future__ import annotations
import os,numpy as np

def petsc_available()->dict:
    try:
        import petsc4py
        from petsc4py import PETSc
        return {"available":True,"version":PETSc.Sys.getVersion(),"scalar_type":str(PETSc.ScalarType)}
    except Exception as exc:return {"available":False,"reason":str(exc)}

def solve_petsc(A,b,ksp_type:str="gmres",pc_type:str="hypre",rtol:float=1e-8,max_it:int=2000):
    from petsc4py import PETSc
    import scipy.sparse as sp
    csr=sp.csr_matrix(A);n=csr.shape[0]
    mat=PETSc.Mat().createAIJ(size=csr.shape,csr=(csr.indptr,csr.indices,csr.data));mat.assemble()
    rhs=PETSc.Vec().createWithArray(np.asarray(b,dtype=float));x=rhs.duplicate();x.set(0)
    ksp=PETSc.KSP().create();ksp.setOperators(mat);ksp.setType(ksp_type);ksp.getPC().setType(pc_type);ksp.setTolerances(rtol=rtol,max_it=max_it);ksp.setFromOptions();ksp.solve(rhs,x)
    arr=x.getArray(readonly=True).copy()
    return arr,{"backend":"petsc","ksp_type":ksp.getType(),"pc_type":ksp.getPC().getType(),"iterations":ksp.getIterationNumber(),"reason":int(ksp.getConvergedReason()),"residual_norm":ksp.getResidualNorm()}

def mpi_partition(count:int)->dict:
    try:
        from mpi4py import MPI
        comm=MPI.COMM_WORLD;rank=comm.Get_rank();size=comm.Get_size()
    except Exception:
        rank=0;size=1
    start=(count*rank)//size;end=(count*(rank+1))//size
    return {"rank":rank,"size":size,"start":start,"end":end,"count":max(0,end-start)}

def mpi_allreduce_sum(array):
    try:
        from mpi4py import MPI
        out=np.zeros_like(array);MPI.COMM_WORLD.Allreduce(np.asarray(array),out,op=MPI.SUM);return out
    except Exception:return np.asarray(array)

def cuda_element_energy(strains,stiffness):
    """Optional CUDA kernel for batched 3-component strain energy."""
    try:
        import cupy as cp
    except Exception as exc:raise RuntimeError("CuPy is required for CUDA element kernels") from exc
    e=cp.asarray(strains,dtype=cp.float64);C=cp.asarray(stiffness,dtype=cp.float64)
    if e.ndim!=2 or e.shape[1]!=3:raise ValueError("strains must be [n,3]")
    stress=e@C.T
    energy=.5*cp.sum(e*stress,axis=1)
    return cp.asnumpy(stress),cp.asnumpy(energy)

def execution_capabilities()->dict:
    caps={"cpu_sparse":True,"petsc":petsc_available()}
    try:
        import mpi4py
        caps["mpi"]=True
    except Exception:caps["mpi"]=False
    try:
        import cupy as cp
        caps["cuda"]=True;caps["cuda_devices"]=int(cp.cuda.runtime.getDeviceCount())
    except Exception:caps["cuda"]=False
    return caps


def cuda_cst_stiffness_batch(nodes_batch,young_kpa:float,nu:float):
    """Batched CST element stiffness assembly on CUDA with CuPy."""
    try:
        import cupy as cp
    except Exception as exc:raise RuntimeError("CuPy is required for CUDA element kernels") from exc
    x=cp.asarray(nodes_batch,dtype=cp.float64)
    if x.ndim!=3 or x.shape[1:]!=(3,2):raise ValueError("nodes_batch must have shape [n,3,2]")
    x1,y1=x[:,0,0],x[:,0,1];x2,y2=x[:,1,0],x[:,1,1];x3,y3=x[:,2,0],x[:,2,1]
    area=.5*((x2-x1)*(y3-y1)-(x3-x1)*(y2-y1))
    if bool(cp.any(area<=0)):raise ValueError("non-positive element area")
    b=cp.stack([y2-y3,y3-y1,y1-y2],axis=1);cc=cp.stack([x3-x2,x1-x3,x2-x1],axis=1)
    B=cp.zeros((x.shape[0],3,6),dtype=cp.float64)
    for i in range(3):
        B[:,0,2*i]=b[:,i];B[:,1,2*i+1]=cc[:,i];B[:,2,2*i]=cc[:,i];B[:,2,2*i+1]=b[:,i]
    B/=2*area[:,None,None]
    lam=young_kpa*nu/((1+nu)*(1-2*nu));mu=young_kpa/(2*(1+nu))
    D=cp.asarray([[lam+2*mu,lam,0],[lam,lam+2*mu,0],[0,0,mu]],dtype=cp.float64)
    DB=cp.einsum("ij,ejk->eik",D,B)
    K=cp.einsum("eji,ejk->eik",B,DB)*area[:,None,None]
    return cp.asnumpy(K),cp.asnumpy(area)
