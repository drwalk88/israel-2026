# Israel 2026 Tour Notes

A one-page site with the teaching notes from our September 2026 tour of Israel: a table of contents, search, and a player for the recording behind each stop.

## Put it on GitHub Pages

1. Create a new repository on GitHub (for example `israel-2026`). Free GitHub Pages sites need a public repo.
2. Upload `index.html` and `recordings.js` (the other files are only needed to rebuild the page).
3. In the repo go to **Settings → Pages**, set **Source** to *Deploy from a branch*, pick `main` and `/ (root)`, and save.
4. After a minute the site is live at `https://<your-username>.github.io/israel-2026/`.

The page tells search engines not to index it, but anyone with the link can open it.

## Hook up the audio (Google Drive)

1. Upload the `.m4a` files from `extracted_audio` to a Google Drive folder.
2. Share the folder: **Anyone with the link → Viewer** (or add the group's emails if you want it restricted; then people must be signed in to Google to play).
3. Paste the folder link into `recordings.js` as `DRIVE_FOLDER_URL`. Every "Listen" button will then point people to the folder.
4. For in-page playback, add each file's ID to its `driveId` in `recordings.js` (the part between `/d/` and `/view` in a file's share link).

Editing `recordings.js` doesn't need a rebuild; just upload the new version.

## Changing the notes

Edit `notes.md`, then run `python3 build.py` (needs `pip install markdown`) and upload the new `index.html`.
