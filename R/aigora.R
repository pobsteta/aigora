# =============================================================================
# AIGORA : fonctions d'aide pour RStudio
# Chargées automatiquement à l'ouverture du projet (voir .Rprofile).
#
#   aigora_verifier()          vérifie les prérequis (Python, Claude Code, Node, Quarto...)
#   aigora_demarrer()          ouvre un terminal RStudio et lance Claude Code
#   aigora_env()               crée .env depuis .env.example (si besoin) et l'ouvre
#   aigora_env_ranger()        remet à leur place les lignes ajoutées en fin de .env (copie gardée)
#   aigora_ksuite(test=FALSE)  état de la connexion kSuite (test=TRUE : teste IMAP/SMTP/CalDAV)
#   aigora_mcp(simulation=TRUE) enregistre les serveurs MCP Infomaniak dans Claude Code
#   aigora_kdrive(chemin=NULL) donne à AIGORA l'accès au dossier kDrive synchronisé
#   aigora_contacts()          exporte et lit les contacts kSuite (CardDAV) en data.frame
#   aigora_taches()            tâches de l'agenda kSuite (CalDAV) en data.frame
#   aigora_leads()             lit data/leads.csv (prospects analysés) en data.frame
#   aigora_odoo_configurer()   connecte Odoo CRM (adresse, base, identifiant, clé API)
#   aigora_odoo_pipeline()     opportunités Odoo CRM en data.frame
#   aigora_installer_r_mcp()   installe btw + mcptools (Claude voit ta session R)
#   aigora_r_mcp(TRUE/FALSE)   active / désactive le serveur MCP de la session R
#   aigora_qgis_mcp(TRUE/FALSE) active / désactive le serveur MCP QGIS
#   aigora_qfieldcloud_installer() installe le SDK QFieldCloud (Python)
#   aigora_qfieldcloud_login(url) connexion QFieldCloud : seul le jeton est enregistré
#   aigora_qfieldcloud_projets() projets QFieldCloud en data.frame
#   aigora_aide()              rappelle ces commandes
# =============================================================================

.aigora_racine <- function() {
  dir <- normalizePath(getwd(), winslash = "/", mustWork = FALSE)
  repeat {
    if (file.exists(file.path(dir, "CLAUDE.md"))) return(dir)
    parent <- dirname(dir)
    if (identical(parent, dir)) stop("Dossier AIGORA introuvable : ouvre le projet AIGORA.Rproj.", call. = FALSE)
    dir <- parent
  }
}

.aigora_python <- function() {
  candidats <- c("python3", "python", "py")
  for (cmd in candidats) {
    chemin <- Sys.which(cmd)
    if (nzchar(chemin) && !grepl("WindowsApps", chemin, fixed = TRUE)) {
      ok <- tryCatch(
        system2(chemin, "--version", stdout = TRUE, stderr = TRUE),
        error = function(e) character(0)
      )
      if (length(ok) && grepl("Python 3", ok[1])) return(unname(chemin))
    }
  }
  ""
}

# Conseil à afficher selon la variable manquante dans .env
.aigora_conseil <- function(variable) {
  if (grepl("^KSUITE_(DAV|MAIL|CARDDAV|CALDAV)|^KCHAT_WEBHOOK", variable)) {
    return("Lance aigora_ksuite_configurer() : quelques questions, et c'est enregistré.")
  }
  if (grepl("^QFIELDCLOUD", variable)) return("Lance aigora_qfieldcloud_login().")
  if (grepl("^ODOO_", variable)) return("Lance aigora_odoo_configurer() (guide : docs/ODOO.md).")
  if (grepl("^INFOMANIAK_TOKEN|^KDRIVE_ID|^KCHAT_TEAM", variable)) {
    return("Voir docs/KSUITE.md, section « Serveurs MCP officiels ».")
  }
  "Voir docs/KSUITE.md."
}

# Lit le champ texte "cle" d'une sortie JSON (sans dépendance)
.aigora_champ <- function(sortie, cle) {
  texte <- paste(sortie, collapse = "\n")
  m <- regmatches(texte, regexpr(paste0('"', cle, '"\\s*:\\s*"(\\\\.|[^"\\\\])*"'), texte))
  if (!length(m)) return(NA_character_)
  valeur <- sub(paste0('^"', cle, '"\\s*:\\s*"'), "", m)
  gsub('\\\\"', '"', sub('"$', "", valeur))
}

