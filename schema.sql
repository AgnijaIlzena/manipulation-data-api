DROP TABLE IF EXISTS avis;
DROP TABLE IF EXISTS paiements;
DROP TABLE IF EXISTS articles_commande;
DROP TABLE IF EXISTS commandes;
DROP TABLE IF EXISTS produits;
DROP TABLE IF EXISTS vendeurs;
DROP TABLE IF EXISTS clients;

CREATE TABLE clients (
    client_id VARCHAR(32) PRIMARY KEY,
    client_unique_id VARCHAR(32),
    code_postal VARCHAR(10),
    ville VARCHAR(100),
    etat VARCHAR(2)
);

CREATE TABLE vendeurs (
    vendeur_id VARCHAR(32) PRIMARY KEY,
    code_postal VARCHAR(10),
    ville VARCHAR(100),
    etat VARCHAR(2)
);

CREATE TABLE produits (
    produit_id VARCHAR(32) PRIMARY KEY,
    categorie VARCHAR(100),
    longueur_nom INT,
    longueur_description INT,
    nb_photos INT,
    poids_g FLOAT,
    longueur_cm FLOAT,
    hauteur_cm FLOAT,
    largeur_cm FLOAT
);

CREATE TABLE commandes (
    commande_id VARCHAR(32) PRIMARY KEY,
    client_id VARCHAR(32),
    statut VARCHAR(50),
    date_achat DATETIME,
    date_approbation DATETIME,
    date_expedition DATETIME,
    date_livraison DATETIME,
    date_livraison_estimee DATETIME,
    FOREIGN KEY (client_id) REFERENCES clients(client_id)
);

CREATE TABLE articles_commande (
    commande_id VARCHAR(32),
    numero_article INT,
    produit_id VARCHAR(32),
    vendeur_id VARCHAR(32),
    date_limite_expedition DATETIME,
    prix DECIMAL(10, 2),
    frais_livraison DECIMAL(10, 2),
    PRIMARY KEY (commande_id, numero_article),
    FOREIGN KEY (commande_id) REFERENCES commandes(commande_id),
    FOREIGN KEY (produit_id) REFERENCES produits(produit_id),
    FOREIGN KEY (vendeur_id) REFERENCES vendeurs(vendeur_id)
);

CREATE TABLE paiements (
    commande_id VARCHAR(32),
    sequence INT,
    type_paiement VARCHAR(50),
    nb_versements INT,
    montant DECIMAL(10, 2),
    PRIMARY KEY (commande_id, sequence),
    FOREIGN KEY (commande_id) REFERENCES commandes(commande_id)
);

CREATE TABLE avis (
    avis_id VARCHAR(32) PRIMARY KEY,
    commande_id VARCHAR(32),
    note INT,
    titre TEXT,
    commentaire TEXT,
    date_creation DATETIME,
    date_reponse DATETIME,
    FOREIGN KEY (commande_id) REFERENCES commandes(commande_id)
);
