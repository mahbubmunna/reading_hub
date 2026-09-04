# Murena Interview Prep — Android Developer (/e/OS Default Apps)

Read this the day you get the call, then again the night before each round.
Process: technical round → HR/culture round → offer.

---

## 1. Know the company (10 minutes, memorize the bold parts)

*Verify current facts on e.foundation and murena.com before the call — this
snapshot may be slightly dated.*

- **Murena / e Foundation** builds **/e/OS**: a **de-Googled Android** fork
  based on **LineageOS**. Founder: **Gaël Duval** (also created Mandrake
  Linux in the 90s — mentioning this shows you did homework).
- De-Googled means: no Google apps or Play Services. **microG** reimplements
  the Google APIs apps expect, so regular apps still run without phoning
  home. **App Lounge** is their app store front-end with privacy scores.
  **Advanced Privacy** blocks trackers, fakes location/IP.
- **Murena Cloud** (based on **Nextcloud**) replaces Google Drive/Photos
  ecosystem; Murena also sells phones preloaded with /e/OS (they've
  partnered with **Fairphone**).
- Many default apps are **forks of open-source apps**: Mail (fork of
  **K-9 Mail**), Message (fork of **QKSMS**), Browser (Chromium/Bromite
  lineage), **Bliss Launcher** (their default launcher). The job is literally
  maintaining these — improving them and **merging upstream changes**.
- Team: **OS&Apps squad**, async-first, everything through **GitLab**
  (gitlab.e.foundation), collective ownership of the roadmap. Contractor
  position, daily rate.

**Why this matters:** your single biggest hook is *"I built a launcher in
Compose; you maintain Bliss Launcher."* Say it early and often.

---

## 2. Your 90-second intro (practice out loud)

"I've been an Android developer for nine years — started in native
Java/Kotlin, later shipped Flutter and React Native too, but native Android
is home. The work I'm proudest of: Ratio Launcher, a full home-screen
launcher built in Jetpack Compose, plus Compose UI and Glance widgets for
the tawk.to app, and fintech apps where secure storage and permission
discipline were hard requirements. I've been fully remote and async since
2021. I'm here specifically because I want my work to run in the open and
respect users — I'm from Bangladesh, where the data-for-services trade is
the default for millions of people, and /e/OS is the project I'd choose to
change that."

---

## 3. Technical round — likely questions & strong answers

### Jetpack Compose (they WILL probe this — it's on your resume twice)

**"Explain recomposition."**
Compose re-executes composable functions when the state they read changes.
Compose skips composables whose inputs are unchanged and stable. Performance
work = controlling what reads what: keep state reads as low in the tree as
possible, pass lambdas instead of values where it defers reads, use
`derivedStateOf` for computed state, `remember` for expensive objects, and
stable/immutable data classes so the compiler can skip.

**"State hoisting?"**
Composables should be stateless where possible: state lives up in the
caller/ViewModel, events flow up, state flows down (unidirectional data
flow). Makes components reusable and testable.

**"Side effects in Compose?"**
`LaunchedEffect` (coroutine tied to composition + keys), `DisposableEffect`
(cleanup on leave), `SideEffect` (publish to non-Compose world),
`rememberCoroutineScope` (launch from callbacks). Know when each dies.

**"Lists performance?"**
`LazyColumn` with stable `key`s, avoid unstable lambdas/params causing item
recomposition, `contentType` for mixed lists, watch overdraw and nested
scroll.

**"Compose vs Views interop?"**
`ComposeView` / `AndroidView` bridges — relevant because /e/OS forks are
often mature View-based codebases adding Compose gradually. Say that: "In
forked apps I'd expect incremental Compose adoption via interop, not
rewrites."

### Launcher internals (your Ratio Launcher story — prepare to go DEEP)

Be ready to whiteboard how a launcher works:
- Manifest: activity with `category.HOME` + `category.DEFAULT` intent filter;
  user sets it via **RoleManager** (ROLE_HOME) / default-apps settings.