.aigora_succes <- function(sortie) {
  any(grepl('"success"\\s*:\\s*true', sortie))
}

# Affiche un échec en français, sans JSON brut
.aigora_echec <- function(sortie) {
  manquant <- .aigora_champ(sortie, "missing")
  erreur <- .aigora_champ(sortie, "error")
  if (!is.na(manquant)) {
    message("AIGORA : il manque ", manquant, " dans .env.\n  -> ", .aigora_conseil(manquant))
  } else if (!is.na(erreur)) {
    message("AIGORA : ", erreur)
  } else {
    message("AIGORA : échec du script.\n", paste(utils::tail(sortie, 5), collapse = "\n"))
  }
}

.aigora_script <- function(script, args = character(0), afficher = TRUE, dossier = "ksuite-setup") {
  py <- .aigora_python()
  if (!nzchar(py)) stop("Python 3 introuvable. Installe-le depuis python.org (cocher 'Add python.exe to PATH').", call. = FALSE)
  racine <- .aigora_racine()
  chemin <- file.path(racine, ".claude", "skills", dossier, "scripts", script)
  ancien <- setwd(racine)
  on.exit(setwd(ancien), add = TRUE)
  sortie <- suppressWarnings(system2(py, c(shQuote(chemin), args), stdout = TRUE, stderr = TRUE))
  # retire les avertissements Python (DeprecationWarning...) qui précèdent le JSON
  debut <- grep("^\\{", sortie)[1]
  if (!is.na(debut)) sortie <- sortie[debut:length(sortie)]
  ok <- .aigora_succes(sortie)
  if (afficher) {
    if (ok) cat(sortie, sep = "\n") else .aigora_echec(sortie)
  }
  attr(sortie, "ok") <- ok
  invisible(sortie)
}

aigora_verifier <- function() {
  racine <- .aigora_racine()
  version_de <- function(cmd, arg = "--version") {
    chemin <- Sys.which(cmd)
    if (!nzchar(chemin)) return(NA_character_)
    v <- tryCatch(system2(chemin, arg, stdout = TRUE, stderr = TRUE)[1], error = function(e) NA_character_)
    if (is.null(v) || !length(v)) NA_character_ else trimws(v)
  }
  py <- .aigora_python()
  verifs <- data.frame(
    outil = c("Python 3", "Claude Code", "Node.js (npx)", "uv (uvx)", "Quarto", "Ollama", "Paquet R btw"),
    requis = c("oui", "oui", "serveurs MCP kSuite", "serveur MCP QGIS", "pour quarto-slides", "mémoire avancée", "serveur MCP session R"),
    version = c(
      if (nzchar(py)) system2(py, "--version", stdout = TRUE, stderr = TRUE)[1] else NA_character_,
      version_de("claude"),
      version_de("npx"),
      version_de("uvx"),
      version_de("quarto"),
      version_de("ollama"),
      if (requireNamespace("btw", quietly = TRUE)) as.character(utils::packageVersion("btw")) else NA_character_
    ),
    stringsAsFactors = FALSE
  )
  verifs$statut <- ifelse(is.na(verifs$version), "absent", "ok")
  print(verifs[, c("outil", "statut", "version", "requis")], row.names = FALSE)

  if (!file.exists(file.path(racine, ".env"))) {
    message("\n.env absent : normal tant que tu n'as pas connecté de service. Lance aigora_env() pour le créer.")
  }
  if (Sys.which("claude") == "") {
    message("\nClaude Code introuvable. Installation : https://docs.claude.com/en/docs/claude-code/setup")
  }
  if (Sys.which("quarto") == "") {
    message("Quarto n'est pas dans le PATH du terminal. RStudio l'embarque, mais pour la ligne de commande : https://quarto.org/docs/get-started/")
  }
  invisible(verifs)
}

