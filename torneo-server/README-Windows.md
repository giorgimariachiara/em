# Torneo web — Emiliana Mölkky

## Edizione Windows — PowerShell

Manuale di installazione e utilizzo per organizzatori, giocatori e pubblico.

## 1. Che cosa fa

Il sistema permette di organizzare i gironi di un torneo di Mölkky attraverso una pagina web. Le squadre indicano quando sono disponibili; il sistema sceglie gli avversari e assegna un campo del loro girone. I partecipanti confermano l'incontro e registrano i risultati. La classifica si aggiorna con i dati salvati.

Funzioni disponibili:

- creazione delle squadre e sorteggio equilibrato dei gironi;
- configurazione dei campi per girone;
- accesso mediante codice condiviso dalla squadra;
- disponibilità, assegnazione del campo e conferme entro tre minuti;
- due set consecutivi per ogni coppia di squadre del girone;
- classifica pubblica e visualizzazione dei campi;
- pausa, ripresa e chiusura delle nuove assegnazioni;
- correzione dei risultati da parte dell'organizzatore;
- salvataggio di squadre e risultati in un database SQLite.

**Stato della versione:** gestione dei gironi. Quarti, semifinali, finale, raccolta foto e notifiche push non sono implementati. Il sistema è una versione iniziale: effettuare una prova completa prima dell'uso in un evento.

## 2. Come è composto

| Componente | Funzione | Dove viene eseguito |
| --- | --- | --- |
| Frontend | Pagina, pulsanti, classifica e pannello organizzatore | Browser |
| Backend | Controllo accessi, incontri, campi e risultati | Processo Python |
| Database SQLite | Conservazione dei dati del torneo | Disco del backend |

GitHub Pages può ospitare il frontend, ma non il backend Python. Pubblicare i file HTML non rende da solo operativo il torneo online.

La procedura locale di questo manuale utilizza due servizi:

- sito: `http://localhost:8000`;
- backend: `http://localhost:8080`.

`localhost` indica il dispositivo sul quale si apre l'indirizzo: sul telefono di un partecipante indica quel telefono, non il PC dell'organizzatore.

## 3. Requisiti

Per installare e provare su Windows:

- Python 3.10 o successivo;
- una copia del repository https://github.com/giorgimariachiara/em;
- un browser;
- un terminale, anche quello integrato in VS Code;
- facoltativamente GitHub Desktop per scaricare gli aggiornamenti.

Il backend usa solo la libreria standard di Python: non richiede `pip install`.

Verificare Python nel terminale:

```powershell
py -3 --version
```

Se il comando non esiste o la versione è inferiore a 3.10, installare Python 3.10 o successivo e riaprire VS Code. Se il launcher `py` non è disponibile ma `python --version` indica una versione compatibile, sostituire `py -3` con `python` in tutti i comandi.

## 4. Scaricare e aprire il progetto

### Con GitHub Desktop

1. Clonare o selezionare il repository `giorgimariachiara/em`.
2. Selezionare il ramo `main` contenente i file del torneo.
3. Premere **Fetch origin** e, se disponibile, **Pull origin**.
4. Aprire la cartella del repository in VS Code.

### Senza GitHub Desktop

Su GitHub scegliere **Code → Download ZIP**, estrarre l'archivio e aprire la cartella estratta in VS Code. I successivi aggiornamenti devono essere scaricati separatamente.

La cartella principale deve contenere:

```text
em/
  torneo.html
  assets/
    css/torneo.css
    js/torneo.js
    js/torneo-config.js
  torneo-server/
    server.py
    test_server.py
    README.md
```

Il nome della cartella scaricata può essere diverso, per esempio `em-main`: conta che contenga questi file.

## 5. Configurazione iniziale

### 5.1 Collegare la pagina al backend locale

Aprire `assets/js/torneo-config.js` e impostare:

```javascript
window.TORNEO_API_URL = 'http://localhost:8080';
```

Salvare con **Ctrl+S**. L'indirizzo non deve terminare con `/api`.

### 5.2 Scegliere come accedono le squadre

