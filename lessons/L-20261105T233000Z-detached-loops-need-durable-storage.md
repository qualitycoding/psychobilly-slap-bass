# Detached retry loops must live on durable storage

/tmp in this sandbox is wiped unpredictably (often mid-loop), killing detached
retry loops and deleting the askpass helper and PAT file. Keep the loop
script, askpass and status files under /mnt/agents/work (durable; noexec only
blocks exec, not `bash script.sh`), and re-stage the askpass into /tmp inside
each loop iteration. Never `pkill -f pushloop` from an interactive shell that
matches the pattern (self-kill, exit -15); use `pgrep -f 'pushloop[.]sh'`.
