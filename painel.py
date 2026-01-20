"""
Painel de Controle para gerenciamento de janelas
Interface visual limpa e organizada para gerenciar todas as janelas do sistema
Com animações neon RGB suaves
"""

import os
from PIL import Image
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QScrollArea, QWidget, QPushButton,
    QLabel, QMessageBox, QGridLayout, QFrame, QSpacerItem, QSizePolicy
)
from PySide6.QtGui import QPixmap, QIcon, QColor, QFont, QLinearGradient, QPainter, QPen, QBrush
from PySide6.QtCore import Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve, QRect, Property


def criar_icone_editar_melhorado():
    """Cria ícone de edição (lápis) simples e visível"""
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor(0, 255, 0), 2))
    
    # Desenhar símbolo de lápis simples
    painter.drawLine(2, 20, 4, 18)  # Ponta
    painter.drawLine(4, 18, 18, 4)   # Corpo
    painter.drawLine(18, 4, 20, 2)   # Ponta superior
    painter.drawLine(20, 2, 22, 4)   # Ângulo
    painter.drawLine(4, 18, 2, 20)   # Base ponta
    
    painter.end()
    return QIcon(pixmap)


def criar_icone_nova_animado():
    """Cria ícone de + simples e visível"""
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor(0, 255, 0), 2.5))
    
    # Desenhar +
    center = 12
    size = 8
    
    # Linha vertical
    painter.drawLine(center, center - size, center, center + size)
    # Linha horizontal
    painter.drawLine(center - size, center, center + size, center)
    
    painter.end()
    return QIcon(pixmap)


def criar_icone_deletar():
    """Cria ícone de X para deletar em vermelho"""
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor(255, 0, 0), 2.5))
    
    # Desenhar X simples
    margin = 4
    painter.drawLine(margin, margin, 24 - margin, 24 - margin)
    painter.drawLine(24 - margin, margin, margin, 24 - margin)
    
    painter.end()
    return QIcon(pixmap)


