use std::io::{BufRead, BufReader, Write};
use std::process::{Child, ChildStdin, ChildStdout, Command, Stdio};
use std::sync::Mutex;

struct PythonBridge {
    process: Option<Child>,
    stdin: Option<ChildStdin>,
    stdout: Option<BufReader<ChildStdout>>,
    next_id: u64,
}

impl PythonBridge {
    fn new() -> Self {
        Self { process: None, stdin: None, stdout: None, next_id: 1 }
    }

    fn request(&mut self, request: &str) -> Result<String, String> {
        if self.process.is_none() {
            let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../../..");
            let mut process = Command::new("python")
                .args(["-m", "spinetoolbox.frontend.user_mode_rpc"])
                .current_dir(root)
                .stdin(Stdio::piped())
                .stdout(Stdio::piped())
                .stderr(Stdio::inherit())
                .spawn()
                .map_err(|error| format!("Could not start Python bridge: {error}"))?;
            self.stdin = process.stdin.take();
            self.stdout = process.stdout.take().map(BufReader::new);
            self.process = Some(process);
        }
        let id = self.next_id;
        self.next_id += 1;
        let mut message: serde_json::Value = serde_json::from_str(request).map_err(|error| error.to_string())?;
        message["id"] = serde_json::json!(id);
        let line = serde_json::to_string(&message).map_err(|error| error.to_string())? + "\n";
        self.stdin.as_mut().ok_or("Python bridge stdin unavailable")?.write_all(line.as_bytes()).map_err(|error| error.to_string())?;
        self.stdin.as_mut().unwrap().flush().map_err(|error| error.to_string())?;
        let mut response = String::new();
        self.stdout.as_mut().ok_or("Python bridge stdout unavailable")?.read_line(&mut response).map_err(|error| error.to_string())?;
        Ok(response)
    }
}

#[tauri::command]
fn python_bridge_request(state: tauri::State<'_, Mutex<PythonBridge>>, request: String) -> Result<String, String> {
    state.lock().map_err(|_| "Python bridge lock poisoned".to_string())?.request(&request)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(Mutex::new(PythonBridge::new()))
        .invoke_handler(tauri::generate_handler![python_bridge_request])
        .run(tauri::generate_context!())
        .expect("error while running Spine Toolbox user mode");
}