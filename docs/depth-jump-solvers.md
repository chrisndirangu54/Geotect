# GeoTect solver depth jump

This release adds the next numerical-computing layer without removing the previously verified first-order solvers.

## Higher-order mixed elements

GeoTect now includes P2 displacement / P1 pressure triangular elements. Six-node quadratic displacement interpolation and three-node linear pressure interpolation are assembled into a monolithic u-p system. A pressure-stabilization operator is also available for mixed-order experiments and nearly incompressible regimes.

## Updated-Lagrangian mechanics

A large-deformation solver updates nodal geometry after each nonlinear increment and assembles both material and geometric stiffness. It uses the existing elastoplastic constitutive state, so geometric and material nonlinearity can coexist.

## Strength reduction

The nonlinear FEM can now be wrapped in phi-c strength reduction. Cohesion and tan(phi) are reduced by a trial factor, equilibrium is solved, and a bisection search brackets the loss-of-equilibrium/displacement-limit factor of safety.

## Cyclic and dynamic mechanics

A Hardin-Drnevich backbone with Masing unloading/reloading provides a transparent cyclic soil model baseline. Newmark-beta average-acceleration integration provides a dynamic SDOF reference path for validating time integration before full dynamic finite elements are introduced.

## Contact

The existing 2D interface law is complemented by a 3D point-to-triangle Coulomb contact law with normal penalty, tangential stiffness, cohesion, friction and plastic slip.

## HPC execution

The standard sparse backend remains SciPy. Optional execution layers now include:

- PETSc KSP with configurable KSP and preconditioner type;
- mpi4py rank partitioning and reductions;
- CuPy GPU sparse solves;
- CuPy batched CST element stiffness kernels;
- threaded element assembly in the monolithic u-p solver.

PETSc, MPI and CUDA dependencies are intentionally optional and are not installed into ordinary CPU CI.

## Verification publishing

Each CI run can generate a static verification site containing benchmark status, numerical metrics, observed convergence rates and detected solver capabilities. The site is uploaded as a GitHub Actions artifact. It can be deployed unchanged to GitHub Pages or any static host.

## Verification status

These additions increase numerical depth but do not make GeoTect a certified solver. Published analytical references, mesh/time convergence, independent commercial cross-checks and project-specific validation remain required for engineering sign-off.
