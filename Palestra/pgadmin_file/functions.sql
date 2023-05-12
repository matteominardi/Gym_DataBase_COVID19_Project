/*
Al momento della creazione di un nuovo corso, si occupa di inserire nelle tabelle corsislot e sedutecorsi gli id del corso 
e dello slot, che inizia all’ora indicata dal parametro “slot”, per ogni giorno della settimana indicato dal parametro “giorno”, 
per ogni settimana, per i prossimi 30 giorni.
*/
DROP PROCEDURE IF EXISTS aggiungi_corsi_slot(idcorso INT, giorno INT, slot TIME);
CREATE PROCEDURE aggiungi_corsi_slot(idcorso INT, giorno INT, slot TIME) AS $$
    DECLARE giorno_finale DATE = CURRENT_DATE + 30;
    DECLARE giorno_buffer DATE = CURRENT_DATE + 1;
    DECLARE giorno_settimana INT;
    DECLARE slot_c INT;
    DECLARE seduta_c INT;
    DECLARE cs_iscrittimax INT;
    BEGIN
        SELECT COALESCE(MAX(id),0) INTO seduta_c FROM sedutecorsi;
        SELECT iscrittimax INTO cs_iscrittimax FROM corsi where id=idcorso;
        WHILE giorno_buffer < giorno_finale LOOP
            SELECT EXTRACT(DOW FROM giorno_buffer) INTO giorno_settimana;
            IF (giorno_settimana = giorno) THEN
                SELECT s.id INTO slot_c FROM slot s WHERE s.giorno = giorno_buffer AND s.orainizio = slot;
                INSERT INTO corsislot VALUES (idcorso, slot_c, cs_iscrittimax);
                seduta_c = seduta_c + 1;
                INSERT INTO sedutecorsi(id, corso, dataseduta) VALUES(seduta_c, idcorso, giorno_buffer+slot);
                giorno_buffer = giorno_buffer + 7;
            ELSE 
                giorno_buffer = giorno_buffer + 1;
            END IF;
        END LOOP;
    END;
$$ LANGUAGE 'plpgsql';




/*
Al momento della creazione di una nuova sala pesi, si occupa di inserire nelle tabelle salapesislot e sedutesalepesi gli id 
della sala pesi e di ogni slot appartenente ai prossimi 30 giorni, perchè abbiamo assunto che le sale pesi siano sempre aperte.
*/
DROP PROCEDURE IF EXISTS aggiungi_salapesi_slot(idsala INT);
CREATE PROCEDURE aggiungi_salapesi_slot(idsala INT) AS $$
    DECLARE giorno_finale DATE = CURRENT_DATE + 30;
    DECLARE giorno_buffer DATE = CURRENT_DATE + 1;
    DECLARE slot_sp INT;
    DECLARE seduta_sp INT;
    DECLARE sp_iscrittimax INT;
    DECLARE slot_s TIME = '05:30:00';
    DECLARE s slot%rowtype;
    BEGIN
        SELECT COALESCE(MAX(id),0) INTO seduta_sp FROM sedutesalepesi;
        SELECT iscrittimax INTO sp_iscrittimax FROM salepesi where id=idsala;
        WHILE giorno_buffer <= giorno_finale LOOP
            FOR s IN SELECT * FROM slot WHERE giorno = giorno_buffer LOOP
                INSERT INTO salapesislot VALUES (idsala, s.id, sp_iscrittimax);
                seduta_sp = seduta_sp + 1;
                INSERT INTO sedutesalepesi(id, salapesi, dataseduta) VALUES(seduta_sp, idsala, giorno_buffer+s.orainizio);
            END LOOP;
            giorno_buffer = giorno_buffer + 1;
        END LOOP;
    END;
$$ LANGUAGE 'plpgsql';




