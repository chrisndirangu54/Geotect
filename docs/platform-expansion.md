# GeoTect platform expansion

GeoTect now includes a shared platform layer for enterprise, field, domain and automation workflows.

## Implemented platform foundations

- multi-tenant organizations and memberships;
- asset registry and health scoring;
- engineering approval workflows;
- 4D event records and emergency events;
- compute-job queue plus worker execution;
- usage metering for billing integration;
- plugin registry;
- client portal filtering;
- offline field record conflict handling;
- drone and satellite processing manifests;
- AI/CAD deterministic command planning with confirmation gating;
- automated risk-rule evaluation;
- probabilistic slope risk;
- investigation-location optimization;
- foundation, settlement, retaining-wall, pile and liquefaction screening;
- engineering and borehole report data generation;
- GeoJSON, LandXML and IFC semantic interchange;
- notifications/webhook dispatch framework;
- templates for tailings dams, highways, foundations, open pits, underground mines, tunnels, corridors, ESG and emergencies.

## External integrations

Some features are intentionally connector-driven because they require customer credentials, licenses or external compute:

- WhatsApp/SMS/email/Slack/Teams delivery;
- commercial BIM/CAD writers/readers;
- provider-specific photogrammetry;
- satellite catalogue/download services;
- billing processors;
- high-end commercial FEM/geotechnical solvers.

Those interfaces are represented by secure admin-managed credentials, plugin registrations and compute jobs instead of hard-coded vendor secrets.

## Safety

Engineering design endpoints in this layer are screening/design-support calculations. They retain method metadata and do not replace competent professional review, jurisdiction-specific codes or signed design.