aigora_demarrer <- function() {
  racine <- .aigora_racine()
  if (Sys.which("claude") == "") {
    stop("Claude Code n'est pas installé (commande 'claude' introuvable). Lance aigora_verifier().", call. = FALSE)
  }
  if (requireNamespace("rstudioapi", quietly = TRUE) && rstudioapi::isAvailable()) {
    # Un terminal "AIGORA" existe déjà ? On le réutilise au lieu d'en créer un second.
    existant <- NULL
    for (tid in rstudioapi::terminalList()) {
      legende <- tryCatch(rstudioapi::terminalContext(tid)$caption, error = function(e) NULL)
      if (identical(legende, "AIGORA")) { existant <- tid; break }
    }
    if (!is.null(existant)) {
      vivant <- tryCatch(rstudioapi::terminalRunning(existant), error = function(e) FALSE)
      occupe <- tryCatch(rstudioapi::terminalBusy(existant), error = function(e) FALSE)
      if (isTRUE(vivant) && isTRUE(occupe)) {
        rstudioapi::terminalActivate(existant, show = TRUE)
        message("AIGORA tourne déjà dans l'onglet Terminal 'AIGORA' : je l'affiche.")
        return(invisible(TRUE))
      }
      if (isTRUE(vivant)) {
        rstudioapi::terminalActivate(existant, show = TRUE)
        rstudioapi::terminalSend(existant, "claude\n")
        message("AIGORA relancé dans l'onglet Terminal 'AIGORA'.")
        return(invisible(TRUE))
      }
      rstudioapi::terminalKill(existant)  # terminal fermé ou planté : on le remplace
    }
    ancien <- setwd(racine)  # le terminal s'ouvre dans le dossier courant
    on.exit(setwd(ancien), add = TRUE)
    id <- tryCatch(
      rstudioapi::terminalCreate(caption = "AIGORA", show = TRUE),
      error = function(e) rstudioapi::terminalCreate(caption = paste("AIGORA", format(Sys.time(), "%H:%M:%S")), show = TRUE)
    )
    Sys.sleep(1)
    rstudioapi::terminalSend(id, "claude\n")
    message("AIGORA démarre dans l'onglet Terminal 'AIGORA'. Pour commencer : « Configure mon business ».")
  } else {
    message("Ouvre l'onglet Terminal de RStudio (Alt+Maj+R), puis tape :  claude")
    message("(Astuce : install.packages(\"rstudioapi\") permet à aigora_demarrer() de le faire pour toi.)")
  }
  invisible(TRUE)
}

aigora_env <- function() {
  racine <- .aigora_racine()
  env <- file.path(racine, ".env")
  if (!file.exists(env)) {
    file.copy(file.path(racine, ".env.example"), env)
    message(".env créé à partir de .env.example. Ne le partage jamais (il est ignoré par git).")
  }
  utils::file.edit(env)
  invisible(env)
}

aigora_ksuite_configurer <- function() {
  racine <- .aigora_racine()
  env <- file.path(racine, ".env")
  if (!file.exists(env)) file.copy(file.path(racine, ".env.example"), env)
  oui <- function(q) tolower(substr(.aigora_demander(paste(q, "(o/n)")), 1, 1)) %in% c("o", "y")
  fait <- character(0)

  cat("\n1/3  Agenda, tâches et contacts (CalDAV / CardDAV)\n",
      "    Identifiant COURT (ex. AB12345), pas ton adresse mail :\n",
      "    https://config.infomaniak.com > Mon agenda > Synchronisation manuelle\n", sep = "")
  if (oui("Configurer l'agenda, les tâches et les contacts ?")) {
    utilisateur <- .aigora_demander("Identifiant court CalDAV (ex. AB12345) :")
    if (grepl("@", utilisateur)) message("  Attention : c'est l'identifiant court qui est attendu, pas l'adresse mail.")
    mdp <- .aigora_demander("Mot de passe d'application (pas celui du compte) :", secret = TRUE)
    if (nzchar(utilisateur) && nzchar(mdp)) {
      .aigora_set_env("KSUITE_DAV_USER", utilisateur)
      .aigora_set_env("KSUITE_DAV_PASSWORD", mdp)
      fait <- c(fait, "agenda, tâches, contacts")
    }
  }

  cat("\n2/3  Mail (IMAP/SMTP) : il faut un mot de passe D'APPAREIL propre à l'adresse mail\n",
      "    (différent du mot de passe d'application utilisé pour l'agenda) :\n",
      "    https://manager.infomaniak.com > Service Mail > ton domaine > ton adresse >\n",
      "    onglet « Appareils » > « Ajouter un appareil » (nom : AIGORA), puis copie le mot de passe.\n",
      "    Autre voie : l'assistant https://config.infomaniak.com\n", sep = "")
  if (oui("Configurer le mail ?")) {
    adresse <- .aigora_demander("Adresse mail kSuite :")
    mdp <- .aigora_demander("Mot de passe d'appareil de l'adresse mail :", secret = TRUE)
    if (nzchar(adresse) && nzchar(mdp)) {
      .aigora_set_env("KSUITE_MAIL_USER", adresse)
      .aigora_set_env("KSUITE_MAIL_PASSWORD", mdp)
      fait <- c(fait, "mail")
    }
  }

  cat("\n3/3  kChat : webhook entrant (kChat : icône « Nouveau » (+) à côté du nom de l'organisation > Intégrations > Webhooks entrants > Ajouter)\n")
  if (oui("Configurer kChat ?")) {
    url <- .aigora_demander("URL du webhook :")
    if (nzchar(url)) { .aigora_set_env("KCHAT_WEBHOOK_URL", url); fait <- c(fait, "kChat") }
  }
  if (exists("mdp")) rm(mdp)

  if (!length(fait)) { message("Rien n'a été modifié."); return(invisible(FALSE)) }
  message("\nEnregistré dans .env : ", paste(fait, collapse = ", "), ". Les mots de passe ne quittent pas ton ordinateur.")

  py <- .aigora_python()
  a_caldav <- length(suppressWarnings(system2(py, c("-c", shQuote("import caldav")), stdout = TRUE, stderr = TRUE))) == 0
  if (!a_caldav && any(grepl("agenda", fait))) {
    if (oui("Le paquet Python 'caldav' manque. L'installer maintenant ?")) {
      system2(py, c("-m", "pip", "install", "--user", "caldav"))
    }
  }
  message("\nTest des connexions (rien n'est envoyé)...")
  aigora_ksuite(test = TRUE)
  invisible(TRUE)
}

