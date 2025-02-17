# SmartNX Control - Interlogix Modern Interface

## Overview

SmartNX Control è un'interfaccia web moderna per interagire con i sistemi di allarme Interlogix tramite connessione TCP/IP. Questo progetto fornisce un'interfaccia utente intuitiva per monitorare lo stato del sistema, armare/disarmare le aree, visualizzare gli eventi di log e gestire le zone.

## Features

-   **Dashboard:** Visualizza lo stato attuale delle aree (armato, disarmato, allarme).
-   **Zone Management:** Monitora lo stato delle zone (normale, allarme, bypassato) e abilita/disabilita il bypass delle zone.
-   **Event Log:** Visualizza lo storico degli eventi di sistema con filtri per tipo di evento (allarmi, inserimenti, disinserimenti).
-   **Responsive Design:** Interfaccia utente ottimizzata per dispositivi desktop e mobile.
-   **Easy Connection:** Configurazione semplificata della connessione al server TCP/IP.
-   **Theme Support:** Modalità chiara e scura per una migliore esperienza utente.

## Technologies Used

-   **Frontend:** HTML, CSS, JavaScript
-   **Backend:** Python (Flask)
-   **Protocol Communication:** TCP/IP

## Requirements

-   Python 3.6+
-   Flask
-   Un sistema di allarme Interlogix compatibile con connessione TCP/IP

## Setup Instructions

1.  **Clone the repository:**

    ```bash
    git clone [repository_url]
    cd [repository_directory]
    ```

2.  **Create a virtual environment (recommended):**

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Linux/macOS
    venv\Scripts\activate  # On Windows
    ```

3.  **Install the dependencies:**

    ```bash
    pip install Flask
    ```

4.  **Configure the connection:**

    *   Modifica l'indirizzo IP e la porta nel file `main.py` o tramite l'interfaccia web.

5.  **Run the application:**

    ```bash
    python main.py
    ```

6.  **Access the web interface:**

    *   Apri il tuo browser web e vai all'indirizzo `http://localhost:5000`.

## Usage

1.  **Connection:**

    *   Inserisci l'indirizzo IP e la porta del server TCP/IP del tuo sistema Interlogix.
    *   Clicca su "Connetti" per stabilire la connessione.

2.  **Dashboard:**

    *   Visualizza lo stato delle aree (armato, disarmato, allarme).
    *   Clicca su un'area per armarla o disarmarla.

3.  **Zones:**

    *   Visualizza lo stato delle zone (normale, allarme, bypassato).
    *   Clicca su una zona per visualizzare il menu di controllo e abilitare/disabilitare il bypass.

4.  **Events:**

    *   Visualizza lo storico degli eventi di sistema.
    *   Utilizza i filtri per visualizzare solo gli eventi di un determinato tipo (allarmi, inserimenti, disinserimenti).
    *   Esporta gli eventi in formato CSV.

## Contributing

Le contribuzioni sono benvenute! Se desideri contribuire a questo progetto, segui questi passaggi:

1.  Fork il repository.
2.  Crea un branch per la tua feature o fix.
3.  Implementa le modifiche.
4.  Invia una pull request.

## License

Questo progetto è rilasciato sotto licenza [MIT License](LICENSE).

## Contact

Per domande o suggerimenti, contatta [your_email@example.com](mailto:your_email@example.com).
