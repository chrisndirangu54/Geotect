from __future__ import annotations
import numpy as np

def solve_fieldsplit_schur(A,b,displacement_dofs:list[int],pressure_dofs:list[int],rtol:float=1e-8,max_it:int=2000,
                           schur_precondition:str="a11",schur_fact:str="full",u_pc:str="hypre",p_pc:str="jacobi"):
    """PETSc FieldSplit Schur solver for u-p block systems."""
    from petsc4py import PETSc
    import scipy.sparse as sp
    csr=sp.csr_matrix(A);mat=PETSc.Mat().createAIJ(size=csr.shape,csr=(csr.indptr,csr.indices,csr.data));mat.assemble()
    rhs=PETSc.Vec().createWithArray(np.asarray(b,float));x=rhs.duplicate();x.set(0)
    ksp=PETSc.KSP().create();ksp.setOperators(mat);ksp.setType("gmres")
    pc=ksp.getPC();pc.setType(PETSc.PC.Type.FIELDSPLIT)
    is_u=PETSc.IS().createGeneral(displacement_dofs,comm=PETSc.COMM_WORLD);is_p=PETSc.IS().createGeneral(pressure_dofs,comm=PETSc.COMM_WORLD)
    pc.setFieldSplitIS(("u",is_u),("p",is_p))
    pc.setFieldSplitType(PETSc.PC.CompositeType.SCHUR)
    fact_map={"diag":PETSc.PC.SchurFactType.DIAG,"lower":PETSc.PC.SchurFactType.LOWER,"upper":PETSc.PC.SchurFactType.UPPER,"full":PETSc.PC.SchurFactType.FULL}
    pc.setFieldSplitSchurFactType(fact_map.get(schur_fact,PETSc.PC.SchurFactType.FULL))
    pre_map={"self":PETSc.PC.SchurPreType.SELF,"selfp":PETSc.PC.SchurPreType.SELFP,"a11":PETSc.PC.SchurPreType.A11,"full":PETSc.PC.SchurPreType.FULL}
    pc.setFieldSplitSchurPreType(pre_map.get(schur_precondition,PETSc.PC.SchurPreType.A11))
    ksp.setTolerances(rtol=rtol,max_it=max_it);ksp.setUp()
    sub=pc.getFieldSplitSubKSP()
    if len(sub)>=2:
        sub[0].getPC().setType(u_pc);sub[1].getPC().setType(p_pc)
    ksp.solve(rhs,x)
    return x.getArray(readonly=True).copy(),{"iterations":ksp.getIterationNumber(),"reason":int(ksp.getConvergedReason()),
      "residual_norm":ksp.getResidualNorm(),"pc":"fieldsplit-schur","schur_fact":schur_fact,"schur_precondition":schur_precondition}
