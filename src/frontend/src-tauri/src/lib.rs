use tauri::Manager;
use std::path::PathBuf;
use std::process::{Command, Child};
use std::sync::Mutex;
use std::time::Duration;

struct ApiProcess(Mutex<Option<Child>>);

fn find_project_root() -> PathBuf {
    // src-tauri is inside src/frontend/, so project root is two levels up
    let cwd = std::env::current_dir().unwrap_or_default();
    if cwd.ends_with("frontend") {
        // CWD is src/frontend/ — go up two levels to project root
        cwd.parent()
            .and_then(|p| p.parent())
            .map(|p| p.to_path_buf())
            .unwrap_or(cwd)
    } else if cwd.ends_with("src") {
        // CWD is src/ — go up one level
        cwd.parent().map(|p| p.to_path_buf()).unwrap_or(cwd)
    } else {
        // Already at project root or somewhere else
        cwd
    }
}

fn start_python_api() -> Option<Child> {
    // If API is already running (started externally), skip spawning
    if check_api_health() {
        println!("Python API already running on port 8741");
        return None;
    }

    let project_root = find_project_root();
    let venv_python = project_root.join(".venv/bin/python");

    // Try venv python first, then system python3, then python
    let python_candidates: Vec<PathBuf> = vec![
        venv_python,
        PathBuf::from("python3"),
        PathBuf::from("python"),
    ];

    for python in &python_candidates {
        println!("Trying Python at: {:?}", python);
        match Command::new(python)
            .args(["-m", "budget_analyser.api.main"])
            .current_dir(&project_root)
            .spawn()
        {
            Ok(child) => {
                println!("Started Python API with {:?} (pid: {})", python, child.id());
                std::thread::sleep(Duration::from_secs(2));
                return Some(child);
            }
            Err(e) => {
                eprintln!("Failed to start with {:?}: {}", python, e);
            }
        }
    }

    eprintln!("Could not start Python API with any python candidate");
    None
}

fn check_api_health() -> bool {
    match reqwest::blocking::get("http://127.0.0.1:8741/api/health") {
        Ok(resp) => resp.status().is_success(),
        Err(_) => false,
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .setup(|app| {
            // Start Python API as sidecar
            let child = start_python_api();
            app.manage(ApiProcess(Mutex::new(child)));

            // Health check with retries
            let mut healthy = false;
            for i in 0..20 {
                if check_api_health() {
                    println!("Python API health check passed (attempt {})", i + 1);
                    healthy = true;
                    break;
                }
                std::thread::sleep(Duration::from_millis(500));
            }

            if !healthy {
                eprintln!("Warning: Python API health check failed after 10s. API may not be running.");
            }

            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                // Kill Python API process on window close
                let app = window.app_handle();
                if let Some(state) = app.try_state::<ApiProcess>() {
                    if let Ok(mut guard) = state.0.lock() {
                        if let Some(ref mut child) = *guard {
                            println!("Shutting down Python API (pid: {})", child.id());
                            let _ = child.kill();
                        }
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