- App list: **`LauncherApps`** service (profile-aware — work profile apps),
  `getActivityList()`, plus `ACTION_MAIN`/`CATEGORY_LAUNCHER` queries via
  PackageManager; listen for package add/remove/change callbacks.
- Launching: `startMainActivity()` on LauncherApps with the user handle.
- Widgets: **`AppWidgetHost`** + `AppWidgetManager` — binding permission
  flow, host views inside your hierarchy; in Compose, host via `AndroidView`.
- Shortcuts: `ShortcutManager` / pinned shortcuts; notification dots via
  NotificationListener (permission-gated).
- Hard parts to mention honestly: keeping the app list in sync, widget
  resize/host lifecycle, gesture navigation conflicts, process death and
  cold-start speed (a launcher must appear instantly), battery discipline.
- Bridge every answer to them: "Bliss Launcher solves the same problems —
  I'd love to see how you handle X."

### Jetpack Glance

Glance = Compose-style syntax that compiles down to RemoteViews for app
widgets. Key differences from real Compose: limited component set, state via
`GlanceStateDefinition`/DataStore, updates are pull-based (`updateAll`),
sizing via `SizeMode`. Pain points worth mentioning (shows real use):
RemoteViews limits, update latency, per-launcher rendering quirks — which
you understand *from both sides*, having built a launcher that hosts widgets
and widgets themselves.

### Kotlin & architecture

- Coroutines: structured concurrency, `viewModelScope`, dispatchers,
  `Flow`/`StateFlow` vs LiveData, `stateIn`, cold vs hot flows.
- Architecture: MVVM + Clean layers (UI → ViewModel → UseCase → Repository →
  data sources), unidirectional data flow, DI (Hilt), Room, WorkManager for
  deferrable background work.
- "Android architecture principles guidelines" from the JD = Google's
  official Guide to App Architecture — reread it the night before
  (developer.android.com/topic/architecture).

### Working with forks & upstream (core of THIS job — think before the call)

Expect: **"How would you maintain a fork of K-9 Mail and keep merging
upstream?"** Strong answer shape:
1. Keep /e/OS-specific changes as a **small, well-isolated patch set** —
   fewer, cleaner commits touching as few upstream files as possible;
   prefer additive modules/flags over edits inside upstream code.
2. Track upstream on a branch; on each upstream release, **merge (or rebase
   the patch set) onto it**, resolve conflicts, run the full test/CI suite.
   Merge preserves history for a long-lived public fork; rebase keeps the
   patch set readable — say you'd follow the team's existing convention.
3. **Upstream everything that isn't /e/OS-specific** — every bugfix
   contributed upstream is a conflict you never merge again.
4. CI guards: build + tests against upstream tip regularly so drift
   surfaces early, not at release time.

### GitLab CI (gap — close it with fluency)

You know GitHub Actions; map the vocabulary: workflow → **pipeline**, job →
**job**, step → **script**, `on:` triggers → **rules/only**, runner =
runner, `.gitlab-ci.yml` at repo root, **stages** (build → test → deploy),
artifacts/caches similar, MR pipelines ≈ PR checks. Android specifics you
already do: lint + unit tests on MR, assemble on merge, signed builds on
tag. One honest line: "I've run this exact pipeline in GitHub Actions;
translating it to `.gitlab-ci.yml` is syntax, not concepts."
*If you have 2 spare hours before the technical round: push any Android
repo to gitlab.com and write a 3-stage `.gitlab-ci.yml`. Then it's not even
a gap.*

### Testing

Unit: JUnit + turbine for Flows, ViewModel tests with fake repos.
UI: Compose testing (`createComposeRule`, semantics matchers,
`onNodeWithText().performClick()`), Espresso for View-based forks.
Say the honest thing: forked apps often arrive with thin tests; first step
is characterization tests around what you're about to change.

### Privacy/security questions they might ask

- Data minimization: request the narrowest permission, request late,
  degrade gracefully when denied.
