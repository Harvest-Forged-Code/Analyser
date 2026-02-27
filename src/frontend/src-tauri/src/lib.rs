use std::path::PathBuf;
use std::process::{Child, Command};
use std::sync::Mutex;
use std::time::Duration;
use tauri::Manager;

struct ApiProcess(Mutex<Option<Child>>);

// ── Sidecar path resolution (release builds only) ────────────────────────────

#[cfg(not(debug_assertions))]
fn resolve_sidecar_path() -> Option<PathBuf> {
    let exe_dir = std::env::current_exe().ok()?.parent()?.to_path_buf();
    let name = if cfg!(windows) {
        "budget-analyser-api.exe"
    } else {
        "budget-analyser-api"
    };
    let path = exe_dir.join(name);
    path.exists().then_some(path)
}

// ── API launch (release) ──────────────────────────────────────────────────────

#[cfg(not(debug_assertions))]
fn start_python_api(data_dir: &PathBuf) -> Option<Child> {
    if check_api_health() {
        println!("Python API already running on port 8741");
        return None;
    }

    let sidecar = match resolve_sidecar_path() {
        Some(p) => p,
        None => {
            eprintln!("Sidecar binary not found next to app executable");
            return None;
        }
    };

    println!("Starting sidecar: {:?}", sidecar);
    match Command::new(&sidecar)
        .env("BUDGET_ANALYSER_DATA_DIR", data_dir.to_string_lossy().as_ref())
        .spawn()
    {
        Ok(child) => {
            println!("Sidecar started (pid: {})", child.id());
            Some(child)
        }
        Err(e) => {
            eprintln!("Failed to start sidecar: {}", e);
            None
        }
    }
}

// ── API launch (dev / debug) ──────────────────────────────────────────────────

#[cfg(debug_assertions)]
fn find_project_root() -> PathBuf {
    let cwd = std::env::current_dir().unwrap_or_default();
    if cwd.ends_with("frontend") {
        cwd.parent()
            .and_then(|p| p.parent())
            .map(|p| p.to_path_buf())
            .unwrap_or(cwd)
    } else if cwd.ends_with("src") {
        cwd.parent().map(|p| p.to_path_buf()).unwrap_or(cwd)
    } else {
        cwd
    }
}

#[cfg(debug_assertions)]
fn start_python_api(_data_dir: &PathBuf) -> Option<Child> {
    if check_api_health() {
        println!("Python API already running on port 8741");
        return None;
    }

    let project_root = find_project_root();
    let candidates: Vec<PathBuf> = vec![
        project_root.join(".venv/bin/python"),
        PathBuf::from("python3"),
        PathBuf::from("python"),
    ];

    for python in &candidates {
        match Command::new(python)
            .args(["-m", "budget_analyser.api.main"])
            .current_dir(&project_root)
            .spawn()
        {
            Ok(child) => {
                println!("Dev: started Python API (pid: {})", child.id());
                std::thread::sleep(Duration::from_secs(2));
                return Some(child);
            }
            Err(_) => continue,
        }
    }

    eprintln!("Dev: could not start Python API");
    None
}

// ── Health check ─────────────────────────────────────────────────────────────

fn check_api_health() -> bool {
    reqwest::blocking::get("http://127.0.0.1:8741/api/health")
        .map(|r| r.status().is_success())
        .unwrap_or(false)
}

// ── Tauri entry point ─────────────────────────────────────────────────────────

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            let data_dir = app
                .path()
                .app_data_dir()
                .expect("Failed to resolve app data directory");

            println!("App data directory: {:?}", data_dir);

            let child = start_python_api(&data_dir);
            app.manage(ApiProcess(Mutex::new(child)));

            // Poll health check — 20 attempts × 500 ms = 10 s max
            let mut healthy = false;
            for attempt in 1..=20 {
                if check_api_health() {
                    println!("API health check passed (attempt {})", attempt);
                    healthy = true;
                    break;
                }
                std::thread::sleep(Duration::from_millis(500));
            }

            if !healthy {
                eprintln!("Warning: Python API did not respond after 10 s");
            }

            Ok(())
        })
        .on_window_event(|window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                let app = window.app_handle();
                if let Some(state) = app.try_state::<ApiProcess>() {
                    if let Ok(mut guard) = state.0.lock() {
                        if let Some(ref mut child) = *guard {
                            println!("Shutting down API sidecar (pid: {})", child.id());
                            let _ = child.kill();
                        }
                    }
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
