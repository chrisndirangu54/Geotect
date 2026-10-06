# Scientific validation and HPC maturity

GeoTect now separates native research formulations from external reference engines.

When OpenSees is installed, GeoTect can execute PM4Sand, 3D Manzari-Dafalias, and SANISAND-MS/SAniSandMS reference models. These adapters are for regression and calibration; they do not make the native research formulations equivalent to those reference implementations.

The dynamic 3D HEX8 u-p solver includes inertia, Newmark integration, pore-pressure coupling, base acceleration, Rayleigh damping, and Lysmer-style absorbing dashpots.

Fracture support includes an AT2 staggered phase-field solver and an XFEM Heaviside enrichment mapper. Nonlinear 3D THM uses tetrahedral u-p-T assembly with temperature-dependent stiffness and permeability.

The optional PETSc path supports displacement/pressure field splitting with Schur-complement preconditioning. MPI scaling scripts measure synchronized wall time, speedup, and parallel efficiency on a real MPI runtime. CUDA support includes batched constitutive integration, element stiffness kernels, sparse global COO/CSR assembly, and GPU sparse solving.

Experimental validation is dataset-driven. The catalog includes CENSEIS, FLIQ, PRESHAKE, LEAP, and NGL sources. GeoTect does not silently redistribute dataset bytes; source-authorized files can be ingested and compared using RMSE, MAE, bias, R², and peak-response error.
