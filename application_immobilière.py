import mysql.connector
import tkinter as tk
from tkinter import messagebox

global Id
biens_ids = []

#--------------------------------------------------------------------------------------------

#function to connect
def conect() : 
    mail = entry_user.get()
    password = entry_pass.get()
    db = mysql.connector.connect(
    host="localhost",
    user="admin", #changer les valeurs en fonction
     passwd="password", #changer les valeurs en fonction,
    port=3306,
    database="immo_data_base"
    
    )
    mycursor = db.cursor()
    global Id
    
    mycursor.execute(""" SELECT * FROM `immo_data_base`.`utilisateurs` WHERE CLIENT = 1 AND email = %s And mot_de_passe = %s
                    """, (mail, password))
    client_result = mycursor.fetchone() #on a besoin que d'une seul personne qui vérifie ces données -> pas fetchall
    if client_result : 
        page_login.pack_forget() #hide the login page
        page_research.pack() #print and use the research page insted of the login page
        Id = get_ID_Users(mail, password)
        return "CLIENT"
    
    mycursor.execute(""" SELECT * FROM `immo_data_base`.`utilisateurs` WHERE COMPTABLE = 1 AND email = %s And mot_de_passe = %s
                    """, (mail, password))
    comptable_result = mycursor.fetchone()
    if comptable_result : 
        page_login.pack_forget() #hide the login page
        page_comptable.pack() #print and use the comptable page insted of the login page
        remplir_page_comptable()
        Id = get_ID_Users(mail, password)
        return "COMPTABLE"
    
    mycursor.execute(""" SELECT * FROM `immo_data_base`.`utilisateurs` WHERE AGENT_IMMOBILLIER = 1 AND email = %s And mot_de_passe = %s
                    """, (mail, password))
    immo_result = mycursor.fetchone()
    if immo_result : 
        page_login.pack_forget() #hide the login page
        page_agent.pack() #print and use the research page insted of the login page
        remplir_page_agent()
        Id = get_ID_Users(mail, password)
        return "AGENT_IMMOBILLIER"
    
    messagebox.showerror("Invalid username and/or password !")
    

# function to get the id of a user when he connect
def get_ID_Users(mail, password) : 
    
    db = mysql.connector.connect(
    host="localhost",
    user="admin", #changer les valeurs en fonction
     passwd="password", #changer les valeurs en fonction
    database="immo_data_base"
    
    )
    mycursor = db.cursor()
    
    mycursor.execute(""" SELECT ID_users FROM `immo_data_base`.`utilisateurs` WHERE email = %s And mot_de_passe = %s
                    """, (mail, password))
    result = mycursor.fetchone()[0] #on a besoin que d'une seul personne qui vérifie ces données -> pas fetchall
    return result


# function to add a new user in the database and land on the search page
def register() : 
    email = mail_user.get()
    mot_de_passe = pass_user.get()
    prénom = name1_user.get()
    nom = name2_user.get()
    telephone = phone_user.get()
    statut = chosen_statut.get()
    Statut = {"COMPTABLE" : None,
            "CLIENT" : None,
            "AGENT_IMMOBILLIER" : None
            }
    Statut[statut] = 1
    
    db = mysql.connector.connect(
    host="localhost",
    user="admin", #changer les valeurs en fonction
     passwd="password", #changer les valeurs en fonction
    database="immo_data_base"
    )
    mycursor = db.cursor()
    global Id
    
    try : 
        mycursor.execute(""" 
                        INSERT INTO `immo_data_base`.`utilisateurs` (`nom`, `prenom`, `email`, `telephone`, `mot_de_passe`, `COMPTABLE`, `CLIENT`, `AGENT_IMMOBILLIER`) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """,(nom, prénom, email, telephone, mot_de_passe, Statut["COMPTABLE"], Statut["CLIENT"], Statut["AGENT_IMMOBILLIER"]))
        db.commit()
        Id = get_ID_Users(email, mot_de_passe)
        page_signUp.pack_forget() #hide the login page
        
        if Statut["CLIENT"] ==1 : #if it's a client, land on the search page
            mycursor.execute("INSERT INTO client (ID_users) VALUES (%s)", (Id,))
            db.commit()
            page_research.pack() 
        
        elif Statut["COMPTABLE"] == 1 : 
            #email suffit car il est Unique
            mycursor.execute(""" SELECT ID_users FROM `immo_data_base`.`utilisateurs` WHERE email = %s 
                    """, (email,))
            ID_users = mycursor.fetchone()
            if ID_users:  # Vérifier si un résultat est trouvé
                mycursor.execute(""" 
                    INSERT INTO `immo_data_base`.`comptable` (`ID_users`)  
                    VALUES (%s)
                    """, (ID_users[0],))  # Extraire l'ID réel #ID_comptable est Auto-increment donc pas besoin de l'ajouter
                db.commit()

            page_comptable.pack() 
            remplir_page_comptable()
        
        elif Statut["AGENT_IMMOBILLIER"] == 1 : 
            mycursor.execute(""" SELECT ID_users FROM `immo_data_base`.`utilisateurs` WHERE email = %s 
                    """, (email,))
            ID_users = mycursor.fetchone()
            agence = "ImmoAgency" #par facilité, on suppose que tout les agent appartienne à la même agence
            if ID_users:  # Vérifier si un résultat est trouvé
                mycursor.execute(""" 
                    INSERT INTO `immo_data_base`.`agent_immobillier` (`ID_users`, `agence`)  
                    VALUES (%s, %s)
                    """, (ID_users[0], agence,))  # Extraire l'ID réel 
                db.commit()
            
            page_agent.pack()
            remplir_page_agent
            
        
        Id = get_ID_Users(email, mot_de_passe)
        return "user added succesfully"
    
    except mysql.connector.IntegrityError as e :
        if e.errno == 1062:
            messagebox.showerror("this email is already used !")


