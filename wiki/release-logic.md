# Release Logic  

Releases are controlled by artifact states. States are configurable in the States admin section. There are 4 kinds of states:
1. **Release state** - This is the state artifacts go into when you want to release them.
2. **Staging state** - This is the state artifacts go into when they are being prepped for release. Any signature that is in the release state and is modified automatically get put into the staging state by the system. Only relevant for signatures.
3. **Retired state** - This excludes a previously released artifact from future releases. Only relevant for signatures.
4. **Any other state** - Any other state has no significance on releases. These will not be included in releases.

The Release, Staging, and Retired states must be configured in the admin section *before* you can generate a release. If they are not, the system will error out.

When a release is created, the system first pulls all signatures that are in the release state. Then, it gathers all signatures that are in the staging state and checks their revision history for the most recently released revision that is in the release state. If it finds it, it will include it in the release. If it does not find any previously released revisions, it will skip the signature.