aigora_ksuite <- function(test = FALSE, details = FALSE) {
  sortie <- .aigora_script("check_status.py", if (test) "--test" else character(0), afficher = details)
  if (details) return(invisible(sortie))
  libelles <- c(mail_imap_smtp = "Mail (IMAP/SMTP)", calendar_tasks_contacts_dav = "Agenda, tâches, contacts",
                kdrive_local_folder = "Dossier kDrive", kchat_webhook = "kChat (webhook)",
                api_token_for_mcp = "Jeton API (serveurs MCP)", r_session_mcp_opt_in = "Session R (MCP)",
                qgis_mcp_opt_in = "QGIS (MCP)", odoo_crm = "Odoo CRM")
  texte <- paste(sortie, collapse = "\n")
  cat("kSuite et connecteurs AIGORA\n")
  for (cle in names(libelles)) {
    actif <- grepl(paste0('"', cle, '"\\s*:\\s*true'), texte)
    cat("  ", format(libelles[[cle]], width = 28), " ", if (actif) "configuré" else "-", "\n", sep = "")
  }
  if (test) {
    cat("Tests de connexion\n")
    for (t in c("imap", "smtp", "caldav", "carddav")) {
      bloc <- regmatches(texte, regexpr(paste0('"', t, '"\\s*:\\s*(\\{[^}]*\\}|"[^"]*")'), texte))
      etat <- if (!length(bloc)) "-" else if (grepl('"ok"\\s*:\\s*true', bloc)) "OK"
              else if (grepl("not configured", bloc)) "non configuré"
              else if (grepl("pip install", bloc)) "paquet caldav manquant (pip install caldav)"
              else paste("ÉCHEC :", sub('.*"error"\\s*:\\s*"([^"]*)".*', "\\1", bloc))
      cat(sprintf("  %-8s %s\n", t, etat))
    }
  }
  if (!grepl('"calendar_tasks_contacts_dav"\\s*:\\s*true', texte) || !grepl('"mail_imap_smtp"\\s*:\\s*true', texte)) {
    cat("\nPour configurer : aigora_ksuite_configurer()   (détails JSON : aigora_ksuite(details = TRUE))\n")
  }
  invisible(sortie)
}