#function to search for a certain type of real estate proprety based on city, number of room, etc
def research() : 
    ville = entry_ville.get()
    nb_pieces = entry_pieces.get()
    superficie_min = entry_surface.get()

    db = mysql.connector.connect(
    host="localhost",
    user="admin", #changer les valeurs en fonction
     passwd="password", #changer les valeurs en fonction
    database="immo_data_base"
    )
    mycursor = db.cursor()

    # Construction dynamique de la requête avec filtres facultatifs
    query = "SELECT adresse, ville, nb_piece, superficie, description FROM logement WHERE disponible = 1"
    params = []

    if ville:
        query += " AND ville = %s"
        params.append(ville)

    if nb_pieces:
        query += " AND nb_piece >= %s"
        params.append(nb_pieces)

    if superficie_min:
        query += " AND superficie >= %s"
        params.append(superficie_min)

    mycursor.execute(query, params)
    resultats = mycursor.fetchall()

    listbox.delete(0, tk.END)
    for ligne in resultats:
        adresse, ville, pieces, surface, description = ligne
        listbox.insert(tk.END, f"-{adresse} ({ville}) | {pieces} pièces | {surface} m² -> {description}")

    mycursor.close()
    db.close()
    
#function to search for a certain type of real estate proprety based on city, number of room, etc
def check_visites() : 
    date = visite_date.get()

    db = mysql.connector.connect(
    host="localhost",
    user="admin", 
     passwd="password", 
    database="immo_data_base"
    )
    mycursor = db.cursor()

    try : 
        # Construction dynamique de la requête avec filtres facultatifs
        query = "SELECT * FROM visite "
        params = []

        if date:
            query += " WHERE date_visite = %s"
            params.append(date)


        mycursor.execute(query, params)
        resultats = mycursor.fetchall()

        listbox3.delete(0, tk.END)
        for ligne in resultats:
            Id_visite, date_visite, frais_visite, status, Id_logement = ligne
            listbox3.insert(tk.END, f"-visite n°{Id_visite} le ({date_visite}) pour le bien n°{Id_logement} |frais : {frais_visite} € |statut : {status}")

        mycursor.close()
        db.close()
        
    except mysql.connector.Error as err:
        messagebox.showerror("Erreur", f"Erreur MySQL : {err}")

#function that add real estate proprety to the database and print the new stock of proprety
def ajouter_bien():

    db = mysql.connector.connect(
    host="localhost",
    user="admin", #changer les valeurs en fonction
     passwd="password", #changer les valeurs en fonction
    database="immo_data_base"
    )
    mycursor = db.cursor()
    type_choisie = chosen_type.get()
    Type = {"KOT" : None,
              "APPARTEMENT" : None
              }
    Type[type_choisie] = 1
    
    adresse  = add_adress.get()
    ville = add_ville.get()
    nb_piece = add_pieces.get() 
    superficie = add_surface.get() 
    description = add_descr.get()
    Id_users = Id
    try : 
        mycursor.execute(""" INSERT INTO logement (`adresse`, `ville`, `superficie`, `nb_piece`, `disponible`, `description`, `KOT`, `APPARTEMENT`, `ID_users`) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """,(adresse, ville, superficie, nb_piece, 1, description, Type["KOT"], Type["APPARTEMENT"], Id_users))
        print("Données à insérer :")
        print(adresse, ville, superficie, nb_piece, 1, description, Type["KOT"], Type["APPARTEMENT"], Id_users)
        print("Types :", [type(x) for x in (adresse, ville, superficie, nb_piece, 1, description, Type["KOT"], Type["APPARTEMENT"], Id_users)])

        db.commit()
        add_logement.pack_forget() #hide the page
        page_agent.pack() 
        remplir_page_agent()
    except mysql.connector.Error as err:
        print(f"Erreur SQL : {err}")
    finally : 
        mycursor.close()
        db.close()

