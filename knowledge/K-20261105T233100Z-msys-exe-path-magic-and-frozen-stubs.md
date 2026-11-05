# MSYS/Cygwin path magic breaks extensionless-binary staging on Windows

Fact (verified 2026-11-05): Git Bash `cp foo.exe foo` fails with "same file",
and `-e foo`/`test` treat `foo` and `foo.exe` as identical, because MSYS path
resolution appends `.exe`. A frozen test stub that resolves binaries by
extensionless name (e.g. `psychobilly-render`) therefore cannot be satisfied
by MSYS file operations. Python file APIs (`pathlib`, `shutil`) use exact
Win32 names and work; CreateProcess also runs an extensionless path by
appending `.exe` itself.

Related: `--input /dev/stdin` in a frozen adapter is POSIX-only; map it (and
`-`) to std::cin in the tool rather than editing the frozen stub.
Also: `git log` timestamps on Actions can stamp a whole flushed block within
microseconds — do not use inter-line timing to judge whether batch output is
real; count occurrences and read the section instead.