# Écrit (ou retire) une variable dans .env, À SA PLACE :
#  - la ligne « CLE=... » existante est mise à jour sur place ;
#  - sinon la ligne modèle « # CLE=... » de .env.example est décommentée et remplie
#    (son commentaire explicatif est conservé sur la ligne au-dessus) ;
#  - une ligne active ajoutée en fin de fichier par une ancienne version reprend la place du modèle ;
#  - les doublons éventuels sont supprimés ; ajout en fin de fichier seulement si la clé est inconnue.
# valeur = NULL : la ligne est recommentée (« # CLE=... »), la variable n'est plus active.
.aigora_env_maj <- function(lignes, cle, valeur) {
  motif_actif <- paste0("^\\s*", cle, "\\s*=")
  motif_modele <- paste0("^\\s*#\\s*", cle, "\\s*=")
  actives <- grep(motif_actif, lignes)
  modeles <- grep(motif_modele, lignes)
  if (is.null(valeur)) {
    if (length(actives)) {
      lignes[actives[1]] <- paste0("# ", sub("^\\s*", "", lignes[actives[1]]))
      if (length(actives) > 1) lignes <- lignes[-actives[-1]]
    }
    return(lignes)
  }
  nouvelle <- paste0(cle, "=", valeur)
  # la ligne modèle gagne si aucune ligne active n'existe, ou si la ligne active est plus bas
  # (ajoutée en fin de fichier par une ancienne version) ; sinon on met à jour la ligne active
  if (length(modeles) && (!length(actives) || actives[1] > modeles[1])) {
    ou <- modeles[1]
    # garde le commentaire en fin de ligne du modèle (« # le nombre dans l'URL... »)
    reste <- sub(paste0(motif_modele, "[^#]*"), "", lignes[ou])
    remplacement <- if (grepl("^#", reste)) c(sub("^#\\s*", "# ", reste), nouvelle) else nouvelle
    a_retirer <- actives
  } else if (length(actives)) {
    ou <- actives[1]
    remplacement <- nouvelle
    a_retirer <- actives[-1]
  } else {
    if (length(lignes) && nzchar(utils::tail(lignes, 1))) lignes <- c(lignes, "")
    return(c(lignes, nouvelle))
  }
  lignes <- c(lignes[seq_len(ou - 1)], remplacement, lignes[seq_len(length(lignes) - ou) + ou])
  if (length(a_retirer)) {
    decalage <- length(remplacement) - 1
    lignes <- lignes[-(a_retirer + ifelse(a_retirer > ou, decalage, 0))]
  }
  lignes
}

.aigora_fichier_env <- function() {
  racine <- .aigora_racine()
  env <- file.path(racine, ".env")
  if (!file.exists(env) && file.exists(file.path(racine, ".env.example"))) {
    file.copy(file.path(racine, ".env.example"), env)
  }
  env
}

.aigora_set_env <- function(cle, valeur) {
  env <- .aigora_fichier_env()
  lignes <- if (file.exists(env)) readLines(env, warn = FALSE, encoding = "UTF-8") else character(0)
  lignes <- .aigora_env_maj(lignes, cle, valeur)
  writeLines(lignes, env, useBytes = TRUE)
}

# Range un .env existant : chaque variable ajoutée en fin de fichier par une ancienne version
# d'AIGORA reprend sa place dans les sections du modèle. Une copie est gardée dans .env.bak.<date>.
aigora_env_ranger <- function() {
  env <- .aigora_fichier_env()
  if (!file.exists(env)) { message("Pas de fichier .env."); return(invisible(FALSE)) }
  lignes <- readLines(env, warn = FALSE, encoding = "UTF-8")
  copie <- paste0(env, ".bak.", format(Sys.time(), "%Y%m%d-%H%M%S"))
  file.copy(env, copie)
  actives <- grep("^\\s*[A-Za-z_][A-Za-z0-9_]*\\s*=", lignes, value = TRUE)
  cles <- unique(trimws(sub("=.*$", "", actives)))
  for (cle in cles) {
    # la première occurrence est celle qu'AIGORA utilise : c'est elle qu'on garde
    ligne <- grep(paste0("^\\s*", cle, "\\s*="), lignes, value = TRUE)[1]
    valeur <- sub("^[^=]*=", "", ligne)
    lignes <- .aigora_env_maj(lignes, cle, valeur)
  }
  # supprime les lignes vides en trop laissées en fin de fichier
  while (length(lignes) > 1 && !nzchar(trimws(utils::tail(lignes, 1)))) lignes <- utils::head(lignes, -1)
  writeLines(lignes, env, useBytes = TRUE)
  message(".env rangé : ", length(cles), " variable(s) remise(s) à leur place.\n",
          "Copie de l'ancien fichier : ", basename(copie), " (ignorée par git ; supprime-la quand tout fonctionne).")
  invisible(TRUE)
}

aigora_installer_r_mcp <- function() {
  utils::install.packages(c("btw", "mcptools"))
  message("Installé. Active ensuite : aigora_r_mcp(TRUE)")
}

