# GeoTect administration and security

## Bootstrap super admin

The backend reserves the verified Firebase email configured in:

`GEOTECT_SUPER_ADMIN_EMAIL`

The repository default is:

`chrisndirangu54@gmail.com`

The email value **does not authenticate the user**. GeoTect first verifies the Firebase ID token server-side, including revocation checks. Only then is a matching verified identity bootstrapped as `super_admin`.

A browser cannot make itself an administrator by submitting this email.

## Firebase setup

Create a Firebase project and enable the desired sign-in providers, typically Google.

Web configuration:

- `VITE_FIREBASE_API_KEY`
- `VITE_FIREBASE_AUTH_DOMAIN`
- `VITE_FIREBASE_PROJECT_ID`
- `VITE_FIREBASE_APP_ID`

Backend verification requires Firebase Admin credentials. Store the service-account JSON outside Git at:

`secrets/firebase-service-account.json`

This path is gitignored.

## Secret encryption

Provider API keys are never stored in plaintext in the database. They are encrypted with Fernet using:

`GEOTECT_MASTER_KEY`

Use a long random deployment secret managed through the hosting platform's secret manager. Do not commit it to Git. Rotating this master key requires re-encrypting existing provider secrets.

The admin API returns only masked values such as:

`••••••••a1b2`

The actual secret is never returned to the web dashboard after storage.

## RBAC

GeoTect defines granular permissions including:

- users read/write/disable;
- role management;
- settings read/write;
- secret metadata/write;
- model read/write;
- audit access;
- all-project access;
- job execution/cancellation;
- system management.

The bootstrap super admin receives every permission. Additional super admins can be granted from the dashboard by an existing super admin.

## Model registry

Model selection is task based. Example task names:

- `assistant`
- `geology_interpretation`
- `vision`
- `embeddings`

Each task can select provider, model, parameters and enabled state. Scientific numerical solvers remain separate from LLM model selection.

## Auditing

Every high-impact admin mutation writes an audit event including:

- actor UID/email;
- action;
- target;
- non-secret change metadata;
- timestamp.

API-key values are never written into audit records.

## Development authentication

The backend contains a development token path only when:

`GEOTECT_DEV_AUTH=true`

This flag must never be enabled in production.
