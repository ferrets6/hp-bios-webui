# hp-bios-webui

Web UI that reconstructs the HP F10 "Computer Setup" BIOS menu for a
specific machine (HP ProDesk 400 G5 MT, BIOS Q03 Ver. 02.07.00) and lets
you read/change every setting remotely, without ever needing a keyboard
plugged into that physical machine.

## Why this works

Recent HP business PCs expose their entire BIOS configuration through the
Linux kernel's `hp-bioscfg` driver, under
`/sys/class/firmware-attributes/hp-bioscfg/`. Every BIOS Setup screen item
shows up there as a small directory with `current_value`,
`possible_values`, and `type` files. Reading is unprivileged; writing
requires root.

In this setup, the machine in question is a TrueNAS SCALE NAS. TrueNAS's
root filesystem is a **read-only** ZFS boot environment (that's also why
`apt`/`dpkg` are disabled on it), so nothing can be installed or dropped
onto `/usr/local` there. The one writable+executable location is the data
pool used for Apps (`/mnt/apps-temp`), which is where the control script
lives.

## Architecture

```
Browser  --https-->  bios-webui container (on your deployment host)  --ssh-->  target machine (hp-bioscfg sysfs)
```

- `backend/` - FastAPI app. Reads sysfs over a persistent SSH connection
  (no privilege needed). Writes and reboot go through a tiny root-owned
  wrapper script on the NAS (`bios-webui-ctl`), invoked via a narrowly
  scoped `NOPASSWD` sudoers rule - the container never holds a root
  password.
- `frontend/` - plain HTML/CSS/JS, styled to resemble the real HP BIOS
  blue-screen setup UI. Tabs = Main/Security/Advanced, matching HP's own
  "HP PC Commercial BIOS (UEFI) Setup Administration Guide"
  (919946-003). Changes are staged locally and only sent to the NAS when
  you click **F10 Save Changes and Exit**, exactly like the real BIOS.
  If the kernel reports `pending_reboot`, a "Reboot Now" prompt appears
  (a graceful `systemctl reboot`, never a hard power cycle).
- `deploy/nas_setup.sh` - **one-time setup you run yourself directly on
  the NAS** (it needs your sudo password once). See below.

## One-time NAS setup

This step needs to be run by you, once, directly via SSH on the NAS - it
edits `/etc/sudoers.d/`, which is sensitive enough that it shouldn't be
automated blindly. The exact commands were given to you separately.
It creates:

1. `/mnt/apps-temp/bios-webui/bios-webui-ctl` - a small root-owned script
   that only knows how to (a) write one attribute's `current_value`, after
   validating the name against the real sysfs directory and rejecting any
   `..`/`/` in it, (b) write a BIOS password via the `authentication/`
   sysfs interface, or (c) run `systemctl reboot`. Nothing else.
2. `/etc/sudoers.d/bios-webui` - `<your-ssh-user> ALL=(root) NOPASSWD:
   <path-to>/bios-webui-ctl` and nothing more. The install path used above
   (`/mnt/apps-temp/...`) is just an example of a writable+executable data
   pool; use whatever equivalent exists on your system if its root
   filesystem is also read-only.

## Deploying

```bash
git clone <this repo> ~/bios-webui
cd ~/bios-webui
cp .env.example .env
# edit .env with your own NAS_HOST, NAS_USER, NAS_SSH_KEY_HOST_PATH, etc.

# generate the dedicated keypair the container uses to reach NAS_HOST
# (empty passphrase - the container reads it non-interactively)
ssh-keygen -t ed25519 -f ./id_ed25519 -N "" -C "bios-webui@$(hostname)"
ssh-copy-id -i ./id_ed25519.pub <your-ssh-user>@<your-nas-host>

docker compose up -d --build
```

`id_ed25519`/`id_ed25519.pub` land in the project root and are
gitignored, never committed. `NAS_SSH_KEY_HOST_PATH` in `.env` just
needs to point at that file.

### Why a mounted file instead of an env var for the key

The key is passed to the container as a read-only bind-mounted file
(`/run/secrets/nas_ssh_key`), not as an environment variable, on
purpose: env vars are visible in plaintext via `docker inspect`, leak
into every child process the container spawns, and are awkward for
multi-line PEM/OpenSSH key material (which needs escaping to survive a
`.env` parser). A mounted, permission-restricted file is the standard
Docker pattern for secrets like this - it's exactly what Docker
Compose's own top-level `secrets:` block does under the hood.

### Managing the key

- `id_ed25519` / `id_ed25519.pub` live in the project root, next to
  `docker-compose.yml`. **Never move or rename `.gitignore`'s entries
  for them** - that's the only thing standing between this key and a
  public GitHub repo.
- Verify at any time that git actually ignores them:
  `git status --ignored` should list `.env`, `id_ed25519` and
  `id_ed25519.pub` under "Ignored files", never under "Changes to be
  committed". `git add -A`/`git add .` cannot pick them up as long as
  they're in `.gitignore`; only an explicit `git add -f` could.
- To rotate the key (e.g. after a suspected leak, or when pointing this
  at a new NAS): delete the two files, regenerate with the
  `ssh-keygen` command above, and re-run `ssh-copy-id` against the new
  target - no code or `.env` changes needed, since `NAS_SSH_KEY_HOST_PATH`
  already points at this fixed location.
- `docker compose up -d` (no rebuild needed) picks up a rotated key
  immediately on the next container restart, since it's just a bind
  mount, not baked into the image.

## Known limitations

- Categorization of the 182 exposed attributes into Main/Security/Advanced
  sections (`backend/app/schema.py`) was built by cross-referencing HP's
  official setup guide against the actual attribute names found on this
  machine. Anything not explicitly mapped still shows up (nothing is
  hidden), just without a curated section - check `known: false` in
  `/api/attributes`.
- `integer`-typed attributes don't expose a min/max via sysfs on this
  kernel version, so the UI just gives you a plain number field.
- This is built for **this specific machine and BIOS version**. Attribute
  names can differ across BIOS revisions.
