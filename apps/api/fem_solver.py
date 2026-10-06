from __future__ import annotations
import numpy as np

def solve_linear_elasticity(width_m:float,height_m:float,nx:int,ny:int,young_pa:float,poisson:float,
                            density_kg_m3:float=2000.0,gravity_m_s2:float=9.81,top_pressure_pa:float=0.0)->dict:
    """2D plane-strain triangular FEM using scikit-fem."""
    try:
        from skfem import MeshTri,Basis,asm,solve,condense,ElementVector,ElementTriP1,LinearForm
        from skfem.models.elasticity import linear_elasticity,lame_parameters
        from skfem.helpers import dot
    except Exception as exc:
        raise RuntimeError("scikit-fem is required for FEM execution") from exc
    x=np.linspace(0,float(width_m),max(2,int(nx)))
    y=np.linspace(0,float(height_m),max(2,int(ny)))
    mesh=MeshTri.init_tensor(x,y)
    basis=Basis(mesh,ElementVector(ElementTriP1()))
    lam,mu=lame_parameters(float(young_pa),float(poisson))
    K=asm(linear_elasticity(lam,mu),basis)

    @LinearForm
    def body(v,w):
        return -float(density_kg_m3)*float(gravity_m_s2)*v[1]

    f=asm(body,basis)
    # Add distributed vertical pressure at the top edge.
    if top_pressure_pa:
        top=mesh.facets_satisfying(lambda X: np.isclose(X[1],float(height_m)))
        fb=basis.boundary(top)
        @LinearForm
        def pressure(v,w): return -float(top_pressure_pa)*v[1]
        f+=asm(pressure,fb)

    bottom=mesh.nodes_satisfying(lambda X: np.isclose(X[1],0.0))
    D=basis.get_dofs(nodes=bottom)
    u=solve(*condense(K,f,D=D))
    uv=u.reshape((-1,2))
    mag=np.linalg.norm(uv,axis=1)
    return {
      "nodes_m":mesh.p.T.tolist(),"triangles":mesh.t.T.tolist(),
      "displacement_m":uv.tolist(),"displacement_magnitude_m":mag.tolist(),
      "max_displacement_m":float(mag.max()) if mag.size else 0.0,
      "method":"2D linear-elastic plane-strain triangular FEM (scikit-fem)",
      "status":"solved","assumptions":["small strain","isotropic linear elasticity","2D plane strain"]
    }
