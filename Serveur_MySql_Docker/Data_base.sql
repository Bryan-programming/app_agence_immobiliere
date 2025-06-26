-- Database Creation
CREATE DATABASE IF NOT EXISTS immo_data_base;
USE immo_data_base;

-- Tables Section
CREATE TABLE utilisateurs (
    ID_users BIGINT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    nom VARCHAR(20) NOT NULL,
    prenom VARCHAR(20) NOT NULL,
    email VARCHAR(50) NOT NULL,
    telephone BIGINT NOT NULL,
    mot_de_passe VARCHAR(255) NOT NULL,
    COMPTABLE BIGINT,
    CLIENT BIGINT,
    AGENT_IMMOBILLIER BIGINT
);
CREATE TABLE agent_immobillier (
    ID_users BIGINT NOT NULL PRIMARY KEY,
    agence VARCHAR(50) NOT NULL
    -- FOREIGN KEY (ID_users) REFERENCES utilisateurs(ID_users)
);
CREATE TABLE logement (
    ID_logement BIGINT NOT NULL PRIMARY KEY auto_increment,
    adresse VARCHAR(100) NOT NULL,
    ville VARCHAR(50) NOT NULL,
    superficie INT NOT NULL,
    nb_piece INT NOT NULL,
    disponible CHAR(1) NOT NULL,
    description VARCHAR(255) NOT NULL,
    KOT BIGINT,
    APPARTEMENT BIGINT,
    ID_users BIGINT NOT NULL,
    FOREIGN KEY (ID_users) REFERENCES agent_immobillier(ID_users),
    CHECK ((KOT IS NOT NULL AND APPARTEMENT IS NULL) OR (KOT IS NULL AND APPARTEMENT IS NOT NULL))
);


CREATE TABLE client (
    ID_users BIGINT NOT NULL PRIMARY KEY,
    ID_logement BIGINT,
    FOREIGN KEY (ID_users) REFERENCES utilisateurs(ID_users),
    FOREIGN KEY (ID_logement) REFERENCES logement(ID_logement)
);

CREATE TABLE comptable (
    ID_users BIGINT NOT NULL PRIMARY KEY,
    FOREIGN KEY (ID_users) REFERENCES utilisateurs(ID_users)
);


CREATE TABLE APPARTEMENT (
    L_A_ID_logement BIGINT NOT NULL PRIMARY KEY,
    ID_logement BIGINT NOT NULL UNIQUE,
    FOREIGN KEY (L_A_ID_logement) REFERENCES logement(ID_logement)
);

CREATE TABLE KOT (
    L_K_ID_logement BIGINT NOT NULL PRIMARY KEY,
    ID_logement BIGINT NOT NULL UNIQUE,
    FOREIGN KEY (L_K_ID_logement) REFERENCES logement(ID_logement)
);

CREATE TABLE visite (
    ID_visite BIGINT NOT NULL PRIMARY KEY auto_increment ,
    date_visite DATE NOT NULL,
    frais_visite DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) NOT NULL,
    ID_logement BIGINT NOT NULL,
    FOREIGN KEY (ID_logement) REFERENCES logement(ID_logement)
);

CREATE TABLE realise (
    ID_visite BIGINT NOT NULL PRIMARY KEY,
    date DATE NOT NULL,
    ID_users BIGINT NOT NULL,
    R_A_ID_users BIGINT NULL,
    FOREIGN KEY (ID_visite) REFERENCES visite(ID_visite),
    FOREIGN KEY (ID_users) REFERENCES client(ID_users)
);

CREATE TABLE FACTURATION_ET_COMPTABILITE (
    ID_transaction BIGINT NOT NULL PRIMARY KEY auto_increment, -- auto_increment ?
    montant DECIMAL(10,2) NOT NULL,
    date_paiement DATE NULL,
    status_paiement CHAR(1) NOT NULL,
    ID_visite BIGINT NOT NULL,
    FOREIGN KEY (ID_visite) REFERENCES visite(ID_visite)
);

CREATE TABLE effectue (
    ID_transaction BIGINT NOT NULL,
    ID_users BIGINT NOT NULL,
    PRIMARY KEY (ID_transaction, ID_users),
    FOREIGN KEY (ID_transaction) REFERENCES FACTURATION_ET_COMPTABILITE(ID_transaction),
    FOREIGN KEY (ID_users) REFERENCES comptable(ID_users)
);