aigora_r_mcp <- function(activer = TRUE) {
  if (activer && !requireNamespace("btw", quietly = TRUE)) {
    stop("Le paquet btw n'est pas installé : lance aigora_installer_r_mcp().", call. = FALSE)
  }
  .aigora_set_env("AIGORA_R_MCP", if (activer) "1" else NULL)
  if (activer) {
    btw::btw_mcp_session()
    aigora_mcp(simulation = FALSE)
    message("\nÀ chaque ouverture du projet, la session R sera visible par AIGORA.")
  } else {
    .aigora_script("register_mcp.py", c("--remove", "--only", "r"))
  }
  invisible(activer)
}

aigora_qgis_mcp <- function(activer = TRUE) {
  if (activer && Sys.which("uvx") == "") {
    stop("uv n'est pas installé : https://docs.astral.sh/uv/getting-started/installation/", call. = FALSE)
  }
  .aigora_set_env("AIGORA_QGIS_MCP", if (activer) "1" else NULL)
  if (activer) {
    aigora_mcp(simulation = FALSE)
    message("\nDans QGIS : installe l'extension « QGIS MCP » (Extensions > Installer), puis clique sur son bouton pour démarrer le serveur.")
  } else {
    .aigora_script("register_mcp.py", c("--remove", "--only", "qgis"))
  }
  invisible(activer)
}

aigora_qfieldcloud_installer <- function() {
  py <- .aigora_python()
  if (!nzchar(py)) stop("Python 3 introuvable.", call. = FALSE)
  system2(py, c("-m", "pip", "install", "--upgrade", "qfieldcloud-sdk"))
  message("SDK installé. Connecte-toi ensuite : aigora_qfieldcloud_login()")
}

.aigora_demander <- function(question, secret = FALSE, titre = "AIGORA") {
  rep <- if (requireNamespace("rstudioapi", quietly = TRUE) && rstudioapi::isAvailable()) {
    if (secret) rstudioapi::askForPassword(question) else rstudioapi::showPrompt(titre, question)
  } else {
    readline(paste0(question, " "))
  }
  if (is.null(rep)) "" else trimws(rep)
}

aigora_qfieldcloud_login <- function(url = NULL) {
  py <- .aigora_python()
  if (!nzchar(py)) stop("Python 3 introuvable.", call. = FALSE)
  demander <- function(question, secret = FALSE) .aigora_demander(question, secret, "QFieldCloud")
  utilisateur <- demander("Nom d'utilisateur ou e-mail QFieldCloud :")
  mot_de_passe <- demander("Mot de passe QFieldCloud (il n'est pas enregistré) :", secret = TRUE)
  if (!nzchar(utilisateur) || !nzchar(mot_de_passe)) stop("Connexion annulée.", call. = FALSE)
  args <- c("-m", "qfieldcloud_sdk", "--json")
  if (!is.null(url)) args <- c(args, "-U", shQuote(url))
  sortie <- suppressWarnings(system2(py, c(args, "login", shQuote(utilisateur), shQuote(mot_de_passe)),
                                     stdout = TRUE, stderr = TRUE))
  rm(mot_de_passe)
  jeton <- regmatches(paste(sortie, collapse = ""), regexpr('"token"\\s*:\\s*"[^"]+"', paste(sortie, collapse = "")))
  if (!length(jeton)) {
    stop("Échec de la connexion : ", paste(utils::tail(sortie, 3), collapse = " "), call. = FALSE)
  }
  jeton <- sub('.*"token"\\s*:\\s*"([^"]+)".*', "\\1", jeton)
  .aigora_set_env("QFIELDCLOUD_TOKEN", jeton)
  if (!is.null(url)) .aigora_set_env("QFIELDCLOUD_URL", url)
  message("Connecté à QFieldCloud. Le jeton est enregistré dans .env (le mot de passe ne l'est pas).")
  invisible(TRUE)
}

aigora_qfieldcloud_projets <- function() {
  sortie <- .aigora_script("qfc.py", "list-projects", afficher = FALSE, dossier = "qfieldcloud")
  if (!isTRUE(attr(sortie, "ok"))) { .aigora_echec(sortie); return(invisible(NULL)) }
  .aigora_json(sortie)$result
}