- Trackers: most "free" SDKs are trackers; /e/OS's Advanced Privacy exists
  because of this. Your line: in fintech work you already treated every
  third-party SDK as a liability to justify, not a default.
- Secure storage: EncryptedSharedPreferences/Keystore, biometric auth
  (you shipped it in SmartDocs), no secrets in logs or backups
  (`android:allowBackup` awareness).

---

## 4. Stories to have ready (STAR, 90 seconds each — write your own details in)

1. **Ratio Launcher deep-dive** — why built, hardest technical problem
   (widget hosting? app-list sync? cold start?), what you'd do differently.
   *This is your centerpiece. Rehearse it twice.*
2. **The 30% performance win** (Fair Pattern) — how you measured (profiler,
   startup metrics, frame stats), what you changed, how CI prevents
   regression. Numbers beat adjectives.
3. **MerchantDesk handover** — delivered feature-complete, wrote handover
   docs, transferred to client team. Shows professionalism when asked
   "tell me about a project that didn't launch."
4. **A hard bug** — pick one real one (ANR? memory leak? sync conflict?).
   They asked for "seamless, bug-free UX" — show your debugging method:
   reproduce → isolate → fix → add a test.
5. **Async remote collaboration** — a time written communication solved
   something (design doc, detailed MR description, issue thread). Their
   culture is async-first; this story matters more here than at most jobs.

---

## 5. HR / culture round

- **"Why Murena?"** — your Bangladesh privacy angle (cover letter, spoken
  aloud). It's genuine and no other candidate has it. Add: you want your
  work in the open, and you like that users of /e/OS *chose* privacy.
- **"Why should we hire you over an AOSP veteran?"** — "I've built the
  hardest class of default app — a launcher — in the modern toolkit you're
  migrating toward (Compose/Glance), I've shipped for users on low-end
  devices and weak networks for nine years, and I work the way your team
  works: async, in writing, through review."
- **Contractor/rate question** — it's a daily-rate contractor role. Decide
  your rate BEFORE the call. Research typical EU remote Android contractor
  rates and set your floor; don't improvise this live.
- **Availability, timezone overlap** (BD is UTC+6 — fine for EU async).

---

## 6. Consistency card — what your resume claims (don't contradict it)

- Compose experience: **Ratio Launcher + tawk.to app + Glance widgets, at
  Appcoder (2021–2023)**, ~6+ months of Compose work.
- Fair Pattern (2023–now): mobile document apps, **MerchantDesk** for
  client Reynal (handed over pre-launch), 30% perf win, GitHub Actions
  CI/CD, technical PM, async team.
- Fintech security work at Appcoder; SmartDocs = Kotlin/MVVM/Room/biometric;
  EzyGlobal = self-hosted Llama for privacy.
- Part-time LLM evaluation (Mercor/Invisible) since Jan 2026 — if asked,
  it's a few hours weekly and won't conflict with a contract role.

---

## 7. Questions YOU ask (pick 3–4)

- "Which default apps need the most love right now, and which are the
  hardest to keep in sync with upstream?"
- "Is Compose adoption happening in the forked apps, or mostly in
  greenfield /e/OS apps?" (Shows you understand interop reality.)
- "How does the team decide what gets upstreamed to the original projects
  versus kept as /e/OS patches?"
- "What does the release train look like — how do app updates reach users
  across /e/OS versions?"
- "How does the roadmap input process work in practice — the posting
  mentions every member shapes it?"

---

## 8. Before you hit send on the application

- [ ] PDF the resume + cover letter (browser → Cmd+P).
- [ ] Pin relevant repos on github.com/mahbubmunna (anything Kotlin/Compose;
      recruiters click the GitHub link).
- [ ] Create a gitlab.com account if you don't have one; poke around
      gitlab.e.foundation so "I've been reading your repos" is true.
- [ ] Decide your daily rate.
- [ ] Skim Bliss Launcher's issue tracker for 15 minutes — being able to
      reference one real open issue in the interview ("I saw the widget
      resize issue on Bliss…") is worth more than an hour of anything else.
