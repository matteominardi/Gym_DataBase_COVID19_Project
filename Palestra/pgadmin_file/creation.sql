--DataBase 'progetto_palestra'

--Utenti
CREATE TABLE utenti(
	id INT PRIMARY KEY,
	username VARCHAR(50),
	password VARCHAR(100),
	nome VARCHAR(100),
	cognome VARCHAR(100),
	email VARCHAR(100),
	datanascita DATE CHECK (datanascita < CURRENT_DATE)
);
CREATE INDEX ON utenti (id);

--Istruttori
CREATE TABLE istruttori(
	id INT PRIMARY KEY,
	FOREIGN KEY(id) REFERENCES utenti ON DELETE CASCADE
);
CREATE INDEX ON istruttori (id);

--Altri
CREATE TABLE altri(
	id INT PRIMARY KEY,
	FOREIGN KEY(id) REFERENCES utenti ON DELETE CASCADE
);
CREATE INDEX ON altri (id);

--Clienti
CREATE TABLE clienti(
	id INT PRIMARY KEY,
	FOREIGN KEY(id) REFERENCES utenti ON DELETE CASCADE
);
CREATE INDEX ON clienti (id);

--Abbonamenti
CREATE TABLE abbonamenti(
	id INT PRIMARY KEY,
	tipo VARCHAR(10),
	costo REAL CHECK(costo > 0)
);
CREATE INDEX ON abbonamenti (id);

--Abbonati
CREATE TABLE abbonati(
	id INT PRIMARY KEY,
	abbonamento INT NOT NULL,
	datainizioabbonamento DATE,
	datafineabbonamento DATE,
	durata INT CHECK(durata > 0), --giorni di durata
	FOREIGN KEY(id) REFERENCES clienti ON DELETE CASCADE,
	FOREIGN KEY(abbonamento) REFERENCES abbonamenti ON DELETE CASCADE,
	CHECK (datafineabbonamento > datainizioabbonamento)
);
CREATE INDEX ON abbonati (id);

--NonAbbonati
CREATE TABLE nonabbonati(
	id INT PRIMARY KEY,
	FOREIGN KEY(id) REFERENCES clienti ON DELETE CASCADE
);
CREATE INDEX ON nonabbonati (id);

--Stanze
CREATE SEQUENCE stanze_id_seq;
CREATE TABLE stanze(
	id smallint NOT NULL DEFAULT nextval('stanze_id_seq'),
	nome VARCHAR(100),
	dimensione INT CHECK(dimensione > 0), --metri quadri
	PRIMARY KEY(id)
);
ALTER SEQUENCE stanze_id_seq OWNED BY stanze.id;
CREATE INDEX ON stanze (id);

--SalePesi
CREATE SEQUENCE salepesi_id_seq;
CREATE TABLE salepesi(
	id smallint NOT NULL DEFAULT nextval('salepesi_id_seq'),	
	dimensione INT CHECK(dimensione > 0), --metri quadri
	iscrittimax INT CHECK(iscrittimax > 0),
	PRIMARY KEY(id)
);
ALTER SEQUENCE salepesi_id_seq OWNED BY salepesi.id;
CREATE INDEX ON salepesi (id);

--Corsi
CREATE SEQUENCE corsi_id_seq;
CREATE TABLE corsi(
	id smallint NOT NULL DEFAULT nextval('corsi_id_seq'),
	nome VARCHAR(100),
	iscrittimax INT CHECK(iscrittimax > 0),
	istruttore INT NOT NULL,
	stanza INT NOT NULL,
	PRIMARY KEY(id),
	FOREIGN KEY(istruttore) REFERENCES istruttori ON DELETE SET NULL,
	FOREIGN KEY(stanza) REFERENCES stanze ON DELETE CASCADE
);
ALTER SEQUENCE corsi_id_seq OWNED BY corsi.id;
CREATE INDEX ON corsi (id);
CREATE INDEX ON corsi (stanza);

--SeduteCorsi
CREATE TABLE sedutecorsi(
	id INT PRIMARY KEY,
	corso INT NOT NULL,
	dataseduta TIMESTAMP,
	FOREIGN KEY(corso) REFERENCES corsi ON DELETE CASCADE
);
CREATE INDEX ON sedutecorsi (id);

