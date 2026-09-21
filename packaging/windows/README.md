# Netejator98 - Guia de Compilació i Desplegament a Windows

Aquest directori conté els scripts necessaris per desplegar i empaquetar **Netejator98** en entorns Microsoft Windows (Windows 10/11 i Windows Server).

---

## 1. Com compilar `netejator98.exe` des d'Ubuntu

PyInstaller no és un compilador creuat (*cross-compiler*): necessita executar-se sota un entorn de Windows per empaquetar l'intèrpret de Windows i les extensions natives en C (`PyNaCl`, `cryptography`).

Per generar el binari `.exe` des d'una màquina Ubuntu, disposes de tres vies:

### Opció A: GitHub Actions & Releases (Recomanat - Descàrrega directa)
El projecte disposa d'un workflow automàtic a `.github/workflows/build-binaries.yml` que compila i publica els executables directament a **GitHub Releases**.

Pots descarregar el binari compilat de Windows directament amb qualsevol navegador o des de PowerShell amb aquesta URL pública:
```powershell
Invoke-WebRequest -Uri "https://github.com/xavi-developer/netejator98/releases/latest/download/netejator98-windows-x64.exe" -OutFile "netejator98.exe"
```
Per forçar una nova compilació:
1. Fes push a la branca `main` o crea un tag (`git tag v1.0.0 && git push origin v1.0.0`).
2. O ves a la pestanya **Actions** -> **Build Cross-Platform Standalone Binaries** -> **Run workflow**.

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

