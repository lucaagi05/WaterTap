# WATER-TAP
WATER-TAP è un'installazione interattiva che trasforma il tocco umano in onde digitali.

## L'Esperienza
Avvicinandosi all'installazione, lo spettatore si trova davanti a una lastra di metallo sospesa. Ogni volta che la superficie viene sfiorata o colpita, il metallo reagisce come se fosse uno specchio d'acqua: dal punto esatto del contatto si genera un anello concentrico che si espande nello spazio digitale, propagandosi fino a svanire delicatamente.


## La Struttura
La base è un supporto cavo stampato in PLA (23x23x5 cm) che sorregge una lastra metallica di 20x20 cm.

## Il Tocco
Al di sotto della lastra, dei sensori piezoelettrici rilevano la vibrazione del tocco, captandone sia la posizione che l'intensità.

## L'Elaborazione
Una scheda Arduino riceve il segnale dai sensori e lo invia in tempo reale a uno script Python all'interno dell'ambiente Grasshopper.

## L'Animazione
Il software elabora i dati all'interno di una regione di punti (un point cloud), calcolando l'origine geometrica dell'impatto per generare la propagazione fluida dell'anello d'acqua.
