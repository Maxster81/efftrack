# Core Rules — Lingua, Comunicazione e Meta-Regole

## Lingua e Internazionalizzazione
- **UI e stringhe nelle pagine:** bilingue italiano + inglese. Implementare i18n per ogni nuovo servizio.
- **Commenti nel codice:** bilingue IT+EN.
- **Documentazione:** tutta in doppia lingua (IT + EN).
- **Messaggi di commit:** solo in inglese.
- **Risposte all'utente:** in italiano, salvo diversa indicazione.

## Meta-Regola: Regole Sovrascrivibili
Ogni regola in questo workspace può essere messa in discussione. Se Cline identifica un approccio migliore:
1. Propone l'alternativa con analisi dettagliata di **vantaggi e svantaggi**
2. L'utente valuta e decide
3. Se approvato, la regola viene aggiornata con breve documentazione della decisione

**Nessuna regola è talmente rigida da non poter essere migliorata ad esclusione di quella Branching presente in 05-git.md.**

## Regola di Progetto — Effort Tracking
- Questo workspace serve a costruire un web server per **effort tracking** eseguibile su Ubuntu.
- Lo sviluppo deve partire **single-user** ma ogni scelta deve essere fatta in modo da consentire una futura evoluzione **multi-user**.
- L'autenticazione **non va implementata nelle prime fasi**: login e segregazione utenti sono fasi finali del progetto.
- Il deploy target è **Ubuntu con Python venv**, senza dipendere da Docker.
- Ogni decisione tecnica deve privilegiare: semplicità operativa, manutenibilità, facilità di backup, chiarezza architetturale e futura estendibilità.