# function that modify a real estate proprety
def modifier_bien():
    try:
        # get the selection in the list
        selected_index = text_biens.curselection()
        if not selected_index:
            messagebox.showwarning("Aucun bien", "Veuillez sélectionner un bien à modifier.")
            return

        index = selected_index[0]
        id_logement = biens_ids[index]  # get the id of the proprety
        
        db = mysql.connector.connect(
            host="localhost",
            user="admin",
             passwd="password",
            database="immo_data_base"
        )
        cursor = db.cursor()
        cursor.execute("""
            SELECT adresse, ville, nb_piece, superficie, description, KOT, APPARTEMENT 
            FROM logement WHERE ID_logement = %s
        """, (id_logement,))
        result = cursor.fetchone()
        cursor.close()
        db.close()

        if not result:
            messagebox.showerror("Erreur", "Ce bien n'existe pas.")
            return

        # create a new window
        modif_win = tk.Toplevel()
        modif_win.title("Modifier le bien")

        # Champs pré-remplis
        tk.Label(modif_win, text="Adresse :").grid(row=0, column=0)
        mod_adresse = tk.Entry(modif_win)
        mod_adresse.insert(0, result[0])
        mod_adresse.grid(row=0, column=1)

        tk.Label(modif_win, text="Ville :").grid(row=1, column=0)
        mod_ville = tk.Entry(modif_win)
        mod_ville.insert(0, result[1])
        mod_ville.grid(row=1, column=1)

        tk.Label(modif_win, text="Pièces :").grid(row=2, column=0)
        mod_pieces = tk.Entry(modif_win)
        mod_pieces.insert(0, result[2])
        mod_pieces.grid(row=2, column=1)

        tk.Label(modif_win, text="Surface :").grid(row=3, column=0)
        mod_surface = tk.Entry(modif_win)
        mod_surface.insert(0, result[3])
        mod_surface.grid(row=3, column=1)

        tk.Label(modif_win, text="Description :").grid(row=4, column=0)
        mod_descr = tk.Entry(modif_win)
        mod_descr.insert(0, result[4])
        mod_descr.grid(row=4, column=1)

        chosen_type_mod = tk.StringVar(value="KOT" if result[5] else "APPARTEMENT")
        tk.Label(modif_win, text="Type :").grid(row=5, column=0)
        tk.OptionMenu(modif_win, chosen_type_mod, "KOT", "APPARTEMENT").grid(row=5, column=1)

        # nested function
        def valider_modif():
            try:
                db = mysql.connector.connect(
                    host="localhost",
                    user="admin",
                     passwd="password",
                    database="immo_data_base"
                )
                cursor = db.cursor()
                cursor.execute("""
                    UPDATE logement
                    SET adresse = %s, ville = %s, nb_piece = %s, superficie = %s,
                        description = %s, KOT = %s, APPARTEMENT = %s
                    WHERE ID_logement = %s
                """, (
                    mod_adresse.get(),
                    mod_ville.get(),
                    int(mod_pieces.get()),
                    float(mod_surface.get()),
                    mod_descr.get(),
                    1 if chosen_type_mod.get() == "KOT" else None,
                    1 if chosen_type_mod.get() == "APPARTEMENT" else None,
                    id_logement
                ))
                db.commit()
                cursor.close()
                db.close()
                modif_win.destroy()
                remplir_page_agent()
                messagebox.showinfo("Succès", "Bien modifié avec succès.")
            except Exception as e:
                messagebox.showerror("Erreur", str(e))

        tk.Button(modif_win, text="Valider les modifications", command=valider_modif).grid(row=6, column=0, columnspan=2, pady=10)

    except Exception as e:
        messagebox.showerror("Erreur", str(e))


