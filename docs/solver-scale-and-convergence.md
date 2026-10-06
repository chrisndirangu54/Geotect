# Coupled nonlinear solver scale and convergence

GeoTect now includes a second-generation geomechanics path focused on fully coupled nonlinear execution.

## 2D monolithic u-p formulation

The 2D solver uses three nodal unknowns:

- horizontal displacement u_x;
- vertical displacement u_y;
- pore pressure p.

The Newton matrix contains K_uu, K_up, K_pu and K_pp blocks assembled on the same triangular mesh. The mechanical block obtains its tangent from the active elastoplastic material model. The hydraulic block uses Darcy flow, storage and pressure-head gradients.

For unsaturated states, van Genuchten-Mualem retention/permeability is evaluated inside every Newton iteration. Bishop effective stress weighting is represented as chi = Se^beta and contributes to the mechanical pore-pressure coupling.

This is materially different from running a flow analysis first and applying pore pressures later: displacement and pressure are solved together.

## Interfaces

GeoTect now includes a Coulomb interface law with:

- normal penalty stiffness;
- shear penalty stiffness;
- opening/contact logic;
- cohesion;
- friction angle;
- dilation angle;
- stick/slip return mapping;
- accumulated plastic slip;
- consistent local tangent contribution.

These elements provide the base for soil-structure, lining-ground, foundation-ground and discontinuity interfaces.

## Arc-length continuation

A Crisfield-style spherical arc-length solver is included for equilibrium paths that cannot be followed by ordinary load control. The regression problem is a scalar snap-through/snap-back nonlinear equilibrium problem.

The continuation engine is separated from the geotechnical residual assembly so it can be attached to footing collapse, slope instability or structural-ground models without duplicating continuation logic.

## Sparse, parallel and GPU execution

Assembly uses sparse COO/CSR matrices. Linear solves support:

- SciPy sparse direct solve;
- GMRES;
- BiCGSTAB;
- CG where appropriate;
- optional CuPy/CUDA sparse CG when CuPy is installed and GPU execution is enabled.

Element assembly can use a thread pool on larger meshes. GPU support is optional rather than a mandatory dependency so CPU deployments remain reproducible.

## Automatic adaptivity

The elastoplastic solver now supports:

solve -> estimate plastic-strain error -> mark -> locally refine -> project displacement/history -> resolve.

Plastic strain magnitude and local gradients drive marking. Child elements inherit parent constitutive history, while newly inserted centroid-node displacement is interpolated from the parent element.

## Verification and convergence

The benchmark system distinguishes:

1. analytical verification;
2. manufactured/regression verification;
3. published commercial-solver cross-checks;
4. project-specific validation.

Automated studies estimate observed convergence order from successive mesh or time-step refinements.

Current benchmark families include:

- Mohr-Coulomb biaxial return mapping;
- elastic-limit FEM;
- Biot/Terzaghi consolidation;
- Richards mass balance and time-step refinement;
- monolithic u-p smoke matrices;
- arc-length snap-through;
- PLAXIS Biot and Hardening Soil comparison fixtures;
- GeoStudio footing comparison fixtures.

Passing these tests is a numerical verification milestone, not regulatory certification or proof of equivalence to a proprietary solver.
