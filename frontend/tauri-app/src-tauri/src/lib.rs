#[tauri::command]
fn python_bridge_url() -> String {
    "http://127.0.0.1:8765".to_string()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![python_bridge_url])
        .run(tauri::generate_context!())
        .expect("error while running Spine Toolbox user mode");
}