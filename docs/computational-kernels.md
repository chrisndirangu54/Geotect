# Computational kernels

## ERT inversion

`ert_inversion.py` solves a regularized inverse system in log-resistivity space. The inversion accepts a sensitivity/Jacobian matrix whose rows correspond to measurements and columns to model cells. A first-difference smoothness operator regularizes adjacent cells. Iteration history exposes log-domain RMS and model-update norm.

This separates **survey forward physics** from the reusable inversion core. A production ERT worker can calculate the Jacobian with pyGIMLi, SimPEG or a validated vendor engine and call the same inversion/output contract.

## Seismic volume reconstruction

`seismic_volume.py` accepts positioned traces, interpolates amplitudes across an x-y grid using inverse-distance weighting, and converts two-way travel time to depth using the supplied propagation velocity. It yields a true 3D amplitude cube.

For reflection surveys, production extensions should add velocity models, NMO, stacking, migration and survey geometry.

## Groundwater PDE

`groundwater_pde.py` solves the steady heterogeneous equation

`div(K grad h) = 0`

on a regular 2D grid using finite differences. Left/right heads are Dirichlet boundaries and top/bottom can be no-flow boundaries. The solver returns head, x/y Darcy flux, convergence state and residual.

## FEM

`fem_solver.py` uses scikit-fem triangular elements for a 2D linear-elastic plane-strain problem. The current executable model includes:

- Young's modulus and Poisson ratio;
- density/gravity body force;
- optional top pressure;
- fixed basal boundary;
- nodal displacement vectors and magnitudes.

Future constitutive plugins should preserve the solver metadata contract and add Mohr-Coulomb, Hoek-Brown, Modified Cam Clay, staged excavation, pore-pressure coupling and dynamic loading only after benchmark validation.

## Geological solids

`geology_solids.py` creates a closed triangulated prism from a geodetic footprint and top/bottom elevations. In the CAD client, interpreted polygons can also be visually extruded for interactive editing.

## LAS/LAZ tiling

`las_tiler.py` loads LAS/LAZ data with laspy/lazrs, spatially partitions points into 3D grid cells, chunks cells to a bounded point count and writes compressed NPZ point tiles plus a manifest. The API packages these as a downloadable ZIP.

A future cloud-scale renderer can translate this manifest into OGC 3D Tiles / point-cloud streaming without changing the source ingestion workflow.

## Safety and validation

Each numerical output exposes its method and assumptions. GeoTect does not equate an executable model with a regulator-approved or signed design. Project governance should define which solver/version/material model is allowed for each engineering decision.
