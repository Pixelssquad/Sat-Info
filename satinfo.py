import sys
import csv
import requests
import io
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush, QFont
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLineEdit, QPushButton, QTableWidget,
                             QTableWidgetItem, QMessageBox, QHeaderView)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SatInfo from JE9PEL CSV - by IU2BWQ Diego Pellacani")
        self.resize(900, 600)

        # URL preimpostato dal tuo screenshot
        default_url = "https://www.ne.jp/asahi/hamradio/je9pel/satslist.csv"

        # Elementi dell'interfaccia
        self.url_input = QLineEdit(default_url)
        self.load_btn = QPushButton("Scarica CSV")
        self.load_btn.clicked.connect(self.load_csv)

        self.table = QTableWidget()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        # Layout
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.url_input)
        top_layout.addWidget(self.load_btn)

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.table)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def load_csv(self):
        url = self.url_input.text().strip()
        if not url:
            return

        try:
            # Disabilita temporaneamente l'ordinamento durante il caricamento dei dati
            # per evitare rallentamenti o bug visivi mentre inseriamo le celle
            self.table.setSortingEnabled(False)

            # 1. Scarica il file dalla rete
            response = requests.get(url)
            response.raise_for_status() 
            response.encoding = 'utf-8'
            
            # 2. Legge il testo scaricato
            csv_data = io.StringIO(response.text)
            
            # 3. Rileva automaticamente il separatore
            sample = csv_data.read(1024)
            csv_data.seek(0)
            
            try:
                dialect = csv.Sniffer().sniff(sample)
                reader = list(csv.reader(csv_data, dialect))
            except csv.Error:
                reader = list(csv.reader(csv_data, delimiter=';'))

            if not reader:
                QMessageBox.warning(self, "Attenzione", "Il file CSV è vuoto o non valido.")
                return

            # Calcola quante colonne reali ci sono nel file CSV
            num_cols = len(reader[0])

            # Nomi delle colonne personalizzati
            mie_colonne = ["Satellite", "Norad ID", "UPlink", "DOWNlink 1", "DOWNlink 2", "Mode", "ID", "Status"]
            headers = mie_colonne[:num_cols]
            while len(headers) < num_cols:
                headers.append(f"Colonna {len(headers) + 1}")

            rows = reader

            # 4. Configura la tabella
            self.table.setColumnCount(num_cols)
            self.table.setHorizontalHeaderLabels(headers)
            self.table.setRowCount(len(rows))

            # Configurazione della tavolozza colori per le righe
            colore_riga_pari = QColor("#e6f2ff")     # Azzurro chiaro
            colore_riga_dispari = QColor("#e6ffed")  # Verde chiaro
            colore_allerta = QColor("#ffcccc")       # Rosso chiaro (inactive / re-entered / failure)
            colore_sconosciuto = QColor("#ffe5cc")   # Arancione chiaro (unknown)
            colore_futuro = QColor("#ffffcc")        # Giallo chiaro (to be launched)
            
            # Configurazione Font e colore testo
            font_grassetto = QFont()
            font_grassetto.setBold(True)
            colore_testo_nero = QColor("#000000")

            # 5. Popola le celle e applica gli stili condizionali
            for row_idx, row_data in enumerate(rows):
                
                # Stati della riga
                attivare_rosso = False
                attivare_arancione = False
                attivare_giallo = False
                
                # CONTROLLO COLONNA 8 (Indice 7)
                if len(row_data) > 7:
                    valore_cella = row_data[7].strip().lower()
                    
                    # Condizioni per il Rosso
                    if "inactive" in valore_cella or "re-entered" in valore_cella or "re entered" in valore_cella or "failure" in valore_cella:
                        attivare_rosso = True
                    # Condizioni per l'Arancione
                    elif "unknown" in valore_cella or "unknow" in valore_cella:
                        attivare_arancione = True
                    # Condizioni per il Giallo
                    elif "to be launched" in valore_cella:
                        attivare_giallo = True

                # Determina il colore di sfondo finale in base alle priorità
                if attivare_rosso:
                    sfondo_riga = colore_allerta
                elif attivare_arancione:
                    sfondo_riga = colore_sconosciuto
                elif attivare_giallo:
                    sfondo_riga = colore_futuro
                elif row_idx % 2 == 0:
                    sfondo_riga = colore_riga_pari
                else:
                    sfondo_riga = colore_riga_dispari

                # Applica le impostazioni a ogni singola cella della riga corrente
                for col_idx, cell_data in enumerate(row_data):
                    item = QTableWidgetItem(cell_data)
                    
                    # Applica testo in grassetto nero
                    item.setFont(font_grassetto)
                    item.setForeground(QBrush(colore_testo_nero))
                    
                    # Applica lo sfondo calcolato
                    item.setBackground(QBrush(sfondo_riga))
                        
                    self.table.setItem(row_idx, col_idx, item)
            
            # 6. Ottimizza la larghezza delle colonne
            self.table.resizeColumnsToContents()

            # LA SOLUZIONE È QUI: Riabilita l'ordinamento a caricamento ultimato.
            # Ora l'utente potrà cliccare sui nomi delle colonne in alto per ordinare A-Z o Z-A.
            self.table.setSortingEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Impossibile caricare il CSV:\n{e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())