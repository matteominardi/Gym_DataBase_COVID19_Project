# Developed by
Matteo Minardi, Massimo Cailotto (maxcail8 on github)

# Made using
Flask, SQLAlchemy, postgresSQL, Python, JavaScript, HTML

# Settaggio parametri applicazione
Parametri DATABASE
nome: `progetto_palestra`

Parametri USER
utente: `postgres`
password: `postgres`

# Creazione e popolamento DataBase
Creare un nuovo DataBase di nome `progetto_palestra` direttamete su pgAdmin.
I file SQL contenenti la creazione delle tabelle, triggers e della popolazione iniziale sono contenuti nella cartella `"pgadmin_file"`.

Copiare direttamente il contenuto dei file all'interno dello strumento Query Tool in questo ordine:
1. `"creation.sql"` per la creazione delle tabelle
2. `"population.sql"` per inserire dati come abbonamenti e stanze, utili per l’utilizzo iniziale dell’applicazione.
1. `"function.sql"` per inserire triggers e funzioni

# Run applicazione
Eseguire `set FLASK_APP=project.py` per settare la flask-app.
Eseguire `flask run` per eseguire l'applicazione. 
Installare eventualmente da riga di comando tutte le librerie e framework mancanti tramite `pip install parametro`
Navigare a `http://localhost:5000/` (equivalentemente `http://127.0.0.1:5000/`).

# Consigli applicazione
Consigliamo di aggiungere immediatamente dei corsi, con i relativi istruttori, e delle sale pesi in modo da poter avere delle attività a cui i clienti potranno iscriversi. 

Inoltre bisognerebbe eseguire i trigger della pagina di amministrazione in questo ordine: 
1. Controlli giornalieri, meno utile al primo avvio perchè i dati vengono tutti generati alla generazione delle varie attività ma diventa fondamentale in futuro per mantenere le diverse funzionalità attive.
2. Modifica mq minimi, in modo che automaticamente si generino dei limiti dentro i quali è garantita la sicurezza per gli utenti della palestra.
3. Modifica persone massime slot, se si vuole inserire un numero diverso da quello generato precedentemente in automatico.

Gli altri due trigger riguardanti il numero massimo di accessi giornalieri e settimanali possono essere eseguiti in ordine qualsiasi.

# Modifiche DataBase postgresSQL
# Installazioni
Run `flask db init` solo la prima volta, per la creazione della directory migrations.
Run `flask db stamp head` +
Run `flask db migrate` per visualizzare le modifiche che verranno effettuate.
Infine run `flask db upgrade` per confermare le modifiche che verranno effettuate sul database.