-- -----------------------Triggers and views---------------------------

-- trigger: A client with the same email shouldn't exist if we want to register
DELIMITER $$
CREATE TRIGGER user_insert
BEFORE INSERT ON utilisateurs
FOR EACH ROW
BEGIN
    DECLARE rowcount INT;

    SELECT COUNT(*) INTO rowcount
    FROM utilisateurs
    WHERE email = NEW.email;

    IF rowcount > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Utilisateur déjà existant';
    END IF;
END$$
DELIMITER ;

-- trigger: Logement unavaible after a visite
DELIMITER $$
CREATE TRIGGER logement_unavaible
AFTER INSERT ON visite
FOR EACH ROW
BEGIN
     UPDATE logement
    SET disponible = '0' 
    WHERE ID_logement = NEW.ID_logement;
END$$
DELIMITER ;

-- Trigger: Generate a transaction after an insertion on visite
DELIMITER $$
CREATE TRIGGER generate_transaction_apres_realisation
AFTER INSERT ON realise
FOR EACH ROW
BEGIN
    DECLARE frais DECIMAL(10,2);

    -- Recover the costs associated with the visit
    SELECT frais_visite INTO frais
    FROM visite
    WHERE ID_visite = NEW.ID_visite;

    --  insert a transaction into FACTURATION_ET_COMPTABILITE
    INSERT INTO FACTURATION_ET_COMPTABILITE (ID_visite, montant, status_paiement)
    VALUES (NEW.ID_visite, frais, '0'  -- ou 'N' si non payé par défaut
    );
END$$
DELIMITER ;
-- trigger: link agent immobillier with logement
DELIMITER $$
CREATE TRIGGER verify_agent_existence_on_logement_insert
BEFORE INSERT ON logement
FOR EACH ROW
BEGIN
    IF NOT EXISTS (SELECT 1 FROM agent_immobillier WHERE ID_users = NEW.ID_users) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Le logement doit être associé à un agent existant.';
    END IF;
END$$
DELIMITER ;
-- trigger: limit the number of logements per agent to 5
DELIMITER $$
CREATE TRIGGER max_logements_par_agent
BEFORE INSERT ON logement
FOR EACH ROW
BEGIN
    DECLARE nb INT;
    SELECT COUNT(*) INTO nb
    FROM logement
    WHERE ID_users = NEW.ID_users;
    
    IF nb >= 5 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Un agent ne peut pas gérer plus de 10 logements.';
    END IF;
END$$
DELIMITER ;

-- trigger: prevent remove Logement
DELIMITER $$
CREATE TRIGGER verification_pour_supprimer_logement
BEFORE DELETE ON logement
FOR EACH ROW
BEGIN
    DECLARE visite_count INT DEFAULT 0;
    DECLARE facture_non_paye_count INT DEFAULT 0;

-- Vérifie s'il y a des visites réalisées pour ce logement
    SELECT COUNT(*) INTO visite_count
    FROM realise r
    JOIN visite v ON r.ID_visite = v.ID_visite
    WHERE v.ID_logement = OLD.ID_logement;

    IF visite_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Suppression impossible : des visites ont déjà été réalisées pour ce logement.';
    END IF;

    -- Vérifie s'il existe des factures non réglées pour ce logement
    SELECT COUNT(*) INTO facture_non_paye_count
    FROM FACTURATION_ET_COMPTABILITE f
    JOIN visite v ON f.ID_visite = v.ID_visite
    WHERE v.ID_logement = OLD.ID_logement
      AND f.status_paiement <> 'O';

    IF facture_non_paye_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Suppression impossible : il existe des factures non réglées liées à ce logement.';
    END IF;

END$$
DELIMITER ;

-- trigger: make logement aviable after statut
DELIMITER $$
CREATE TRIGGER remise_disponibilite_apres_annulation_visite
AFTER DELETE ON visite
FOR EACH ROW
BEGIN
    DECLARE nb_visites_planifiees INT;

    -- Compte le nombre de visites encore planifiées sur ce logement
    SELECT COUNT(*) INTO nb_visites_planifiees
    FROM visite
    WHERE ID_logement = OLD.ID_logement
      AND status = 'Planifiée'; -- ou selon le champ qui indique visite active

    -- Si aucune visite planifiée, remettre le logement disponible
    IF nb_visites_planifiees = 0 THEN
        UPDATE logement
        SET disponible = 'O'
        WHERE ID_logement = OLD.ID_logement;
    END IF;
