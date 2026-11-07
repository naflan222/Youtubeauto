# Free operation, platform limits, and policy references

Checked against the official pages below on **2026-11-07**. These services can change. The Cloud Console and repository account show the limits actually applied to your account. This project does not describe any service as unlimited free.

## GitHub Actions

[GitHub Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions) says standard GitHub-hosted runners in public repositories are free. This repository is public and uses standard `ubuntu-24.04`, not larger runners. Private repositories have account-specific included compute/storage allowances; this project does not promise free private-repository operation. Do not enable a paid spending budget for it.

Artifact storage, caches, service policies, and platform limits still apply. Video artifacts have a **three-day** retention; caches hold only the approximately 63 MB model and Python packages. GitHub rounds artifact retention according to its supported settings. If artifacts or caches hit your included allowance, remove old ones or reduce retention; no paid storage is necessary. Rendered videos are never committed to Git.

[Scheduled event documentation](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule): schedules run from the default branch, may be delayed or dropped under load, and public-repository scheduled workflows are automatically disabled after **60 days without repository activity**. Meaningless keep-alive commits are not used. Check and re-enable schedules when needed. Normal state commits represent real uploads and must not be relied upon as a guarantee against inactivity enforcement.

The default cron is `45 12 * * *`, meaning 12:45 UTC, which is 18:15 Sri Lanka time. It is a target start, not a promised publication time. Network transfer and YouTube processing add delay. There is no daily catch-up burst: at most one new job for the current configured local date is considered.

## YouTube Data API and OAuth

Current [quota documentation](https://developers.google.com/youtube/v3/determine_quota_cost) lists default daily quotas of **100 `videos.insert` calls**, **100 `search.list` calls**, and **10,000 units for other endpoints combined**. Upload/search have separate buckets and a listed cost of one per call in their respective buckets. Daily quota resets at midnight Pacific Time. Earlier references to every upload consuming 1,600 general quota units are outdated for this checked documentation.

A normal new episode uses one chart-discovery call, channel/category lookup, one upload insertion, upload-list reconciliation (at most ten pages per check), processing polls (at most twelve), and a status update/verification. Existing-video recovery uses no insertion. There are no paid API calls, no required API key, and no billing-enabled integration. Account upload limits, project-specific quotas, rate limits, and temporary outages may still stop operation. Failed requests and retries can consume quota.

The checked [videos.insert reference](https://developers.google.com/youtube/v3/docs/videos/insert) explicitly states: **“Videos uploaded from unverified API projects are not restricted to private viewing mode.”** Do not repeat the older automatic private-only rule. Account settings can still affect default privacy, and OAuth verification, API compliance, and quota-extension rules are separate matters. This project deliberately requests private first, then confirms processing and requests public status; it reports failure if public status cannot be observed. See [quota and compliance audits](https://developers.google.com/youtube/v3/guides/quota_and_compliance_audits).

[OAuth token expiration](https://developers.google.com/identity/protocols/oauth2#expiration): External apps in Testing normally issue refresh tokens that expire after seven days for YouTube scopes. Production configuration does not make tokens permanent. Revocation, account security changes, inactivity, organization restrictions, or token issuance limits can invalidate them. Google limits refresh tokens per account/client; avoid unnecessary repeated authorization. OAuth credentials are exclusively in Actions Secrets for routine operation, apart from the temporary private local setup file.

## Shorts, children, and disclosure

The official [Shorts requirements](https://support.google.com/youtube/answer/15424877) describe current square/vertical short-video classification; this project's vertical 25–40-second output fits comfortably within the duration profile. There is no separate Shorts/Reels endpoint. Upload acceptance alone does not guarantee Shorts shelf distribution.

Set [`status.selfDeclaredMadeForKids`](https://developers.google.com/youtube/v3/docs/videos#status.selfDeclaredMadeForKids) to true for every upload. Review [made-for-kids guidance](https://support.google.com/youtube/answer/9528076). Child-directed videos have platform feature restrictions, including limitations on comments and personalized advertising. Placement in YouTube Kids is a separate platform decision.

The [altered-content guidance](https://support.google.com/youtube/answer/14328491) and [`containsSyntheticMedia`](https://developers.google.com/youtube/v3/docs/videos#status.containsSyntheticMedia) distinguish meaningful realistic synthetic/altered depictions from obviously fictional animation. The default original cartoon stories use a generic narrator, do not impersonate real people, and do not portray realistic footage of actual events, so the default is false. Reassess this if the content format changes. This is not an evasion mechanism.

## Discovery and data retention

Use only official [`videos.list` charts](https://developers.google.com/youtube/v3/docs/videos/list), following [YouTube Developer Policies](https://developers.google.com/youtube/terms/developer-policies). Discovery is a small, best-effort topic signal, not a children-safe recommendation feed. No scraping, Google Trends unofficial endpoints, copied scripts, downloaded videos, or unlicensed media are used.

The curated concept whitelist and unsafe-term filter limit how external titles influence selection; independently authored episodes determine what is actually said and shown. Missing data, errors, and unmatched terms yield `evergreen-fallback`. Observed popularity does not imply a topic is suitable for children, promise reach, or establish search volume.

Source/retrieval date and a source video ID appear only in the generated short-lived `script.json`. Raw titles, third-party metrics, and thumbnails are not retained. Actions artifacts expire after three days, comfortably inside the common 30-day API-data refresh/delete window; do not permanently archive external discovery signals without reviewing applicable policy. The state branch holds only the channel owner's own operational job records and upload identifiers. On disconnecting, remove Secrets and delete retained API-derived records/artifacts as appropriate under current policies. Revocation-related deletion obligations still apply.

## Maintenance and practical limits

- Forty episodes are provided. Automated original creation is bounded by reviewed content: when the library is exhausted, it stops. Add substantive new stories and goals, not color/name substitutions. No claim of infinite original content is made.
- All generated speech runs locally on the temporary runner. Model hosting and package repositories can be unavailable or change terms. Downloads are pinned and checksum-verified; there is no paid fallback.
- The default voice is general-purpose English, not a cloned celebrity or identifiable user's voice. Review intelligibility for your audience. Its model card identifies public-domain training material; repository model metadata declares MIT.
- Automated checks cannot prove every educational claim, artistic choice, or account policy outcome. Human review is needed when adding episodes or changing the format, not for routine daily uploads from the reviewed pack.
- Neither cross-platform exactly-once delivery nor exact-time publishing is guaranteed. Ambiguous uploads stop for recovery; failures use GitHub's job summaries and native notifications.
