import pandas as pd
from datetime import datetime, date
from datetime import timedelta
import matplotlib.pyplot as plt
from scipy.stats import linregress
import pymongo
from pymongo import MongoClient
import certifi
import configparser
import json
import numpy as np
import streamlit as st
from PIL import Image
from io import StringIO
#import termios
import webbrowser

CONN_ID='dev_postgres'

def main():
    #def get_data():
        #upload_file = st.sidebar.file_uploader('Upload a file containing CEC data')
        #if upload_file is None:
            #st.header(":red[CEC : Capacité d'Echange Cathionique#]")
        #else:
            #CEC_ = pd.read_excel(upload_file)
            #CEC_Courbe_ = pd.read_excel(upload_file, sheet_name=1)
            #return (CEC_, CEC_Courbe_)
    def get_data():
        upload_file = st.sidebar.file_uploader('Upload a file containing CEC data')
        if upload_file is None:
            st.header(":red[CEC : Capacité d'Echange Cathionique]")
        return (upload_file)



    #CEC, CEC_Courbe = get_data()
    file=get_data()
    if file is None:
        st.header("Dosage Colorimétrique des ions NH4 extraits par Chlorure de Sodium")
    else:
        CEC = pd.read_excel(file)
        CEC_Courbe= pd.read_excel(file, sheet_name=1)

        def trace_courbe():
            x = CEC_Courbe['C méq/ml']
            y = CEC_Courbe['ABS']
            fig, ax = plt.subplots()
            ax.plot(x, y, color='b')
            plt.xlabel("Concentration")
            plt.ylabel('ABS')
            plt.show()
            slope, intercept, r_value, p_value, std_err = linregress(x, y)
            return slope
        def Calcul_C_CEC():
        #CEC, CEC_Courbe = get_data()
            a = trace_courbe()
            CEC1 = CEC.assign(C=None)
            CEC1 = CEC1.assign(CEC=None)
            CEC1['C'] = CEC1['A410'] / a
            CEC1['CEC'] = (CEC1['C'] * 250 * 100) / CEC['Poids']
        # CEC = CEC.to_json()
            return (CEC1)

        #################################### Référentiel :46B ##############################################""

        def Extract_46B():
            CEC = Calcul_C_CEC()
            # CEC = pd.read_json(CEC)
            CEC_listed = CEC.values.tolist()
            ##### Fonction permet d'avoir une liste du référentiel 46B avec tt les informations qui lui correspondent
            data_46B = []
            Echantillon = []
            for i in (CEC_listed):
                Echantillon.append(i[1])
            for k in Echantillon:
                if k[0:3] == '46B':
                    data_46B.append(k)
            # print(data_46B)
            ##### Fonction permet d'avoir une liste du référentiel 46B avec tt les informations qui lui correspondent
            data_46B_I = []
            for i in range(len(data_46B)):
                for k in range(len(CEC_listed)):
                    if CEC_listed[k][1] == data_46B[i]:
                        data_46B_I.append(CEC_listed[k][0])
                        data_46B_I.append(data_46B[i])
                        for l in [2, 3, 4, 5, 6]:
                            data_46B_I.append(CEC_listed[k][l])

            # print(data_46B_I)
            ##### Définir une fonction permettant la convertion de la liste plate à une liste imbriquée dont chaque liste représente une ligne pour notre DataFrame
            step, size = 7, 7
            JDD_46B = []
            for i in range(0, len(data_46B_I), step):
                # slicing list
                JDD_46B.append(data_46B_I[i: i + size])
            # print(JDD_46B)

            ##### Convertir List to DataFrame
            JDD_46B = pd.DataFrame(JDD_46B, columns=['Date', 'Echantillon', 'ABS', 'Concentration', 'poids', 'C', 'CEC'])
            # JDD_46B = JDD_46B.to_json()
            return JDD_46B

        def insert_46B_MDB():
            CEC = Extract_46B()
            if CEC.empty:
                return None

            ca = certifi.where()
            client = MongoClient(
                "mongodb+srv://team_lotfi:teamLotfi@cluster0.zdz0hto.mongodb.net/?retryWrites=true&w=majority",
                tlsCAFile=ca)
            db = client.CEC  # use or create a database named db
            CEC_collection = db.CEC_collection  # use or create a collection named JDD46B_collection
            JDD_46B_Dict = CEC.to_dict(orient='records')
            for doc in JDD_46B_Dict:
                if not CEC_collection.find_one(doc):
                    CEC_collection.insert_one(doc)

            #CEC_collection.insert_many(JDD_46B_Dict)
            return CEC_collection

        def recap_46B_MDB():
            # CEC = Extract_46B()
            ca = certifi.where()
            connect_timeout_ms = 10000
            client = MongoClient(
                "mongodb+srv://team_lotfi:teamLotfi@cluster0.zdz0hto.mongodb.net/?retryWrites=true&w=majority",
                tlsCAFile=ca)
            db = client.CEC
            CEC_collection = db.CEC_collection
            last_elt_46B = []
            mydoc = db.CEC_collection.find().sort('_id', -1).limit(37)
            for x in mydoc:
                last_elt_46B.append(x)
            B46_last_37 = pd.DataFrame(last_elt_46B)
            B46_last_37 = B46_last_37.drop(['_id'], axis=1)
            return B46_last_37

        def Statistique_46B():
            B46 = recap_46B_MDB()
            # print(B46["CEC"])
            # Calculer la moyenne
            moy_46B = round(B46['CEC'].mean(), 5)
            # Calculer l'écart type
            ecartType_46B = round(B46['CEC'].std(), 5)
            # Calculer le coefficient de variation
            CV_46B = round(((ecartType_46B / moy_46B) * 100), 5)
            # Calculer le nombre
            Nb_46B = len(B46)
            Date_Premier_Echantillon = B46['Date'].iloc[-1]
            Date_Dernier_Echantillon = B46['Date'].iloc[0]
            # Calculer l'écart-type expérimentale de la moyenne
            EcarType_Moy_46B = round((ecartType_46B / np.sqrt(Nb_46B)), 5)
            ##### calculer la limite de surveillance
            LS_46B = round(2.03 * CV_46B, 5)
            # Calculer la limite d'action
            LA_46B = round(2.72 * CV_46B, 5)
            ##### Définition de la liste qui resulte les différents standars statistiques
            Liste_Stats_46B = [moy_46B, ecartType_46B, CV_46B, Nb_46B, Date_Premier_Echantillon, Date_Dernier_Echantillon,
                               EcarType_Moy_46B, LS_46B, LA_46B]
            List_Labels_46B = ['Moyenne', 'Ecart-Type Expérimental', 'CV (%)', 'Nb', 'Date_Premier_Echantillon',
                               'Date_Dernier_Echantillon',
                               'Ecart-Type Expérimental de la moyenne',
                               'Limite de surveillance (%)', 'Limite d action (%)']
            Statistiques_46B = pd.DataFrame(list(zip(List_Labels_46B, Liste_Stats_46B)),
                                            columns=['Mesures Statistiques', 'valueur'])
            # DataSet_46B_Stats = Statistiques_46B.to_json()
            return (Liste_Stats_46B)

        statistique_46B = Statistique_46B()

        def calcul_LSS_LSI_46B():
            LSS_46B = round(statistique_46B[0] * (1 + (statistique_46B[7] / 100)), 5)
            LSI_46B = round(statistique_46B[0] * (1 - (statistique_46B[7] / 100)), 5)
            return (LSS_46B, LSI_46B)

        def calcul_LAS_LAI_46B():
            LAS_46B = round(statistique_46B[0] * (1 + (statistique_46B[8] / 100)), 5)
            LAI_46B = round(statistique_46B[0] * (1 - (statistique_46B[8] / 100)), 5)

            return (LAS_46B, LAI_46B)

        def mesures_stati_dataframe():
            LSS_46B, LSI_46B = calcul_LSS_LSI_46B()
            LAS_46B, LAI_46B = calcul_LAS_LAI_46B()
            Moy = statistique_46B[0]
            B46_latest = recap_46B_MDB()
            x = list(B46_latest.index.values)
            B46_latest = B46_latest.assign(Nombre_Echantillons=x)
            B46_latest = B46_latest.assign(Moyenne=Moy)
            B46_latest = B46_latest.assign(LSSupérieure=LSS_46B)
            B46_latest = B46_latest.assign(LSInférieure=LSI_46B)
            B46_latest = B46_latest.assign(LASupérieure=LAS_46B)
            B46_latest = B46_latest.assign(LAInférieure=LAI_46B)
            return (B46_latest)

        #################################### Référentiel :S4 ##############################################""

        def Extract_S4():
            CEC = Calcul_C_CEC()
            CEC_listed = CEC.values.tolist()
            ##### Fonction permet d'avoir une liste du référentiel 46B avec tt les informations qui lui correspondent
            data_S4 = []
            Echantillon = []
            for i in (CEC_listed):
                Echantillon.append(i[1])
            for k in Echantillon:
                if k[0:2] == 'S4':
                    data_S4.append(k)
            ##### Fonction permet d'avoir une liste du référentiel 46B avec tt les informations qui lui correspondent
            data_S4_I = []
            for i in range(len(data_S4)):
                for k in range(len(CEC_listed)):
                    if CEC_listed[k][1] == data_S4[i]:
                        data_S4_I.append(CEC_listed[k][0])
                        data_S4_I.append(data_S4[i])
                        for l in [2, 3, 4, 5, 6]:
                            data_S4_I.append(CEC_listed[k][l])
            ##### Définir une fonction permettant la convertion de la liste plate à une liste imbriquée dont chaque liste représente une ligne pour notre DataFrame
            step, size = 7, 7
            JDD_S4 = []
            for i in range(0, len(data_S4_I), step):
                # slicing list
                JDD_S4.append(data_S4_I[i: i + size])

            ##### Convertir List to DataFrame
            JDD_S4 = pd.DataFrame(JDD_S4, columns=['Date', 'Echantillon', 'ABS', 'Concentration', 'poids', 'C', 'CEC'])
            return JDD_S4

        def insert_S4_MDB():
            CEC = Extract_S4()
            if CEC.empty:
                return None
            ca = certifi.where()
            client = MongoClient(
                "mongodb+srv://team_lotfi:teamLotfi@cluster0.zdz0hto.mongodb.net/?retryWrites=true&w=majority",
                tlsCAFile=ca)
            db = client.CEC  # use or create a database named db
            S4_collection = db.S4_collection  # use or create a collection named JDD46B_collection
            JDD_S4_Dict = CEC.to_dict(orient='records')
            for doc in JDD_S4_Dict:
                if not S4_collection.find_one(doc):
                    S4_collection.insert_one(doc)
            #S4_collection.insert_many(JDD_S4_Dict)
            return S4_collection

        def recap_S4_MDB():
            ca = certifi.where()
            client = MongoClient(
                "mongodb+srv://team_lotfi:teamLotfi@cluster0.zdz0hto.mongodb.net/?retryWrites=true&w=majority",
                tlsCAFile=ca)
            db = client.CEC
            S4_collection = db.S4_collection
            # last_elt_46B = []
            mydoc = db.S4_collection.find().sort('_id', -1).limit(37)
            last_elt_S4 = []
            for x in mydoc:
                last_elt_S4.append(x)
            S4_last_37 = pd.DataFrame(last_elt_S4)
            S4_last_37 = S4_last_37.drop(['_id'], axis=1)
            return S4_last_37

        def Statistique_S4():
            S4 = recap_S4_MDB()
            # Calculer la moyenne
            moy_S4 = round(S4['CEC'].mean(), 5)
            # Calculer l'écart type
            ecartType_S4 = round(S4['CEC'].std(), 5)
            # Calculer le coefficient de variation
            CV_S4 = round(((ecartType_S4 / moy_S4) * 100), 5)
            # Calculer le nombre
            Nb_S4 = len(S4)
            Date_Premier_Echantillon = S4['Date'].iloc[-1]
            Date_Dernier_Echantillon = S4['Date'].iloc[0]
            # Calculer l'écart-type expérimentale de la moyenne
            EcarType_Moy_S4 = round((ecartType_S4 / np.sqrt(Nb_S4)), 5)
            ##### calculer la limite de surveillance
            LS_S4 = round(2.03 * CV_S4, 5)
            # Calculer la limite d'action
            LA_S4 = round(2.72 * CV_S4, 5)
            ##### Définition de la liste qui resulte les différents standars statistiques
            Liste_Stats_S4 = [moy_S4, ecartType_S4, CV_S4, Nb_S4, Date_Premier_Echantillon, Date_Dernier_Echantillon,
                              EcarType_Moy_S4, LS_S4, LA_S4]
            # List_Labels_S4 = ['Moyenne', 'Ecart-Type Expérimental', 'CV (%)', 'Nb', 'Ecart-Type Expérimental de la moyenne',
            # 'Limite de surveillance (%)', 'Limite d action (%)']
            # Statistiques_S4 = pd.DataFrame(list(zip(List_Labels_S4, Liste_Stats_S4)),
            # columns=['Mesures Statistiques', 'valueur'])
            return (Liste_Stats_S4)

        statistique_S4 = Statistique_S4()

        def calcul_LSS_LSI_S4():
            LSS_S4 = round(statistique_S4[0] * (1 + (statistique_S4[7] / 100)), 5)
            LSI_S4 = round(statistique_S4[0] * (1 - (statistique_S4[7] / 100)), 5)

            return (LSS_S4, LSI_S4)

        def calcul_LAS_LAI_S4():
            LAS_S4 = round(statistique_S4[0] * (1 + (statistique_S4[8] / 100)), 5)
            LAI_S4 = round(statistique_S4[0] * (1 - (statistique_S4[8] / 100)), 5)

            return (LAS_S4, LAI_S4)

        #B46_latest = insert_S4_MDB()

        def mesures_stati_dataframe_S4():
            LSS_S4, LSI_S4 = calcul_LSS_LSI_S4()
            LAS_S4, LAI_S4 = calcul_LAS_LAI_S4()
            Moy = statistique_S4[0]
            S4_latest = recap_S4_MDB()
            x = list(S4_latest.index.values)
            S4_latest = S4_latest.assign(Index=x)
            S4_latest = S4_latest.assign(Moyenne=Moy)
            S4_latest = S4_latest.assign(LSSupérieure=LSS_S4)
            S4_latest = S4_latest.assign(LSInférieure=LSI_S4)
            S4_latest = S4_latest.assign(LASupérieure=LAS_S4)
            S4_latest = S4_latest.assign(LAInférieure=LAI_S4)
            return (S4_latest)

            #################################### Référentiel :ER ##############################################""

        def Extract_ER():
            CEC = Calcul_C_CEC()
            CEC_listed = CEC.values.tolist()
            ##### Fonction permet d'avoir une liste du référentiel ER avec tt les informations qui lui correspondent
            data_ER = []
            Echantillon = []
            for i in (CEC_listed):
                Echantillon.append(i[1])
            for k in Echantillon:
                if k[0:2] == 'ER':
                    data_ER.append(k)
            ##### Fonction permet d'avoir une liste du référentiel ER avec tt les informations qui lui correspondent
            data_ER_I = []
            for i in range(len(data_ER)):
                for k in range(len(CEC_listed)):
                    if CEC_listed[k][1] == data_ER[i]:
                        data_ER_I.append(CEC_listed[k][0])
                        data_ER_I.append(data_ER[i])
                        for l in [2, 3, 4, 5, 6]:
                            data_ER_I.append(CEC_listed[k][l])
            ##### Définir une fonction permettant la convertion de la liste plate à une liste imbriquée dont chaque liste représente une ligne pour notre DataFrame
            step, size = 7, 7
            JDD_ER = []
            for i in range(0, len(data_ER_I), step):
                # slicing list
                JDD_ER.append(data_ER_I[i: i + size])

            ##### Convertir List to DataFrame
            JDD_ER = pd.DataFrame(JDD_ER, columns=['Date', 'Echantillon', 'ABS', 'Concentration', 'poids', 'C', 'CEC'])
            return JDD_ER

        def insert_ER_MDB():
            CEC = Extract_ER()
            if CEC.empty:
                return None
            ca = certifi.where()
            client = MongoClient(
                "mongodb+srv://team_lotfi:teamLotfi@cluster0.zdz0hto.mongodb.net/?retryWrites=true&w=majority",
                tlsCAFile=ca)
            db = client.CEC  # use or create a database named db
            ER_collection = db.ER_collection  # use or create a collection named JDD46B_collection
            JDD_ER_Dict = CEC.to_dict(orient='records')
            for doc in JDD_ER_Dict:
                if not ER_collection.find_one(doc):
                    ER_collection.insert_one(doc)

            #ER_collection.insert_many(JDD_ER_Dict)
            return ER_collection

        def recap_ER_MDB():
            ca = certifi.where()
            client = MongoClient(
                "mongodb+srv://team_lotfi:teamLotfi@cluster0.zdz0hto.mongodb.net/?retryWrites=true&w=majority",
                tlsCAFile=ca)
            db = client.CEC
            ER_collection = db.ER_collection
            # last_elt_46B = []
            mydoc = db.ER_collection.find().sort('_id', -1).limit(37)
            last_elt_ER = []
            for x in mydoc:
                last_elt_ER.append(x)
            ER_last_37 = pd.DataFrame(last_elt_ER)
            ER_last_37 = ER_last_37.drop(['_id'], axis=1)
            return ER_last_37

        def Statistique_ER():
            ER = recap_ER_MDB()
            # Calculer la moyenne
            moy_ER = round(ER['CEC'].mean(), 5)
            # Calculer l'écart type
            ecartType_ER = round(ER['CEC'].std(), 5)
            # Calculer le coefficient de variation
            CV_ER = round(((ecartType_ER / moy_ER) * 100), 5)
            # Calculer le nombre
            Nb_ER = len(ER)
            Date_Premier_Echantillon = ER['Date'].iloc[-1]
            Date_Dernier_Echantillon = ER['Date'].iloc[0]
            # Calculer l'écart-type expérimentale de la moyenne
            EcarType_Moy_ER = round((ecartType_ER / np.sqrt(Nb_ER)), 5)
            ##### calculer la limite de surveillance
            LS_ER = round(2.03 * CV_ER, 5)
            # Calculer la limite d'action
            LA_ER = round(2.72 * CV_ER, 5)
            ##### Définition de la liste qui resulte les différents standars statistiques
            Liste_Stats_ER = [moy_ER, ecartType_ER, CV_ER, Nb_ER, Date_Premier_Echantillon, Date_Dernier_Echantillon,
                              Date_Dernier_Echantillon, EcarType_Moy_ER, LS_ER, LA_ER]
            return (Liste_Stats_ER)

        statistique_ER = Statistique_ER()

        def calcul_LSS_LSI_ER():
            LSS_ER = round(statistique_ER[0] * (1 + (statistique_ER[7] / 100)), 5)
            LSI_ER = round(statistique_ER[0] * (1 - (statistique_ER[7] / 100)), 5)

            return (LSS_ER, LSI_ER)

        def calcul_LAS_LAI_ER():
            LAS_ER = round(statistique_ER[0] * (1 + (statistique_ER[8] / 100)), 5)
            LAI_ER = round(statistique_ER[0] * (1 - (statistique_ER[8] / 100)), 5)

            return (LAS_ER, LAI_ER)

        #ER_latest = insert_ER_MDB()

        def mesures_stati_dataframe_ER():
            LSS_ER, LSI_ER = calcul_LSS_LSI_ER()
            LAS_ER, LAI_ER = calcul_LAS_LAI_ER()
            Moy = statistique_ER[0]
            ER_latest = recap_ER_MDB()
            x = list(ER_latest.index.values)
            ER_latest = ER_latest.assign(Index=x)
            ER_latest = ER_latest.assign(Moyenne=Moy)
            ER_latest = ER_latest.assign(LSSupérieure=LSS_ER)
            ER_latest = ER_latest.assign(LSInférieure=LSI_ER)
            ER_latest = ER_latest.assign(LASupérieure=LAS_ER)
            ER_latest = ER_latest.assign(LAInférieure=LAI_ER)
            return (ER_latest)

    ############################################ Streamlit #####################################

    #st.header(":red[Capacité d'Echange Cathionique(CEC): Dosage Colorimétrique des ions NH4 extrait par Chlorure de Sodium]")
        S4_latest = insert_S4_MDB()
        B46_latest = insert_46B_MDB()
        ER_latest = insert_ER_MDB()

        st.header("Statistiques Descriptives")
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns([1, 1, 1,1])

        with stat_col1:
            st.title("")

        with stat_col2:
            image = Image.open('Statistique.png')
            st.image(image, use_column_width=True)

        with stat_col3:
            st.title("")

        if st.button("Matériel de Référence Interne: 46B"):
            st.header(":blue[Matériel de Référence Interne: 46B]")
            st.write(pd.DataFrame({
                        'CEC ':'cmol+/Kg',
                        'Moyenne': [statistique_46B[0]],
                        'Ecart-Type Expérimental': [statistique_46B[1]],
                        'CV (%)': [statistique_46B[2]],
                        'Nb': [statistique_46B[3]],
                        'Date Premier Echantillon': [statistique_46B[4]],
                        'Date Dernier Echantillon': [statistique_46B[5]],
                        'Ecart-Type Expérimental de la moyenne': [statistique_46B[6]],
                        'Limite de surveillance (%)': [statistique_46B[7]],
                        'Limite d action (%)': [statistique_46B[8]],
                    }))

            #st.title("Table des Statistiques")
        if st.button("Matériel de Référence Interne: S4"):
            st.header(":blue[Matériel de Référence Interne : S4]")
            st.write(pd.DataFrame({
                        'CEC ': 'cmol+/Kg',
                        'Moyenne': [statistique_S4[0]],
                        'Ecart-Type Expérimental': [statistique_S4[1]],
                        'CV (%)': [statistique_S4[2]],
                        'Nb': [statistique_S4[3]],
                        'Date Premier Echantillon': [statistique_S4[4]],
                        'Date Dernier Echantillon': [statistique_S4[5]],
                        'Ecart-Type Expérimental de la moyenne': [statistique_S4[4]],
                        'Limite de surveillance (%)': [statistique_S4[5]],
                        'Limite d action (%)': [statistique_S4[6]],
                    }))
        if st.button("Matériel de Référence Interne: ER"):
            st.header(":blue[Matériel de Référence Interne : ER]")
            st.write(pd.DataFrame({
                        'CEC ': 'cmol+/Kg',
                        'Moyenne': [statistique_ER[0]],
                        'Ecart-Type Expérimental': [statistique_ER[1]],
                        'CV (%)': [statistique_ER[2]],
                        'Nb': [statistique_ER[3]],
                        'Date Premier Echantillon': [statistique_ER[4]],
                        'Date Dernier Echantillon': [statistique_ER[5]],
                        'Ecart-Type Expérimental de la moyenne': [statistique_ER[4]],
                        'Limite de surveillance (%)': [statistique_ER[5]],
                        'Limite d action (%)': [statistique_ER[6]],
                    }))

        B46_last_37 = mesures_stati_dataframe()
        S4_last_37 = mesures_stati_dataframe_S4()
        ER_last_37 = mesures_stati_dataframe_ER()

        st.header("Cartes de Contrôle")
        with stat_col1:
            st.title("")

        #with stat_col2:
        #    image = Image.open('carte_controle.png')
        #   st.image(image, use_column_width=True)

        with stat_col3:
            st.title("")


        if st.button("Matériel de Référence Interne : 46B"):
            st.header(":blue[Matériel de Référence Interne : 46B]")
            x=list(B46_last_37.index.values)
            y1 = B46_last_37['CEC']
            y2 = B46_last_37['Moyenne']
            y3 = B46_last_37['LSSupérieure']
            y4 = B46_last_37['LSInférieure']
            y5 = B46_last_37['LASupérieure']
            y6 = B46_last_37['LAInférieure']
            plt.rcParams["figure.figsize"] = [16, 15]
            fig, ax = plt.subplots()
            ax.plot(x, y1, label="CEC", color='k')
            plt.scatter(x, y1, color='r')
            ax.plot(x, y2, label="Moyenne", color='g')
            ax.plot(x, y3, label="LSS", color='b')
            ax.plot(x, y4, label="LSI", color='b')
            ax.plot(x, y5, label="LAS", color='r')
            ax.plot(x, y6, label="LAI", color='r')
            ax.legend(loc='best')
            st.pyplot(fig)

        if st.button("Matériel de Référence Interne : S4"):
            st.header(":blue[Matériel de Référence Interne : S4]")
            x=list(S4_last_37.index.values)
            y1 = S4_last_37['CEC']
            y2 = S4_last_37['Moyenne']
            y3 = S4_last_37['LSSupérieure']
            y4 = S4_last_37['LSInférieure']
            y5 = S4_last_37['LASupérieure']
            y6 = S4_last_37['LAInférieure']
            plt.rcParams["figure.figsize"] = [16, 15]
            fig, ax = plt.subplots()
            ax.plot(x, y1, label="CEC", color='k')
            plt.scatter(x, y1, color='r')
            ax.plot(x, y2, label="Moyenne", color='g')
            ax.plot(x, y3, label="LSS", color='b')
            ax.plot(x, y4, label="LSI", color='b')
            ax.plot(x, y5, label="LAS", color='r')
            ax.plot(x, y6, label="LAI", color='r')
            ax.legend(loc='best')
            st.pyplot(fig)
        if st.button("Matériel de Référence Interne : ER"):
            st.header(":blue[Matériel de Référence Interne : ER]")

            x=list(ER_last_37.index.values)
            y1 = ER_last_37['CEC']
            y2 = ER_last_37['Moyenne']
            y3 = ER_last_37['LSSupérieure']
            y4 = ER_last_37['LSInférieure']
            y5 = ER_last_37['LASupérieure']
            y6 = ER_last_37['LAInférieure']
            plt.rcParams["figure.figsize"] = [16, 15]
            fig, ax = plt.subplots()
            ax.plot(x, y1, label="CEC", color='k')
            plt.scatter(x, y1, color='r')
            ax.plot(x, y2, label="Moyenne", color='g')
            ax.plot(x, y3, label="LSS", color='b')
            ax.plot(x, y4, label="LSI", color='b')
            ax.plot(x, y5, label="LAS", color='r')
            ax.plot(x, y6, label="LAI", color='r')
            ax.legend(loc='best')
            st.pyplot(fig)



if __name__ == '__main__':
    main()
