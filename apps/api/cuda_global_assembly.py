from __future__ import annotations

def assemble_cuda_coo(element_dofs,element_matrices,ndof:int):
    """GPU sparse global assembly from batched element matrices/dof maps."""
    try:
        import cupy as cp
        import cupyx.scipy.sparse as csp
    except Exception as exc:raise RuntimeError("CuPy is required for CUDA global assembly") from exc
    dofs=cp.asarray(element_dofs,dtype=cp.int64);Ke=cp.asarray(element_matrices,dtype=cp.float64)
    if dofs.ndim!=2 or Ke.ndim!=3 or Ke.shape[1]!=dofs.shape[1] or Ke.shape[2]!=dofs.shape[1]:raise ValueError("incompatible element DOFs/matrices")
    ne,nloc=dofs.shape
    rows=cp.repeat(dofs[:,:,None],nloc,axis=2).reshape(-1)
    cols=cp.repeat(dofs[:,None,:],nloc,axis=1).reshape(-1)
    data=Ke.reshape(-1)
    A=csp.coo_matrix((data,(rows,cols)),shape=(int(ndof),int(ndof))).tocsr();A.sum_duplicates()
    return A

def cuda_assemble_and_solve(element_dofs,element_matrices,rhs,ndof:int,tol:float=1e-8,maxiter:int=2000):
    try:
        import cupy as cp
        import cupyx.scipy.sparse.linalg as spla
    except Exception as exc:raise RuntimeError("CuPy is required") from exc
    A=assemble_cuda_coo(element_dofs,element_matrices,ndof);b=cp.asarray(rhs,dtype=cp.float64)
    x,info=spla.cg(A,b,tol=tol,maxiter=maxiter)
    return cp.asnumpy(x),{"info":int(info),"nnz":int(A.nnz),"backend":"CUDA COO->CSR + CG"}
