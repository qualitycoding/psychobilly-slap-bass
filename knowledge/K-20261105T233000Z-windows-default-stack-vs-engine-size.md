# Windows 1 MB default stack vs large value-type DSP objects

Fact (verified 2026-11-05 on windows-2025, VS 18 2026 / cl 14.51): a ~3.5 MB
object held as a local in `main` crashes pre-main with 0xC00000FD
(STATUS_STACK_OVERFLOW) — MSVC stack probing touches the guard page before the
first statement runs, so no diagnostic output appears. Linux/macOS default
8 MB main stacks mask the same bug. Git Bash reports the crash as exit 127
with no output; Python shows 0xC0000005 (access violation); PowerShell shows
0xC00000FD — launcher-dependent codes for the same event.

Diagnosis pattern that worked: a cl.exe flag/arch matrix (/O2 vs /Od, /MD vs
/MT, x64 vs x86) all crashing identically rules out codegen, runtime library
and architecture — measure `sizeof(BigThing)` and heap-allocate it.

CI defence: add a `static_assert(sizeof(Engine) < (1u<<20))` guard to CLI
translation units so a future DSP growth fails the build instead of the runner.