/*
Sistema per ogni corso e sala pesi il numero massimo di persone che possono accedervi in base alla dimensione dello spazio di 
allenamento e al numero di metri quadri minimi da garantire ad ogni persona.
Imposta il numero di persone massime all’interno di ogni slot come la somma degli iscritti massimi possibili dei corsi e delle 
sale pesi presenti in quello slot.
*/
DROP TRIGGER IF EXISTS t_personemq ON informazioni CASCADE;
DROP FUNCTION IF EXISTS trigger_personemq();
CREATE FUNCTION trigger_personemq() RETURNS trigger AS $$
    BEGIN
        UPDATE corsi c SET iscrittimax = (SELECT s.dimensione
                                            FROM stanze s
                                            WHERE c.stanza=s.id) / NEW.personemq;
        UPDATE salepesi sp SET iscrittimax = (sp.dimensione) / NEW.personemq;
        UPDATE slot s SET personemax = 1 + (SELECT COALESCE(SUM(c.iscrittimax),0) 
                                        FROM corsi c JOIN corsislot cs ON c.id=cs.corso
                                        WHERE s.id=cs.slot)
                                        +
                                        (SELECT COALESCE(SUM(sp.iscrittimax),0) 
                                        FROM salepesi sp JOIN salapesislot ss ON sp.id=ss.salapesi
                                        WHERE s.id=ss.slot)
                        WHERE giorno > CURRENT_DATE + 7; 
        UPDATE salapesislot ps SET iscrittimax = (SELECT sp.iscrittimax FROM salepesi sp WHERE sp.id=ps.salapesi)
                                WHERE slot IN (SELECT id FROM slot WHERE giorno > CURRENT_DATE + 7);
        UPDATE corsislot cs SET iscrittimax = (SELECT c.iscrittimax FROM corsi c WHERE c.id=cs.corso)
                                WHERE slot IN (SELECT id FROM slot WHERE giorno > CURRENT_DATE + 7);
        UPDATE informazioni SET personemaxslot = (SELECT COALESCE(MAX(personemax),0) FROM slot WHERE giorno > CURRENT_DATE + 7);
        RETURN NULL;
    END;
$$ LANGUAGE 'plpgsql';

CREATE TRIGGER t_personemq AFTER UPDATE OF personemq ON informazioni
FOR EACH ROW
EXECUTE FUNCTION trigger_personemq();




/*
Sistema per ogni nuovo corso, dopo il suo inserimento, il numero massimo di iscritti che può avere in base alla stanza in cui 
si svolge.
*/
DROP TRIGGER IF EXISTS t_iscrittimax_corso_stanza ON corsi CASCADE;
DROP FUNCTION IF EXISTS trigger_iscrittimax_corso_stanza();
CREATE FUNCTION trigger_iscrittimax_corso_stanza() RETURNS trigger AS $$
    DECLARE pmq INT;
    BEGIN
        SELECT personemq INTO pmq FROM informazioni;
        UPDATE corsi c SET iscrittimax = (SELECT s.dimensione
                                            FROM stanze s
                                            WHERE c.stanza=s.id) / pmq;
        RETURN NULL;
    END;
$$ LANGUAGE 'plpgsql';

CREATE TRIGGER t_iscrittimax_corso_stanza AFTER INSERT ON corsi
FOR EACH ROW
EXECUTE FUNCTION trigger_iscrittimax_corso_stanza();




/*
Si occupa di gestire il caso in cui si voglia mettere un limite al numero massimo di persone che possono accedere ad uno slot 
e abbassa il numero di persone iscrivibili ai corsi/sale di ciascuno slot.
*/