aigora_mcp <- function(simulation = TRUE) {
  Sys.setenv(AIGORA_RSCRIPT = file.path(R.home("bin"), if (.Platform$OS.type == "windows") "Rscript.exe" else "Rscript"))
  if (simulation) message("Simulation : rien n'est modifié. aigora_mcp(simulation = FALSE) pour enregistrer.\n")
  .aigora_script("register_mcp.py", if (simulation) "--dry-run" else character(0))
  if (!simulation) message("\nRedémarre Claude Code dans le terminal (/exit puis claude) pour charger les outils.")
}

aigora_kdrive <- function(chemin = NULL, retirer = FALSE) {
  args <- if (retirer) "--unlink" else if (!is.null(chemin)) c("--path", shQuote(path.expand(chemin))) else character(0)
  .aigora_script("link_kdrive.py", args)
  message("\nRedémarre Claude Code dans le terminal (/exit puis claude) pour appliquer.")
}

.aigora_json <- function(sortie) {
  if (!requireNamespace("jsonlite", quietly = TRUE)) {
    stop("install.packages(\"jsonlite\") est nécessaire pour cette fonction.", call. = FALSE)
  }
  debut <- grep("^\\{", sortie)[1]
  jsonlite::fromJSON(paste(sortie[debut:length(sortie)], collapse = "\n"))
}

aigora_contacts <- function() {
  sortie <- .aigora_script("contacts.py", c("export", "--output", "data/contacts.csv"), afficher = FALSE)
  if (!isTRUE(attr(sortie, "ok"))) { .aigora_echec(sortie); return(invisible(NULL)) }
  f <- file.path(.aigora_racine(), "data", "contacts.csv")
  utils::read.csv2(f, fileEncoding = "UTF-8-BOM", stringsAsFactors = FALSE)
}

aigora_taches <- function(toutes = FALSE) {
  sortie <- .aigora_script("calendar_events.py", c("tasks", if (toutes) "--all"), afficher = FALSE)
  if (!isTRUE(attr(sortie, "ok"))) { .aigora_echec(sortie); return(invisible(NULL)) }
  .aigora_json(sortie)$tasks
}

aigora_leads <- function() {
  f <- file.path(.aigora_racine(), "data", "leads.csv")
  if (!file.exists(f)) {
    message("Aucun prospect enregistré pour l'instant (skill research-lead).")
    return(invisible(NULL))
  }
  utils::read.csv2(f, fileEncoding = "UTF-8-BOM", stringsAsFactors = FALSE)
}

aigora_odoo_configurer <- function() {
  demander <- function(question, secret = FALSE) .aigora_demander(question, secret, "Odoo CRM")
  cat("Configuration d'Odoo CRM (guide : docs/ODOO.md)\n",
      "Avant de commencer, crée une clé API dans Odoo : avatar > Mon profil > Sécurité du compte > Nouvelle clé API.\n",
      "Ton mot de passe Odoo n'est jamais demandé.\n\n", sep = "")
  url <- demander("1/4 Adresse d'Odoo (ex. http://localhost:8069 ou https://monentreprise.odoo.com) :")
  if (!nzchar(url)) stop("Configuration annulée.", call. = FALSE)
  if (!grepl("^https?://", url)) {
    local <- grepl("^(localhost|127\\.0\\.0\\.1)(:|/|$)", url)
    url <- paste0(if (local) "http://" else "https://", url)
  }
  url <- sub("/+$", "", sub("/(web|odoo)(/.*)?$", "", url))
  base <- demander("2/4 Nom de la base Odoo (laisser vide si une seule base, cas habituel sur odoo.com) :")
  login <- demander("3/4 Ton identifiant Odoo (souvent ton e-mail) :")
  cle <- demander("4/4 Clé API Odoo (saisie masquée) :", secret = TRUE)
  if (!nzchar(cle)) stop("Configuration annulée : clé API vide.", call. = FALSE)
  .aigora_set_env("ODOO_URL", url)
  .aigora_set_env("ODOO_DB", if (nzchar(base)) base else NULL)
  .aigora_set_env("ODOO_LOGIN", if (nzchar(login)) login else NULL)
  .aigora_set_env("ODOO_API_KEY", cle)
  rm(cle)
  cat("\nEnregistré dans .env. Test de connexion...\n")
  sortie <- .aigora_script("odoo.py", "status", afficher = FALSE, dossier = "odoo")
  if (!isTRUE(attr(sortie, "ok"))) {
    .aigora_echec(sortie)
    message("Corrige avec aigora_odoo_configurer() ou en éditant .env (aigora_env()).")
    return(invisible(FALSE))
  }
  protocole <- .aigora_champ(sortie, "protocol")
  etapes <- regmatches(paste(sortie, collapse = ""), regexpr('"crm_stages"\\s*:\\s*\\[[^]]*\\]', paste(sortie, collapse = "")))
  etapes <- if (length(etapes)) trimws(strsplit(gsub('"', "", sub('.*\\[(.*)\\]', "\\1", etapes)), ",")[[1]]) else character(0)
  Encoding(etapes) <- "UTF-8"
  cat("Connecté à Odoo (API ", if (identical(protocole, "json2")) "JSON-2" else "XML-RPC", ").\n",
      "Étapes du pipeline : ", paste(etapes, collapse = ", "), "\n",
      "Voir les opportunités : aigora_odoo_pipeline()\n", sep = "")
  invisible(TRUE)
}

