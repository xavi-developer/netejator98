# Netejator98 — Manual d'Usuari i Guia d'Administració
*(User Guide and Administration Manual)*

**Netejator98** és una solució de programari de codi obert dissenyada per a centres educatius (instituts, escoles i universitats) que gestionen ordinadors compartits, aules d'informàtica i equips de préstec. 

El seu objectiu principal és doble:
1. **Privadesa de l'alumnat**: Garantir que cap alumne trobi documents, sessions obertes, historials o claus del company que ha utilitzat l'ordinador prèviament.
2. **Auditabilitat institucional**: Registrar de forma segura, asimètrica i resistent a manipulacions qui i quan ha utilitzat cada màquina, sense exposar dades personals en clar.

---

## Taula de Continguts

1. [Característiques Principals](#característiques-principals)
2. [Guia per a l'Alumnat](#guia-per-a-lalumnat)
3. [Guia per a l'Equip Docent i Coordinació TIC](#guia-per-a-lequip-docent-i-coordinació-tic)
   - [Primer inici i configuració de contrasenya](#primer-inici-i-configuració-de-contrasenya)
   - [Accés al Tauler d'Administració (`Ctrl+Alt+A`)](#accés-al-tauler-dadministració-ctrlalta)
   - [Consulta del Registre d'Auditoria](#consulta-del-registre-dauditoria)
   - [Verificació de la Cadena Criptogràfica](#verificació-de-la-cadena-criptogràfica)
   - [Exportació d'Auditories a CSV](#exportació-dauditories-a-csv)
   - [Política de Neteja i Sistemes Operatius Suportats](#política-de-neteja-i-sistemes-operatius-suportats)
   - [Neteja Manual i Simulació (Dry-run)](#neteja-manual-i-simulació-dry-run)
4. [Idiomes Suportats](#idiomes-suportats)
5. [Ubicació de Fitxers de Configuració](#ubicació-de-fitxers-de-configuració)
6. [Resolució de Problemes Freqüents (FAQ)](#resolució-de-problemes-freqüents-faq)

---

## Característiques Principals

- **Pantalla de Benvinguda Kiosk**: Bloqueja l'escriptori a l'inici de sessió a pantalla completa, sempre al capdamunt i sense botó de tancar fins que l'estudiant s'identifica correctament.
- **Validació de Domini Institucional**: Comprova estrictament que l'adreça pertanyi al domini del centre (per defecte `@insestatut.cat`).
- **Detecció Intel·ligent de Canvi d'Usuari**:
  - *Mateix usuari consecutiu*: Si el mateix estudiant torna a iniciar sessió (per exemple després d'un reinici), la neteja s'omet per agilitar l'accés.
  - *Usuari nou o diferent*: Executa immediatament la neteja profunda abans de permetre l'accés a l'escriptori.
- **Motor de Neteja Profunda Multiplataforma**:
  - Tanca navegadors actius amb seguretat.
  - Esborra historials, cookies, bases de dades locals i memòria cau (Google Chrome, Chromium, Mozilla Firefox, Microsoft Edge, Brave, Opera, Safari), tant en instal·lacions natives com en paquets Snap o Flatpak.
  - Buida carpetes personals: Escriptori, Documents, Baixades, Imatges, Vídeos, Música i Paperera de reciclatge.
  - Neteja historials de consola (`.bash_history`, `.zsh_history`, PowerShell).
  - Elimina credencials en disc (`.git-credentials`, tokens de GitHub CLI, etc.).
- **Invariants de Protecció Inviolables**: Cap configuració o atac pot esborrar binaris del sistema operatiu (`/bin`, `C:\Windows`), llibreries essencials o el directori protegit de Netejator98 (`/var/lib/netejator98`, `C:\ProgramData\netejator98`).
- **Registre d'Auditoria Asimètric "Només Escriptura"**:
  - L'agent local només té la clau pública (X25519) per xifrar esdeveniments (`crypto_box_seal`).
  - La clau privada està xifrada amb Argon2id utilitzant la contrasenya d'administració.
  - Encara que un usuari o programari maliciós obtingui accés root local, no pot llegir ni falsificar els registres anteriors.
- **Cadena de Resums SHA-256 (Hash Chain)**:
  - Cada entrada d'auditoria enllaça el resum de l'entrada prèvia.
  - Qualsevol eliminació, alteració o reordenació de registres es detecta de forma immediata i matemàtica, sense necessitat d'introduir la contrasenya.

---

## Guia per a l'Alumnat

Com a estudiant, quan encenguis l'ordinador de l'aula o iniciïs sessió, veuràs una pantalla com aquesta:

```text
+-----------------------------------------------------------------------------+
|                                                                             |
|  [⚙ Administració]                                                          |
|   (Ctrl+Alt+A)        +===================================================+ |
|                       | [*] Inici de sessió a Netejator 98            [X] | |
|                       +---------------------------------------------------+ |
|                       | [Key/PC]  Benvingut/da a la sessió                | |
|                       |           Introduïu el vostre correu del centre:  | |
|                       |                                                   | |
|                       |           Nom d'usuari / Correu:                  | |
|                       |           | usuari@insestatut.cat          |      | |
|                       |           ----------------------------------      | |
|                       |           [ D'acord ]  [ Ometre ]  [ Administració] |
|                       +===================================================+ |
|                                                                             |
+-----------------------------------------------------------------------------+
| [Inici de sessió a Netejator 98]                               | [CA] 09:15 |
+-----------------------------------------------------------------------------+
```

### Passes per utilitzar l'ordinador:
1. **Introdueix el teu correu del centre**: P. ex. `maria.garcia@insestatut.cat`.
2. Fes clic a **Iniciar Sessió** o prem la tecla **Retorn (Enter)**.
3. Si un altre company havia utilitzat la màquina abans, veuràs breument l'avís *"Netejant dades de la sessió anterior..."*. L'ordinador quedarà net com si fos nou.
4. Un cop finalitzada la neteja, la pantalla es desbloquejarà automàticament i tindràs accés complet a l'escriptori.

> [!IMPORTANT]
> **Consell sobre els teus fitxers**:
> Netejator98 esborrarà tots els fitxers desats a l'Escriptori, Documents i Baixades quan un altre alumne entri a l'ordinador.
> Desa sempre els teus treballs al teu núvol escolar (Google Drive, Microsoft OneDrive) o en un llapis de memòria USB abans d'acabar la classe!

---

## Guia per a l'Equip Docent i Coordinació TIC

### Primer inici i configuració de contrasenya
Quan s'executa Netejator98 per primera vegada en una màquina:
1. La base de dades administrativa encara no té contrasenya registrada.
2. Prem la drecera administrativa: **`Ctrl + Alt + A`**.
3. S'obrirà la finestra de creació de contrasenya inicial.
4. Introdueix una contrasenya segura (mínim 8 caràcters). Aquesta contrasenya:
   - Protegeix l'accés al tauler d'administració.
   - Genera el parell de claus criptogràfiques X25519.
   - Xifra la clau privada mitjançant derivació de clau Argon2id.

---

### Accés al Tauler d'Administració (`Ctrl+Alt+A`)
En qualsevol moment, des de la pantalla de bloqueig kiosk:
1. Prem simultàniament les tecles **`Ctrl + Alt + A`**.
2. Introdueix la contrasenya d'administrador configurada.
3. S'obrirà el **Tauler d'Administració de Netejator98**, compost per tres pestanyes:
   - **Registre d'Auditoria**: Visualització i exportació de sessions.
   - **Polítiques de Neteja**: Configuració YAML de rutes i objectius de neteja.
   - **Manteniment**: Eines de neteja forçada, simulació i tancament d'emergència.

---

### Consulta del Registre d'Auditoria
Dins la pestanya **Registre d'Auditoria**:
- Fes clic a **Actualitzar Registre**.
- L'agent desxifrarà les entrades amb la clau privada alliberada durant la sessió administrativa.
- La taula mostrarà:
  - **Data i Hora (UTC)**
  - **Esdeveniment** (`USER_LOGIN`, `SANITISATION_EXECUTED`, `ADMIN_ACTION`)
  - **Correu Institucional** (desxifrat)
  - **Estat** (`SUCCESS`, `FAILED`)
  - **Resum de l'acció** (detalls, rutes netejades, motius d'error).

---

### Verificació de la Cadena Criptogràfica
A la mateixa pestanya d'auditoria:
- Fes clic al botó **Verificar Integritat de la Cadena**.
- L'aplicació analitza seqüencialment tots els blocs JSONL emmagatzemats a disc.
- Si no s'ha alterat cap registre, es mostrarà un missatge de confirmació verd:
  `Cadena d'auditoria íntegra. Totes les entrades són vàlides.`
- Si algun usuari o procés ha modificat, esborrat o reordenat alguna línia del fitxer de registre, el sistema indicarà exactament a quina entrada s'ha trencat la cadena.

---

### Exportació d'Auditories a CSV
Per complir amb requeriments d'inspecció o protocols de seguretat del centre:
1. Fes clic a **Exportar a CSV**.
2. Selecciona la carpeta i el nom del fitxer de destí (p. ex. `auditoria-aula1-2026.csv`).
3. El fitxer es generarà amb codificació UTF-8, contenint totes les capçaleres estàndard i els camps desxifrats.

---

### Política de Neteja i Sistemes Operatius Suportats

La política de neteja defineix de manera declarativa quines carpetes, arxius temporals, perfils d'aplicacions i historials s'han de purgar quan un estudiant tanca la seva sessió o quan un nou estudiant inicia sessió a la màquina.

#### A quins Sistemes Operatius aplica

Netejator98 és completament multiplataforma i la seva política de neteja està adaptada i s'aplica específicament als següents sistemes operatius:

1. **Linux (Ubuntu, Debian, Linux Mint, Fedora, Arch Linux, openSUSE)**:
   - **Àmbit d'aplicació**: Directori personal de l'usuari actiu (`/home/<usuari>/`).
   - **Plantilla per defecte**: [`policies/defaults/linux.yaml`](file:///home/xavi/Documents/projects/professor/TIC/netejator98/policies/defaults/linux.yaml) (desada a `/var/lib/netejator98/config.yaml`).
   - **Objectius de neteja gestionats**:
     - *Documents personals*: `Desktop/*`, `Documents/*`, `Downloads/*`, `Pictures/*`, `Videos/*`, `Music/*`.
     - *Memòria cau i temporals*: `.cache/*`, `.thumbnails/*`.
     - *Perfils de navegadors web*: Google Chrome (`.config/google-chrome/*`), Chromium (`.config/chromium/*`), Mozilla Firefox (`.mozilla/firefox/*`), Microsoft Edge (`.config/microsoft-edge/*`), Brave (`.config/BraveSoftware/Brave-Browser/*`), Opera (`.config/opera/*`), així com paquets Snap (`snap/chromium/current/*`, `snap/firefox/common/.mozilla/firefox/*`, `snap/brave/...`, `snap/opera/...`) i paquets Flatpak (`.var/app/com.google.Chrome/*`, `.var/app/org.mozilla.firefox/*`, `.var/app/org.chromium.Chromium/*`, etc.).
     - *Fitxers recents*: `.local/share/recently-used.xbel`, registre d'arxius recents de LibreOffice (`.config/libreoffice/*/user/registrymodifications.xcu`).
     - *Credencials en disc*: Claus SSH (`.ssh/*`), claus AWS (`.aws/*`), tokens de GitHub CLI (`.config/gh/*`), `.git-credentials` i `.config/git/credentials`.
     - *Historials de terminal*: `.bash_history`, `.zsh_history`, `.python_history`.
     - *Paperera de reciclatge*: Paperera estàndard FreeDesktop (`.local/share/Trash/*`).
   - **Invariants de seguretat protegits (mai s'esborren)**: `/`, `/bin`, `/sbin`, `/usr`, `/etc`, `/lib`, `/lib64`, `/var/lib/netejator98`, `/root`.

2. **Microsoft Windows (Windows 10, Windows 11 i Windows Server)**:
   - **Àmbit d'aplicació**: Perfil de l'usuari actiu de Windows (`C:\Users\<usuari>\`).
   - **Plantilla per defecte**: [`policies/defaults/windows.yaml`](file:///home/xavi/Documents/projects/professor/TIC/netejator98/policies/defaults/windows.yaml) (desada a `C:\ProgramData\netejator98\config.yaml`).
   - **Objectius de neteja gestionats**:
     - *Biblioteques d'usuari*: `Desktop/*`, `Documents/*`, `Downloads/*`, `Pictures/*`, `Videos/*`, `Music/*`.
     - *Fitxers temporals i memòria cau*: `AppData/Local/Temp/*`, `AppData/Local/CrashDumps/*`, memòria cau de miniatures de l'Explorador (`AppData/Local/Microsoft/Windows/Explorer/thumbcache_*.db`).
     - *Perfils de navegadors*: Google Chrome (`AppData/Local/Google/Chrome/User Data/*`), Microsoft Edge (`AppData/Local/Microsoft/Edge/User Data/*`), Brave (`AppData/Local/BraveSoftware/Brave-Browser/User Data/*`), Mozilla Firefox (`AppData/Roaming/Mozilla/Firefox/Profiles/*`), Opera (`AppData/Roaming/Opera Software/Opera Stable/*`).
     - *Fitxers recents i Jump Lists*: Fitxers recents (`AppData/Roaming/Microsoft/Windows/Recent/*`), destinacions automàtiques i personalitzades (`AutomaticDestinations/*`, `CustomDestinations/*`).
     - *Historial i credencials*: Historial de línia d'ordres PowerShell (`AppData/Roaming/Microsoft/Windows/PowerShell/PSReadLine/ConsoleHost_history.txt`), credencials de GitHub CLI (`AppData/Roaming/GitHub CLI/*`), `.git-credentials`.
     - *Paperera de reciclatge*: Paperera del sistema Windows (`$Recycle.Bin`).
   - **Invariants de seguretat protegits (mai s'esborren)**: `C:\`, `C:\Windows`, `C:\Program Files`, `C:\Program Files (x86)`, `C:\ProgramData\netejator98`, `C:\Users\Default`.

3. **Apple macOS (macOS 12+ Monterey, Ventura, Sonoma, Sequoia)**:
   - **Àmbit d'aplicació**: Directori personal de l'usuari (`/Users/<usuari>/`).
   - **Plantilla per defecte**: [`policies/defaults/macos.yaml`](file:///home/xavi/Documents/projects/professor/TIC/netejator98/policies/defaults/macos.yaml) (desada a `/var/lib/netejator98/config.yaml`).
   - **Objectius de neteja gestionats**:
     - *Carpetes personals*: `Desktop/*`, `Documents/*`, `Downloads/*`, `Pictures/*`, `Movies/*`, `Music/*`.
     - *Memòria cau del sistema*: `Library/Caches/*`.
     - *Perfils de navegadors*: Apple Safari (`Library/Safari/*`), Google Chrome (`Library/Application Support/Google/Chrome/*`), Mozilla Firefox (`Library/Application Support/Firefox/Profiles/*`), Microsoft Edge (`Library/Application Support/Microsoft Edge/*`), Brave (`Library/Application Support/BraveSoftware/Brave-Browser/*`).
     - *Fitxers recents*: Llistes de fitxers compartits i servidors recents a `Library/Application Support/com.apple.sharedfilelist/*` i `Library/Recent Servers/*`.
     - *Historial i credencials*: Historial de terminal Zsh (`.zsh_history`), claus SSH (`.ssh/*`), `.git-credentials`.
     - *Paperera*: Paperera d'escriptori (`.Trash/*`).
   - **Invariants de seguretat protegits (mai s'esborren)**: `/`, `/System`, `/Library`, `/Applications`, `/usr`, `/bin`, `/sbin`, `/etc`, `/private`, `/var/lib/netejator98`.

#### Detecció Automàtica del Sistema Operatiu
Quan s'inicia el servei dimoni de fons (`netejator98 agent`):
- L'agent utilitza la detecció de plataforma de Python (`platform.system().lower()`) per identificar si s'executa a Linux, Windows o macOS.
- Si encara no existeix un fitxer de configuració local personalitzat (`config.yaml`), s'inicialitza automàticament carregant la plantilla específica per defecte (`policies/defaults/<os>.yaml`).
- En obrir el Tauler d'Administració (`Ctrl+Alt+A`), la pestanya **Política de neteja** indica el sistema operatiu amfitrió actiu i permet ajustar les regles de neteja específiques per a aquest entorn.

#### Configuració Gràfica des del Tauler d'Administració
A la pestanya **Política de neteja**, en lloc d'haver d'escriure codi YAML a mà, es disposa d'un entorn visual complet:
- **Caselles de selecció (Checkboxes)**:
  - `Mode simulació (Dry-run)`: Permet provar la política sense esborrar cap fitxer real.
  - `Netejar sempre a l'arrencada`: Força la neteja quan l'equip s'encén.
  - `Esborrat segur`: Sobreescriu fitxers amb zeros abans d'esborrar-los (`shred`).
  - `Restablir eines per defecte`: Restaura les eines i dreceres netes predefinides.
- **Control numèric (Spinbox)**:
  - `Dies de retenció dels registres`: Configura la caducitat de l'auditoria (p. ex. 365 dies).
- **Llista interactiva d'objectius de neteja (Treeview)**:
  - Conté tots els objectius de neteja definits per a tots els sistemes operatius (Linux, Windows i macOS), cobrint les 11 categories possibles de neteja.
  - Taula amb columnes: **Estat** (`🟢 Actiu` / `⚪ Inactiu`), **OS** (`Linux`, `Windows`, `macOS` o `ALL`), **Nom de l'objectiu**, **Categoria**, **Estratègia**, **Patrons de rutes** i **Descripció**.
  - **Estratègies suportades per categoria i SO**:
    - `STANDARD`: Esborrat estàndard de fitxers i carpetes (utilitzat p. ex. a dreceres d'escriptori).
    - `PURGE_CHILDREN`: Purga del contingut intern conservant la carpeta pare (`USER_DOCUMENTS`, `TEMP_AND_CACHE`).
    - `TRUNCATE`: Buidatge a 0 bytes mantenint el fitxer intacte (`SHELL_HISTORY`, `RECENT_FILES`).
    - `SHRED_NIST`: Sobreescriptura segura multipassada (`CREDENTIALS`, claus SSH i tokens).
    - `EMPTY_TRASH`: Neteja de la paperera del sistema operatiu (`RECYCLE_BIN`).
    - `BROWSER_CLEAN`: Purga de perfils, galetes i sessions web (`BROWSER_PROFILES`).
    - `CLOUD_WIPE`: Neteja de dades d'emmagatzematge al núvol (`CLOUD_SYNC`).
    - `GOLDEN_RESET`: Reversió a la plantilla neta predefinida (`GOLDEN_PROFILE`).
    - `CUSTOM_CLEAN`: Neteja d'espais de treball i projectes personalitzats (`CUSTOM`).
    - `SECURE`: Sobreescriptura d'1 passada amb zeros abans d'eliminar.
  - Botó `🔘 Activar / Desactivar` (o tecla `Espai`): Canvia l'estat de l'objectiu seleccionat a l'instant.
  - Botó `➕ Afegir Objectiu...`: Obre una finestra amb selector de sistema operatiu (**OS**), menús desplegables de les 11 categories i totes les estratègies per afegir objectius nous.
  - Botó `✏️ Editar Objectiu...`: Modifica el sistema operatiu destí (OS), categoria, estratègia o rutes de l'objectiu seleccionat.
  - Botó `🗑️ Eliminar Objectiu`: Suprimeix l'objectiu de la llista.
  - Botons `✅ Activar Tots` / `❌ Desactivar Tots`: Canvi massiu ràpid.
  - Botó `🔄 Restablir per Defecte`: Recarrega tots els 33 objectius oficials per a Linux, Windows i macOS.
- **Desar i Validar**:
  - En fer clic a `💾 Desar Política`, el sistema valida automàticament els invariants de seguretat (rebutjant rutes prohibides com `/usr` o `C:\Windows`) i desa els canvis de forma transparent al fitxer de configuració del sistema.
  - El botó `👁️ Veure YAML` permet consultar el document YAML generat si es desitja.


---

### Ometre l'Inici de Sessió (Bypass sense neteja)
Per a docents o tècnics informàtics que necessiten utilitzar l'ordinador sense esborrar la sessió prèvia ni passar per la identificació d'estudiant:
1. A la pantalla de benvinguda Kiosk, fes clic al botó **`🔑 Ometre inici de sessió (Sense neteja)`**.
2. Introdueix la contrasenya d'administrador quan el diàleg la sol·liciti.
3. El sistema valida la contrasenya contra l'algorisme Argon2id. Si és correcta, l'escriptori es desbloqueja a l'instant **sense executar cap esborrat de fitxers ni tancar processos**.
4. L'acció queda registrada criptogràficament a l'auditoria com a `ADMIN_BYPASS_SUCCESS`.

---

### Control de l'Estat del Dimoni de Protecció (Habilitar / Deshabilitar)
Per defecte i per seguretat durant proves inicials, el dimoni de neteja està **desactivat** (`daemon_enabled: false`).

Quan el dimoni està desactivat:
- Els estudiants poden identificar-se normalment per registrar qui utilitza la màquina.
- La neteja automàtica queda suspesa (cap arxiu s'esborra).
- Es mostra un avís a la pantalla de bloqueig: `⚠️ Dimoni desactivat (Sense neteja activa)`.

#### Com activar o desactivar el dimoni:
1. **Des del Tauler d'Administració (`Ctrl+Alt+A`)**:
   - Ves a la pestanya **Manteniment**.
   - A l'apartat **Estat del Dimoni de Protecció**, comprova l'estat actual i fes clic a **Habilitar Dimoni** o **Deshabilitar Dimoni**.
2. **Mitjançant la línia d'ordres (CLI)**:
   ```bash
   # Activar el dimoni de protecció
   sudo netejator98 enable-daemon
   # o bé:
   sudo python3 -m netejator98.main enable-daemon

   # Desactivar el dimoni de protecció
   sudo netejator98 disable-daemon
   # o bé:
   sudo python3 -m netejator98.main disable-daemon
   ```

---

### Neteja Manual i Simulació (Dry-run)
A la pestanya **Manteniment**:
- **Simular Neteja (Dry-run)**: Analitza el sistema d'arxius i calcula quins fitxers i processos s'eliminarien segons la política activa, sense tocar cap arxiu real. El resultat es mostra en un informe detallat.
- **Executar Neteja Immediata**: Força la neteja completa de la màquina al moment.
- **Sortir del Kiosk (Manteniment)**: Tanca la interfície de bloqueig per permetre tasques tècniques a l'escriptori sense reiniciar.

---

## Idiomes Suportats

Netejator98 incorpora suport multilingüe en temps real:
- **Català (`ca`)**: Idioma per defecte.
- **Castellà (`es`)**: Disponible a través de l'enllaç d'idioma o paràmetre de configuració.
- **Anglès (`en`)**: Disponible a través de l'enllaç d'idioma o paràmetre de configuració.

---

## Ubicació de Fitxers de Configuració

Totes les dades d'estat i d'auditoria s'allotgen en directoris restringits:

| Sistema Operatiu | Directori de Dades i Registres | Fitxer de Configuració |
| :--- | :--- | :--- |
| **Linux** | `/var/lib/netejator98/` | `/var/lib/netejator98/config.yaml` |
| **macOS** | `/var/lib/netejator98/` | `/var/lib/netejator98/config.yaml` |
| **Windows** | `C:\ProgramData\netejator98\` | `C:\ProgramData\netejator98\config.yaml` |

Fitxers clau:
- `config.yaml`: Política de dominis permesos i regles de neteja.
- `audit.jsonl`: Registre xifrat continu amb cadena de hash SHA-256.
- `log_public.key`: Clau pública X25519 emprada per l'agent de fons per xifrar.
- `log_private.enc`: Clau privada X25519 xifrada amb Argon2id i SecretBox.
- `last_user.hash`: Hash salat de l'últim correu identificat (mai l'email en text pla).
- `admin.json`: Credencials d'administrador xifrades.

---

## Resolució de Problemes Freqüents (FAQ)

#### Què passa si un alumne intenta tancar la finestra amb `Alt + F4`?
La finestra de Netejator98 intercepta tots els esdeveniments de tancament de la finestra del sistema operatiu (`WM_DELETE_WINDOW`) i manté la prioritat sempre al capdamunt (`always-on-top`). L'única manera de desbloquejar l'escriptori és introduint un correu institucional vàlid o amb la clau d'administrador (`Ctrl+Alt+A`).

#### Què passa si l'alumne escriu un correu personal (`@gmail.com`)?
El sistema rebutja la identificació amb l'avís *"Només es permeten adreces del centre educatiu (@insestatut.cat)"* i manté la màquina bloquejada.

#### Es poden recuperar els fitxers després de la neteja?
Netejator98 realitza un esborrat complet dels fitxers i directoris especificats a la política, incloent sobreescriptura de zeros en fitxers sensibles. No obstant això, en discos SSD moderns amb anivellament de desgast (wear-leveling) o sistemes de fitxers CoW (Btrfs, ZFS, APFS), fragments de blocs lògics podrien romandre a nivell de hardware fins que el controlador apliqui el cicle de TRIM. Per a estacions amb requisits de neteja forense militar, es recomana complementar Netejator98 amb xifratge complet de disc (BitLocker / LUKS / FileVault) o desplegament d'imatges PXE efímeres.

#### Com puc canviar la contrasenya d'administrador?
Accedeix al tauler d'administració amb `Ctrl+Alt+A`, prem el botó de canvi de contrasenya i introdueix la contrasenya antiga i la nova. La clau privada del registre d'auditoria serà re-xifrada amb la nova contrasenya sense perdre la capacitat de llegir cap registre antic.