DROP TRIGGER IF EXISTS t_personemaxslot ON informazioni CASCADE;
DROP FUNCTION IF EXISTS trigger_personemaxslot();
CREATE FUNCTION trigger_personemaxslot() RETURNS trigger AS $$
    DECLARE valori INT;
    DECLARE totale INT;
    DECLARE totale_corsi INT;
    DECLARE totale_sale INT;
    DECLARE s slot%rowtype;
    DECLARE corso_r corsi%rowtype;
    DECLARE sala_r salepesi%rowtype;
    BEGIN
        UPDATE slot sl SET personemax = 1 + (SELECT COALESCE(SUM(iscrittimax),0) 
                                        FROM corsislot WHERE slot=sl.id) 
                                        + 
                                        (SELECT COALESCE(SUM(iscrittimax),0)
                                        FROM salapesislot WHERE slot=sl.id) 
                        WHERE giorno >= CURRENT_DATE AND giorno <= CURRENT_DATE + 7;
        FOR s IN SELECT * FROM slot WHERE giorno > CURRENT_DATE + 7 ORDER BY giorno LOOP
            SELECT COUNT(DISTINCT(c.corso)) INTO totale_corsi FROM corsislot c WHERE c.slot = s.id;
            SELECT COUNT(DISTINCT(sp.salapesi)) INTO totale_sale FROM salapesislot sp WHERE sp.slot = s.id;
            totale = totale_corsi + totale_sale;
            IF (totale = 0) THEN
                totale = 1;
            END IF;
            valori = NEW.personemaxslot / totale;
            UPDATE corsislot SET iscrittimax = valori WHERE slot=s.id AND iscrittimax > 1 AND iscrittimax > valori;
            UPDATE salapesislot SET iscrittimax = valori WHERE slot=s.id AND iscrittimax > 1 AND iscrittimax > valori;
            UPDATE slot SET personemax = 1 + (SELECT COALESCE(SUM(iscrittimax),0) 
                                        FROM corsislot WHERE slot=s.id) 
                                        + 
                                        (SELECT COALESCE(SUM(iscrittimax),0)
                                        FROM salapesislot WHERE slot=s.id) 
                        WHERE id=s.id;
        END LOOP;
        
        RETURN NEW;      
    END;
$$ LANGUAGE 'plpgsql';

CREATE TRIGGER t_personemaxslot BEFORE UPDATE OF personemaxslot ON informazioni
FOR EACH ROW
EXECUTE FUNCTION trigger_personemaxslot();




/*
Serve per far si che non esistano due utenti con lo stesso username o con la stessa email, questo è utile anche per motivi di 
sicurezza dato che le password uguali appaiono come diverse quando vengono cifrate e inserite all’interno del database.
*/
DROP TRIGGER IF EXISTS t_username_diversi_utenti ON utenti CASCADE;
DROP FUNCTION IF EXISTS trigger_username_diversi_utenti();
CREATE FUNCTION trigger_username_diversi_utenti() RETURNS trigger AS $$
    BEGIN
        IF (EXISTS (SELECT * FROM utenti u WHERE u.username=NEW.username OR u.email=NEW.email)) THEN
            RETURN NULL;
        END IF;
        RETURN NEW;
    END;
$$ LANGUAGE 'plpgsql';

CREATE TRIGGER t_username_diversi_utenti BEFORE INSERT OR UPDATE ON utenti
FOR EACH ROW
EXECUTE FUNCTION trigger_username_diversi_utenti();




DROP TRIGGER IF EXISTS t_username_diversi_clienti ON clienti CASCADE;
DROP FUNCTION IF EXISTS trigger_username_diversi_clienti();
CREATE FUNCTION trigger_username_diversi_clienti() RETURNS trigger AS $$
    BEGIN
        IF (NOT EXISTS (SELECT * FROM utenti u WHERE u.id=NEW.id)) THEN
            RETURN NULL;
        END IF;
        RETURN NEW;
    END;
$$ LANGUAGE 'plpgsql';

CREATE TRIGGER t_username_diversi_clienti BEFORE INSERT OR UPDATE ON clienti
FOR EACH ROW
EXECUTE FUNCTION trigger_username_diversi_clienti();




/*
Serve per far si che vengano inseriti all’interno delle tabelle abbonati e non abbonati solo utenti che sono effettivamente 
clienti della palestra.
*/
DROP TRIGGER IF EXISTS t_insert_nonabbonati ON nonabbonati CASCADE;
DROP TRIGGER IF EXISTS t_insert_abbonati ON abbonati CASCADE;
DROP FUNCTION IF EXISTS trigger_insert_clienti();
CREATE FUNCTION trigger_insert_clienti() RETURNS trigger AS $$
    BEGIN
        IF (NOT EXISTS (SELECT * FROM clienti c WHERE c.id=NEW.id)) THEN
            RETURN NULL;
        END IF;
        RETURN NEW;
    END;
