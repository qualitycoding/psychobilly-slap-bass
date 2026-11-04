# Planning adversarial review

**Scope:** plan contracts and foreseeable implementation abuse. No implementation was executed and no implementation break is claimed fixed. S-ADVERSARIAL must replace this record after hostile testing.

## Challenges and resulting controls

1. **False-green host validation:** exit zero can conceal skipped pluginval coverage. D-014/D-022 research and S-080 require configuration/test-family/skip parsing plus artifacts; stable-race fallback is narrow under D-011.
2. **Host corruption through malformed state:** size alone is insufficient. D-012/D-022 and T-005 require schema/order/content validation and unchanged active sound; audio-thread state copying is forbidden by D-008.
3. **Renderer resource exhaustion:** D-024 byte/event/duration bounds and S-050/S-090 require fail-closed parsing, bounded resources and hostile cases.
4. **An analyser validating itself:** T-015 uses independent known answers; matched-note conditioning is restricted to T-014, and adapters must return measured data under D-027.
5. **Metric pass sold as realism:** D-017/D-071, G-004 and S-LISTEN explicitly prohibit that inference; ordinary-pluck references cannot validate slap.
6. **Disclosed blind key reused:** D-015 and S-100/S-LISTEN require a new seed after disclosure, sealed base64 key, balanced sides and maximum three rounds.
7. **Performance target relaxed after a miss:** D-018/D-029 and G-005 require native measurements, stored baselines and human rescope.
8. **Secrets in evidence or URLs:** D-026/D-030, T-051 and S-090 prohibit credentials/local paths/listener metadata and scan repository history and bundles.
9. **CI platform hidden by fail-fast or emulation:** TRACEABILITY and ENVIRONMENT map every declared target to native versioned jobs with `fail-fast:false`.
10. **Blind-pair pseudoreplication:** seven recordings cannot support a claim of twelve independent acoustic sources. D-028 narrows the p-value to descriptive use and leaves qualitative listening authoritative.

No unresolved Critical/High plan break remains after D-028–D-031. Frozen tests were not weakened. Any new implementation regression test must use the full unfreeze/red/refreeze procedure.