# function to delete a real estate proprety
def supprimer_bien():
    selected_index = text_biens.curselection()
    
    if not selected_index:
        messagebox.showwarning("Aucun bien sélectionné", "Veuillez sélectionner un bien à supprimer.")
        return

    index = selected_index[0]
    id_logement = biens_ids[index]

    confirm = messagebox.askyesno("Confirmation", f"Supprimer le bien ID {id_logement} ?")
    if not confirm:
        return

    try:
        db = mysql.connector.connect(
            host="localhost",
            user="admin",
             passwd="password",
            database="immo_data_base"
        )
        cursor = db.cursor()

        # Supprimer d'abord les dépendances (si des VISITES sont liées à ce logement, par exemple)
        cursor.execute("DELETE FROM visite WHERE ID_logement = %s", (id_logement,))

        # Puis supprimer le logement
        cursor.execute("DELETE FROM logement WHERE ID_logement = %s", (id_logement,))
        db.commit()

        cursor.close()
        db.close()

        messagebox.showinfo("Succès", f"Le bien ID {id_logement} a été supprimé.")
        remplir_page_agent()

    except mysql.connector.Error as err:
        messagebox.showerror("Erreur SQL", f"Impossible de supprimer le bien : {err}")
        
# function that compute the fees of a visite based on the proprety's propretiess
def calculer_frais(id_logement):
    
    try:
        db = mysql.connector.connect(
            host="localhost",
            user="admin",
             passwd="password",
            database="immo_data_base"
        )
        
        cursor = db.cursor()
        cursor.execute("""
            SELECT superficie, nb_piece, KOT, APPARTEMENT
            FROM logement WHERE ID_logement = %s
        """, (id_logement,))
        result = cursor.fetchone()
        cursor.close()
        db.close()

        if not result:
            return 0

        superficie, nb_piece, is_kot, is_appart = result
        frais = 20  # base

        # Exemple of fees (we can adjust it if we want)
        if is_kot:
            frais += 5
        elif is_appart:
            frais += 10

        if superficie > 100:
            frais += 10
        if nb_piece >= 4:
            frais += 5

        return frais

    except Exception as e:
        print(f"Erreur lors du calcul des frais : {e}")
        return 0


# function to create a visite when a client want to visit a proprety
def create_visite():
    selected_index = listbox.curselection()
    if not selected_index:
        messagebox.showwarning("Aucun bien", "Veuillez sélectionner un bien.")
        return

    # get the text of the selected line
    selected_line = listbox.get(selected_index[0])
    print("Ligne sélectionnée :", selected_line)

    try:
        # take the adress and the city from the text
        partie_adresse = selected_line.split("|")[0].strip() 
        adresse = partie_adresse.split("(")[0].strip("- ").strip()
        ville = partie_adresse.split("(")[1].replace(")", "").strip()

        # find the ID of the proprety based on those two informationss
        db = mysql.connector.connect(
            host="localhost",
            user="admin",
             passwd="password",
            database="immo_data_base"
        )
        cursor = db.cursor()
        cursor.execute("""
            SELECT ID_logement FROM logement 
            WHERE adresse = %s AND ville = %s LIMIT 1
        """, (adresse, ville))
        result = cursor.fetchone()
        cursor.close()
        db.close()

        if not result:
            messagebox.showerror("Erreur", "Logement non trouvé.")
            return

        id_logement = result[0]
        print("ID_logement trouvé :", id_logement)

    except Exception as e:
        messagebox.showerror("Erreur", f"Impossible d’extraire les données du logement : {e}")
        return

    # Créer la fenêtre pour entrer la date
    set_date_win = tk.Toplevel()
    set_date_win.title("Planifier une visite")

    tk.Label(set_date_win, text="Date de la visite (AAAA-MM-JJ) :").grid(row=0, column=0)
    set_date = tk.Entry(set_date_win)
    set_date.grid(row=0, column=1)

    def get_date():
        date_visite = set_date.get()
        statut = "planifiée"
        frais = calculer_frais(id_logement)

        try:
            db = mysql.connector.connect(
                host="localhost",
                user="admin",
                 passwd="password",
                database="immo_data_base"
            )
            cursor = db.cursor()

            cursor.execute("""
                INSERT INTO visite (date_visite, frais_visite, status, ID_logement)
                VALUES (%s, %s, %s, %s)
            """, (date_visite, frais, statut, id_logement))
            
            # get the ID for later
            cursor.execute("SELECT LAST_INSERT_ID()")
            id_visite = cursor.fetchone()[0]
            
            cursor.execute("""
                INSERT INTO realise (ID_visite, date, ID_users)
                VALUES (%s, %s, %s)
            """, (id_visite, date_visite, Id))



            db.commit()
            cursor.close()
            db.close()

            messagebox.showinfo("Succès", f"Visite enregistrée avec succès avec {frais} € de frais.")
            set_date_win.destroy()

        except Exception as e:
            messagebox.showerror("Erreur", str(e))

    tk.Button(set_date_win, text="Valider la visite", command=get_date).grid(row=1, column=0, columnspan=2, pady=10)