$$ LANGUAGE 'plpgsql';

CREATE TRIGGER t_insert_abbonati BEFORE INSERT OR UPDATE ON abbonati
FOR EACH ROW
EXECUTE FUNCTION trigger_insert_clienti();

CREATE TRIGGER t_insert_nonabbonati BEFORE INSERT OR UPDATE ON nonabbonati
FOR EACH ROW
EXECUTE FUNCTION trigger_insert_clienti();




/*
Si occupa della creazione dei giorni con i relativi slot prenotabili per i prossimi 30 giorni, controllando che tutti o in 
parte non siano già presenti.
*/
DROP PROCEDURE IF EXISTS check_genera_giorno_e_slot();
CREATE PROCEDURE check_genera_giorno_e_slot() AS $$
    DECLARE pms INT; 
    DECLARE idSlot INT;
    DECLARE giorno_tmp DATE;
    DECLARE oraIn TIME = '05:30:00';
	DECLARE oraFin TIME = '08:50:00';
    BEGIN
        SELECT personemaxslot INTO pms FROM informazioni;
        SELECT MAX(id) INTO idSlot FROM slot;
        idSlot = idSlot + 1;
        FOR i IN 1..30 LOOP
            giorno_tmp = CURRENT_DATE + i;
            IF (NOT EXISTS(SELECT * FROM giorni WHERE data = giorno_tmp)) THEN
                INSERT INTO giorni VALUES(giorno_tmp);
                FOR j IN 0..5 LOOP
                    INSERT INTO slot VALUES(idSlot, pms, giorno_tmp, oraIn, oraFin);
                    idSlot = idSlot + 1;
                    oraIn = oraFin + '00:10:00';
                    oraFin = oraIn + '02:50:00';
                END LOOP;
                oraIn = '05:30:00';
                oraFin = '08:50:00';
            END IF;
        END LOOP;
    END;
$$ LANGUAGE 'plpgsql';




/*
Si occupa di aggiornare per ogni corso le relative sedute, gestendo direttamente anche la tabella corsislot.
*/
DROP PROCEDURE IF EXISTS check_aggiungi_corsi_slot();
CREATE PROCEDURE check_aggiungi_corsi_slot() AS $$
    DECLARE idSedute INT;
    DECLARE idSlot INT;
    DECLARE c corsi%rowtype;
    DECLARE data_tmp TIMESTAMP;
    DECLARE data_buff TIMESTAMP;
    BEGIN
        SELECT COALESCE(MAX(id),0) INTO idSedute FROM sedutecorsi;
        idSedute = idSedute + 1;
        FOR c IN SELECT * FROM corsi ORDER BY id LOOP
            FOR i IN 0..6 LOOP
                SELECT se.dataseduta INTO data_tmp FROM sedutecorsi se WHERE se.corso=c.id AND i=(SELECT EXTRACT(DOW FROM se.dataseduta));
                IF (data_tmp IS NOT NULL) THEN
                    FOR j IN 0..3 LOOP
                        IF (NOT EXISTS(SELECT * FROM sedutecorsi se WHERE se.corso=c.id AND se.dataseduta=(data_tmp + (INTERVAL '1 day' * 7*j)))) THEN
                            INSERT INTO sedutecorsi VALUES(idSedute, c.id, data_tmp + (INTERVAL '1 day' * 7*j)); 
                            SELECT dataseduta INTO data_buff FROM sedutecorsi WHERE id=idSedute;
                            SELECT id INTO idSlot FROM slot WHERE giorno=(data_buff::date) AND orainizio=(data_buff::time);
                            IF (NOT EXISTS (SELECT * FROM corsislot WHERE corso=c.id AND slot=idSlot)) THEN
                                INSERT INTO corsislot VALUES(c.id, idSlot, c.iscrittimax);
                            END IF;
                            idSedute = idSedute + 1;
                        END IF;
                    END LOOP; 
                END IF;
            END LOOP;    
        END LOOP;
    END;
