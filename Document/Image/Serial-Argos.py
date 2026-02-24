# -------------------------------------------------------------
# Fichier : Serial-Argos-Demo.py
# Auteur  : Paul Miailhe
# Date    : 21/03/2025
# Objet   : Script de démonstration Argos-SMD ARRIBADA
#
# Copyright (c) 2025 CNES - Centre National d'Études Spatiales 
# -------------------------------------------------------------

"""
Liste complète des commandes AT pour le module SMD Argos (avec tailles approximatives) :

- AT+PING=?                                    : Ping du module SMD                                 (~10 octets)
- AT+FW=?                                      : Lecture de la version firmware                     (~8 octets)
- AT+ADDR=?                                    : Lecture de l'adresse (MAC)                         (~10 octets)
- AT+ADDR=xxxx                                 : Écriture de l'adresse (MAC)                        (~14 octets)
- AT+SECKEY=?                                  : Lecture de la clé secrète                          (~12 octets)
- AT+SECKEY=xxxx                               : Écriture de la clé secrète                         (~38 octets)
- AT+SN=?                                      : Lecture du numéro de série                         (~8 octets)
- AT+ID=?                                      : Lecture de l'identifiant SMD                       (~8 octets)
- AT+ID=xxxx                                   : Écriture de l'identifiant                          (~14 octets)
- AT+TCXO_WU=?                                 : Lecture du temps de warm-up du TCXO                (~14 octets)
- AT+TCXO_WU=xxxx                              : Écriture du temps de warm-up du TCXO               (~20 octets)
- AT+RCONF=?                                   : Lecture de la configuration radio                  (~12 octets)
- AT+SAVE_RCONF=                               : Sauvegarde de la configuration radio               (~16 octets)
- AT+TX=...                                    : Envoi d'un message uplink                          (~58 octets)
- AT+CW=...                                    : Envoi d’un signal en mode onde continue (CW)       (~30 octets)
- AT+LPM=?                                     : Lecture du mode basse consommation                 (~10 octets)
- AT+LPM=...                                   : Écriture du mode basse consommation                (~12 octets)
- AT+VERSION=?                                 : Lecture de la version AT                           (~14 octets)
- AT+UDATE=?                                   : Lecture de la date UTC                             (~12 octets)
- AT+KMAC=0                                    : Réinitialisation de profil KMAC                    (~10 octets)
- AT+KMAC=1                                    : Activation de profil KMAC                          (~10 octets)
- AT+RCONF=44cd3a299068292a74d2126f3402610d    : Configuration radio : LDA2 bande 7                 (~44 octets)
- AT+RCONF=bd176535b394a665bd86f354c5f424fb    : Configuration radio : LDA2L                        (~44 octets)
- AT+RCONF=efd2412f8570581457f2d982e76d44d7    : Configuration radio : VLDA4                        (~44 octets)
- AT+RCONF=41bc11b8980df01ba8b4b8f41099620b    : Configuration radio : LDK                          (~44 octets)
- AT+RCONF=9e51ca0d73594fdb8c3b82d9b799b2b0    : Configuration radio : LDA2 bande 2                 (~44 octets)
"""

import serial
import time
from datetime import datetime

# Configuration du port série
SERIAL_PORT = 'COM4'       # À adapter à votre système
BAUD_RATE = 9600
TIMEOUT = 2   
TX_INTERVAL = 5  # secondes

# Liste des codes d’erreur +ERROR=XX retournés par le module SMD
ERROR_CODES = {
    0:  "Aucune erreur (OK)",
    1:  "Commande AT inconnue",
    2:  "Format de paramètre invalide",
    3:  "Paramètres manquants",
    4:  "Trop de paramètres",
    5:  "Valeur incompatible",
    6:  "Commande AT non reconnue",
    7:  "ID invalide",
    8:  "ID inconnu",
    20: "Longueur des données utilisateur invalide",
    21: "File d'attente de données pleine",
    22: "File d'attente de données vide",
    30: "Timeout de réception RX",
    40: "Erreur transceiver (par ex : message non émis)",
    41: "Erreur d’auto-réglage du transceiver",
    42: "Erreur PLL transceiver",
    43: "Timeout oscillateur transceiver",
    44: "Reset transceiver",
    60: "Fréquence de TX/Modulation non valide dans la config",
}

