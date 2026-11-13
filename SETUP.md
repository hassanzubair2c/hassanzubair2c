# Setup (about 10 minutes)

1. **Create the profile repo.** On GitHub, make a new public repo named exactly
   `hassanzubair1c` (same as your username). GitHub shows its README on your profile.

2. **Upload these files** to it, keeping the folder structure:
   `README.md`, `today.py`, `ascii_art.py`, `ascii.txt`, `dark_mode.svg`,
   `light_mode.svg`, `.github/workflows/build.yaml`.

3. **Create a token.** Settings → Developer settings → Personal access tokens →
   Tokens (classic) → Generate. Scopes: `repo` and `read:user`. Copy it.

4. **Add it as a secret.** In the profile repo: Settings → Secrets and variables →
   Actions → New repository secret. Name: `ACCESS_TOKEN`, value: the token.

5. **Run it.** Actions tab → "Update profile card" → Run workflow. The first run can
   take a few minutes (GitHub computes line counts per repo). After that it
   refreshes every 6 hours on its own.

## Customising

- **Your text:** edit the `INFO` list and `UPTIME_SINCE` at the top of `today.py`.
- **Your face in ASCII:** put a cropped headshot in the folder and run
  `pip install pillow && python ascii_art.py photo.png`
  (options: `--cols`, `--zoom`, `--crop`, `--invert`; a background-removed PNG works best). It overwrites `ascii.txt`;
  commit it and the workflow rebuilds the card.
- **Preview locally without a token:** `python today.py --demo`.
