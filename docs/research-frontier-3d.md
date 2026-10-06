# Research frontier: 3D, liquefaction, remeshing and distributed execution

GeoTect now includes an explicitly research-grade 3D computational branch alongside the verified 2D production-oriented solver paths.

## 3D u-p finite elements

Two monolithic displacement-pore-pressure formulations are available:

- four-node tetrahedral u-p elements generated from structured hexahedral grids;
- true HEX8 u-p elements using 2x2x2 Gauss integration.

Both use three displacement components plus pore pressure at each node and assemble mechanical, hydraulic and Biot coupling blocks into a sparse Newton system.

## Dynamic effective-stress liquefaction research model

GeoTect includes a cyclic effective-stress sand model inspired by concepts used by PM4Sand and UBCSAND:

- density-dependent cyclic response;
- effective-stress-dependent shear stiffness;
- contraction and dilation;
- evolving backstress;
- fabric evolution;
- cyclic strain accumulation;
- generated pore-pressure ratio.

This implementation is deliberately named a *PM4Sand/UBCSAND-style research formulation*. It is not the PM4Sand reference implementation and is not claimed to reproduce UBCSAND exactly. PM4Sand has a much richer calibrated state-parameter/fabric-dilatancy formulation and should be cross-checked against the published model/reference implementation before engineering use.

## Anisotropic critical-state plasticity

The 3D material library also contains an anisotropic critical-state model with:

- pressure-dependent yield surface;
- critical-state stress ratio;
- volumetric hardening;
- evolving preconsolidation pressure;
- kinematic anisotropy/backstress.

It provides a research foundation for SANISAND-like and anisotropic modified Cam-Clay developments.

## Nonlocal softening

Local accumulated plastic strain can be regularized with a Gaussian nonlocal kernel and physical length scale. Strength degradation then uses the nonlocal variable rather than raw element-local plastic strain, reducing mesh dependence in strain-softening experiments.

## Fracture/contact remeshing

Damage-marked triangles can be split across their longest edge. The remesher emits explicit fracture/contact-interface metadata so a newly created discontinuity can subsequently receive contact/cohesive behavior.

This is a topology-remeshing baseline, not yet a full XFEM or phase-field fracture solver.

## Thermo-hydro-mechanical coupling

A 1D THM baseline couples:

- transient heat conduction;
- hydraulic diffusion;
- thermal strain;
- Biot hydraulic strain.

It provides verification infrastructure before extending temperature and fluid coupling into the nonlinear 2D/3D finite-element blocks.

## Distributed PETSc execution

The optional PETSc layer now uses DMPlex rather than synthetic rank slicing. It can create/distribute unstructured simplex/tensor meshes, distribute a numpy tetrahedral mesh across MPI ranks, and expose local/global ownership metadata.

PETSc documents DMPlex as its dimension-independent unstructured-grid abstraction with distributed mesh ownership, repartitioning and domain-decomposition support.

## GPU constitutive integration

The optional CuPy backend includes:

- batched Mohr-Coulomb elastic predictor/yield projection;
- batched CST stiffness assembly;
- sparse GPU solve support from the previous solver release.

The CUDA path is optional so ordinary CPU CI remains deterministic.

## Verification status

These models are research implementations. Their presence in GeoTect does not imply regulatory validation or equivalence with PM4Sand, UBCSAND, SANISAND, PLAXIS, FLAC3D, Abaqus or OpenSees.

Required next validation work includes single-element cyclic tests, centrifuge/shake-table benchmarks, 3D consolidation benchmarks, mesh-objectivity studies, fracture-energy regularization checks and multi-rank PETSc scaling studies.
