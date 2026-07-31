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

## Criteri di successo
- Un utente tecnico installa il servizio su Ubuntu con pochi comandi e lo mette in produzione.
- Il codice è leggibile da uno sviluppatore Python medio senza dover decifrare framework esotici.
- L'estensione a multi-utente non richiede riscrittura del modello dati.