$$ LANGUAGE 'plpgsql';




/*
Si occupa di aggiornare per ogni salapesi le relative sedute, gestendo direttamente anche la tabella salapesislot.
*/
DROP PROCEDURE IF EXISTS check_aggiungi_salepesi_slot();
CREATE PROCEDURE check_aggiungi_salepesi_slot() AS $$
    DECLARE idSedute INT;
    DECLARE sp salepesi%rowtype;
    DECLARE g giorni%rowtype;
    DECLARE s slot%rowtype;
    BEGIN
        SELECT COALESCE(MAX(id),0) INTO idSedute FROM sedutesalepesi;
        idSedute = idSedute + 1;
        FOR sp IN SELECT * FROM salepesi ORDER BY id LOOP
            FOR g IN SELECT * FROM giorni ORDER BY data LOOP
                FOR s IN SELECT * FROM slot WHERE giorno=g.data LOOP
                    IF (NOT EXISTS(SELECT * FROM sedutesalepesi se WHERE se.salapesi=sp.id AND se.dataseduta=(s.giorno + s.orainizio))) THEN
                        INSERT INTO sedutesalepesi VALUES(idSedute, sp.id, s.giorno + s.orainizio);
                        IF (NOT EXISTS (SELECT * FROM salapesislot WHERE salapesi=sp.id AND slot=s.id)) THEN
                            INSERT INTO salapesislot VALUES(sp.id, s.id, sp.iscrittimax);
                        END IF;
                        idSedute = idSedute + 1;
                    END IF;
                END LOOP;
            END LOOP;
        END LOOP;
    END;
$$ LANGUAGE 'plpgsql';




/*
Si occupa di mantenere il database aggiornato per quanto riguarda gli utenti abbonati, non abbonati, i giorni, gli slot, 
le sedute dei corsi e delle sale, e la possibilità di prenotare le sedute future.
*/
DROP TRIGGER IF EXISTS check_data_fine_abbonamento ON controlli CASCADE;
DROP FUNCTION IF EXISTS trigger_check_data_fine_abbonamento();
CREATE FUNCTION trigger_check_data_fine_abbonamento() RETURNS trigger AS $$
    DECLARE personemaxslot_buffer INT;
    BEGIN
        DELETE FROM giorni WHERE data < CURRENT_DATE - 7;
        INSERT INTO nonabbonati (id) SELECT id FROM abbonati WHERE datafineabbonamento < CURRENT_DATE;
        INSERT INTO prenotazioninonabbonati (nonabbonato, slot) SELECT p.abbonato, p.slot 
                                                                FROM prenotazioni p JOIN slot sl ON p.slot=sl.id
                                                                WHERE p.abbonato IN (SELECT * FROM nonabbonati) AND sl.giorno >= CURRENT_DATE - 7;
        DELETE FROM abbonati WHERE datafineabbonamento < CURRENT_DATE;
        CALL check_genera_giorno_e_slot();
        CALL check_aggiungi_corsi_slot();
        CALL check_aggiungi_salepesi_slot();
        SELECT personemaxslot INTO personemaxslot_buffer FROM informazioni;
        UPDATE informazioni SET personemaxslot = personemaxslot_buffer;
        RETURN NEW;
    END;
$$ LANGUAGE 'plpgsql';

CREATE TRIGGER check_data_fine_abbonamento BEFORE UPDATE ON controlli
FOR EACH ROW
EXECUTE FUNCTION trigger_check_data_fine_abbonamento();




