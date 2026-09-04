# fafaudio — XACT Web Builder

Personal-use web service to compile WAV files into FAF-compatible XACT bundles (`.xwb` / `.xsb` / `.xgs`) without opening the XACT GUI. Password-protected.

## Deployment

### 1. Put XACT binaries on your proxmox host

The container needs the XACT command-line builder plus its DLLs. These live on your Windows PC after installing the older DirectX SDK. Copy the whole `Utilities\Bin\x86\` folder contents to a folder on your proxmox host, e.g.:

```
/root/fafaudio-xact-binaries/
├── XactBld3.exe        (or XactBld.exe)
├── XactEngine3_*.dll
├── XactInterop3.dll
└── (other files from that Bin\x86 folder)
```

These MUST NOT go into git (Microsoft licence). The container mounts this folder read-only.

### 2. Set up the stack in dockhand

Create a new stack in dockhand and paste the following `docker-compose.yml`:

```yaml
name: fafaudio

volumes:
  fafaudio_wine:

services:
  app:
    build: https://github.com/Nuggets75/fafaudio.git#main
    container_name: fafaudio
    restart: unless-stopped
    ports:
      - "8096:5000"
    volumes:
      - fafaudio_wine:/wine
      - /root/fafaudio-xact-binaries:/xact-binaries:ro
    environment:
      - ADMIN_PASSWORD=CHANGE-ME-BEFORE-DEPLOY
```

Replace:
- The left-hand side of the `xact-binaries` mount → your actual host path from step 1
- `CHANGE-ME-BEFORE-DEPLOY` → a strong password of your choice

Deploy the stack. On first start, dockhand triggers a docker build (clones this repo, installs wine + python, ~5 minutes). Subsequent restarts are instant.

### 3. Reverse proxy

Point NPM at `<proxmox-ip>:8096` for `fafaudio.doodlepros.com`. Nothing else to configure — the app assumes HTTPS via reverse proxy.

## Using the site

- Open https://fafaudio.doodlepros.com
- Log in with your ADMIN_PASSWORD
- Enter a bank name (defaults to `SoundBank`)
- Upload WAV files (cue name = filename without extension)
- Hit Build → downloads a zip with the three output files

## Security

- Password from env var, compared with `hmac.compare_digest` (constant-time)
- Session cookies: signed, HTTPS-only, HttpOnly, SameSite=Lax, 12h expiry
- Login rate-limited: 5 attempts per IP per 5 min → 429
- SECRET_KEY auto-generated on first start and persisted with the wine volume so sessions survive restarts

Only login/health are unauthenticated. Everything else requires a valid session.

## Troubleshooting

- **First build is slow** (~5 min): normal, wine + apt packages downloading
- **"XactBld binary not found"**: check host path is correct and folder isn't empty; `docker exec fafaudio ls /wine/drive_c/xact/` should show the exe
- **Force re-install XACT**: `docker exec fafaudio rm /wine/.dxsdk-installed`, then restart
- **Build fails with output errors**: the UI shows wine's stdout/stderr plus the generated `.xap` — most likely a missing field in `app/xap_generator.py`. See the section below.

## Iterating on the .xap format

`app/xap_generator.py` is my best-effort recreation of the 2008 XACT project format. If XactBld rejects it, the error page shows both the wine output AND the generated `.xap`. Compare the `.xap` against one you built with the GUI, find the missing/wrong fields, edit the string constants at the top of `xap_generator.py`, `git push`, redeploy the stack (dockhand rebuilds).
