# Mobile Roadmap — Android, iOS, Capacitor, AltStore

**Status**: Plan (not yet implemented)  
**PWA**: Done (manifest, service worker, icons, meta injection)  
**Environment**: Mac, Xcode 26.3, Apple Dev account

---

## Current State

| Output | Status |
|--------|--------|
| Web app (React/HTMX, FastAPI/Node) | Done |
| PWA (manifest, sw, icons, add-to-home-screen) | Done |
| Native Android APK | Not implemented |
| Native iOS IPA | Not implemented |
| Capacitor wrapper | Not implemented |

---

## Phase 1: PWA — Done

- manifest.json, sw.js, icons, theme-color, apple-mobile-web-app-capable
- Add-to-home-screen on iPhone and Android
- No store submission required

---

## Phase 2: Capacitor Wrapper (WebView + Native Shell)

**Goal**: Package the web app as a native shell (Android APK, iOS IPA) via Capacitor.

**Flow**:
1. Factory builds web app as today (React/HTMX + backend)
2. New specialist or post-step: run `npx cap init` in output
3. Add Capacitor config (app ID, name)
4. Copy web build (or serve from URL) into Capacitor `www/`
5. Add `capacitor.config.ts` with backend URL for API
6. Run `npx cap add android` and `npx cap add ios`

**Requirements**:
- Node/npm in factory environment
- For iOS: macOS + Xcode (we have both)
- For Android: Android SDK / Android Studio (or run on Mac via Capacitor CLI)

**Output**:
- `android/` and `ios/` folders in output
- User runs `npx cap sync` and opens in Xcode/Android Studio to build

**Complexity**: Medium. Capacitor CLI is well-documented. Main work: wiring into factory, handling hybrid vs static-only stacks.

---

## Phase 3: Automated iOS Build (Xcode + AltStore)

**Goal**: Produce IPA from factory run, distributable via AltStore.

**Flow**:
1. Capacitor output present (Phase 2)
2. Run `npx cap sync ios`
3. Use `xcodebuild` (or Fastlane) to archive and export IPA
4. Sign with Apple Dev account (provisioning profile, certificate)
5. Output: `output_001/builds/MyApp.ipa`

**Requirements**:
- Mac with Xcode 26.3 — we have
- Apple Developer account — we have
- Provisioning profile + signing cert (configurable)
- Optional: Fastlane for automation

**AltStore**:
- AltStore accepts standard IPA files
- User installs AltServer on Mac/PC, adds device, sideloads IPA
- No change to build output — same IPA works for TestFlight, AltStore, or ad-hoc

**Complexity**: High. Signing and provisioning are fiddly. Recommend Fastlane match for cert management.

---

## Phase 4: Automated Android Build

**Goal**: Produce APK/AAB from factory run.

**Flow**:
1. Capacitor output present (Phase 2)
2. Run `npx cap sync android`
3. Run `./gradlew assembleRelease` (or bundleRelease for AAB)
4. Sign with keystore (user-provided or generated)
5. Output: `output_001/builds/MyApp.apk`

**Requirements**:
- Android SDK (Android Studio or cmdline-tools)
- Keystore for release signing

**Complexity**: Medium. Gradle builds are scriptable. Keystore handling is the main config item.

---

## Suggested Implementation Order

| Phase | Content | Effort |
|-------|---------|--------|
| 1 | PWA | Done |
| 2a | Capacitor init + android/ios folders | 1–2 days |
| 2b | Factory flag: `--mobile` to enable Capacitor step | 0.5 day |
| 3 | iOS build script (xcodebuild or Fastlane) | 2–3 days |
| 4 | Android build script (Gradle) | 1–2 days |
| 5 | AltStore distribution doc (how to sideload) | 0.5 day |

---

## File Layout (Target)

```
output_001/
  ...existing app...
  android/           # Capacitor
  ios/               # Capacitor
  capacitor.config.ts
  builds/            # After build step
    MyApp.ipa
    MyApp.apk
```

---

## References

- [Capacitor](https://capacitorjs.com/docs)
- [AltStore](https://altstore.io/)
- [Fastlane](https://fastlane.tools/)
- [Xcode build for export](https://developer.apple.com/documentation/xcode/distributing-your-app-for-testing)
