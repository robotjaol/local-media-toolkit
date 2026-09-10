# Privacy Model

## Primary control

The strongest privacy property offered here is architectural: media is not intentionally uploaded by the application.

## No telemetry

The Python code contains no analytics SDK, tracking pixel, remote logging endpoint, account system, or API key integration.

## What still matters

Local processing does not eliminate every data exposure path. Consider:

- Cloud-synchronized input/output folders
- Operating system telemetry and crash reporting
- Endpoint security products
- Backup agents
- Third-party FFmpeg and ImageMagick binaries/delegates
- Temporary image copies on the local system temporary drive during conversion
- Shell history containing sensitive paths
- Media content that visibly reveals identifying information
- Embedded metadata not covered by a simple global metadata strip

For highly sensitive media, treat the entire workstation as part of the security boundary.
