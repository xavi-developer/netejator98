# Netejator98 - Guia de Compilació i Desplegament a Windows

Aquest directori conté els scripts necessaris per desplegar i empaquetar **Netejator98** en entorns Microsoft Windows (Windows 10/11 i Windows Server).

---

## 1. Com compilar `netejator98.exe` des d'Ubuntu

PyInstaller no és un compilador creuat (*cross-compiler*): necessita executar-se sota un entorn de Windows per empaquetar l'intèrpret de Windows i les extensions natives en C (`PyNaCl`, `cryptography`).

Per generar el binari `.exe` des d'una màquina Ubuntu, disposes de tres vies:

### Opció A: GitHub Actions (Recomanat - 100% Natiu)
El projecte ja disposa d'un workflow automàtic a `.github/workflows/build-binaries.yml`.
1. Fes push del codi a GitHub (`git push`).
2. A GitHub, ves a la pestanya **Actions** -> **Build Cross-Platform Standalone Binaries**.
3. Prem **Run workflow** (o crea un tag de versió tipus `v0.1.0`).
4. GitHub compilarà el projecte en un entorn Windows natiu (`windows-latest`) i podràs descarregar directament l'arxiu:
   `netejator98-windows-x64.exe`

### Opció B: Utilitzant Wine directament a Ubuntu
Pots instal·lar l'emulador Wine i l'intèrpret oficial de Python per a Windows:
```bash
# 1. Instal·lar Wine a Ubuntu
sudo dpkg --add-architecture i386
sudo apt update
sudo apt install -y wine64 wine32

# 2. Descarregar i instal·lar Python 3.11 per a Windows
wget https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
wine python-3.11.9-amd64.exe /quiet InstallAllUsers=1 PrependPath=1

# 3. Instal·lar dependències i compilar
wine python -m pip install --upgrade pip
wine python -m pip install -e .
wine python -m pip install pyinstaller
wine python build.py
```
El fitxer executable es generarà a `dist/netejator98.exe`.

---

## 2. Desplegament i Instal·lació a les Aules Windows

Un cop tinguis el fitxer `netejator98.exe`, copia la carpeta del projecte o l'executable a la màquina Windows (p. ex. a `C:\Program Files\Netejator98\`):

### Pas 1: Execució directa i comprovació
Pots obrir el tauler d'administració directament sense necessitat de serveis:
```powershell
.\netejator98.exe admin
```

### Pas 2: Instal·lació del servei d'Agent en segon pla (Opcional)
Obre PowerShell com a Administrador:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\packaging\windows\install-service.ps1 -Install
```
*Nota: Per defecte el servei s'instal·la desactivat (`daemon_state.json -> {"enabled": false}`). Es pot activar des del tauler d'administració.*

### Pas 3: Configuració de la pantalla de bloqueig/inici de sessió (Kiosk)
Per forçar la neteja en iniciar sessió abans que l'alumne accedeixi a l'escriptori:
```powershell
.\packaging\windows\setup-logon-task.ps1
```
Això configurarà una tasca programada que aixeca `netejator98.exe ui` en arrencar l'equip.