/*
Nella rimozione di un corso si occupa di rimuovere anche le prenotazioni effettuate per quel corso in futuro.
*/
DROP TRIGGER IF EXISTS cancella_prenotazioni_corsi ON corsi CASCADE;
DROP FUNCTION IF EXISTS trigger_cancella_prenotazioni_corsi();
CREATE FUNCTION trigger_cancella_prenotazioni_corsi() RETURNS trigger AS $$
    DECLARE sc sedutecorsi%rowtype;
    DECLARE da_eliminare TIMESTAMP;
    DECLARE c INT;
    BEGIN
        SELECT id INTO c FROM corsi WHERE id=OLD.id;
        FOR sc IN SELECT * FROM sedutecorsi WHERE corso=c AND dataseduta > CURRENT_DATE LOOP
            da_eliminare = sc.dataseduta;
            DELETE FROM prenotazioni WHERE slot = (
                SELECT id FROM SLOT WHERE giorno = da_eliminare::date AND orainizio = da_eliminare::time)
                                            AND abbonato IN (SELECT abbonato FROM abbonatisedutecorsi WHERE seduta = sc.id);
        END LOOP;
        RETURN OLD;
    END;
$$ LANGUAGE 'plpgsql';

CREATE TRIGGER cancella_prenotazioni_corsi BEFORE DELETE ON corsi
FOR EACH ROW
EXECUTE FUNCTION trigger_cancella_prenotazioni_corsi();




/*
Nella rimozione di una sala pesi si occupa di rimuovere anche le prenotazioni effettuate successivamente per quella sala pesi
*/
DROP TRIGGER IF EXISTS cancella_prenotazioni_salepesi ON salepesi CASCADE;
DROP FUNCTION IF EXISTS trigger_cancella_prenotazioni_salepesi();
CREATE FUNCTION trigger_cancella_prenotazioni_salepesi() RETURNS trigger AS $$
    DECLARE sc sedutesalepesi%rowtype;
    DECLARE s INT;
    BEGIN
        SELECT id INTO s FROM salepesi WHERE id=OLD.id;
        FOR sc IN SELECT * FROM sedutesalepesi WHERE salapesi=s AND dataseduta > CURRENT_DATE LOOP
            DELETE FROM prenotazioni WHERE slot IN (SELECT id FROM SLOT WHERE giorno > CURRENT_DATE)
                                            AND abbonato IN (SELECT abbonato FROM abbonatisedutesalepesi WHERE seduta = sc.id);
        END LOOP;
        RETURN OLD;
    END;
$$ LANGUAGE 'plpgsql';

CREATE TRIGGER cancella_prenotazioni_salepesi BEFORE DELETE ON salepesi
FOR EACH ROW
EXECUTE FUNCTION trigger_cancella_prenotazioni_salepesi();




/*
Controlla che prima di rimuovere una stanza non sia utilizzata da nessun corso.
*/
DROP TRIGGER IF EXISTS cancella_stanza_occupata ON stanze CASCADE;
DROP FUNCTION IF EXISTS trigger_cancella_stanza_occupata();
CREATE FUNCTION trigger_cancella_stanza_occupata() RETURNS trigger AS $$
    BEGIN
        IF (EXISTS (SELECT * FROM corsi WHERE stanza=OLD.id)) THEN
            RETURN NULL;
        END IF;
        RETURN OLD;
    END;
$$ LANGUAGE 'plpgsql';

CREATE TRIGGER cancella_stanza_occupata BEFORE DELETE ON stanze
FOR EACH ROW
EXECUTE FUNCTION trigger_cancella_stanza_occupata();





/*
Controlla che prima di rimuovere un istruttore non sia resposabile di nessun corso.
*/
DROP TRIGGER IF EXISTS cancella_istruttore_occupato ON utenti CASCADE;
DROP FUNCTION IF EXISTS trigger_cancella_istruttore_occupato();
CREATE FUNCTION trigger_cancella_istruttore_occupato() RETURNS trigger AS $$
    BEGIN
        IF (EXISTS (SELECT * FROM corsi WHERE istruttore=OLD.id)) THEN
            RETURN NULL;
        END IF;
        RETURN OLD;
    END;
$$ LANGUAGE 'plpgsql';

CREATE TRIGGER cancella_istruttore_occupato BEFORE DELETE ON utenti
FOR EACH ROW
EXECUTE FUNCTION trigger_cancella_istruttore_occupato();