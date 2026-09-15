# Desktop releases

`announcement.json` has exactly three fields: `version`, `download`, and `messages`.
The website reads it to display the download link and release message.

The app's Tauri updater reads `https://plorangelab.com/updates/latest.json`.
That file is created by `scripts/prepare_update.py` only after the first signed
release has been built and uploaded. There is deliberately no fake installer URL
or signature in this repository. Until publication, the app's background update
check silently ignores the missing manifest; a manual check reports unavailable.

## Publish a release

1. Build in the app repository with `pnpm release:build --version 0.2.0 --notes-file docs/release-notes.md`.
2. Upload the `.exe` and `.exe.sig` from its `release/v0.2.0` directory to the
   `v0.2.0` release in `bpodol/landing`. The installer asset name must match
   `latest.json` exactly. Release assets must be publicly downloadable.
3. Publish that GitHub release before announcing it on the website.
4. From this repository, run:

   ```powershell
   python scripts/prepare_update.py --release-dir "D:\flopzilla plo\tauri2-starter\release\v0.2.0" --assets-published
   git add updates/latest.json updates/announcement.json index.html
   git commit -m "Publish desktop version 0.2.0"
   git push origin main
   ```

The script copies only public metadata and updates the fallback download link.
It does not build, upload, test, commit, or push anything. `--assets-published`
confirms that you have already published the referenced installer. This prevents
announcing an installer while it is still a draft release.

Vercel must deploy the commit before the app can see the update. Repeat with a
higher version for each release. Never overwrite an already published installer:
each `latest.json` signature must correspond to its exact installer bytes.

Updater signing keys and passwords belong only in the app's ignored local files
or private CI secrets. They must never enter this website repository or deployment.
The updater public key is embedded in the desktop app; the existing license key
is separate and is not changed by this process.
