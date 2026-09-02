# Spine Toolbox User Mode

This is a parallel Tauri + Vue interface. The existing Qt interface and its startup path are unchanged.

## Development

From `frontend/tauri-app`:

```powershell
npm install
npm run tauri:dev
```

Tauri starts one managed Python bridge process automatically. The Vue application communicates with it through
Tauri commands and JSON-lines messages; no manually started web server is required.