END$$

DELIMITER ;
-- trigger: forbid past visit
DELIMITER $$
CREATE TRIGGER prevent_past_visite
BEFORE INSERT ON visite
FOR EACH ROW
BEGIN
    IF NEW.date_visite < CURDATE() THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Impossible de planifier une visite dans le passé.';
    END IF;
END$$
DELIMITER ;

-- View: aviable Logement with their type
 SELECT
   l.adresse, l.ville, l.superficie, l.nb_piece, l.description,
    CASE
        WHEN a.ID_logement IS NOT NULL THEN 'Appartement'
        WHEN k.ID_logement IS NOT NULL THEN 'KOT'
        ELSE 'Inconnu' -- Pour le cas où un logement n'est ni dans APPARTEMENT ni dans KOT 
    END AS type_logement
FROM logement l
LEFT JOIN APPARTEMENT a ON l.ID_logement = a.ID_logement
LEFT JOIN KOT k ON l.ID_logement = k.ID_logement
WHERE l.disponible = 'O';

-- View: Customer-related visits
CREATE VIEW Vue_Visites_Client AS
SELECT 
    c.ID_users, u.nom, u.prenom, v.ID_visite, v.date_visite, v.frais_visite, v.status, l.adresse, l.ville
FROM client c
JOIN utilisateurs u ON u.ID_users = c.ID_users
JOIN realise r ON r.ID_users = c.ID_users
JOIN visite v ON v.ID_visite = r.ID_visite
JOIN logement l ON v.ID_logement = l.ID_logement;

-- View: Monthly revenue
CREATE VIEW Vue_Recettes_Mensuelles AS
SELECT
    DATE_FORMAT(date_paiement, '%Y-%m') AS mois,
    SUM(montant) AS total_recettes
FROM FACTURATION_ET_COMPTABILITE
WHERE status_paiement = 'O'
GROUP BY DATE_FORMAT(date_paiement, '%Y-%m')
ORDER BY mois;
-- View: Logement associated with customers
 CREATE VIEW Logements_par_client AS
SELECT DISTINCT
   c.ID_users, u.nom, u.prenom, u.telephone, l.ID_logement, l.adresse, l.ville, l.superficie, l.nb_piece, l.description, l.disponible
FROM client c 
JOIN utilisateurs u ON c.ID_users = u.ID_users
JOIN realise r ON c.ID_users = r.ID_users
JOIN visite v ON r.ID_visite = v.ID_visite
JOIN logement l ON v.ID_logement = l.ID_logement;

-- VISITE must be referenced in 'FACTURATION_ET_COMPTABILITE.ID_visite' and 'realise.ID_visite'
-- Already enforced by foreign keys, no need for additional trigger

-- Indexes (optional)
CREATE UNIQUE INDEX IDX_agent_immobilier ON agent_immobillier(ID_users);
CREATE UNIQUE INDEX IDX_client ON client(ID_users);
CREATE UNIQUE INDEX IDX_comptable ON comptable(ID_users);
CREATE UNIQUE INDEX IDX_logement_app ON APPARTEMENT(ID_logement);
CREATE UNIQUE INDEX IDX_logement_kot ON KOT(ID_logement);
CREATE UNIQUE INDEX IDX_transaction ON FACTURATION_ET_COMPTABILITE(ID_transaction);
CREATE UNIQUE INDEX IDX_visite ON visite(ID_visite);
CREATE UNIQUE INDEX IDX_users ON utilisateurs(ID_users);

-- ------------------------------------------------privileges-------------------------------------------------------------
-- Création des utilisateurs

CREATE USER 'client_user'@'%' IDENTIFIED BY 'clientpass';
CREATE USER 'comptable_user'@'%' IDENTIFIED BY 'comptablepass';
CREATE USER 'agent_user'@'%' IDENTIFIED BY 'agentpass';

