DROP TABLE IF EXISTS restaurants;
DROP TABLE IF EXISTS pays;

CREATE TABLE pays (
    code_pays INT PRIMARY KEY,
    nom_pays VARCHAR(100)
);

CREATE TABLE restaurants (
    restaurant_id INT PRIMARY KEY,
    nom VARCHAR(255),
    code_pays INT,
    ville VARCHAR(100),
    adresse TEXT,
    localite VARCHAR(255),
    localite_complete VARCHAR(255),
    longitude FLOAT,
    latitude FLOAT,
    cuisines VARCHAR(255),
    cout_moyen_deux INT,
    devise VARCHAR(50),
    reservation_table TINYINT(1),
    livraison_en_ligne TINYINT(1),
    livre_maintenant TINYINT(1),
    commande_en_ligne TINYINT(1),
    gamme_prix INT,
    note FLOAT,
    couleur_note VARCHAR(50),
    texte_note VARCHAR(50),
    votes INT,
    FOREIGN KEY (code_pays) REFERENCES pays(code_pays)
);
