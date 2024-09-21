import cv2
import numpy as np
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtCore import QTimer, Qt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Detección de Monedas")
        
        # Crear un layout vertical
        layout = QVBoxLayout()

        # Crear etiquetas de advertencias
        advertencia1 = QLabel("Advertencia: Poner cámara web a una distancia de 23.5 cm", self)
        advertencia2 = QLabel("Advertencia: Tener buena iluminación blanca", self)
        advertencia3 = QLabel("Advertencia: Fondo color blanco", self)
        layout.addWidget(advertencia1)
        layout.addWidget(advertencia2)
        layout.addWidget(advertencia3)

        # Crear un label para mostrar la imagen o video procesado
        self.label = QLabel(self)
        layout.addWidget(self.label)

        # Crear etiquetas para mostrar el conteo de monedas y el total de dinero
        self.label_conteo = QLabel("Conteo de Monedas:", self)
        layout.addWidget(self.label_conteo)
        self.label_total = QLabel("Total de Dinero: 0 pesos", self)
        layout.addWidget(self.label_total)

        btn_abrir_camara = QPushButton("Abrir Cámara", self)
        btn_abrir_camara.clicked.connect(self.abrir_camara)
        layout.addWidget(btn_abrir_camara)
        
        # Crear un widget central con el layout
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.mostrar_frame)
        
        self.cap = None  # Variable para almacenar el objeto de captura

        # Centrar la ventana
        self.centrar_ventana()

    def centrar_ventana(self):
        screen_geometry = QApplication.primaryScreen().availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

    def identificar_moneda(self, radio):
        if radio < 30:
            return "1 peso"
        elif 30 <= radio <= 32:
            return "2 pesos"
        elif 34 <= radio <= 35:
            return "5 pesos"
        elif radio > 36:
            return "10 pesos"
        else:
            return "Desconocida"

    def calcular_scale_percent(self, img):
        # Calcular scale_percent dinámico basado en las dimensiones de la imagen
        height, width, _ = img.shape
        max_dimension = max(height, width)
        
        if max_dimension <= 800:
            scale_percent = 80
        elif max_dimension <= 1600:
            scale_percent = 50
        elif max_dimension <= 2400:
            scale_percent = 30
        else:
            scale_percent = 10
        
        return scale_percent

    def procesar_imagen(self, img):
        # Obtener el scale_percent dinámico
        scale_percent = self.calcular_scale_percent(img)

        # Redimensionar la imagen a un tamaño más pequeño
        width = int(img.shape[1] * scale_percent / 100)
        height = int(img.shape[0] * scale_percent / 100)
        dim = (width, height)
        resized_img = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)

        # Convertir a escala de grises y aplicar filtro Gaussiano
        imgGris = cv2.cvtColor(resized_img, cv2.COLOR_BGR2GRAY)
        imgGris = cv2.GaussianBlur(imgGris, (9, 9), 2)

        # Detectar círculos
        circulos = cv2.HoughCircles(
            imgGris, cv2.HOUGH_GRADIENT, dp=1, minDist=20, param1=70, param2=30, minRadius=8, maxRadius=70)

        conteo_monedas = {
            "1 peso": 0,
            "2 pesos": 0,
            "5 pesos": 0,
            "10 pesos": 0,
            "Desconocida": 0
        }

        # Definir colores para cada tipo de moneda
        colores_monedas = {
            "1 peso": (255, 0, 0),  # Azul
            "2 pesos": (0, 255, 0),  # Verde
            "5 pesos": (0, 0, 255),  # Rojo
            "10 pesos": (0, 255, 255),  # Amarillo
            "Desconocida": (255, 255, 255)  # Blanco
        }

        if circulos is not None:
            circulos = np.uint16(np.around(circulos))
            for circulo in circulos[0, :]:
                centro = (circulo[0], circulo[1])
                radio = circulo[2]
                tipo_moneda = self.identificar_moneda(radio)
                conteo_monedas[tipo_moneda] += 1
                color = colores_monedas[tipo_moneda]
                cv2.putText(resized_img, tipo_moneda, (centro[0] - 20, centro[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                cv2.circle(resized_img, centro, radio, color, 2)

        return resized_img, conteo_monedas

    def calcular_total_dinero(self, conteo_monedas):
        valores_monedas = {
            "1 peso": 1,
            "2 pesos": 2,
            "5 pesos": 5,
            "10 pesos": 10
        }

        total_dinero = 0
        for tipo, conteo in conteo_monedas.items():
            if tipo in valores_monedas:
                total_dinero += conteo * valores_monedas[tipo]
        return total_dinero

    def abrir_camara(self):
        for webcam_device_index in range(1, 4):  # Rango de puertos de 1 a 3
            self.cap = cv2.VideoCapture(webcam_device_index)
            if self.cap.isOpened():
                print(f"Cámara encontrada en el puerto {webcam_device_index}")
                self.timer.start(20)  # Iniciar el timer para actualizar cada 20 ms
                return
            else:
                self.cap.release()
        print("No se pudo abrir ninguna cámara web en los puertos 1, 2, y 3")

    def mostrar_frame(self):
        ret, frame = self.cap.read()
        if ret:
            self.mostrar_resultado(frame)
        else:
            self.timer.stop()
            self.cap.release()

    def mostrar_resultado(self, img):
        # Procesar la imagen y obtener el conteo de monedas
        processed_img, conteo_monedas = self.procesar_imagen(img)

        # Calcular el total de dinero
        total_dinero = self.calcular_total_dinero(conteo_monedas)

        # Mostrar la imagen en la ventana
        height, width, channel = processed_img.shape
        bytes_per_line = 3 * width
        img_qt = QImage(processed_img.data, width, height, bytes_per_line, QImage.Format.Format_RGB888).rgbSwapped()
        pixmap = QPixmap.fromImage(img_qt)
        self.label.setPixmap(pixmap)
        self.label.setScaledContents(True)

        # Actualizar el conteo de monedas y el total de dinero en la etiqueta
        conteo_texto = "Conteo de Monedas:\n"
        for tipo, conteo in conteo_monedas.items():
            conteo_texto += f"{tipo}: {conteo}\n"
        self.label_conteo.setText(conteo_texto)
        self.label_total.setText(f"Total de Dinero: {total_dinero} pesos")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