# function to print the facturation table for the Comptable
def remplir_page_comptable():
    comptable_info.delete("1.0", tk.END)
    
    db = mysql.connector.connect(
    host="localhost",
    user="admin", #changer les valeurs en fonction
     passwd="password", #changer les valeurs en fonction
    database="immo_data_base"
    )
    mycursor = db.cursor()
    
    mycursor.execute(""" SELECT montant, date_paiement, status_paiement, ID_visite  FROM FACTURATION_ET_COMPTABILITE 
                     """)
    resultats = mycursor.fetchall()
    for lines in resultats : 
        montant, date_paiement, status_paiement, ID_visite = lines
        comptable_info.insert(tk.END, f"visite n° {ID_visite} |-montant : {montant} | à payer pour ({date_paiement}) | statut paiement : {status_paiement}")
     
    mycursor.close()
    db.close()

#function to print the page for the Agent_immobilier
def remplir_page_agent():
    global biens_ids

    text_biens.delete(0, tk.END)
    db = mysql.connector.connect(
    host="localhost",
    user="admin", #changer les valeurs en fonction
     passwd="password", #changer les valeurs en fonction
    database="immo_data_base"
    )
    cursor = db.cursor()
    cursor.execute("""
            SELECT ID_logement, adresse, ville, nb_piece, superficie, description, KOT, APPARTEMENT, ID_users 
            FROM logement
        """)

    global biens_ids
    biens_ids  = []

    for bien in cursor.fetchall():
        id_logement, adresse, ville, nb_piece, superficie, description, is_kot, is_appart, id_agent = bien
        type_bien = "KOT" if is_kot else ("APPARTEMENT" if is_appart else "Inconnu")
        ligne = (
            f"ID: {id_logement} | {type_bien}. "
            f"Adresse: {adresse}, Ville: {ville}. "
            f"Pièces: {nb_piece}, Surface: {superficie} m². "
            f"Description: {description}. "
            f"Ajouté par agent ID: {id_agent}  "
        )
        text_biens.insert(tk.END, ligne)
        biens_ids.append(id_logement)

    cursor.close()
    db.close()


#function to land on the sign up page
def signUp() : 
    global page_signUp
    page_login.pack_forget() #hide the login page
    page_signUp.pack()

#function to go back to the login page
def retour_login(page_a_cacher):
    page_a_cacher.pack_forget()
    page_login.pack()
    
# function to print the add proprety page
def print_add_page() : 
    page_agent.pack_forget()
    add_logement.pack()
    
#function to print the page where we can access the visites
def print_check_visite() : 
    page_agent.pack_forget()
    page_visite.pack()
    
    
    
# function to print the monthly and anual report
def afficher_rapport_annuel():
    annee = entry_annee.get()
    if not annee.isdigit():
        messagebox.showerror("Erreur", "Veuillez entrer une année valide (ex : 2023).")
        return

    annee = int(annee)
    db = mysql.connector.connect(
        host="localhost",
        user="admin",
         passwd="password",
        database="immo_data_base"
    )
    cursor = db.cursor()

    try:
        # Total annuel
        cursor.execute("""
            SELECT SUM(montant) 
            FROM FACTURATION_ET_COMPTABILITE 
            WHERE YEAR(date_paiement) = %s AND status_paiement = 1
        """, (annee,))
        total_annuel = cursor.fetchone()[0] or 0

        # Totaux mensuels
        cursor.execute("""
            SELECT MONTH(date_paiement), SUM(montant)
            FROM FACTURATION_ET_COMPTABILITE
            WHERE YEAR(date_paiement) = %s AND status_paiement = 1
            GROUP BY MONTH(date_paiement)
            ORDER BY MONTH(date_paiement)
        """, (annee,))
        mois_resultats = cursor.fetchall()

        # Affichage
        rapport_resultat.delete("1.0", tk.END)
        rapport_resultat.insert(tk.END, f" Rapport de l'année {annee}\n")
        rapport_resultat.insert(tk.END, f"$ Chiffre d'affaires total : {total_annuel} €\n\n")

        mois_noms = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
                     "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]

        for mois, total in mois_resultats:
            rapport_resultat.insert(tk.END, f"{mois_noms[mois - 1]} : {total} €\n")

    except Exception as e:
        messagebox.showerror("Erreur", f"Une erreur est survenue : {e}")
    finally:
        cursor.close()
        db.close()

