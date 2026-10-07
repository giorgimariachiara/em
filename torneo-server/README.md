# Torneo web Emiliana Mölkky

Pagina `torneo.html` integrata nel sito statico; API Python 3.10+ e SQLite su un server separato. Nessun token Telegram, dipendenza Python esterna o servizio Telegram richiesto.

## Prova locale

Dalla radice del repository: `python3 -m http.server 8000`.
In `assets/js/torneo-config.js` impostare `window.TORNEO_API_URL = 'http://localhost:8080';`.
In un altro terminale:

```bash
cd torneo-server
export TORNEO_ADMIN_PASSWORD='scegli-una-password-lunga'
export TORNEO_ORIGIN='http://localhost:8000'
python3 server.py
```

Aprire `http://localhost:8000/torneo.html`, selezionare organizzatore e usare la password. Inserire le squadre, scegliere 2 o 4 gironi e i campi per girone. I gironi vengono sorteggiati. Copiare subito i codici generati e consegnarli alle singole squadre. I codici sono memorizzati solo come hash. Le sessioni durano 12 ore e scadono a ogni riavvio del server.

## Pubblicazione

GitHub Pages pubblica solo il frontend. Il backend richiede un processo Python sempre attivo, HTTPS tramite reverse proxy e un volume persistente per SQLite. Impostare:

- `TORNEO_ADMIN_PASSWORD`: password privata non vuota, come variabile del server.
- `TORNEO_ORIGIN`: origine esatta del sito (per GitHub Pages `https://giorgimariachiara.github.io`, senza `/em`).
- `TORNEO_DB`: percorso del database su un disco persistente.
- `PORT`: porta del processo, predefinita 8080.

Inserire l'origine HTTPS del backend in `assets/js/torneo-config.js`. Non inserire password in quel file. Eseguire una sola istanza del backend: le sessioni sono in memoria; HTTPServer serializza le richieste e ogni modifica usa una transazione SQLite. Effettuare backup del database. Il proxy deve limitare tentativi di accesso e dimensioni delle richieste, applicare HTTPS e timeout. La pubblicazione effettiva del backend e la configurazione del suo URL sono ancora necessarie.

## Regole e flusso

Ogni coppia del girone disputa due set consecutivi. Le squadre segnalano la disponibilità; il sistema assegna campi del loro girone e privilegia chi ha giocato meno, poi la somiglianza tra set giocati e vittorie. Basta una conferma per squadra entro 180 secondi. Il timeout rende entrambe indisponibili; il rifiuto rende indisponibile solo chi rifiuta. L'API verifica le scadenze a ogni richiesta, quindi la pagina aggiornata ogni cinque secondi mantiene attivo il controllo.

Un solo partecipante registra il risultato: esattamente una squadra a 50, l'altra tra 0 e 49. I due set sono conteggiati separatamente. Classifica per vittorie e punti; a parità completa l'ordine alfabetico è solo di visualizzazione, non uno spareggio sportivo. L'organizzatore può correggere risultati, mettere in pausa o chiudere nuove assegnazioni. Pausa e chiusura permettono di concludere entrambi i set di incontri già assegnati. Nessun limite fisso a dieci set: si completa il calendario del girone. I quarti e la fase eliminatoria non sono implementati in questa prima versione.

La pagina deve restare aperta: non ci sono notifiche push. Il codice condiviso identifica la squadra, non le singole persone. Non è previsto il recupero di un codice perso né il reset tramite interfaccia. Per un nuovo torneo usare un nuovo percorso `TORNEO_DB`, conservando il precedente come archivio. La raccolta fotografica del bot non fa parte di questa versione.

## Verifica

```bash
cd torneo-server
python3 -m unittest -v
```
