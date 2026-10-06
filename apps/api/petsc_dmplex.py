from __future__ import annotations
import numpy as np

def create_distributed_box(dim:int=3,faces:list[int]|None=None,simplex:bool=True):
    try:
        from petsc4py import PETSc
    except Exception as exc:raise RuntimeError("petsc4py is required for DMPlex distribution") from exc
    faces=faces or ([4,4,4] if dim==3 else [8,8])
    dm=PETSc.DMPlex().createBoxMesh(faces=faces,simplex=simplex,comm=PETSc.COMM_WORLD)
    dm.setName("GeoTectDMPlex")
    distributed=dm.distribute(overlap=1)
    if distributed is not None:dm=distributed
    cStart,cEnd=dm.getHeightStratum(0);vStart,vEnd=dm.getDepthStratum(0)
    return dm,{"dimension":dim,"cells_local":cEnd-cStart,"vertices_local":vEnd-vStart,"rank":PETSc.COMM_WORLD.getRank(),"size":PETSc.COMM_WORLD.getSize()}

def partition_numpy_tets(nodes,tets):
    try:
        from petsc4py import PETSc
    except Exception as exc:raise RuntimeError("petsc4py is required") from exc
    nodes=np.asarray(nodes,float);tets=np.asarray(tets,int)
    # petsc4py API varies; createFromCellList supports collective mesh creation.
    dm=PETSc.DMPlex().createFromCellList(3,tets,nodes,comm=PETSc.COMM_WORLD)
    distributed=dm.distribute(overlap=1)
    if distributed is not None:dm=distributed
    cStart,cEnd=dm.getHeightStratum(0)
    return {"rank":PETSc.COMM_WORLD.getRank(),"size":PETSc.COMM_WORLD.getSize(),"local_cells":cEnd-cStart,"dm_name":dm.getName()}

def domain_decomposition_metadata(dm):
    from petsc4py import PETSc
    # expose ownership ranges and local/global sizes through section/vector layout
    g=dm.createGlobalVector();l=dm.createLocalVector()
    return {"rank":PETSc.COMM_WORLD.getRank(),"size":PETSc.COMM_WORLD.getSize(),"global_size":g.getSize(),"local_size":l.getLocalSize(),"ownership_range":g.getOwnershipRange()}