Nella versione originale, il sistema genera un codice casuale per ogni squadra. Il codice viene mostrato all'organizzatore subito dopo la creazione e deve essere conservato e consegnato alla squadra. Non viene inviato automaticamente per email o messaggio.

Se si preferisce usare il nome della squadra come codice, aprire `torneo-server/server.py`, trovare:

```python
code=secrets.token_urlsafe(9); g=i%groups+1
```

E sostituire con:

```python
code=name; g=i%groups+1
```

Salvare. Da quel momento le **nuove** squadre usano il nome esatto, comprese maiuscole e spazi. Le squadre già create conservano il vecchio codice. Chi conosce il nome di una squadra può accedere per quella squadra: per eventi pubblici è preferibile mantenere i codici casuali.

### 5.3 Password organizzatore

La password viene impostata sul backend tramite `TORNEO_ADMIN_PASSWORD`; deve contenere almeno 12 caratteri. Non va inserita nell'HTML o nel JavaScript pubblico.

Nei comandi seguenti viene usata `ScegliUnaPassword!`: sostituirla con la password scelta e usare la stessa nella pagina. Le virgolette del comando non fanno parte della password.

## 6. Avvio locale passo per passo

### 6.1 Primo terminale: sito

In VS Code scegliere **Terminale → Nuovo terminale**. Dal menu accanto al pulsante **+** selezionare **PowerShell**, se non è già la shell attiva. I comandi `$env:` di questa guida richiedono PowerShell, non il Prompt dei comandi (cmd). Controllare la posizione:

```powershell
pwd
ls
```

Si deve essere nella cartella principale del progetto, con `torneo.html` nell'elenco. Se occorre cambiare cartella, usare per esempio `cd "C:\Users\NomeUtente\Documents\GitHub\em"`, sostituendo il percorso con quello reale del progetto. Se il terminale è dentro `torneo-server`, tornare al livello superiore con:

```powershell
cd ..
```

Avviare il sito:

```powershell
py -3 -m http.server 8000
```

Risultato atteso: un messaggio contenente `Serving HTTP` e `port 8000`.

**Lasciare il terminale aperto.** Finché il comando è attivo, quel terminale è occupato: scrivere altri comandi non li esegue nella shell.

### 6.2 Secondo terminale: backend

Aprire un secondo terminale con il pulsante **+**. Dalla cartella principale del progetto eseguire:

```powershell
cd torneo-server
$env:TORNEO_ADMIN_PASSWORD = 'ScegliUnaPassword!'
$env:TORNEO_ORIGIN = 'http://localhost:8000'
$env:TORNEO_DB = 'torneo-evento.db'
py -3 server.py
```

Premere Invio dopo ciascuna riga.

Risultato atteso: il processo rimane in esecuzione, anche senza mostrare un messaggio iniziale. Il prompt PowerShell, per esempio `PS C:\progetti\em\torneo-server>` non ricompare. Quando il browser lo contatta, compaiono richieste HTTP.

**Lasciare aperto anche questo terminale.** Le variabili `$env:` vanno reimpostate quando si apre un nuovo terminale; non sono memorizzate automaticamente per le prossime sessioni.

### 6.3 Aprire la pagina

Aprire nel browser:

http://localhost:8000/torneo.html

Usare esattamente questo indirizzo, senza sostituire `localhost` con `127.0.0.1`: l'origine configurata deve corrispondere a quella del browser. Per queste istruzioni non usare l'indirizzo di Live Server.

Risultato atteso: compare lo stato del torneo. Se sono stati aggiornati i file, forzare il ricaricamento con **Ctrl+F5**.

## 7. Database: nuovo torneo o ripresa

Il nome impostato in `TORNEO_DB` identifica il database del torneo. Un percorso relativo viene risolto rispetto alla cartella dalla quale si avvia Python.

| Obiettivo | Operazione |
| --- | --- |
| Riprendere un torneo | Usare esattamente lo stesso percorso database |
| Creare un torneo nuovo | Usare un nome database nuovo e non ancora esistente |
| Conservare lo storico | Conservare i file dei tornei precedenti |

Esempio di nuovo torneo:

```powershell
$env:TORNEO_DB = 'torneo-2026-10-10.db'
py -3 server.py
```

Se il backend è già attivo, interromperlo con **Ctrl+C** prima di eseguire questi comandi.

Non esiste un pulsante per azzerare il torneo. Non cancellare il database per creare un nuovo evento: scegliere un nome nuovo preserva lo storico. Annotare il nome usato.

## 8. Guida organizzatore

### 8.1 Accedere

1. Aprire la pagina del torneo.
2. Premere **Esci** se è già presente un accesso squadra o una vecchia sessione.
3. Spuntare **Sono un organizzatore**.
4. Inserire la password impostata in `TORNEO_ADMIN_PASSWORD`.
5. Premere **Accedi**.

Risultato atteso: compare **Gestione torneo**.

### 8.2 Creare il torneo

Se il database è nuovo:

1. Inserire le squadre, una per riga, senza duplicati.
2. Scegliere **2 o 4 gironi**.
3. Impostare i **campi per girone**, da 1 a 8.
4. Premere **Crea torneo e sorteggia i gironi**.
5. Copiare subito i codici visualizzati e consegnarli alle rispettive squadre.

Servono almeno due squadre per girone: quattro squadre per due gironi o otto per quattro gironi. I nomi devono essere diversi e lunghi al massimo 60 caratteri. Il numero totale dei campi è gironi × campi per girone: scegliere un valore coerente con i campi fisici disponibili.

Esempio:

```text
Asini
Birilli
Lupi
Tigri
```

Con due gironi e un campo per girone il sistema crea due campi.

Le squadre vengono mescolate e distribuite a rotazione tra i gironi. Il calendario comprende due set per ogni coppia del girone. La configurazione tramite interfaccia è disponibile solo prima della creazione: non sono implementate aggiunta/rimozione squadre o modifica dei gironi a torneo avviato.

Non è previsto il recupero di un codice casuale perso. L'organizzatore deve conservarlo prima di ricaricare o chiudere la pagina.

### 8.3 Controllare le assegnazioni

| Indicazione | Effetto |
| --- | --- |
| APERTE, verde | Nuovi incontri possono essere assegnati |
| IN PAUSA, giallo | Le nuove assegnazioni sono sospese |
| CHIUSE, rosso | Le nuove assegnazioni sono chiuse |

Comandi:

- **Pausa:** sospende nuove assegnazioni.
- **Riprendi:** riapre le assegnazioni anche dopo una chiusura.
- **Chiudi nuove assegnazioni:** impedisce nuove convocazioni.

Gli incontri già assegnati possono proseguire e completare entrambi i set. Pausa e chiusura non annullano automaticamente gli incontri in attesa di conferma. Le disponibilità già espresse restano salvate: alla ripresa possono produrre nuove assegnazioni.

### 8.4 Correggere un risultato

Nel pannello **Correzione risultati**:

1. Individuare squadre e numero del set.
2. Modificare i due punteggi.
3. Premere **Correggi risultato**.

Il risultato deve rispettare la stessa regola: una sola squadra a 50, l'altra tra 0 e 49. La classifica viene ricalcolata dai risultati, evitando di contare due volte la correzione.

## 9. Guida giocatore

### 9.1 Accesso

1. Aprire il collegamento ricevuto dagli organizzatori.
2. Lasciare **Sono un organizzatore** non selezionato.
3. Inserire il codice della squadra.
4. Premere **Accedi**.

Il codice è condiviso dai componenti: il sistema identifica la squadra, non le singole persone. Se è stata attivata la modalità nome squadra, inserire il nome esatto.

### 9.2 Disponibilità

- Premere **Voglio giocare** quando tutta la squadra è pronta.
- Premere **Ora riposo** per diventare indisponibili, se non è già assegnato un incontro.

Per assegnare un incontro servono due squadre disponibili dello stesso girone, un campo libero di quel girone e un abbinamento ancora da disputare.

Il sistema privilegia chi ha giocato meno set; a parità favorisce una maggiore somiglianza nel numero di set disputati e vittorie. Gli incontri vengono assegnati dinamicamente, senza orari fissi.

