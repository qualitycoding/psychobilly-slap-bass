# Execution deviations

## S-000 transport recovery — no version substitution

The direct PyPI CDN connection stalled at approximately 16 KB/s for large wheels. NumPy 2.2.6 and SciPy 1.15.3 were retrieved from their exact `files.pythonhosted.org` URLs using parallel byte ranges and verified against the SHA-256 values published by PyPI. The previously unreachable configured mirror `pypi.mirrors.msh.team` later became reachable and was used for small direct/transitive packages with constraints preventing a NumPy/SciPy version change. This is a transport deviation from D-010's historical mirror-unavailability note, not a dependency substitution. All four direct versions match ENVIRONMENT exactly; the complete transitive lock and its SHA-256 are in `artifacts/s000/`.

CMake 3.31.6/3.22.4 and the three pluginval archives likewise used retrying byte-range transport. Their versions, byte counts and frozen hashes were verified after download. No toolchain version, runner label, action SHA, test threshold or product scope was changed.
