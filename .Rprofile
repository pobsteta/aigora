# .Rprofile du projet AIGORA
# 1. Charge d'abord ton .Rprofile personnel (sinon R l'ignorerait dans ce projet).
# 2. Charge les fonctions d'aide AIGORA (R/aigora.R). Rien n'est lancé automatiquement.
# 3. Si AIGORA_R_MCP=1 dans .env et que le paquet btw est installé, rend cette session R
#    visible par Claude Code (serveur MCP « r-session », voir docs/RSTUDIO-QGIS.md).
local({
  perso <- path.expand("~/.Rprofile")
  if (file.exists(perso) && normalizePath(perso) != normalizePath(".Rprofile", mustWork = FALSE)) {
    source(perso)
  }
  if (file.exists("R/aigora.R")) {
    sys.source("R/aigora.R", envir = attach(NULL, name = "aigora"))
    if (interactive()) {
      message("AIGORA chargé. aigora_demarrer() pour lancer l'assistant, aigora_aide() pour les commandes.")
    }
  }
  if (interactive() && file.exists(".env") &&
      any(grepl("^\\s*AIGORA_R_MCP\\s*=\\s*1\\s*$", readLines(".env", warn = FALSE))) &&
      requireNamespace("btw", quietly = TRUE)) {
    ok <- tryCatch({ btw::btw_mcp_session(); TRUE }, error = function(e) FALSE)
    if (ok) message("Session R visible par AIGORA (MCP r-session).")
  }
})