#function to print the profil page
def afficher_profil():
    global Id  # ID de l'utilisateur connecté
    db = mysql.connector.connect(host="localhost", user="admin",  passwd="password", database="immo_data_base")
    cursor = db.cursor()
    cursor.execute("""
        SELECT nom, prenom, email, telephone FROM utilisateurs WHERE ID_users = %s
    """, (Id,))
    user = cursor.fetchone()
    cursor.close()
    db.close()

    if user:
        entry_nom.delete(0, tk.END)
        entry_nom.insert(0, user[0])

        entry_prenom.delete(0, tk.END)
        entry_prenom.insert(0, user[1])

        entry_email.delete(0, tk.END)
        entry_email.insert(0, user[2])

        entry_telephone.delete(0, tk.END)
        entry_telephone.insert(0, user[3])

        # Affiche la page
        page_agent.pack_forget()
        page_research.pack_forget()
        page_comptable.pack_forget()
        page_profil.pack()

# function to modify th user's information
def update_profil():
    nom = entry_nom.get()
    prenom = entry_prenom.get()
    email = entry_email.get()
    telephone = entry_telephone.get()

    db = mysql.connector.connect(host="localhost", user="admin",  passwd="password", database="immo_data_base")
    cursor = db.cursor()
    try:
        cursor.execute("""
            UPDATE utilisateurs
            SET nom = %s, prenom = %s, email = %s, telephone = %s
            WHERE ID_users = %s
        """, (nom, prenom, email, telephone, Id))
        db.commit()
        messagebox.showinfo("Succès", "Profil mis à jour avec succès.")
    except mysql.connector.Error as err:
        messagebox.showerror("Erreur", f"Erreur MySQL : {err}")
    finally:
        cursor.close()
        db.close()


# function to delete a user
def delete_user():
    confirmation = messagebox.askquestion(
        "Confirmation", 
        "Êtes-vous sûr(e) de vouloir supprimer votre compte ? Vos données personnelles seront anonymisées."
    )
    
    if confirmation == 'yes':
        try:
            db = mysql.connector.connect(
                host="localhost",
                user="admin",
                 passwd="password",
                database="immo_data_base"
            )
            mycursor = db.cursor()

            # Anonymiser les données personnelles
            mycursor.execute("""
                UPDATE utilisateurs
                SET nom = '0',
                    prenom = '0',
                    email = CONCAT('supprimé_', ID_users, '@gmail.com'),
                    telephone = '0',
                    mot_de_passe = '',
                    CLIENT = NULL,
                    COMPTABLE = NULL,
                    AGENT_IMMOBILLIER = NULL
                WHERE ID_users = %s
            """, (Id,))

            db.commit()
            messagebox.showinfo("Succès", "Vos données ont été anonymisées.")

            # go back to the login page
            page_profil.pack_forget()
            page_login.pack()

        except mysql.connector.Error as err:
            messagebox.showerror("Erreur MySQL", f"Une erreur est survenue :\n{err}")
        finally:
            mycursor.close()
            db.close()



#--------------------------------------------------------------------------------
#fenêtre principale
root = tk.Tk()
root.geometry("600x600")
root.title("Application Immobilière")
root.resizable(True, True)

# login page --------------------------------------------------------------------------------------
page_login = tk.Frame(root)
page_login.pack()
tk.Label(page_login, text="Veuillez vous connecter ").pack(pady=10)


tk.Label(page_login, text="mail : ").pack(pady=5)
entry_user = tk.Entry(page_login)
entry_user.pack(pady=5)

tk.Label(page_login, text="password : ").pack(pady=5)
entry_pass = tk.Entry(page_login, show="*")
entry_pass.pack(pady=5)

btn_connecter = tk.Button(page_login, text="login", command=conect)
btn_connecter.pack(pady=10)

tk.Label(page_login, text="première visite ? Inscrivez vous ! ").pack(pady=5)
btn_signUp = tk.Button(page_login, text="sign up", command=signUp)
btn_signUp.pack(pady=10)

#sign-up page -------------------------------------------------------------------------
page_signUp = tk.Frame(root) #crée la page login
tk.Label(page_signUp, text="Bienvenue! veuiller vous enregistrez ").pack(pady=5)

tk.Label(page_signUp, text="first name : ").pack(pady=5)
name1_user = tk.Entry(page_signUp)
name1_user.pack(pady=3)

tk.Label(page_signUp, text="Last name : ").pack(pady=5)
name2_user = tk.Entry(page_signUp)
name2_user.pack(pady=3)

