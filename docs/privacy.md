# Privadesa i Compliment Normatiu (GDPR / LOPD-GDD)
*(Privacy and Regulatory Compliance Notes)*

Aquest document estableix les bases legals, consideracions tècniques i recomanacions d'organització per a la implantació de **Netejator98** en centres educatius de la Unió Europea, d'acord amb el **Reglament General de Protecció de Dades (RGPD / GDPR 2016/679)** i la **Llei Orgànica 3/2018 (LOPD-GDD)**.

---

## 1. Bases Jurídiques del Tractament

La recollida i tractament de dades personals (adreça de correu institucional de l'alumne i identificador de la màquina) a través de Netejator98 s'emmarca en les següents bases de l'Article 6 del RGPD:

1. **Compliment d'una missió realitzada en interès públic o en l'exercici de poders públics (Art. 6.1.e RGPD)**:
   - Els centres educatius tenen el deure legal de custodiar les instal·lacions, equips informàtics i xarxes telemàtiques destinades a la formació de l'alumnat.
2. **Interès Legítim i Protecció de la Intimitat de l'Alumnat (Art. 6.1.f RGPD)**:
   - Netejator98 té per finalitat principal protegir el dret a la intimitat i la confidencialitat de les dades dels menors, evitant que un estudiant accedeixi als documents, credencials, historials de cerca o missatgeria de l'usuari precedent en equips compartits.

---

## 2. Principi de Minimització de Dades (Art. 5.1.c RGPD)

Netejator98 s'ha dissenyat des de la base aplicant el principi de **Privadesa des del Disseny i per Defecte** (*Privacy by Design and by Default*):

| Tipus de Dada | Estat d'Emmagatzematge | Finalitat |
| :--- | :--- | :--- |
| **Últim Usuari Identificat** | **Hash Criptogràfic Salat** (`last_user.hash`) | Només es desa el resum Argon2id/SHA256 salat amb la clau de la màquina. L'adreça de correu **mai s'emmagatzema en clar** al disc de control. |
| **Registre d'Auditoria** | **Xifrat Asimètric X25519** (`audit.jsonl`) | El fitxer conté el correu de l'estudiant i la marca de temps de la sessió, però està xifrat amb la clau pública. Cap alumne ni atacant local amb privilegis ordinaris pot llegir el correu dels companys. |
| **Contingut de Documents i Navegació** | **Mai es registra** | Netejator98 **no fa cap mena de monitoratge ni keylogging**. No es registra cap nom de fitxer obert, ni URL visitada, ni cerca realitzada. |

---

## 3. Mesures Tècniques i Organitzatives de Seguretat (TOMs)

D'acord amb l'Article 32 del RGPD, Netejator98 implementa:

1. **Xifrat d'Extrem a Extrem Local (Asymmetric Sealing)**:
   - L'agent de fons utilitza criptografia asimètrica (corba el·líptica X25519 mitjançant libsodium `crypto_box_seal`).
   - La clau privada mai resideix a la memòria durant les sessions habituals dels alumnes. Està desada xifrada amb derivació Argon2id a partir de la contrasenya del coordinador TIC.
2. **Integritat i No-Repudi (Cadena de Resums SHA-256)**:
   - Cada entrada de sessió inclou el resum de l'entrada anterior (`H_n = SHA256(H_{n-1} + ciphertext)`).
   - Qualsevol intent d'esborrar registres concrets o alterar la cronologia és detectat automàticament durant l'auditoria.
3. **Separació de Privilegis**:
   - La interfície d'usuari interactiva s'executa amb el compte d'estudiant limitat. No pot accedir a les dades administratives situades a `/var/lib/netejator98/` o `C:\ProgramData\netejator98\`.

---

## 4. Política de Retenció i Supressió de Dades

- **Termini de Conservació Recomanat**:
  - Els registres d'auditoria d'accés a les màquines haurien de conservar-se únicament durant el **curs acadèmic vigent** (màxim 12 mesos), llevat que s'hagi iniciat un expedient disciplinari o una investigació judicial.
- **Procediment de Rotació i Destrucció**:
  - Al final de cada curs escolar (juliol), la coordinació TIC ha d'exportar el registre a un mitjà segur si és necessari, i buidar el fitxer `audit.jsonl` a les màquines locals mitjançant l'eina administrativa de Netejator98.

---

## 5. Drets dels Interessats (ARCO / GDPR)

L'alumnat (o els seus representants legals en cas de menors) té dret a:
- **Accés**: Sol·licitar informació sobre les sessions registrades al seu nom. La coordinació TIC pot consultar i filtrar el registre desxifrat des del tauler d'administració.
- **Rectificació i Supressió**: Exigir l'esborrat de les seves dades un cop exhaurit el termini necessari per a les finalitats educatives i de seguretat.
- **Informació transparent**: El centre ha d'informar clarament a la comunitat educativa sobre el funcionament del programari a les aules.

---

## 6. Model de Clàusula Informativa per al Centre Educatiu

Es recomana incloure el següent text a la normativa d'ús dels equips informàtics del centre o a la pantalla d'inici de sessió:

> **Avís d'Ús i Protecció de Dades en Equips Compartits**  
> Els ordinadors d'aquest centre estan equipats amb el sistema de protecció i neteja **Netejator98**.  
> En iniciar sessió, se us sol·licitarà el vostre correu corporatiu (`@insestatut.cat`). Aquesta dada s'emmagatzema en un registre xifrat d'accés amb finalitats d'auditoria, custòdia dels recursos públics i garantia de la privadesa entre usuaris, d'acord amb la missió docent del centre (Art. 6.1.e RGPD).  
> Totes les dades temporals, baixades i historials personals seran esborrats de forma automàtica quan finalitzi la vostra sessió. No deseu treballs exclusivament al disc dur local de la màquina.

