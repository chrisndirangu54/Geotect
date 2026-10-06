# Vendor integrations

GeoTect uses two integration patterns:

1. **Cloud REST connectors** for products that expose supported web APIs.
2. **Local bridge agents** for desktop applications whose automation APIs run on the user's workstation.

Secrets are not stored in connection records. Cloud credentials are stored in the encrypted GeoTect API-secret vault. Desktop bridge tokens are shown once; only a SHA-256 hash is retained.

## Esri ArcGIS

GeoTect supports ArcGIS Feature Service discovery, queries and edits through the ArcGIS REST API.

Typical configuration:

- provider: `esri_arcgis`
- base URL: FeatureServer or layer URL
- encrypted secret provider: `esri_arcgis`
- secret name: `access_token`

Implemented calls:

- service information;
- layer query;
- `applyEdits` for adds, updates and deletes.

ArcGIS Enterprise deployments on private networks should use a colocated GeoTect worker or an explicitly approved network path instead of opening a generic private-address proxy.

## Seequent Evo / Leapfrog-connected workflows

Seequent Evo is the API-facing integration layer for connected subsurface workflows. GeoTect supports:

- Evo service discovery;
- Geoscience Object API requests;
- Block Model API requests;
- File and workspace services;
- compute/geostatistics/geophysics/geotechnical task endpoints when exposed by the user's Evo tenant.

Credentials are OAuth access tokens stored in the encrypted secret vault.

GeoTect does not claim direct control of every Leapfrog desktop UI function. Instead it exchanges structured geoscience objects, block models, files and tasks through Evo.

## Archicad

Graphisoft Archicad exposes an Automation API using HTTP/JSON, with an official Python connection package, while deeper extensions can be implemented through the Archicad Add-On Development Kit.

Because the Automation API runs with the desktop application, GeoTect uses:

`services/archicad_bridge.py`

The bridge:

- connects locally through Graphisoft's official Python connection;
- polls GeoTect for approved commands;
- executes a restricted command set;
- returns results to GeoTect;
- authenticates with a one-time bridge token.

Initial bridge operations:

- health;
- all-element IDs;
- selected-element IDs;
- trusted Add-On command execution.

This is suitable for building deeper IFC/property/classification/3D workflows without exposing Archicad itself to the public internet.

## Micromine Origin & Beyond

Micromine Origin & Beyond provides an embedded Python environment and the MMpy API.

GeoTect uses:

`services/micromine_bridge.py`

The bridge is designed to run in a Micromine-compatible Python environment and currently supports:

- bridge health;
- explicit MMpy command execution;
- block-model metadata inspection.

More MMpy operations can be added as typed bridge commands rather than allowing arbitrary remote Python execution.

## Micromine Alastri / Nexus

Micromine Nexus is the governed enterprise data-sharing layer used by Micromine applications, including Alastri, and supports Open API applications.

GeoTect provides a managed Nexus connector that:

- stays pinned to the configured Nexus tenant origin;
- stores authentication material in the encrypted secret vault;
- supports authenticated tenant-relative requests without inventing unsupported vendor endpoints.

Specific Nexus operations should be enabled against the API contract available to the customer's tenant/version.

## OGC, GeoServer and QGIS

GeoTect also supports open interoperability paths:

- OGC API Features;
- GeoServer REST/WFS/WMS/WMTS-oriented integration;
- QGIS via GeoPackage, GeoJSON, PostGIS and OGC services.

These make it possible to exchange terrain, observations, engineering geometry and interpreted layers without vendor lock-in.

## Connector roadmap

Recommended next adapters:

- Autodesk Construction Cloud / APS for Civil 3D and Revit;
- Bentley iTwin;
- Trimble Connect;
- Hexagon mining/geospatial services;
- Datamine;
- Deswik;
- Maptek;
- OpenGround;
- PLAXIS/GeoStudio solver exchange;
- MODFLOW/FloPy project interchange.

Each should follow the same rule: use an official supported API or a local vendor-supported automation bridge, never a fabricated cloud endpoint.