--AbbonatiSeduteCorsi
CREATE TABLE abbonatisedutecorsi(
	abbonato INT,
	seduta INT,
	PRIMARY KEY(abbonato,seduta),
	FOREIGN KEY(abbonato) REFERENCES abbonati ON DELETE CASCADE,
	FOREIGN KEY(seduta) REFERENCES sedutecorsi ON DELETE CASCADE
);
CREATE INDEX ON abbonatisedutecorsi (seduta, abbonato);

--SeduteSalePesi
CREATE TABLE sedutesalepesi(
	id INT PRIMARY KEY,
	salapesi INT NOT NULL,
	dataseduta TIMESTAMP,
	FOREIGN KEY(salapesi) REFERENCES salepesi ON DELETE CASCADE
);
CREATE INDEX ON sedutesalepesi (id);
CREATE INDEX ON sedutesalepesi (salapesi);

--AbbonatiSeduteSalePesi
CREATE TABLE abbonatisedutesalepesi(
	abbonato INT,
	seduta INT,
	PRIMARY KEY(abbonato,seduta),
	FOREIGN KEY(abbonato) REFERENCES abbonati ON DELETE CASCADE,
	FOREIGN KEY(seduta) REFERENCES sedutesalepesi ON DELETE CASCADE
);
CREATE INDEX ON abbonatisedutesalepesi (seduta, abbonato);

--Giorni
CREATE TABLE giorni(
	data DATE PRIMARY KEY
);
CREATE INDEX ON giorni (data);

--Slot
CREATE SEQUENCE slot_id_seq;
CREATE TABLE slot(
	id smallint NOT NULL DEFAULT nextval('slot_id_seq'),
	personemax INT CHECK(personemax > 0),
	giorno DATE,
	orainizio TIME,
	orafine TIME,
	PRIMARY KEY(id),
	FOREIGN KEY(giorno) REFERENCES giorni ON DELETE CASCADE,
	CHECK (orafine > orainizio) 
);
ALTER SEQUENCE slot_id_seq OWNED BY slot.id;
CREATE INDEX ON slot (id);
CREATE INDEX ON slot (giorno);

--CorsiSlot
CREATE TABLE corsislot(
	corso INT,
	slot INT,
	iscrittimax INT,
	PRIMARY KEY(corso, slot),
	FOREIGN KEY(corso) REFERENCES corsi ON DELETE CASCADE,
	FOREIGN KEY(slot) REFERENCES slot ON DELETE CASCADE
);
CREATE INDEX ON corsislot (corso, slot);

--SalaPesiSlot
CREATE TABLE salapesislot(
	salapesi INT,
	slot INT,
	iscrittimax INT,
	PRIMARY KEY(salapesi, slot),
	FOREIGN KEY(salapesi) REFERENCES salepesi ON DELETE CASCADE,
	FOREIGN KEY(slot) REFERENCES slot ON DELETE CASCADE
);
CREATE INDEX ON salapesislot (salapesi, slot);

--Prenotazioni
CREATE TABLE prenotazioni(
	abbonato INT,
	slot INT,
	PRIMARY KEY(abbonato, slot),
	FOREIGN KEY(abbonato) REFERENCES abbonati ON DELETE CASCADE,
	FOREIGN KEY(slot) REFERENCES slot ON DELETE CASCADE
);
CREATE INDEX ON prenotazioni (abbonato, slot);

--PrenotazioniNonAbbonati
CREATE TABLE prenotazioninonabbonati(
	nonabbonato INT,
	slot INT,
	PRIMARY KEY(nonabbonato, slot),
	FOREIGN KEY(nonabbonato) REFERENCES nonabbonati ON DELETE CASCADE,
	FOREIGN KEY(slot) REFERENCES slot ON DELETE CASCADE
);
CREATE INDEX ON prenotazioninonabbonati (nonabbonato, slot);

--Informazioni
CREATE TABLE informazioni(
	accessisettimana INT CHECK(accessisettimana > 0), --accessi alla settimana
	slotgiorno INT CHECK(slotgiorno > 0 AND slotgiorno < 6), --slot prenotabili al giorno
	personemaxslot INT CHECK(personemaxslot > 0), --persone massime in uno slot
	personemq INT CHECK(personemq > 0), --metri quadri garantiti a persona
	PRIMARY KEY(accessisettimana, slotgiorno, personemaxslot, personemq)
);

CREATE TABLE controlli(
	controllo INT CHECK(controllo >= 0),
	PRIMARY KEY(controllo)
);