tk.Label(page_signUp, text="phone number : ").pack(pady=5)
phone_user = tk.Entry(page_signUp)
phone_user.pack(pady=3)

tk.Label(page_signUp, text="mail : ").pack(pady=5)
mail_user = tk.Entry(page_signUp)
mail_user.pack(pady=3)

tk.Label(page_signUp, text="password : ").pack(pady=5)
pass_user = tk.Entry(page_signUp)
pass_user.pack(pady=3)

# Create the menu button 
chosen_statut = tk.StringVar() 
statuts = ('CLIENT', 'COMPTABLE', 'AGENT_IMMOBILLIER') 
# Create the Menubutton 
def on_hover(event):
    event.widget.config(bg='blue')  # Change la couleur d'arrière-plan

def on_leave(event):
    event.widget.config(bg='lightblue')  
    
menu_button = tk.Menubutton(page_signUp, text='Select your statut', bg='lightblue', fg='black') 
menu_button.bind("<Enter>", on_hover) 
menu_button.bind("<Leave>", on_leave)  
# Create a new menu instance 
menu = tk.Menu(menu_button, tearoff=0) 
for statut in statuts: 
    menu.add_radiobutton( label=statut, value=statut, variable=chosen_statut ) 
    menu_button["menu"] = menu 
    menu_button.pack(expand=True, pady=10)

btn_signUp = tk.Button(page_signUp, text="register", command=register)
btn_signUp.pack(pady=10)

#research page --------------------------------------------------------------------------
page_research = tk.Frame(root)

# Widgets de recherche
tk.Label(page_research, text="Ville :").grid(row=0, column=0)
entry_ville = tk.Entry(page_research)
entry_ville.grid(row=0, column=1)

tk.Label(page_research, text="Min. pièces :").grid(row=2, column=0)
entry_pieces = tk.Entry(page_research)
entry_pieces.grid(row=2, column=1)

tk.Label(page_research, text="Min. surface (m²) :").grid(row=3, column=0)
entry_surface = tk.Entry(page_research)
entry_surface.grid(row=3, column=1)

tk.Button(page_research, text="Rechercher", command=research).grid(row=4, column=0, columnspan=2)
listbox = tk.Listbox(page_research, width=80)
listbox.grid(row=5, column=0, columnspan=2)

# Scrollbar horizontale
xscroll = tk.Scrollbar(page_research, orient=tk.HORIZONTAL)
xscroll.grid(row=6, column=0, sticky="ew")
xscroll.config(command=listbox.xview)

tk.Label(page_research, text="Créer une visite").grid(row=7, column=0, columnspan=2)
tk.Button(page_research, text="visiter", command=create_visite).grid(row=8, column=0, columnspan=2)

tk.Button(page_research, text="Mon Profil", command=afficher_profil).grid(row=13)

#comptable page -------------------------------------------------------------------------------
page_comptable = tk.Frame(root)

tk.Label(page_comptable, text="Bienvenue, Comptable").pack(pady=10)

# Exemple de tableau ou zone de texte
comptable_info = tk.Text(page_comptable, height=20, width=80)
comptable_info.pack(pady=10)

tk.Label(page_comptable, text="Année du rapport :").pack()
entry_annee = tk.Entry(page_comptable)
entry_annee.pack()

tk.Button(page_comptable, text="Afficher le rapport annuel", command=afficher_rapport_annuel).pack(pady=10)

# Zone de résultat (en-dessous de ton Text actuel ou dans un nouveau)
rapport_resultat = tk.Text(page_comptable, width=60, height=15)
rapport_resultat.pack()

# Bouton de retour ou de déconnexion
tk.Button(page_comptable, text="Déconnexion", command =lambda: retour_login(page_comptable)).pack(pady=10)

tk.Button(page_comptable, text="Mon Profil", command=afficher_profil).pack(pady=5)

#agent immobilier page ----------------------------------------------------------------

page_agent = tk.Frame(root)

tk.Label(page_agent, text="Espace Agent Immobilier", font=("Arial", 16)).pack(pady=10)

# Scrollbar horizontale
xscroll = tk.Scrollbar(page_agent, orient=tk.HORIZONTAL)
xscroll.pack(side=tk.BOTTOM, fill=tk.X)

# Zone de texte pour afficher les biens
text_biens = tk.Listbox(page_agent, width=80, height=20, xscrollcommand=xscroll.set)
text_biens.pack()

# Lien entre scrollbar et listbox
xscroll.config(command=text_biens.xview)

