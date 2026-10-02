#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

// Tauri Desktop Shell Entrypoint
// Strictly isolates frontend from OS shell and raw database credentials.
// All communication flows over authenticated HTTPS/WSS to FastAPI backend.

fn main() {
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error while running AI DataLab desktop application");
}
