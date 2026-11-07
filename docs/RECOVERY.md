# Recovery and troubleshooting

Failures name the stage in the job summary. Logs suppress raw Google/HTTP errors to avoid exposing credentials. Never paste tokens or OAuth callback URLs into an issue.

## Interrupted upload: do not start a replacement

Each live run writes an `upload-intent` record **before** inserting a video. A crash after YouTube accepts it can happen before its ID is saved. Every retry reconciles the authenticated channel's recent uploads with the stable `[LittleWonderJob:wonder-YYYY-MM-DD]` description marker.

- **Known video ID:** rerun the original day's job in `recover` mode; processing/publication resumes on that ID.
- **Intent or ambiguous response:** reconciliation may find it and resume. If it cannot, the workflow stops. API visibility can lag; a negative search is not proof an upload failed.
- **Earlier unresolved day:** newer daily jobs stop too, preserving order and avoiding accumulating orphans.

Open **Actions → Daily original Short → Run workflow**, select `recover`, and enter the exact job ID in `recover_job`. Keep the two upload opt-ins enabled. Recovery never creates a fresh insertion. It works for earlier dates as well as today's date. It can publish an already uploaded private video after processing succeeds, which is why it requires the explicit upload opt-in.

Inspect YouTube Studio's **Content** list, including private videos and processing/rejected entries. Match the job marker in the description. Do not remove this marker while recovery is pending.

If a video exists but API reconciliation cannot see it, check the authorized account/channel and wait for consistency. As an advanced manual repair, record its verified ID and `status: "uploaded"` on the existing entry in `shorts-state/daily-records.json`, preserving the topic/fingerprint/job ID, then run recovery. Confirm ownership and the marker first. If multiple videos match, resolve the situation deliberately in Studio; the bot will not delete videos automatically.

**Only after you establish that no upload was created** may you deliberately reset that one record to `status: "selected"` with `video_id: null`. Preserve its topic and fingerprint and all other records. This is an explicit human recovery decision, not an automated inference. A new attempt is allowed only for the same daily job while it is still that Colombo date; for past days, leave the repaired selected record reserved and let the next scheduled day choose another unused topic. Recheck Studio before any retry. The software cannot guarantee exactly-once delivery across YouTube and GitHub.

Never delete the journal, remove a successful record, reset fingerprints, or use a new daily ID just to get around a blocked upload. State updates are meaningful records, not schedule keep-alives.

## Common failures

| Stage / symptom | Action |
| --- | --- |
| Uploads disabled | Confirm a successful preview, then set both `upload_enabled = true` and Actions variable `UPLOAD_ENABLED=true`. |
| Missing credentials | Add all three correctly named Actions Secrets. Do not put them in TOML. |
| Authorization / channel mismatch | Reauthorize the exact expected YouTube channel, including the correct Brand Account. |
| OAuth stops after a week | Check External consent Testing status; use appropriate Production configuration and authorize again. |
| Revoked or expired token | Run the local helper again (see ANDROID.md on a phone) and replace Secrets. Inspect Google account third-party access and organization policies. |
| State 403 / conflict | Check `contents: write`, repository rules, and `shorts-state`. Preserve existing state; retry only after fixing access. |
| Ambiguous upload / processing timeout | Use recovery, not a new upload. Processing can take longer than the polling window. |
| Private status remains | Check actual channel/account restrictions and Studio. Do not evade restrictions with browser automation. |
| Quota / rate limit | Check the project's Quotas page; wait for reset or review unexpected consumers. No paid quota upgrade is needed for one daily video. |
| Model download / checksum failure | Retry a temporary outage; do not disable checksum validation. Investigate upstream changes before editing the lock. |
| Render / captions / silence check fails | Download available artifacts, revise the episode/layout, and rerun preview. Publication has been skipped. |
| Topic library exhausted | Add a reviewed original pack. The current 40 episodes are never automatically recycled. |
| Schedule stopped | Check Actions enablement, default branch, latest failures, and GitHub's 60-day public-repository inactivity rule. |
| Schedule is late | GitHub cron is approximate; watch the run and processing status. There is no exact-time SLA. |
| Artifacts disappeared | Retention is three days. Run another preview or download them promptly next time. |

## Safety properties and their limits

The uploader retries transient resumable errors at most four times, using the same upload request, and never intentionally repeats a video insertion after an ambiguous result. Recovery scans up to 500 recent uploads; older missing markers need human inspection. It verifies the channel and made-for-kids setting before making a video public. No restriction is bypassed.

Checks cover ffprobe dimensions, timing, codecs, frame rate, audio presence/level, long silent gaps, black gaps, caption geometry, metadata limits, manifest presence, and duplicate fingerprints. They are conservative mechanical checks. Source-linked facts, appropriate tone, and meaningful scene semantics still need review when adding content. Captions are aligned by narrated sentence, not individual phonemes.
