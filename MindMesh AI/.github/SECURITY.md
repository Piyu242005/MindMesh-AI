# Security Policy

## Supported Versions

MindMesh AI actively maintains security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| v1.0.x  | :white_check_mark: |
| < v1.0  | :x:                |

## Reporting a Vulnerability

Security is a top priority for MindMesh AI. If you discover a security vulnerability within the project, please **DO NOT** open a public issue.

Instead, please send an email to the maintainer: **Piyush Ramteke**.
Include a detailed description of the vulnerability and the steps to reproduce it.

### Vulnerability Disclosure Policy

* We will acknowledge receipt of your vulnerability report within 48 hours.
* We will provide an estimated timeline for the fix and keep you updated on progress.
* Once the vulnerability is resolved, we will publish a security advisory and credit you for the discovery (unless you prefer to remain anonymous).

## Protecting Credentials and Data

MindMesh AI interacts with third-party cloud services and handles sensitive data. As a user or contributor, ensure the following best practices:

* **API Keys**: Never commit your `.env` file or hardcode your `GEMINI_API_KEY`, `GROQ_API_KEY`, or `QDRANT_API_KEY` into the source code.
* **Qdrant Credentials**: Keep your Qdrant Cloud Cluster URL and API Keys completely private.
* **User Data**: Ensure that uploaded video files and transcribed chunks are stored securely. Do not commit the `jsons/`, `audios/`, or `videos/` directories containing personal data.

If you accidentally commit an API key, revoke it immediately from the provider's dashboard and rotate it.
