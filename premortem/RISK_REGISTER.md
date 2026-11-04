# Risk register

Severity is the unmitigated consequence; status reflects the converged plan. No Critical/High risk is accepted without mitigation.

| ID | Risk / root cause | Lens | Severity | Likelihood | Trace | Mitigation / status |
|---|---|---|---|---|---|---|
| R-001 | False-green validation from skipped tests or broad race fallback | Integrity | Critical | Medium | C-021/C-022, S-080 | D-011/D-014 log coverage and narrow fallback; mitigated |
| R-002 | Host/resource compromise through malformed state/events | Security | Critical | Medium | A-012, S-020/S-050 | D-008/D-012/D-022/D-024/D-026 plus hostile tests; mitigated |
| R-003 | Credential/local/listener data in evidence | Security | Critical | Low | S-090/S-100 | D-026/D-030, history/bundle scans and no metadata; mitigated |
| R-004 | Native target misses realtime budget | Performance | High | Medium | D-018, S-040 | D-029 native baselines and G-005; mitigated |
| R-005 | Listening evidence inaccessible or branch-invalid | Integrity | High | Medium | S-100 | D-028/D-030 and T-051; mitigated |
| R-006 | Pizzicato metrics overclaimed as slap realism | Research premise | High | Medium | C-010, S-LISTEN | D-071 demos-only slap and qualitative override; mitigated |
| R-007 | Silent tool/runner/version drift | Supply chain | High | Medium | ENVIRONMENT | Pins, S-000, deviations and retro diff; mitigated |
| R-008 | Hosted hardware varies under the same runner label | Performance | Medium | Medium | D-018/D-029 | Record host/raw maxima and same-class history; residual Medium |
| R-009 | Seven ordinary-pluck references limit breadth/independence | Research | Medium | Certain | D-028/D-070 | Descriptive p-value only, demos and human judgement; residual Medium |
| R-010 | No independent model tiers available | Review | Medium | Certain | PROFILE | Sequential fresh planning reviews and mandatory fresh implementation reviewers; residual Medium |
| R-011 | Python adapter misses host ABI behaviour | Host integration | Low | Medium | D-027 | Native pluginval plus measured adapter; residual Low |
| R-012 | Python vulnerability feed misses native advisories | Supply chain | Low | Medium | C-029/S-090 | Separate exact native dependency review; residual Low |
| R-013 | Store write access at intake may not survive until S-KNOW | External access | Medium | Medium | A-015/S-KNOW | S-000 recheck and protocol bundle fallback; residual Medium |
