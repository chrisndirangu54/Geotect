# Industrial validation and scale

GeoTect's production validation layer adds:
- official DIGGS 3.0 bundle-based XML/XSD validation;
- persisted STAC API collections/items/search;
- persisted SensorThings-style Things/Datastreams/Observations;
- Redis-backed distributed request rate limiting with local fallback;
- S3-compatible presigned upload/download and HTTP byte-range access for COPC/E57-scale objects;
- X.509 detached-signature verification and external HTTPS PKI signing-provider hooks;
- a staggered nonlinear hydro-mechanical solver combining groundwater, stress-dependent stiffness/permeability and FEM;
- solver benchmark cases for linear groundwater head, elastic modulus scaling and coupled-solver smoke regression;
- background worker support for nonlinear HM and benchmark jobs.

## DIGGS

The official v3.0.0 release archive is downloaded from the DIGGS GitHub release/tag path, safely extracted, and validated using the real multi-file XSD bundle with local include/import resolution. XML entities and network schema resolution are disabled during validation.

## STAC and SensorThings

The API persists STAC Collections/Items and SensorThings-style Things, Datastreams and Observations in PostgreSQL. The current implementation covers core GeoTect production workflows; full external certification against every STAC API or OGC SensorThings conformance class should be handled through conformance test suites and, where required, federation with a certified implementation.

## Distributed runtime

Redis provides cross-instance rate counters. MinIO provides a development S3-compatible object store and initializes a private `geotect` bucket. Production deployments may replace MinIO with AWS S3, Google-compatible gateways or another S3-compatible service.

## PKI

GeoTect can verify RSA/ECDSA X.509 detached signatures and can delegate signing of release digests to an external HTTPS signing service whose token is stored in the encrypted secret vault. This supports HSM/KMS/e-signature providers without embedding private keys in GeoTect.

## Solver benchmarks

The nonlinear HM solver is intentionally explicit about assumptions. It is a staggered Picard-style coupling of steady saturated groundwater, stress-dependent stiffness/permeability and small-strain isotropic FEM. It is not yet a replacement for a validated nonlinear constitutive FE platform. The benchmark suite is intended to catch regressions and establish reproducible solver behavior before higher-fidelity constitutive/coupled formulations are introduced.
