# Nonlinear geomechanics solver

GeoTect now contains an incremental small-strain elastoplastic FEM path separate from the earlier linear/staggered baseline.

## Constitutive integration

### Mohr-Coulomb

The Mohr-Coulomb model uses:

- linear elastic predictor;
- exact Mohr-Coulomb shear-envelope target in p-q form;
- non-associated flow through a separate dilation angle;
- element-level plastic strain and accumulated equivalent plastic shear state;
- return mapping at each Newton iteration;
- numerically differentiated algorithmic tangent for global equilibrium.

### Hardening Soil

The GeoTect Hardening Soil implementation contains:

- E50, Eoed and Eur reference stiffnesses;
- stress-level stiffness dependency through power m;
- hyperbolic shear hardening;
- non-associated shear flow;
- an isotropic compression cap;
- volumetric hardening of preconsolidation pressure;
- persistent element history.

It follows the classical Hardening Soil architecture, but it is not claimed to be bit-for-bit equivalent to PLAXIS. Initial stress generation, surface smoothing, tensile cutoffs, small-strain stiffness and some cap/shear intersection details still require additional verification.

## Global nonlinear FEM

The 2D solver uses:

- constant-strain triangular elements;
- incremental loading;
- Newton-Raphson global equilibrium;
- element-level return mapping;
- numerical consistent/algorithmic tangent;
- line-step limiting;
- staged element activation/deactivation;
- stress/plastic-history transfer between stages;
- unilateral penalty contact against a support plane.

## Biot poroelasticity

A monolithic 1D u-p finite-element solver implements backward-Euler Biot consolidation with displacement/pore-pressure coupling. It provides a clean verification target before expanding the same mixed formulation into the 2D nonlinear mesh.

## Richards flow

The unsaturated solver implements the mixed Richards equation using:

- van Genuchten retention;
- Mualem relative permeability;
- backward Euler time integration;
- finite-volume spatial fluxes;
- Picard nonlinear iterations;
- rainfall/flux boundary;
- mass-balance tracking.

## Adaptive meshing

Plastic strain magnitude and local plastic-strain gradients produce element error indicators. Marked triangles can be locally refined by centroid subdivision, preserving shared-edge conformity because no hanging node is placed on an existing neighbor edge.

State projection onto a refined mesh is the next refinement step for fully automatic solve-refine-resolve cycles.

## Verification

The automated suite contains:

- Mohr-Coulomb local biaxial yield-envelope return-map check;
- 1D Biot/Terzaghi-style consolidation behavior;
- Richards mass-balance regression;
- FEM elastic-limit regression.

The benchmark catalog also provides importable comparison targets for published PLAXIS and GeoStudio verification problems. Commercial reference results are deliberately stored as external fixtures rather than copied into the solver, so a licensed reference run can be compared using `/api/v1/nonlinear/benchmarks/compare`.

## Engineering status

These solvers are engineering R&D implementations. Passing regression tests means the numerical implementation is behaving consistently against its selected benchmarks; it does not constitute regulatory certification or universal equivalence with PLAXIS, FLAC3D, Abaqus, GeoStudio or another commercial solver.
