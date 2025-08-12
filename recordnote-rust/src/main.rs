use anyhow::Result;
use env_logger;
use recordnote::ui::app::RecordNoteApp;

#[tokio::main]
async fn main() -> Result<()> {
    // Initialize logger
    env_logger::init();

    log::info!("Starting RecordNote application");

    // Create and launch the application
    let app = RecordNoteApp::new()?;
    app.launch()?;

    log::info!("Application terminated");
    Ok(())
}