# Hosting ExpatCalculator: Deployment, Maintenance & Cost Report

## Executive summary

ExpatCalculator is cheap to host: a stateless Streamlit app, ~16KB of code, three small
JSON data files, three light dependencies (streamlit/pandas/plotly), **no database, no user
accounts, and no secrets** (the exchange-rate API is keyless with a hardcoded fallback). That
profile means the recommended path costs **£0/month**.

The one honest tension: *"100% uptime"* and *"zero cost"* don't fully coexist in the managed-
hosting world. Every free managed platform puts idle apps to sleep. The recommendation is to
**start on Streamlit Community Cloud (free, ~10 minutes, auto-deploys from the existing GitHub
repo)** and only move up if the idle-sleep behaviour becomes a problem in practice — for a
low-traffic personal project, it usually doesn't.

> ⚠️ **Blocker to fix before deploying** — see "Critical pre-deploy fix". The code uses
> `use_container_width`, which Streamlit scheduled for removal after 2025-12-31. A fresh deploy
> pulling the latest Streamlit may break or hard-warn.

---

## The cost landscape

| Option | Monthly cost | Always-on? | Setup effort | Notes |
|---|---|---|---|---|
| **Streamlit Community Cloud** | **£0** | No — sleeps when idle, ~30s wake | Very low (10 min) | Native Streamlit host, auto-redeploy on `git push`. **Recommended start.** |
| Hugging Face Spaces | £0 | No — sleeps after 48h idle | Low | More RAM (16GB), slightly more generic. |
| Oracle Cloud "Always Free" | £0 | **Yes** | High (Linux sysadmin) | True always-on for free, but real maintenance + provisioning/reliability caveats. |
| Render / Railway / Fly.io | ~£4–6 | Yes | Low–medium | Managed always-on; trivial for this app's size. |
| Hetzner CX22 VPS | ~£3.50 | Yes | Medium–high | Cheapest reliable paid box, but you own the OS. |
| Custom domain (optional) | ~£1 (≈£10–12/yr) | — | Low | e.g. Cloudflare/Porkbun at cost. |

The cheapest *always-on* free option is Oracle's free tier, but it trades money for time and
carries reliability caveats. The cheapest *always-on managed* option is ~£4–6/month. The
cheapest option overall is Streamlit Community Cloud at £0 with the sleep caveat.

---

## Recommended path: Streamlit Community Cloud

### Why it fits this project specifically
- Built for Streamlit — no Dockerfile, no reverse proxy, no TLS setup.
- Deploys straight from the existing **public** repo (`github.com/Madalad/ExpatCalculator`) and
  **auto-redeploys on every push to `main`** — the existing workflow becomes the deploy pipeline.
- **No secrets to configure** (the FX API needs no key), removing the one fiddly part of
  Streamlit deployment.
- Fits comfortably in the free tier's ~1GB RAM — it loads three small JSON files and does
  in-memory pandas/plotly work, and already uses `@st.cache_data`/`@st.cache_resource`, which is
  exactly what shared hosting rewards.

### The domain name / URL

Streamlit Community Cloud apps are served at:

```
https://<subdomain>.streamlit.app
```

- The **subdomain** is chosen at deploy time. For this repo the likely default is
  **`https://expatcalculator.streamlit.app`** if free.
- Subdomains are **globally unique** across all Streamlit apps. If `expatcalculator` is taken,
  append a qualifier (e.g. `expatcalculator-madalad.streamlit.app`). If none is chosen, one is
  auto-generated from the app name plus a short random hash.
- It is always a subdomain of `streamlit.app`. A **bare custom domain** (e.g.
  `expatcalculator.com`) is **not supported on the free tier** without putting a proxy
  (e.g. Cloudflare) in front.

### Deployment steps
1. **Fix the `use_container_width` issue** (see below) and push to `main`.
2. Confirm `requirements.txt` is accurate — it is (streamlit/pandas/plotly).
3. Go to **share.streamlit.io**, sign in with GitHub, authorise access to the repo.
4. **New app** → repo `Madalad/ExpatCalculator`, branch `main`, main file `app.py`.
5. (Optional) set the custom subdomain, e.g. `expatcalculator`.
6. Deploy. You get the public `*.streamlit.app` URL.
7. Future `git push`es redeploy automatically.

