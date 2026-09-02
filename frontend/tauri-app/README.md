# Spine Toolbox User Mode

This is a parallel Tauri + Vue interface. The existing Qt interface and its startup path are unchanged.

## Development

From `frontend/tauri-app`:

```powershell
npm install
npm run tauri:dev
```

The Python bridge is optional for the first UI pass. Run it separately from the repository root when testing the local API:

```powershell
python -m spinetoolbox.frontend.user_mode
```

The bridge listens on `http://127.0.0.1:8765`.