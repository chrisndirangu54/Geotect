# Extended engineering integrations

GeoTect's second integration wave adds:

- Autodesk APS / Autodesk Construction Cloud cloud APIs.
- Civil 3D and Revit desktop bridge contracts for their supported .NET APIs.
- Bentley iTwin REST integration with OAuth bearer credentials.
- OpenGround-connected workflows through Bentley/iTwin repositories and governed exchange.
- Trimble Connect regional cloud API integration.
- Datamine Studio local COM automation bridge.
- Deswik governed file/API exchange contract, without assuming undocumented public endpoints.
- Maptek Python SDK / Vulcan Python SDK bridge modes.
- PLAXIS local Remote Scripting bridge.
- GeoStudio project/file exchange contract.
- Native MODFLOW 6 / FloPy project creation and execution.

## Security model

Cloud tokens remain in GeoTect's encrypted secret vault. Desktop products use one-time bridge tokens with only hashes retained in the database. Cloud adapters use fixed vendor hosts or a configured approved tenant base URL.

## MODFLOW / FloPy

GeoTect can create a baseline MODFLOW 6 groundwater-flow project from JSON input, write the simulation, run it when the `mf6` executable is available, and load head results. This is a real FloPy/MF6 interchange path rather than a generic file placeholder.

## Desktop bridges

Desktop APIs are intentionally executed locally so GeoTect does not expose CAD/mining/geotechnical desktop applications directly to the internet. The bridge queue remains the same one used by Archicad and Micromine.