aigora_odoo_pipeline <- function(etape = NULL, limite = 50) {
  args <- c("pipeline", "--limit", as.character(limite))
  if (!is.null(etape)) args <- c(args, "--stage", shQuote(etape))
  sortie <- .aigora_script("odoo.py", args, afficher = FALSE, dossier = "odoo")
  if (!isTRUE(attr(sortie, "ok"))) { .aigora_echec(sortie); return(invisible(NULL)) }
  if (!requireNamespace("jsonlite", quietly = TRUE)) {
    stop("install.packages(\"jsonlite\") est nécessaire pour cette fonction.", call. = FALSE)
  }
  debut <- grep("^\\{", sortie)[1]
  leads <- jsonlite::fromJSON(paste(sortie[debut:length(sortie)], collapse = "\n"),
                              simplifyVector = FALSE)$leads
  if (!length(leads)) {
    message("Aucune opportunité", if (!is.null(etape)) paste0(" à l'étape « ", etape, " »"), ".")
    return(invisible(data.frame()))
  }
  # Odoo renvoie false pour un champ vide et [id, "nom"] pour une relation : on aplatit
  valeur <- function(x) {
    if (is.null(x) || identical(x, FALSE)) return(NA_character_)
    if (is.list(x)) return(if (length(x) >= 2) as.character(x[[2]]) else NA_character_)
    enc2utf8(as.character(x))
  }
  champs <- unique(unlist(lapply(leads, names)))
  df <- as.data.frame(
    lapply(stats::setNames(champs, champs), function(ch) vapply(leads, function(l) valeur(l[[ch]]), "")),
    stringsAsFactors = FALSE, check.names = FALSE
  )
  if ("id" %in% names(df)) df$id <- as.integer(df$id)
  if ("expected_revenue" %in% names(df)) df$expected_revenue <- as.numeric(df$expected_revenue)
  if ("probability" %in% names(df)) df$probability <- as.numeric(df$probability)
  df$active <- NULL
  df
}

aigora_aide <- function() {
  cat(
    "AIGORA dans RStudio\n",
    "  aigora_verifier()            vérifier les prérequis\n",
    "  aigora_demarrer()            lancer Claude Code dans un terminal\n",
    "  aigora_env()                 créer / ouvrir le fichier .env (clés et mots de passe d'application)\n",
    "  aigora_env_ranger()          ranger .env (variables remises dans leur section)\n",
    "  aigora_ksuite_configurer()   configurer kSuite (questions dans RStudio)\n",
    "  aigora_ksuite(test = TRUE)   tester la connexion kSuite\n",
    "  aigora_mcp(simulation=FALSE) enregistrer les serveurs MCP Infomaniak\n",
    "  aigora_kdrive()              relier le dossier kDrive synchronisé\n",
    "  aigora_contacts()            contacts kSuite (data.frame)\n",
    "  aigora_taches()              tâches kSuite (data.frame)\n",
    "  aigora_leads()               prospects analysés (data.frame)\n",
    "  aigora_odoo_configurer()     connecter Odoo CRM (clé API)\n",
    "  aigora_odoo_pipeline()       opportunités Odoo (data.frame)\n",
    "  aigora_r_mcp(TRUE)           AIGORA voit ta session R (objets, aide des paquets)\n",
    "  aigora_qgis_mcp(TRUE)        AIGORA pilote QGIS (couches, traitements, cartes)\n",
    "  aigora_qfieldcloud_login()   connexion à QFieldCloud (relevés terrain QField)\n",
    sep = ""
  )
}
