# Product Context — Effort Tracking

## Perché questo progetto esiste
Il vecchio tool di effort tracking aziendale era un applicativo desktop/legacy non più mantenuto. Serve un sostituto moderno:
- web-based, raggiungibile dal browser;
- installabile su un server Ubuntu con poche dipendenze (Python + venv);
- manutenibile da un piccolo team;
- estendibile, senza riscritture, quando arriverà la necessità di multi-utente.

## Problemi che risolve
- Registrazione quotidiana di ore e attività per cliente, con storico ricercabile.
- Visibilità immediata del mese in corso (derivato dalla data, non ridondante).
- Esportazione dati per la rendicontazione (CSV / XLSX).
- Predisposizione a separazione dei dati per utente, senza dover rifare tutto.

## Come deve funzionare (esperienza utente)
- L'utente apre la pagina principale.
- Vede un **form in alto** con i campi: User (testo), Data, Cliente, Gruppo, Attività, Ore Spese, Note, e un campo **Descrizione** che appare solo se l'attività scelta è "Supporto Specialistico".
- Vede una **tabella in basso** con l'elenco dei record salvati, ordinata per data decrescente.
- Cliccando su una riga, il form si popola con i dati del record e diventa un'operazione di **update** (non insert).
- Un pulsante **Salva** centrale gestisce sia insert che update.
- C'è un'icona utente in alto a destra (solo decorativa nelle fasi iniziali, diventerà login in Fase 10).

## Obiettivi di esperienza
- UI **sobria e professionale**, palette blu navy + grigi neutri.
- "Single-page feeling" con rendering server-side, niente SPA pesante.
- Tempi di risposta percepiti < 200ms sulle operazioni CRUD (con SQLite locale è realistico).
- Accessibilità di base: navigazione da tastiera, label associate, contrasti sufficienti.

## Non-goal (al momento)
- Autenticazione / login (Fase 10+).
- Multi-utente / segregazione (Fase 11+).
- Grafiche evolute, animazioni, microinterazioni (rimandate a fasi tarde, se mai).
- Internazionalizzazione (UI in italiano, niente i18n).

## Ruoli utente (da Fase 10 in poi)
- **User (semplice)**: può inserire nuovi record e visualizzare solo la propria tabella.
- **Manager**: gestisce le persone del proprio gruppo; inizialmente potrà esportare gli excel (CSV o XLSX, da definire) di tutti gli appartenenti al proprio gruppo. Non gestisce lookup né utenti.
- **Admin**: gestisce la piattaforma — aggiunge utenti che accedono al web, aggiorna i campi dei record aggiungendo nuovi gruppi, attività, clienti (clienti/attività cambieranno nel tempo). Ha una sezione `/admin`.
- La **sidebar (menu hamburger)** sarà visibile a tutti gli utenti in tutto il web server, ma le voci dipenderanno dal ruolo: le voci verranno popolate a partire dalle Fasi 12–13. Il contenitore viene predisposto in Fase 4b.

## Inserimento bulk "copia su settimana" (Fase 5b)
- Quando l'effort è identico per più giorni della stessa settimana (stesso cliente, gruppo, attività, ore), l'utente può evitare di inserire 7 volte gli stessi dati.
- Un pulsante "Copia su settimana" prende i valori del form corrente e crea un record per ogni giorno feriale (lunedì→venerdì) della settimana corrente, con data corrispondente.

## Criteri di successo
- Un utente tecnico installa il servizio su Ubuntu con pochi comandi e lo mette in produzione.
- Il codice è leggibile da uno sviluppatore Python medio senza dover decifrare framework esotici.
- L'estensione a multi-utente non richiede riscrittura del modello dati.