### 9.3 Conferma

Quando compare un incontro assegnato:

1. Controllare avversari e campo.
2. Premere **Siamo pronti** entro tre minuti.
3. Attendere la conferma dell'altra squadra.
4. Raggiungere il campo indicato quando il set risulta iniziato.

Basta una conferma per ciascuna squadra. Se una squadra preme **Non possiamo giocare**, l'incontro torna da disputare, il campo viene liberato e quella squadra diventa indisponibile. L'altra mantiene la disponibilità e può essere riassegnata.

Se scadono i tre minuti senza le conferme necessarie, entrambe le squadre diventano indisponibili. Devono segnalare nuovamente la disponibilità.

### 9.4 Risultati

Dopo il primo set:

1. Un solo giocatore inserisce i punti di entrambe le squadre nei campi associati ai loro nomi.
2. Una sola squadra deve avere 50; l'altra deve avere un intero da 0 a 49.
3. Per una sconfitta per falli, indicare 0 per la squadra perdente.
4. Premere **Registra risultato**.
5. Disputare il secondo set, avviato automaticamente sullo stesso campo.
6. Inserire e registrare anche il secondo risultato.

Il sistema impedisce una seconda registrazione dello stesso set da parte dei giocatori. Una correzione richiede l'organizzatore.

Alla fine dei due set, il campo viene liberato e le squadre restano disponibili: se hanno altri incontri possono essere riassegnate. Per una pausa scegliere **Ora riposo** prima della successiva assegnazione.

### 9.5 Aggiornamenti

Tenere aperta la pagina. Quando è visibile, controlla gli aggiornamenti ogni cinque secondi. Non ci sono notifiche push, email o messaggi Telegram. Una scheda nascosta sospende i controlli periodici; tornando alla pagina attendere il successivo aggiornamento oppure premere **Aggiorna**.

## 10. Classifica e pubblico

La classifica e i campi sono consultabili senza accesso. Ogni set conta come una partita separata.

Ordine della classifica per girone:

1. vittorie, in ordine decrescente;
2. punti totali, in ordine decrescente;
3. nome della squadra per la visualizzazione in caso di parità completa.

L'ordine alfabetico non costituisce uno spareggio sportivo: l'organizzatore deve stabilire come risolvere una parità completa.

Esempio:

| Set | Squadra A | Squadra B |
| --- | ---: | ---: |
| 1 | 50 | 35 |
| 2 | 20 | 50 |
| Totale | 70 | 85 |

Entrambe aggiungono due set giocati e una vittoria. B precede A a parità di vittorie grazie ai punti totali.

Non viene applicato il limite fisso di dieci set del vecchio bot: si completa il calendario del girone.

## 11. Prova sullo stesso computer

Prima dell'evento:

1. Creare un database di prova separato.
2. Configurare almeno quattro squadre in due gironi.
3. Accedere a una squadra in una finestra normale.
4. Aprire una finestra in incognito e accedere a un'altra squadra dello stesso girone.
5. Rendere disponibili entrambe.
6. Confermare l'incontro da entrambe.
7. Registrare il primo e il secondo set.
8. Controllare campi e classifica.
9. Accedere come organizzatore e provare una correzione.

Le sessioni vengono conservate per scheda tramite `sessionStorage`. Per evitare interferenze nella prova usare finestre separate, preferibilmente normale e incognito.

Per i test automatici, dalla cartella principale:

```powershell
py -3 -m unittest discover -s torneo-server -v
```

## 12. Arresto, salvataggio e riavvio

### Arrestare

In ciascuno dei due terminali premere **Ctrl+C**.  Aspettare che ricompaia il prompt PowerShell, per esempio `PS C:\progetti\em\torneo-server>`.

`KeyboardInterrupt` nel terminale del backend è normale. Squadre, disponibilità, impostazioni e risultati restano nel database. Le sessioni di accesso sono invece in memoria e si perdono al riavvio.

### Fare un backup

Arrestare il backend, poi copiare il file database in una cartella di backup. Non affidarsi al repository Git come backup del database: i file `.db` sono esclusi dai file tracciati nella cartella del server.