# Payloads typiques selon les configurations

TXpayload_LDA2 =  "cafebabe0000000000000000000000000000000000000000"

TXpayload =       "000000000000000000000000000000000000000000000000"
TXpayload_LDA2L = "000000000000000000000000000000000000000000000000"
TXpayload_LDK =   "00000000000000000000000000000000000000"
TXpayload_VLDA4 = "000000"
TXpayload_VLDA4 = "cafebe"

def log_to_file(content):
    with open("argos_log.txt", "a", encoding="utf-8") as f:
        f.write(content + "\n")

def interpret_error(response: str):
    if "+ERROR=" in response:
        try:
            code = int(response.split("+ERROR=")[1].split()[0])
            meaning = ERROR_CODES.get(code, "Code d'erreur inconnu")
            print(f"Erreur détectée : +ERROR={code} → {meaning}")
            log_to_file(f"[ERROR {code}] {meaning}")
        except Exception:
            print("Format d'erreur non reconnu.")
            log_to_file("[ERROR] Format non reconnu")

def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def send_command(ser, command):
    now = timestamp()
    print(f"\n{now} > Envoi : {command}")
    log_to_file(f"[{now}] > {command}")
    ser.write(command.encode() + b'\r\n')
    response = b""
    while True:
        chunk = ser.read(1)
        if not chunk:
            break
        response += chunk
    decoded = response.decode(errors='replace').strip()
    print(f"< Réponse : {decoded}")
    log_to_file(f"[{now}] < {decoded}")
    interpret_error(decoded)
    return decoded

def interactive_mode(ser):
    print("\n Mode interactif activé. Tape une commande AT ou 'exit' pour quitter.")
    while True:
        try:
            user_input = input(">>> ")
            if user_input.lower() in ['exit', 'quit']:
                print("Fin du mode interactif.")
                break
            send_command(ser, user_input)
        except KeyboardInterrupt:
            print("\nInterruption par l'utilisateur.")
            break

def main():
    
    print(f"Démarrage du script : envoi automatique toutes les {TX_INTERVAL} secondes...\n")

    with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=TIMEOUT) as ser:
        time.sleep(1)

        # send_command(ser, 'AT+PING=?')
        # time.sleep(0.1)
        # send_command(ser, 'AT+FW=?')
        # time.sleep(0.1)
        # send_command(ser, 'AT+ADDR=?')
        # time.sleep(0.1)
        # send_command(ser, 'AT+SN=?')
        # time.sleep(0.1)
        # send_command(ser, 'AT+ID=?')
        # time.sleep(0.1)

        # This section configures the SMD protocol
        send_command(ser, 'AT+RCONF=44cd3a299068292a74d2126f3402610d')
        time.sleep(0.1)
        send_command(ser, ' ')
        time.sleep(0.1)
        send_command(ser, 'AT+RCONF=?')
        time.sleep(0.1)
        send_command(ser, 'AT+SAVE_RCONF=')
        time.sleep(0.1)
        #send_command(ser, 'AT+ADDR=00000029')
        #time.sleep(0.1)
        send_command(ser, 'AT+ADDR=11223344')
        time.sleep(0.1)
        send_command(ser, 'AT+ADDR=?')
        time.sleep(0.1)
        send_command(ser, 'AT+SECKEY=00112233445566778899AABBCCDDEEFF')
        time.sleep(0.1)
        send_command(ser, 'AT+SECKEY=?')
        time.sleep(0.1)

        # This section sends two "AT+KMAC" commands to the SMD module to perform a configuration reload.
        send_command(ser, 'AT+KMAC=0')
        time.sleep(0.1)
        send_command(ser, 'AT+KMAC=1')
        time.sleep(0.1)
        send_command(ser, 'AT+RCONF=?')
        time.sleep(0.1)

        # Automatic send loop
        try:
            while True:
                print("\nEnvoi du message Argos...")
                send_command(ser, f"AT+TX={TXpayload_LDA2}")
                print(f"Attente de {TX_INTERVAL} secondes...\n")
                time.sleep(TX_INTERVAL)

        except KeyboardInterrupt:
            print("⏸Script interrompu. Passage en mode interactif...")
            interactive_mode(ser)

if __name__ == "__main__":
    main()
