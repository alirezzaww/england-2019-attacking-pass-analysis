# Website and device support

`web/` is a buildless, static HTML/CSS/JavaScript site. It has no backend, API keys,
account requirement or external script dependency. The website presents saved research;
it does not run Python or download match events in visitors' browsers.

## Preview locally

From the repository root, run `python -m http.server 8848 --directory web` and open
`http://localhost:8848`. Serve it over HTTP: opening `index.html` directly can prevent
JavaScript from loading `research.json`.

## Deploy your own copy

Upload the **contents of `web/`** to a static host (for example, GitHub Pages using a
`web/` artifact, Netlify, Cloudflare Pages, or another HTTP server). There is no build
command. Keep `index.html`, `style.css`, `app.js`, `research.json` and `assets/` together.
All local asset URLs are relative, allowing hosting under a path prefix.

The published portfolio uses Sites. Its source is mirrored from `web/` into a separate
hosting checkout. Editing this GitHub repository does not automatically update that
Sites deployment; publish the changed static files again through your host.

## Update research content

Reproduce and validate the Python evidence first. Update `web/research.json` from the
saved evidence and copy revised charts into `web/assets/`. Run
`python scripts/check_web.py` to check the mirror against current research artifacts.
Check interactions and narrow/wide layouts in a browser before publishing.

## Devices

The responsive presentation is intended for current desktop, tablet and phone browsers.
Wide scientific figures scroll inside their panels and can be opened at full size.
Python execution requires a suitable computer environment; this is not a native iOS
or Android application. Cross-platform CI checks artifacts and syntax, not every
operating system's plotting installation or every physical device.