### Riavviare

Primo terminale, dalla cartella principale:

```powershell
py -3 -m http.server 8000
```

Secondo terminale, dalla cartella principale:

```powershell
cd torneo-server
$env:TORNEO_ADMIN_PASSWORD = 'ScegliUnaPassword!'
$env:TORNEO_ORIGIN = 'http://localhost:8000'
$env:TORNEO_DB = 'torneo-evento.db'
py -3 server.py
```

Usare il database corretto, riaprire la pagina, uscire da eventuali vecchie sessioni e accedere nuovamente. Gli incontri salvati in corso restano tali; le richieste in attesa vengono controllate alla prima chiamata all'API, anche per eventuali scadenze.

## 13. Accesso da più dispositivi sulla stessa rete

Questa sezione richiede una rete Wi-Fi condivisa che consenta ai dispositivi di comunicare tra loro. Alcune reti pubbliche isolano i client.

1. Collegare PC e telefoni alla stessa rete.
2. Trovare l'indirizzo IP locale del PC in Impostazioni → Rete e Internet → proprietà della connessione, alla voce indirizzo IPv4 (oppure eseguire `ipconfig` nel terminale e leggere IPv4 della scheda Wi-Fi attiva). Esempio: `192.168.1.50`.
3. In `assets/js/torneo-config.js` impostare, sostituendo l'IP reale:

```javascript
window.TORNEO_API_URL = 'http://192.168.1.50:8080';
```

4. Fermare e riavviare il backend con l'origine del sito in rete:

```powershell
$env:TORNEO_ORIGIN = 'http://192.168.1.50:8000'
py -3 server.py
```

Le altre variabili devono essere ancora impostate nel terminale; altrimenti reimpostarle come nella procedura di avvio.

5. Tenere attivo il sito sulla porta 8000.
6. Consentire a Python le connessioni in ingresso sulla rete privata se Windows Defender Firewall lo richiede. Non autorizzare indiscriminatamente le reti pubbliche.
7. Aprire su tutti i dispositivi, anche su Windows:

```text
http://192.168.1.50:8000/torneo.html
```

8. Effettuare una prova completa con due telefoni prima dell'evento.

L'IP può cambiare: se cambia, aggiornare configurazione, origine e collegamento. Il PC deve restare acceso e non andare in stop durante il torneo.

Questa configurazione HTTP è adatta a una prova su rete fidata: password e codici non sono protetti da HTTPS. Per l'uso pubblico preferire la pubblicazione HTTPS. Non esporre semplicemente queste porte su Internet.

## 14. Pubblicazione online

Il frontend può restare su GitHub Pages. Serve un hosting separato per il backend con:

- esecuzione continuativa di Python;
- HTTPS tramite reverse proxy;
- disco persistente per il database;
- backup;
- limite ai tentativi di accesso e alle dimensioni delle richieste sul proxy.

Configurazione backend:

| Variabile | Valore |
| --- | --- |
| `TORNEO_ADMIN_PASSWORD` | Password privata di almeno 12 caratteri |
| `TORNEO_ORIGIN` | Origine esatta del frontend, senza percorso |
| `TORNEO_DB` | Percorso del database sul disco persistente |
| `PORT` | Porta del servizio; predefinita 8080 |

Per il sito GitHub Pages di questo progetto, l'origine è `https://giorgimariachiara.github.io`, senza `/em`.

Nel frontend impostare l'URL HTTPS reale del backend:

```javascript
window.TORNEO_API_URL = 'https://indirizzo-reale-del-backend';
```

L'indirizzo sopra è un segnaposto, non un servizio esistente. Non inserire password in questo file.

La versione attuale usa un server Python singolo che serializza le richieste; le modifiche sono in transazioni SQLite. Eseguire una sola istanza: più istanze non condividono automaticamente le sessioni. Per grandi eventi occorre valutare capacità e architettura prima dell'uso.

La documentazione non implica che il backend sia già pubblicato: fino alla sua configurazione il sito GitHub Pages può mostrare la pagina, ma le operazioni del torneo non funzionano.

## 15. Risoluzione dei problemi