class CartaJanela(QFrame):
    """Card individual para cada janela no painel"""
    
    def __init__(self, nome_janela, cfg, parent=None):
        super().__init__(parent)
        self.nome_janela = nome_janela
        self.cfg = cfg
        
        # Estilo do card com borda neon
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            CartaJanela {
                background-color: #1a1a1a;
                border: 2px solid #ff00ff;
                border-radius: 8px;
                padding: 8px;
            }
            CartaJanela:hover {
                background-color: #2a2a2a;
                border: 3px solid #ff33ff;
            }
        """)
        self.setMinimumHeight(200)
        self.setMinimumWidth(150)
        self.setCursor(Qt.PointingHandCursor)
        
        # Iniciar animação de cor neon
        self.cor_neon = 0
        self.timer_neon = QTimer(self)
        self.timer_neon.timeout.connect(self._animar_cor_neon)
        self.timer_neon.start(30)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # ===== Número da janela (título) =====
        lbl_numero = QLabel(nome_janela)
        font_numero = QFont()
        font_numero.setPointSize(12)
        font_numero.setBold(True)
        lbl_numero.setFont(font_numero)
        lbl_numero.setStyleSheet("color: #ff00ff;")
        lbl_numero.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_numero)
        
        # ===== Prévia da imagem =====
        self.img_preview = QLabel()
        self.img_preview.setAlignment(Qt.AlignCenter)
        self.img_preview.setMinimumHeight(120)
        self.img_preview.setStyleSheet("""
            background-color: #0a0a0a;
            border: 1px solid #ff00ff;
            border-radius: 4px;
        """)
        self._carregar_preview()
        layout.addWidget(self.img_preview)
        
        # ===== Botões de ação =====
        layout_botoes = QHBoxLayout()
        layout_botoes.setSpacing(4)
        
        # Botão Editar
        btn_editar = QPushButton()
        btn_editar.setMaximumWidth(35)
        btn_editar.setMinimumHeight(30)
        btn_editar.setToolTip("Editar janela")
        btn_editar.setIcon(criar_icone_editar_melhorado())
        btn_editar.setIconSize(QSize(18, 18))
        btn_editar.setFlat(True)
        btn_editar.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #00ff00;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #00ff00;
                border: 1px solid #00ff00;
            }
            QPushButton:pressed {
                background-color: #00cc00;
                border: 1px solid #00cc00;
            }
        """)
        btn_editar.clicked.connect(self.on_editar)
        layout_botoes.addWidget(btn_editar)
        
        # Stretch para separar botões
        layout_botoes.addStretch()
        
        # Botão Deletar
        btn_deletar = QPushButton()
        btn_deletar.setMaximumWidth(35)
        btn_deletar.setMinimumHeight(30)
        btn_deletar.setToolTip("Deletar janela")
        btn_deletar.setIcon(criar_icone_deletar())
        btn_deletar.setIconSize(QSize(18, 18))
        btn_deletar.setFlat(True)
        btn_deletar.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 1px solid #ff0000;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #ff0000;
                border: 1px solid #ff0000;
            }
            QPushButton:pressed {
                background-color: #cc0000;
                border: 1px solid #cc0000;
            }
        """)
        btn_deletar.clicked.connect(self.on_deletar)
        layout_botoes.addWidget(btn_deletar)
        
        layout.addLayout(layout_botoes)
        
        # Armazenar botões para futuro acesso
        self.btn_editar = btn_editar
        self.btn_deletar = btn_deletar
    
    def _animar_cor_neon(self):
        """Anima a cor do card em RGB suave"""
        self.cor_neon = (self.cor_neon + 1) % 360
        
        # Criar variações de cor
        if self.cor_neon < 60:
            # Magenta para Ciano
            r = 255
            g = int((self.cor_neon / 60) * 255)
            b = 255
        elif self.cor_neon < 120:
            # Ciano para Verde
            r = int((1 - (self.cor_neon - 60) / 60) * 255)
            g = 255
            b = int((1 - (self.cor_neon - 60) / 60) * 255)
        elif self.cor_neon < 180:
            # Verde para Amarelo
            r = int(((self.cor_neon - 120) / 60) * 255)
            g = 255
            b = 0
        elif self.cor_neon < 240:
            # Amarelo para Magenta
            r = 255
            g = int((1 - (self.cor_neon - 180) / 60) * 255)
            b = 0
        elif self.cor_neon < 300:
            # Magenta para Azul
            r = 255
            g = 0
            b = int(((self.cor_neon - 240) / 60) * 255)
        else:
            # Azul para Magenta
            r = int((1 - (self.cor_neon - 300) / 60) * 255)
            g = 0
            b = 255
        
        cor_hex = f"#{int(r):02x}{int(g):02x}{int(b):02x}"
        self.setStyleSheet(f"""
            CartaJanela {{
                background-color: #1a1a1a;
                border: 2px solid {cor_hex};
                border-radius: 8px;
                padding: 8px;
            }}
            CartaJanela:hover {{
                background-color: #2a2a2a;
                border: 3px solid {cor_hex};
            }}
        """)
    
    def _carregar_preview(self):
        """Carrega prévia da imagem template ou imagem"""
        try:
            # Tentar carregar template primeiro
            caminho = self.cfg.get("caminho_template")
            if not caminho or not os.path.exists(caminho):
                # Se template não existe, tentar imagem
                caminho = self.cfg.get("caminho_imagem")
            
            if caminho and os.path.exists(caminho):
                img = Image.open(caminho).convert("RGBA")
                # Redimensionar para caber no preview (máximo 120x120)
                img.thumbnail((120, 120), Image.LANCZOS)
                
                # Converter para QPixmap
                data = img.tobytes("raw", "RGBA")
                from PySide6.QtGui import QImage
                qimg = QImage(data, img.width, img.height, QImage.Format_RGBA8888)
                pixmap = QPixmap.fromImage(qimg)
                
                self.img_preview.setPixmap(pixmap)
            else:
                self.img_preview.setText("Sem\nimagem")
                self.img_preview.setStyleSheet("""
                    background-color: #0a0a0a;
                    border: 1px dashed #ff00ff;
                    border-radius: 4px;
                    color: #ff00ff;
                """)
        except Exception as e:
            self.img_preview.setText("Erro")
            self.img_preview.setStyleSheet("""
                background-color: #0a0a0a;
                border: 1px dashed #ff0000;
                border-radius: 4px;
                color: #ff0000;
            """)
    
    def on_editar(self):
        """Emitir sinal para editar"""
        # Será capturado pelo painel
        pass
    
    def on_deletar(self):
        """Emitir sinal para deletar"""
        # Será capturado pelo painel
        pass


class PainelControle(QDialog):
    """Janela principal do painel de controle"""
    
    def __init__(self, app_manager=None, parent=None):
        super().__init__(parent)
        self.app_manager = app_manager
        
        self.setWindowTitle("Painel de Controle - Vaporwave Windows")
        self.setMinimumSize(900, 600)
        self.setMaximumSize(1400, 900)
        
        # Inicializar animação de cores
        self.cor_rgb = 0
        self.timer_rgb = QTimer(self)
        self.timer_rgb.timeout.connect(self._atualizar_cor_rgb)
        self.timer_rgb.start(50)
        
        # Estilo escuro vaporwave
        self._atualizar_estilo()
        
        # Layout principal
        layout_main = QVBoxLayout(self)
        layout_main.setSpacing(12)
        layout_main.setContentsMargins(16, 16, 16, 16)
        
        # ===== Header =====
        layout_header = QHBoxLayout()
        
        lbl_titulo = QLabel("Gerenciador de Janelas")
        font_titulo = QFont()
        font_titulo.setPointSize(14)
        font_titulo.setBold(True)
        lbl_titulo.setFont(font_titulo)
        lbl_titulo.setStyleSheet("color: #ff00ff;")
        layout_header.addWidget(lbl_titulo)
        
        layout_header.addStretch()
        
        # Botão adicionar nova janela com animação RGB
        self.btn_nova = QPushButton()
        self.btn_nova.setMinimumHeight(35)
        self.btn_nova.setMaximumWidth(40)
        self.btn_nova.setIcon(criar_icone_nova_animado())
        self.btn_nova.setIconSize(QSize(20, 20))
        self.btn_nova.setToolTip("Nova Janela")
        self.btn_nova.setFlat(True)
        self.btn_nova.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 2px solid #00ff00;
                border-radius: 6px;
                padding: 3px;
            }
            QPushButton:hover {
                background-color: #00ff00;
                border: 2px solid #00ff00;
            }
            QPushButton:pressed {
                background-color: #00cc00;
                border: 2px solid #00cc00;
            }
        """)
        self.btn_nova.clicked.connect(self.on_nova_janela)
        layout_header.addWidget(self.btn_nova)
        
        layout_main.addLayout(layout_header)
        
        # ===== Área de scroll com cards =====
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #0a0a0a;
                border: 2px solid #ff00ff;
                border-radius: 4px;
            }
            QScrollBar:vertical {
                background-color: #1a1a1a;
                width: 12px;
            }
            QScrollBar::handle:vertical {
                background-color: #ff00ff;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #ff33ff;
            }
        """)
        
        # Container para cards em grid
        self.container_cards = QWidget()
        self.grid_layout = QGridLayout(self.container_cards)
        self.grid_layout.setSpacing(12)
        self.grid_layout.setContentsMargins(8, 8, 8, 8)
        
        self.scroll_area.setWidget(self.container_cards)
        layout_main.addWidget(self.scroll_area)
        
        # Armazenar cards para futuro acesso
        self.cards = {}
        
        # Carregar janelas
        self._carregar_janelas()
    
    def _atualizar_cor_rgb(self):
        """Atualiza as cores RGB animadas suavemente"""
        self.cor_rgb = (self.cor_rgb + 1) % 360
        self._atualizar_estilo()
        
        # Animar botão Nova Janela também
        if self.cor_rgb < 60:
            r = 0
            g = 255
            b = int((self.cor_rgb / 60) * 255)
        elif self.cor_rgb < 120:
            r = 0
            g = int((1 - (self.cor_rgb - 60) / 60) * 255)
            b = 255
        elif self.cor_rgb < 180:
            r = int(((self.cor_rgb - 120) / 60) * 255)
            g = 0
            b = 255
        elif self.cor_rgb < 240:
            r = 255
            g = 0
            b = int((1 - (self.cor_rgb - 180) / 60) * 255)
        elif self.cor_rgb < 300:
            r = 255
            g = int(((self.cor_rgb - 240) / 60) * 255)
            b = 0
        else:
            r = int((1 - (self.cor_rgb - 300) / 60) * 255)
            g = 255
            b = 0
        
        cor_hex = f"#{int(r):02x}{int(g):02x}{int(b):02x}"
        self.btn_nova.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 2px solid {cor_hex};
                border-radius: 6px;
                padding: 3px;
            }}
            QPushButton:hover {{
                background-color: {cor_hex};
                border: 2px solid {cor_hex};
            }}
            QPushButton:pressed {{
                background-color: {cor_hex};
                border: 2px solid {cor_hex};
            }}
        """)
    
    def _atualizar_estilo(self):
        """Atualiza o estilo principal com cores neon animadas"""
        # Calcular cor neon para bordas
        if self.cor_rgb < 60:
            r = 255
            g = 0
            b = int((self.cor_rgb / 60) * 255)
        elif self.cor_rgb < 120:
            r = int((1 - (self.cor_rgb - 60) / 60) * 255)
            g = 0
            b = 255
        elif self.cor_rgb < 180:
            r = 0
            g = int(((self.cor_rgb - 120) / 60) * 255)
            b = 255
        elif self.cor_rgb < 240:
            r = 0
            g = 255
            b = int((1 - (self.cor_rgb - 180) / 60) * 255)
        elif self.cor_rgb < 300:
            r = int(((self.cor_rgb - 240) / 60) * 255)
            g = 255
            b = 0
        else:
            r = 255
            g = int((1 - (self.cor_rgb - 300) / 60) * 255)
            b = 0
        
        cor_neon = f"#{int(r):02x}{int(g):02x}{int(b):02x}"
        
        self.setStyleSheet(f"""
            PainelControle {{
                background-color: #0a0a0a;
            }}
            QScrollArea {{
                background-color: #0a0a0a;
                border: 2px solid {cor_neon};
                border-radius: 4px;
            }}
            QScrollBar:vertical {{
                background-color: #1a1a1a;
                width: 12px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {cor_neon};
                border-radius: 6px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: #ffffff;
            }}
        """)
    
    def _carregar_janelas(self):
        """Carrega todas as janelas do config e cria cards"""
        if not self.app_manager:
            return
        
        # Limpar cards antigos - verificar se é widget antes de remover
        for i in reversed(range(self.grid_layout.count())):
            item = self.grid_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    widget.setParent(None)
                else:
                    # Se é um spacer ou outro item, remover diretamente
                    self.grid_layout.removeItem(item)
        
        self.cards.clear()
        
        cfg = self.app_manager.cfg
        janelas = cfg.get("janelas", {})
        
        if not janelas:
            lbl_vazio = QLabel("Nenhuma janela criada ainda.\nClique em '+ Nova Janela' para começar.")
            lbl_vazio.setAlignment(Qt.AlignCenter)
            lbl_vazio.setStyleSheet("color: #ff00ff; font-size: 14px;")
            self.grid_layout.addWidget(lbl_vazio, 0, 0)
            return
        
        # Ordenar janelas por nome
        janelas_ordenadas = sorted(janelas.items())
        
        # Criar cards em grid
        row, col = 0, 0
        for nome, cfg_janela in janelas_ordenadas:
            card = CartaJanela(nome, cfg_janela, self)
            
            # Conectar botões
            card.btn_editar.clicked.connect(lambda checked=False, n=nome: self._editar_janela(n))
            card.btn_deletar.clicked.connect(lambda checked=False, n=nome: self._deletar_janela(n))
            
            # Conectar clique na imagem/card para editar
            card.img_preview.mousePressEvent = lambda event, n=nome: self._editar_janela(n)
            
            self.grid_layout.addWidget(card, row, col)
            self.cards[nome] = card
            
            col += 1
            if col >= 4:  # 4 colunas
                col = 0
                row += 1
        
        # Adicionar spacer vertical para preencher espaço vazio
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.grid_layout.addItem(spacer, row + 1, 0)
    
    def _editar_janela(self, nome):
        """Abre diálogo de edição de janela"""
        if not self.app_manager:
            return
        
        janela = self.app_manager.janelas.get(nome)
        if janela:
            self.app_manager.editar_via_dialog(janela)
            # Atualizar cards após edição
            QTimer.singleShot(100, self._carregar_janelas)
    
    def _deletar_janela(self, nome):
        """Deleta janela com confirmação"""
        if not self.app_manager:
            return
        
        # Confirmar com usuário
        msg = QMessageBox()
        msg.setWindowTitle("Confirmar Exclusão")
        msg.setText(f"Deseja excluir a janela '{nome}'?\n\nEsta ação não pode ser desfeita.")
        msg.setIcon(QMessageBox.Warning)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.button(QMessageBox.Yes).setText("Excluir")
        msg.button(QMessageBox.No).setText("Cancelar")
        
        if msg.exec() == QMessageBox.Yes:
            self.app_manager.excluir_janela(nome)
            self._carregar_janelas()
    
    def on_nova_janela(self):
        """Abre diálogo para criar nova janela"""
        if not self.app_manager:
            return
        
        self.app_manager.criar_via_dialog()
        # Atualizar cards após criação
        QTimer.singleShot(100, self._carregar_janelas)
    
    def recarregar(self):
        """Recarrega a lista de janelas"""
        self._carregar_janelas()
    
    def closeEvent(self, event):
        """Para as animações ao fechar"""
        self.timer_rgb.stop()
        for card in self.cards.values():
            if hasattr(card, 'timer_neon'):
                card.timer_neon.stop()
        super().closeEvent(event)