### The honest limitations
- **Idle sleep**: after a stretch of no visitors, the app sleeps; the next visitor sees a
  "wake up" button and waits ~30 seconds. This is the gap versus literal "100% uptime."
- **Custom domains**: not natively supported on the free tier (Cloudflare-proxy workaround only).
- **Public-only** apps on the free plan (fine — repo and data are already public).

### If idle-sleep genuinely bothers you, in increasing order of cost/effort
- **Accept the ~30s cold start.** For a personal/portfolio tool this is almost always the right
  call — £0, zero extra work.
- **Keep-alive ping.** A free monitor (UptimeRobot, cron-job.org) hitting the URL every few
  minutes keeps it warm. Caveat: this sits in a grey area of shared-resource fair-use, and is a
  workaround rather than a fix.
- **Move to true always-on:** Oracle free tier (£0, high effort) or a managed host at ~£4–6/month
  (low effort).

---

## The always-on alternatives (if/when you outgrow free)

**For £0 and you don't mind Linux:** Oracle Cloud's Always Free ARM instance runs 24/7 with no
sleep. Real cost is setup and upkeep — provision the VM, install Python, run the app under
`systemd`, put nginx in front as a reverse proxy, and get TLS via Let's Encrypt. Caveats: ARM
capacity can be hard to grab in busy regions, signup needs a card, and Oracle has historically
reclaimed idle free instances. The only genuinely-free always-on route, but the highest-
maintenance one.

**For ~£4–6/month and you value your time:** Render, Railway, or Fly.io will run this app
always-on with a fraction of the effort — connect the GitHub repo, set the start command
(`streamlit run app.py --server.port $PORT`), deploy. Fly.io needs a small Dockerfile;
Render/Railway can often infer the Python setup. The path to pick the moment uptime becomes a
real requirement rather than a nice-to-have.

---

## Critical pre-deploy fix

`requirements.txt` pins `streamlit>=1.32.0` (lower bound only), so a fresh deploy installs the
**latest** Streamlit. Streamlit warns:

> `use_container_width` will be removed after 2025-12-31. For `use_container_width=True`, use
> `width='stretch'`.

That removal deadline has passed. `app.py` uses `use_container_width` in roughly seven places
(every `st.dataframe` and `st.plotly_chart`). A clean deploy could therefore break or throw hard
warnings. Two ways to handle it:

- **Quick & safe for now:** pin a known-good version, e.g. `streamlit==1.40.x` (a release before
  the removal), so the deployed environment matches what's been tested. Lowest risk, defers the
  work.
- **Proper fix:** replace `use_container_width=True` → `width='stretch'` throughout `app.py` and
  drop the version ceiling. ~10 minutes, future-proof.

Recommended: do the proper fix before first deploy.

---

## Maintenance going forward

Low-maintenance — no database to back up, no user data, no auth, no secrets. Code and data both
live in git, so "backup" is already handled. The ongoing work is small and mostly about
dependency drift:

- **Dependency updates.** The real recurring task. Streamlit moves fast and deprecates APIs. Pin
  versions in `requirements.txt` so deploys are reproducible, and bump deliberately. Enabling
  **GitHub Dependabot** gives automatic update PRs to review and merge.
- **The external FX API.** `open.er-api.com` could rate-limit or disappear. Already protected —
  the hardcoded fallback means the app degrades gracefully rather than crashing. On a server the
  fetch runs at process start (and again on each restart/wake).
- **Uptime monitoring.** UptimeRobot's free tier emails/alerts on downtime — worth setting up
  regardless of host.
- **Security.** Minimal surface: a public read-only calculator with no persisted input and no
  secrets. Keep dependencies patched and don't commit secrets (currently none).
- **If you go paid.** Set a billing alert on whichever platform so a surprise can't run away.

---

## Bottom line on economic feasibility

- **£0/month** on Streamlit Community Cloud covers everything needed, with the sole compromise
  being a ~30-second cold start for the first visitor after an idle period.
- **True 100% uptime** costs either *effort* (Oracle free tier, £0 but you run a Linux box) or
  *money* (~£4–6/month managed). Neither is necessary unless this becomes more than a personal/
  portfolio tool.
- **Optional polish** — a custom domain — adds ~£1/month and is the only thing worth spending
  money on early, purely for presentation.

**Recommendation:** fix the `use_container_width` deprecation, deploy free to Streamlit Community
Cloud, and revisit always-on hosting only if real usage makes the idle-sleep a genuine problem.
