# Arxiver Bringup Troubleshooting

| Symptom | Diagnosis | Action |
|---|---|---|
| `v2_substrate_status.docker_ok=false` | Docker daemon not running | User starts Docker (`systemctl start docker` on Linux). Do not retry until daemon is up. |
| `v2_build_image` fails with permission denied | User lacks docker group membership | User adds themselves to the `docker` group, logs out and back in. |
| `v2_build_image` fails with no space left | Image layers exceed disk free | User prunes old images: `docker system prune -a`. |
| `v2_substrate_status.datasets_present.cifar10=false` after staging | Dataset script wrote to the wrong path | Verify `~/.arxiver/datasets/cifar10/cifar-10-batches-py/` exists. Re-run staging. |
| `v2_smoke_test` verdict=error on `smoke_timeout` fixture | **Expected.** This fixture asserts the 2.0s timeout fires. | No action — `smoke_timeout` is supposed to error. |
| `v2_smoke_test` verdict=error on any other fixture | The sandbox image or runner is broken | Read the fixture's `stdout_tail`; common causes: stale image (rebuild), missing dataset (re-stage), bad container mount permissions. |
| `v2_verify` returns verdict=error with "RunnerError" in stdout_tail | Image is missing or daemon stopped between calls | Re-run Step 1 (substrate_status) to confirm image still exists. |
| `v2_smoke_test` duration > 90s | Disk or CPU pressure during the run | Re-run when system is idle; persistent slowness suggests image bloat — rebuild. |

## Escalation rules

If you ran through this table and the symptom does not match: stop and surface the full failure (verdict, stdout_tail, image_digest) to the user. Do not proceed to running hypotheses on a substrate that hasn't passed smoke.