| Problema | Causa possibile | Soluzione |
| --- | --- | --- |
| Servizio non disponibile o errore di connessione | Backend spento, URL errato o origine diversa | Controllare secondo terminale, `torneo-config.js` e `TORNEO_ORIGIN` |
| Password non valida | Password diversa o casella organizzatore non selezionata | Spuntare organizzatore e usare il valore impostato nel backend |
| Codice squadra non valido | Codice errato o nome usato per una squadra creata prima della modifica | Usare il codice originale; per nuovi nomi creare un nuovo torneo |
| Accesso richiesto dopo riavvio | Sessione precedente non più valida | Premere Esci e accedere nuovamente |
| Voglio giocare disabilitato | Pausa, chiusura o incontro già assegnato | Controllare stato e riquadro dell'incontro |
| Nessun incontro assegnato | Nessuna squadra disponibile del girone, campo occupato o calendario completato | Controllare disponibilità, campi e risultati |
| I comandi scritti non partono | Terminale ancora occupato dal server | Ctrl+C, attendere il prompt PowerShell, poi eseguire i comandi |
| Address already in use | Porta già occupata | Fermare il vecchio servizio nel suo terminale; non avviare copie multiple |
| Il telefono non apre localhost | localhost indica il telefono | Usare configurazione di rete o backend pubblico |
| Il telefono non raggiunge il PC | Rete diversa, isolamento Wi-Fi o firewall | Controllare rete, IP e autorizzazioni in ingresso |
| Compare un torneo vuoto | Percorso database diverso | Fermare il backend e impostare il database corretto |
| Non compaiono modifiche alla pagina | Cache o file non aggiornati | Pull del repository e ricaricamento con Ctrl+F5 |

### Leggere i messaggi del terminale

- `200`: richiesta completata correttamente.
- `204` su `OPTIONS`: verifica preliminare del browser completata.
- `400`: dati o operazione non validi; leggere l'errore nella pagina.
- `401`: accesso necessario o sessione scaduta.
- `403`: operazione non consentita a quell'utente.
- `500`: errore interno; verificare configurazione e database.

Se PowerShell non riconosce `py`, controllare l’installazione di Python. Se invece segnala errore sulla sintassi `$env:`, verificare di non essere nel Prompt dei comandi (cmd) o in Git Bash.

## 16. File principali

| File | Responsabilità |
| --- | --- |
| `torneo.html` | Struttura della pagina |
| `assets/css/torneo.css` | Stile e layout responsive |
| `assets/js/torneo-config.js` | Indirizzo pubblico dell'API |
| `assets/js/torneo.js` | Interazioni e aggiornamenti |
| `torneo-server/server.py` | API, accessi, database e assegnazioni |
| `torneo-server/test_server.py` | Test di integrazione |

## 17. Checklist prima dell'evento

- [ ] Verificare che si stia usando il database dell'evento giusto.
- [ ] Provare il collegamento dai dispositivi effettivi dei partecipanti.
- [ ] Controllare numero dei campi e gironi.
- [ ] Conservare e consegnare i codici squadra.
- [ ] Usare una password organizzatore privata.
- [ ] Verificare che le assegnazioni siano aperte.
- [ ] Provare conferme, due set e correzione risultati in un database di prova.
- [ ] Definire la regola per eventuali parità complete.
- [ ] Predisporre backup e un referente organizzatore.
- [ ] Tenere attivo il backend e impedire lo stop del computer se usato come server.


## Note specifiche per Windows

- Usare PowerShell per tutti i comandi di questa guida.
- In VS Code, aprire due terminali distinti tramite il pulsante **+**.
- `pwd` e `ls` funzionano in PowerShell come alias per mostrare percorso e file.
- Se un percorso contiene spazi, racchiuderlo tra virgolette: `cd "C:\Users\Nome Utente\Documents\GitHub\em"`.
- Non serve attivare un ambiente virtuale per il backend attuale.
- Per le prove da telefoni, usare una rete privata fidata e autorizzare Python nel firewall solo dove necessario.
- Il comando `py -3 server.py` occupa il terminale finché non si preme **Ctrl+C**.
