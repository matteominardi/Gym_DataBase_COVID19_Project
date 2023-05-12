/* Query per analizzare trigger */
delete from giorni where data > '2021-09-15';
delete from sedutecorsi where dataseduta > '2021-09-15';
delete from sedutesalepesi where dataseduta > '2021-09-15';

/*Esegui controlli giornalieri*/
select s.giorno, s.orainizio, sp.salapesi, sp.iscrittimax, s.personemax from slot s join salapesislot sp on sp.slot=s.id order by giorno;

/*Persone mq e personemax*/
select cs.corso, cs.iscrittimax, s.giorno, s.orainizio, sp.salapesi, sp.iscrittimax, s.personemax from corsislot cs join slot s on cs.slot=s.id join salapesislot sp on sp.slot=s.id order by giorno;

/* Utenti nel database */
select * from utenti;

/*Salepesi-slot e corsi-slot*/
select * from salapesislot sp join slot s on sp.slot=s.id order by giorno;
select * from corsislot cs join slot s on cs.slot=s.id order by giorno;

select * from sedutecorsi order by dataseduta;
select * from sedutesalepesi order by dataseduta;

select * from slot order by giorno;







































/* Prenotazioni per contact tracing */
--giorno 30-08-2021 alle 05.30
insert into prenotazioni values(100, 1);
insert into prenotazioni values(101, 1);
insert into prenotazioninonabbonati values(104, 1);

--giorno 30-08-2021 alle 21.00
insert into prenotazioni values(102, 6);
insert into prenotazioni values(103, 6);

--giorno 31-08 2021 alle 12.00
insert into prenotazioni values(100, 9);
insert into prenotazioni values(101, 9);
insert into prenotazioni values(102, 9);
insert into prenotazioni values(103, 9);
insert into prenotazioninonabbonati values(104, 9);

--giorno 31-08 2021 alle 18.00
insert into prenotazioni values(100, 11);
insert into prenotazioninonabbonati values(104, 11);

--giorno 31-08 2021 alle 21.00
insert into prenotazioni values(101, 12);
insert into prenotazioninonabbonati values(104, 12);

--giorno 01-09 2021 alle 05.30
insert into prenotazioni values(100, 13);
insert into prenotazioni values(101, 13);
insert into prenotazioni values(102, 13);
insert into prenotazioni values(103, 13);
insert into prenotazioninonabbonati values(104, 13);

/**/
