# GeoTect open standards, governance, field and enterprise layer

This layer turns GeoTect into a standards-aware ground-engineering information backbone.

## Open standards

Implemented baseline contracts and endpoints include:

- DIGGS 3.0 canonical export model;
- AGS-to-GeoTect borehole interval crosswalk;
- IFC 4.3 geotechnical manifests for boreholes, strata, cuts and fills;
- IFC IDS-style requirement validation;
- STAC Item and Catalog generation for Earth-observation assets;
- OGC SensorThings-compatible observation payloads;
- BCF issue payloads and openCDE-style document containers;
- GeoParquet export;
- Zarr array export;
- COPC inspection through laspy;
- E57 exchange manifests.

Binary or schema-heavy formats are deliberately separated into canonical contracts plus serializers/validators so official schemas can be upgraded without changing GeoTect's internal project model.

## Advanced engineering

Executable design-support kernels now include:

- Mohr-Coulomb shear strength;
- Hoek-Brown rock strength;
- Hardening-Soil stress-dependent stiffness baseline;
- Modified Cam Clay yield check;
- Biot effective-stress hydro-mechanical coupling;
- transient groundwater diffusion;
- unsaturated rainfall-infiltration screening;
- one-dimensional consolidation settlement versus time;
- Newmark sliding-block seismic displacement;
- discontinuity-set wedge screening;
- rock-mass classification proxies;
- convergence-confinement tunnel response;
- tailings freeboard;
- inverse-velocity failure forecasting;
- pile-group efficiency screening.

These remain transparent engineering-support methods. More advanced nonlinear FEM, fully coupled Richards/Biot formulations and jurisdiction-specific design checks should be added as validated solver plugins rather than hidden behind generic labels.

## Engineering AI

GeoTect now exposes:

- discipline agent routing for geology, hydrogeology, geophysics, geotechnical engineering, monitoring and reporting;
- evidence-grounded recommendation envelopes;
- anomaly detection;
- root-cause ranking;
- model-selection assistance;
- scalar model calibration against monitoring observations.

AI outputs explicitly carry evidence references and confidence.

## Governance

Project governance includes:

- design-basis records;
- assumption register;
- risk register linked to model objects;
- RFI/NCR/general engineering issues;
- BCF/openCDE-compatible issue/document views;
- immutable released-revision SHA-256 digests;
- account-attestation signatures tied to a release digest.

Account attestation is not represented as a statutory engineer's digital seal. External PKI/e-signature providers can be plugged in where legally required.

## Field operations

The web client includes an installable/offline field console with:

- service-worker caching;
- offline queue and later synchronization;
- browser GNSS capture;
- browser speech-to-text notes when supported;
- camera/video attachment selection;
- Web Bluetooth discovery when supported;
- sample creation with QR/RFID identifiers;
- sample chain-of-custody transfers;
- instrument calibration records and expiry status.

## Enterprise controls

Enterprise policy records cover:

- Firebase/OIDC/SAML mode configuration;
- SAML metadata;
- SCIM provisioning endpoints;
- data-residency policy;
- customer-managed encryption-key references;
- API rate-limit policy;
- retention policy;
- marketplace/plugin records.

GeoTect also includes a global request-rate limiter. Tenant-specific quotas continue through the usage ledger and billing/quota layer.

## Background compute

Advanced groundwater, seismic, consolidation, Newmark, hydro-mechanical and calibration jobs can be queued to the existing compute worker.

## Production follow-ups

The largest remaining depth items are solver validation suites, formal official-schema XML serializers/validators, external PKI signatures, distributed rate limiting, production object-storage STAC catalogs, and cloud-native COPC/E57 streaming.