-- Droits pour le client
GRANT SELECT ON immo_data_base.Vue_Visites_Client TO 'client_user'@'%';
GRANT SELECT ON immo_data_base.logement TO 'client_user'@'%';
GRANT INSERT ON immo_data_base.visite TO 'client_user'@'%';
GRANT INSERT ON immo_data_base.realise TO 'client_user'@'%';

-- Droits pour le comptable
GRANT SELECT ON immo_data_base.Vue_Recettes_Mensuelles TO 'comptable_user'@'%';
GRANT SELECT ON immo_data_base.FACTURATION_ET_COMPTABILITE TO 'comptable_user'@'%';

-- Droits pour l'agent immobilier
GRANT SELECT, INSERT, UPDATE ON immo_data_base.logement TO 'agent_user'@'%';
GRANT INSERT ON immo_data_base.visite TO 'agent_user'@'%';
GRANT INSERT ON immo_data_base.realise TO 'agent_user'@'%';

-- --------------------------------------------remplissage des tables-------------------------------------------------------------

-- Comptable
INSERT INTO utilisateurs (nom, prenom, email, telephone, mot_de_passe, COMPTABLE)
VALUES ('Martin', 'Luc', 'luc.martin@mail.com', 324700001, 'pass123', 1);
INSERT INTO comptable (ID_users) VALUES (1);

-- Client
INSERT INTO utilisateurs (nom, prenom, email, telephone, mot_de_passe, CLIENT)
VALUES ('Durand', 'Emma', 'emma.durand@mail.com', 324700002, 'emma2024', 1);
INSERT INTO client (ID_users) VALUES (2);

-- Agent Immobilier
INSERT INTO utilisateurs (nom, prenom, email, telephone, mot_de_passe, AGENT_IMMOBILLIER)
VALUES ('Bernard', 'Paul', 'paul.bernard@mail.com', 324700003, 'paulagent', 1);
INSERT INTO agent_immobillier (ID_users, agence) VALUES (3, 'ImmoPlus');

-- Autre client
INSERT INTO utilisateurs (nom, prenom, email, telephone, mot_de_passe, CLIENT)
VALUES ('Lemoine', 'Sarah', 'sarah.lemoine@mail.com', 324700004, 'sarahpass', 1);
INSERT INTO client (ID_users) VALUES (4);



-- logement
INSERT INTO logement (adresse, ville, superficie, nb_piece, disponible, description, KOT, APPARTEMENT, ID_users)
VALUES ('12 Rue de Paris', 'Bruxelles', 80, 3, '1', 'Appartement lumineux 3 pièces', NULL, 1, 3);

INSERT INTO logement (adresse, ville, superficie, nb_piece, disponible, description, KOT, APPARTEMENT, ID_users)
VALUES ('7 Avenue Louise', 'Bruxelles', 25, 1, '1', 'KOT proche université', 1, NULL, 3);

INSERT INTO logement (adresse, ville, superficie, nb_piece, disponible, description, KOT, APPARTEMENT, ID_users)
VALUES ('144 Rue du rampart', 'Bruxelles', 120, 5, '1', 'Belle vue', NULL, 1, 3);

INSERT INTO logement (adresse, ville, superficie, nb_piece, disponible, description, KOT, APPARTEMENT, ID_users)
VALUES ('Porte de Liege 23', 'Bruxelles', 20, 1, '1', 'Super pour etudiant', 1, NULL, 3);


-- Lier avec les sous-tables
INSERT INTO APPARTEMENT (L_A_ID_logement, ID_logement) VALUES (1, 1);
INSERT INTO KOT (L_K_ID_logement, ID_logement) VALUES (2, 2);



-- Visite planifiée sur appartement
INSERT INTO visite (date_visite, frais_visite, status, ID_logement)
VALUES ('2025-12-02', 50.00, 'Planifiée', 1);

-- Visite planifiée sur KOT
INSERT INTO visite (date_visite, frais_visite, status, ID_logement)
VALUES ('2025-12-14', 30.00, 'Planifiée', 2);



-- Client 2 (Emma) a réalisé la 1ère visite
INSERT INTO realise (ID_visite, date, ID_users) VALUES (1, '2025-12-02' , 2);

-- Client 4 (Sarah) a réalisé la 2e visite
INSERT INTO realise (ID_visite, date, ID_users) VALUES (2, '2025-12-14', 4);