# Boutons pour gérer les biens
frame_actions = tk.Frame(page_agent)
frame_actions.pack(pady=10)

tk.Button(frame_actions, text="Ajouter un bien", command=print_add_page).pack(side=tk.LEFT, padx=5)
tk.Button(frame_actions, text="Modifier un bien", command=modifier_bien).pack(side=tk.LEFT, padx=5)
tk.Button(frame_actions, text="Supprimer un bien", command=supprimer_bien).pack(side=tk.LEFT, padx=5)

tk.Button(frame_actions, text="visites prévues", command=print_check_visite).pack(side=tk.LEFT, pady=5)

# Bouton de déconnexion
tk.Button(page_agent, text="Déconnexion", command=lambda: retour_login(page_agent)).pack(pady=10)

tk.Button(page_agent, text="Mon Profil", command=afficher_profil).pack(pady=5)

#--------------------------agent immobilier add logement ----------------------------------
add_logement = tk.Frame(root)
tk.Label(add_logement, text="Ajout d'un bien immobilier", font=("Arial", 16)).grid(row=0, column=0, columnspan=2, pady=10)

tk.Label(add_logement, text="Ville :").grid(row=1, column=0)
add_ville = tk.Entry(add_logement)
add_ville.grid(row=1, column=1)

tk.Label(add_logement, text="Adresse :").grid(row=2, column=0)
add_adress = tk.Entry(add_logement)
add_adress.grid(row=2, column=1)

tk.Label(add_logement, text="nbr. pièces :").grid(row=3, column=0)
add_pieces = tk.Entry(add_logement)
add_pieces.grid(row=3, column=1)

tk.Label(add_logement, text="surface (m²) :").grid(row=4, column=0)
add_surface = tk.Entry(add_logement)
add_surface.grid(row=4, column=1)

tk.Label(add_logement, text="description :").grid(row=5, column=0)
add_descr = tk.Entry(add_logement)
add_descr.grid(row=5, column=1)

# Menu pour le type
chosen_type = tk.StringVar()
statuts2 = ('KOT', 'APPARTEMENT')

menu_button2 = tk.Menubutton(add_logement, text='Type de bien', relief="raised")
menu2 = tk.Menu(menu_button2, tearoff=0)
menu_button2["menu"] = menu2
for statut in statuts2:
    menu2.add_radiobutton(label=statut, variable=chosen_type, value=statut)
menu_button2.grid(row=6, column=0, columnspan=2, pady=10)

# Bouton Ajouter
tk.Button(add_logement, text="Ajouter", command=ajouter_bien).grid(row=7, column=0, columnspan=2, pady=10)

#-------------------------------------Agent immo check visite---------------------------------------
page_visite = tk.Frame(root)

# Widgets de recherche
tk.Label(page_visite, text="date :").grid(row=0, column=0)
visite_date = tk.Entry(page_visite)
visite_date.grid(row=0, column=1)

tk.Button(page_visite, text="Rechercher", command=check_visites).grid(row=2, column=0, columnspan=2)
listbox3 = tk.Listbox(page_visite, width=80)
listbox3.grid(row=1, column=0, columnspan=2)

# Scrollbar horizontale
xscroll = tk.Scrollbar(page_visite, orient=tk.HORIZONTAL)
xscroll.grid(row=3, column=0, sticky="ew")
xscroll.config(command=listbox.xview)

# user profil page-------------------------------------------------------------------------
page_profil = tk.Frame(root)

tk.Label(page_profil, text="Mon Profil", font=("Arial", 16)).grid(row=0, column=0, columnspan=2, pady=10)

tk.Label(page_profil, text="Nom :").grid(row=1, column=0, sticky='e')
entry_nom = tk.Entry(page_profil)
entry_nom.grid(row=1, column=1)

tk.Label(page_profil, text="Prénom :").grid(row=2, column=0, sticky='e')
entry_prenom = tk.Entry(page_profil)
entry_prenom.grid(row=2, column=1)

tk.Label(page_profil, text="Email :").grid(row=3, column=0, sticky='e')
entry_email = tk.Entry(page_profil)
entry_email.grid(row=3, column=1)

tk.Label(page_profil, text="Téléphone :").grid(row=4, column=0, sticky='e')
entry_telephone = tk.Entry(page_profil)
entry_telephone.grid(row=4, column=1)

tk.Button(page_profil, text="Mettre à jour", command=update_profil).grid(row=5, column=0, columnspan=2, pady=10)

tk.Button(page_profil, text="supprimer mon compte", command=delete_user).grid(row=6, column=0, columnspan=2, pady=10)

#boucle principale
root.mainloop()