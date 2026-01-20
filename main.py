# vaporwave_window_manager.py
import sys, os, json, random, logging
from datetime import datetime
import numpy as np
from PIL import Image
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QSystemTrayIcon, QMenu, QMessageBox,
    QGraphicsOpacityEffect, QFileDialog, QDialog, QFormLayout, QLineEdit,
    QHBoxLayout, QPushButton, QCheckBox, QSpinBox, QComboBox, QStyle
)
from PySide6.QtGui import QPixmap, QImage, QMovie, QIcon, QAction, QKeySequence, QPainter, QPen, QColor, QPolygon
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect, QPoint, QPointF
from animacoes import executar_animacao

CONFIG_PATH = "config.json"
LOG_PATH = "app.log"

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(LOG_PATH, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ---------------- util ----------------

def carregar_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"janelas": {}}

def salvar_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4, ensure_ascii=False)

def detectar_area_verde(img_pil):
    arr = np.array(img_pil.convert("RGB"))
    mask = (arr[:, :, 1] > 200) & (arr[:, :, 0] < 100) & (arr[:, :, 2] < 100)
    coords = np.argwhere(mask)
    if coords.size == 0:
        return None
    y0, x0 = coords.min(axis=0)
    y1, x1 = coords.max(axis=0)
    return (x0, y0, x1, y1)  # left, top, right, bottom

def pil_to_qpixmap(pil_img):
    data = pil_img.tobytes("raw", "RGBA")
    qimg = QImage(data, pil_img.width, pil_img.height, QImage.Format_RGBA8888)
    return QPixmap.fromImage(qimg)

def center_on_primary(widget):
    screen = QApplication.primaryScreen().availableGeometry()
    x = screen.x() + (screen.width() - widget.width()) // 2
    y = screen.y() + (screen.height() - widget.height()) // 2
    widget.move(x, y)

def criar_icone_branco(tipo, tamanho=16):
    """Cria ícones minimalistas brancos."""
    pixmap = QPixmap(tamanho, tamanho)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    pen = QPen(QColor(255, 255, 255), 2)
    painter.setPen(pen)
    
    margin = 3
    
    if tipo == "novo":
        # Ícone de +
        center = tamanho // 2
        painter.drawLine(center, margin, center, tamanho - margin)
        painter.drawLine(margin, center, tamanho - margin, center)
    
    elif tipo == "editar":
        # Ícone de lápis/editar
        painter.drawLine(tamanho - margin - 2, margin + 2, margin + 2, tamanho - margin - 2)
        painter.drawLine(margin, tamanho - margin, margin + 4, tamanho - margin)
    
    elif tipo == "excluir":
        # Ícone de X
        painter.drawLine(margin, margin, tamanho - margin, tamanho - margin)
        painter.drawLine(tamanho - margin, margin, margin, tamanho - margin)
    
    elif tipo == "mover":
        # Ícone de setas (cadeado/movimento)
        painter.drawRect(margin + 2, margin + 4, tamanho - 2*margin - 4, tamanho - 2*margin - 6)
        painter.drawLine(margin + 4, margin + 4, margin + 4, margin + 2)
        painter.drawLine(tamanho - margin - 4, margin + 4, tamanho - margin - 4, margin + 2)
    
    elif tipo == "ajuda":
        # Ícone de ?
        painter.drawArc(margin + 1, margin, tamanho - 2*margin - 2, tamanho//2, 0, 180 * 16)
        painter.drawPoint(tamanho // 2, tamanho - margin - 2)
    
    elif tipo == "sair":
        # Ícone de porta/saída
        painter.drawRect(margin, margin + 2, tamanho - 2*margin, tamanho - 2*margin - 4)
        painter.drawLine(tamanho // 2, margin + 5, tamanho - margin - 3, tamanho // 2)
        painter.drawLine(tamanho // 2, tamanho - margin - 3, tamanho - margin - 3, tamanho // 2)
    
    elif tipo == "sobre":
        # Ícone de i (informação)
        painter.drawPoint(tamanho // 2, margin + 2)
        painter.drawLine(tamanho // 2, margin + 5, tamanho // 2, tamanho - margin - 2)
    
    painter.end()
    return QIcon(pixmap)

# ------------- diálogo de criação/edição -------------

class WindowConfigDialog(QDialog):
    def __init__(self, parent=None, dados=None, titulo="Configurar janela"):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.setModal(True)
        self.setMinimumWidth(520)

        self.ed_template = QLineEdit()
        btn_template = QPushButton("Selecionar...")
        btn_template.clicked.connect(self.sel_template)

        self.ed_imagem = QLineEdit()
        btn_imagem = QPushButton("Selecionar...")
        btn_imagem.clicked.connect(self.sel_imagem)

        self.ed_pasta = QLineEdit()
        btn_pasta = QPushButton("Selecionar...")
        btn_pasta.clicked.connect(self.sel_pasta)

        self.chk_loop = QCheckBox("Usar pasta em loop")
        self.spin_intervalo = QSpinBox()
        self.spin_intervalo.setRange(1, 3600)
        self.spin_intervalo.setValue(5)

        self.cmb_ordem = QComboBox()
        self.cmb_ordem.addItems(["alfabetica", "aleatoria"])

        self.cmb_animacao = QComboBox()
        self.cmb_animacao.addItems(["fade", "slide", "wipe_top", "wipe_bottom", "wipe_left", "wipe_right"])

        self.chk_transp = QCheckBox("Verde transparente")
        self.chk_prop = QCheckBox("Manter proporção")

        form = QFormLayout()
        row_t = QHBoxLayout(); row_t.addWidget(self.ed_template); row_t.addWidget(btn_template)
        row_i = QHBoxLayout(); row_i.addWidget(self.ed_imagem); row_i.addWidget(btn_imagem)
        row_p = QHBoxLayout(); row_p.addWidget(self.ed_pasta);   row_p.addWidget(btn_pasta)

        form.addRow("Template:", row_t)
        form.addRow("Imagem única:", row_i)
        form.addRow("Pasta de imagens:", row_p)
        form.addRow(self.chk_loop)
        form.addRow("Intervalo (s):", self.spin_intervalo)
        form.addRow("Ordem:", self.cmb_ordem)
        form.addRow("Animação:", self.cmb_animacao)
        form.addRow(self.chk_transp)
        form.addRow(self.chk_prop)

        btn_ok = QPushButton("OK"); btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Cancelar"); btn_cancel.clicked.connect(self.reject)
        row_b = QHBoxLayout(); row_b.addStretch(); row_b.addWidget(btn_ok); row_b.addWidget(btn_cancel)

        form.addRow(row_b)
        self.setLayout(form)

        if dados:
            self.ed_template.setText(dados.get("caminho_template", ""))
            self.ed_imagem.setText(dados.get("caminho_imagem", ""))
            self.ed_pasta.setText(dados.get("pasta_imagens", ""))
            self.chk_loop.setChecked(dados.get("modo_loop", False))
            self.spin_intervalo.setValue(int(dados.get("intervalo", 5)))
            self.cmb_ordem.setCurrentText(dados.get("ordem", "alfabetica"))
            self.cmb_animacao.setCurrentText(dados.get("tipo_animacao", "fade"))
            self.chk_transp.setChecked(dados.get("transparente", True))
            self.chk_prop.setChecked(dados.get("manter_proporcao", False))

    def sel_template(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Escolher template", "", "Imagens (*.png *.jpg *.jpeg *.bmp)")
        if fn: self.ed_template.setText(fn)

    def sel_imagem(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Escolher imagem", "", "Imagens/GIF (*.png *.jpg *.jpeg *.bmp *.gif)")
        if fn: self.ed_imagem.setText(fn)

    def sel_pasta(self):
        dn = QFileDialog.getExistingDirectory(self, "Escolher pasta de imagens", "")
        if dn: self.ed_pasta.setText(dn)

    def dados(self):
        return {
            "caminho_template": self.ed_template.text().strip(),
            "caminho_imagem": self.ed_imagem.text().strip(),
            "pasta_imagens": self.ed_pasta.text().strip() or None,
            "modo_loop": self.chk_loop.isChecked(),
            "intervalo": int(self.spin_intervalo.value()),
            "ordem": self.cmb_ordem.currentText(),
            "tipo_animacao": self.cmb_animacao.currentText(),
            "transparente": self.chk_transp.isChecked(),
            "manter_proporcao": self.chk_prop.isChecked(),
        }

# ------------- janela individual -------------

class JanelaComChroma(QWidget):
    def __init__(self, nome, cfg):
        super().__init__()
        self.nome = nome
        self.setWindowTitle(nome)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowOpacity(0.99)

        # parâmetros
        self.caminho_template = cfg["caminho_template"]
        self.caminho_imagem   = cfg.get("caminho_imagem") or ""
        self.pasta_imagens    = cfg.get("pasta_imagens")
        self.modo_loop        = bool(cfg.get("modo_loop", False))
        self.intervalo        = int(cfg.get("intervalo", 5))
        self.ordem            = cfg.get("ordem", "alfabetica")
        self.tipo_animacao    = cfg.get("tipo_animacao", "fade")
        self.transparente     = bool(cfg.get("transparente", True))
        self.manter_proporcao = bool(cfg.get("manter_proporcao", False))

        self.passo = 10
        self.offset_x = 0
        self.offset_y = 0
        self.primeira_troca = True
        self.z_order = int(cfg.get("z_order", 0))  # Ordem de camada

        # mantém cópia base do template para evitar perda de qualidade
        self.template_base = Image.open(self.caminho_template).convert("RGBA")
        self.template = self.template_base.copy()
        self.area_chroma = detectar_area_verde(self.template_base)
        if not self.area_chroma:
            raise ValueError(f"[{self.nome}] Área verde não detectada no template.")

        # camadas: imagem por baixo, template por cima
        self.label_overlay = QLabel(self)
        self.label_overlay.setAttribute(Qt.WA_TranslucentBackground, True)
        self.opacity_effect = QGraphicsOpacityEffect(self.label_overlay)
        self.label_overlay.setGraphicsEffect(self.opacity_effect)

        self.label_template = QLabel(self)
        self.label_template.setAttribute(Qt.WA_TranslucentBackground, True)

        self.movie = None
        self.current_frame = None

        # render inicial
        self._render_template()
        if self.caminho_imagem and os.path.exists(self.caminho_imagem):
            self._carregar_fonte(self.caminho_imagem)
        self._render_overlay()
        self.label_template.raise_()

        # slideshow timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._trocar_imagem_timer)

        # tamanho e posição
        largura_cfg = int(cfg.get("largura", self.template.width))
        altura_cfg  = int(cfg.get("altura", self.template.height))
        self.resize(largura_cfg, altura_cfg)
        self._aplicar_tamanho(largura_cfg, altura_cfg)

        x = int(cfg.get("pos_x", 0))
        y = int(cfg.get("pos_y", 0))
        if x == 0 and y == 0:
            center_on_primary(self)
        else:
            self.move(x, y)

        # atalhos
        self.addAction(self._mk_action("Novo (Ctrl+N)", self.criar_nova, QKeySequence("Ctrl+N")))
        self.addAction(self._mk_action("Editar (Ctrl+E)", self.editar_config, QKeySequence("Ctrl+E")))
        self.addAction(self._mk_action("Excluir (Ctrl+Del)", self.excluir, QKeySequence("Ctrl+Delete")))

        if self.modo_loop:
            self.iniciar_slideshow()

    # ======= util =======
    def _mk_action(self, text, slot, seq=None):
        act = QAction(text, self)
        if seq:
            act.setShortcut(seq)
        act.triggered.connect(slot)
        return act

    # ======= renderização =======
    def _aplicar_tamanho(self, largura, altura):
        """Redimensiona template sem perda de qualidade."""
        self.template = self.template_base.copy().resize((largura, altura), Image.LANCZOS)
        self.area_chroma = detectar_area_verde(self.template)
        self._render_template()
        self._render_overlay()

    def _render_template(self):
        base = self.template.copy()
        if self.transparente:
            arr = np.array(base)
            mask = (arr[:, :, 1] > 200) & (arr[:, :, 0] < 100) & (arr[:, :, 2] < 100)
            arr[mask] = [0, 0, 0, 0]
            base = Image.fromarray(arr)
        pm = pil_to_qpixmap(base)
        self.label_template.setPixmap(pm)
        self.label_template.setGeometry(0, 0, base.width, base.height)
        x0, y0, x1, y1 = self.area_chroma
        self.label_overlay.setGeometry(x0, y0, x1 - x0, y1 - y0)
        self.label_template.raise_()

    def _carregar_fonte(self, caminho):
        if self.movie:
            self.movie.frameChanged.disconnect(self._on_gif_frame)
            self.movie.stop()
            self.movie = None
        self.caminho_imagem = caminho
        if caminho.lower().endswith(".gif"):
            self.movie = QMovie(caminho)
            self.movie.frameChanged.connect(self._on_gif_frame)
            self.movie.start()
        else:
            self.current_frame = Image.open(caminho).convert("RGBA")
            self._render_overlay()

    def _on_gif_frame(self, _):
        img = self.movie.currentImage()
        qimg = img.convertToFormat(QImage.Format_RGBA8888)
        w, h = qimg.width(), qimg.height()
        arr = np.frombuffer(qimg.bits().tobytes(), dtype=np.uint8).reshape((h, w, 4))
        self.current_frame = Image.fromarray(arr)
        self._render_overlay()

    def _render_overlay(self):
        if self.current_frame is None:
            self.label_overlay.clear()
            return

        x0, y0, x1, y1 = self.area_chroma
        cw, ch = x1 - x0, y1 - y0
        img = self.current_frame.copy()

        if self.manter_proporcao:
            img.thumbnail((cw, ch), Image.LANCZOS)
        else:
            img = img.resize((cw, ch), Image.LANCZOS)

        img_w, img_h = img.size
        px = min(max((cw - img_w)//2 + self.offset_x, 0), cw - img_w)
        py = min(max((ch - img_h)//2 + self.offset_y, 0), ch - img_h)

        # desenha dentro da área e mantém template acima
        # cria imagem transparente
        canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        canvas.alpha_composite(img, (px, py))

        # aplica máscara do template (limita área verde)
        template_crop = self.template.crop((x0, y0, x1, y1))
        mask_arr = np.array(template_crop.convert("RGB"))
        mask = (mask_arr[:, :, 1] > 200) & (mask_arr[:, :, 0] < 100) & (mask_arr[:, :, 2] < 100)
        mask_img = Image.fromarray((mask * 255).astype(np.uint8))

        # aplica máscara como canal alfa
        canvas.putalpha(mask_img)

        self.label_overlay.setPixmap(pil_to_qpixmap(canvas))
        self.label_template.raise_()

    # ======= slideshow =======
    def iniciar_slideshow(self):
        if not self.pasta_imagens or not os.path.isdir(self.pasta_imagens):
            return
        exts = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp")
        lista = [os.path.join(self.pasta_imagens, f)
                 for f in os.listdir(self.pasta_imagens)
                 if f.lower().endswith(exts)]
        if not lista:
            return
        if self.ordem == "aleatoria":
            random.shuffle(lista)
        else:
            lista.sort()
        self.lista_imagens = lista
        self.index_imagem = 0
        self.primeira_troca = True
        self._trocar_para(lista[self.index_imagem], usar_fade=False)
        self.timer.start(self.intervalo * 1000)

    def _trocar_imagem_timer(self):
        if not hasattr(self, "lista_imagens") or not self.lista_imagens:
            return
        self.index_imagem += 1
        if self.index_imagem >= len(self.lista_imagens):
            if self.ordem == "aleatoria":
                random.shuffle(self.lista_imagens)
            else:
                self.lista_imagens.sort()
            self.index_imagem = 0
        self._trocar_para(self.lista_imagens[self.index_imagem], usar_fade=not self.primeira_troca)
        self.primeira_troca = False

    def _trocar_para(self, caminho, usar_fade=True):
        if not usar_fade:
            self._carregar_fonte(caminho)
            return
        
        # Usar módulo de animações externo
        executar_animacao(self.tipo_animacao, self, caminho)
    
    # ======= redimensionamento =======
    def _redimensionar(self, fator):
        """Ajusta tamanho da janela mantendo qualidade."""
        if fator <= 0:
            return
        new_w = max(50, int(self.width() * fator))
        new_h = max(50, int(self.height() * fator))
        self.resize(new_w, new_h)
        self._aplicar_tamanho(new_w, new_h)

    # ======= eventos =======
    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton:
            # Se janelas estão fixadas, restaurar ordem de camadas após clique
            if not AppManager.instance().janelas_moviveis:
                # Agendar para restaurar z-order após o evento de clique ser processado
                QTimer.singleShot(0, AppManager.instance().restaurar_z_order)
            else:
                # Se janelas são móveis, trazer para frente
                AppManager.instance().trazer_para_frente(self)
                self._drag_off = ev.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, ev):
        if ev.buttons() & Qt.LeftButton and AppManager.instance().janelas_moviveis:
            self.move(ev.globalPosition().toPoint() - self._drag_off)

    def keyPressEvent(self, ev):
        k = ev.key()
        if   k == Qt.Key_Up:    self.offset_y -= self.passo
        elif k == Qt.Key_Down:  self.offset_y += self.passo
        elif k == Qt.Key_Left:  self.offset_x -= self.passo
        elif k == Qt.Key_Right: self.offset_x += self.passo
        elif k == Qt.Key_T:     self.transparente = not self.transparente; self._render_template()
        elif k == Qt.Key_R:     self.manter_proporcao = not self.manter_proporcao
        elif k in (Qt.Key_Plus, Qt.Key_Equal):      self._redimensionar(1.1)
        elif k in (Qt.Key_Minus, Qt.Key_Underscore):self._redimensionar(0.9)
        elif ev.matches(QKeySequence.New):          self.criar_nova()
        elif ev.matches(QKeySequence("Ctrl+E")):    self.editar_config()
        elif ev.matches(QKeySequence("Ctrl+Delete")): self.excluir()
        self._render_overlay()

    def moveEvent(self, _):
        AppManager.instance().salvar_estado(self)

    def resizeEvent(self, _):
        AppManager.instance().salvar_estado(self)

    def closeEvent(self, e):
        AppManager.instance().salvar_estado(self)
        e.accept()

    # ======= persistência =======
    def to_dict(self):
        return {
            "caminho_template": self.caminho_template,
            "caminho_imagem": self.caminho_imagem,
            "pasta_imagens": self.pasta_imagens,
            "modo_loop": self.modo_loop,
            "intervalo": self.intervalo,
            "ordem": self.ordem,
            "tipo_animacao": self.tipo_animacao,
            "transparente": self.transparente,
            "manter_proporcao": self.manter_proporcao,
            "pos_x": self.x(),
            "pos_y": self.y(),
            "largura": self.width(),
            "altura": self.height(),
            "z_order": getattr(self, 'z_order', 0)
        }

    # ======= integração com AppManager =======
    def criar_nova(self):
        AppManager.instance().criar_via_dialog(base=self)

    def editar_config(self):
        AppManager.instance().editar_via_dialog(self)

    def excluir(self):
        AppManager.instance().excluir_janela(self.nome)


# ------------- gerenciador global + tray -------------

class AppManager:
    _inst = None
    def __init__(self, app):
        self.app = app
        self.cfg = carregar_config()
        self.janelas = {}  # nome -> JanelaComChroma
        self.janelas_moviveis = self.cfg.get("janelas_moviveis", False)  # Global: padrão fixado
        AppManager._inst = self

        # tray
        icon_path = os.path.join(os.path.dirname(__file__), "vaporwave.ico")
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
        self.tray = QSystemTrayIcon(icon)
        self.tray.setToolTip("vaporwave_window")
        self.menu = QMenu()

        self.act_new = QAction("Nova Janela", self.menu); self.act_new.triggered.connect(self.criar_via_dialog)
        self.act_edit = QAction("Editar Janela Atual", self.menu); self.act_edit.triggered.connect(self.editar_atual)
        self.act_del = QAction("Excluir Janela Atual", self.menu); self.act_del.triggered.connect(self.excluir_atual)
        self.act_move = QAction("Fixar Janelas", self.menu); self.act_move.triggered.connect(self.toggle_move_atual)
        self.act_help = QAction("Ajuda / Atalhos", self.menu); self.act_help.triggered.connect(self.show_help)
        self.act_about = QAction("Sobre", self.menu); self.act_about.triggered.connect(self.show_about)
        self.act_quit = QAction("Sair", self.menu); self.act_quit.triggered.connect(self.sair)

        self.menu.addAction(self.act_new)
        self.menu.addAction(self.act_edit)
        self.menu.addAction(self.act_del)
        self.menu.addAction(self.act_move)
        self.menu.addSeparator()
        self.menu.addAction(self.act_help)
        self.menu.addAction(self.act_about)
        self.menu.addSeparator()
        self.menu.addAction(self.act_quit)

        self.tray.setContextMenu(self.menu)
        self.tray.show()

        # Definir ícones minimalistas brancos para as ações
        self.act_new.setIcon(criar_icone_branco("novo"))
        self.act_edit.setIcon(criar_icone_branco("editar"))
        self.act_del.setIcon(criar_icone_branco("excluir"))
        self.act_move.setIcon(criar_icone_branco("mover"))
        self.act_help.setIcon(criar_icone_branco("ajuda"))
        self.act_about.setIcon(criar_icone_branco("sobre"))
        self.act_quit.setIcon(criar_icone_branco("sair"))

        # Definir texto inicial baseado no estado global
        self.act_move.setText("Fixar Janelas" if self.janelas_moviveis else "Desfixar Janelas")

        self.carregar_todas()

    @classmethod
    def instance(cls): return cls._inst

    def carregar_todas(self):
        if not self.cfg.get("janelas"):
            # cria padrão se vazio
            dlg = WindowConfigDialog(None, titulo="Criar primeira janela")
            if dlg.exec() == QDialog.Accepted:
                dados = dlg.dados()
                # dimensão pelo template
                if not os.path.exists(dados["caminho_template"]):
                    QMessageBox.critical(None, "Erro", "Template inválido.")
                    return  # não encerrar, apenas retornar
                img = Image.open(dados["caminho_template"]).convert("RGBA")
                nome = self._proximo_nome()
                base = {
                    **dados,
                    "pos_x": 0, "pos_y": 0,
                    "largura": img.width, "altura": img.height,
                    "z_order": 0
                }
                self.cfg["janelas"] = {nome: base}
                salvar_config(self.cfg)
            else:
                return  # não encerrar, usuário pode criar depois pelo tray

        # Ordenar janelas por z_order para carregar na ordem correta
        janelas_ordenadas = sorted(
            self.cfg["janelas"].items(),
            key=lambda item: item[1].get("z_order", 0)
        )
        
        janelas_carregadas = 0
        janelas_falhadas = []
        
        for nome, jcfg in janelas_ordenadas:
            try:
                self._instanciar(nome, jcfg)
                janelas_carregadas += 1
            except Exception as e:
                janelas_falhadas.append((nome, jcfg, str(e)))
                logger.warning(f"Falha ao carregar {nome}: {e}")
        
        # Processar janelas falhadas com opções de Remover ou Editar
        for nome, jcfg, erro in janelas_falhadas:
            msg = f"Erro ao carregar '{nome}':\n\n{erro}\n\nDeseja editar ou remover esta janela?"
            
            # Dialog com 3 botões customizados
            msgbox = QMessageBox()
            msgbox.setWindowTitle(f"Janela com Problema - {nome}")
            msgbox.setText(msg)
            msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            msgbox.button(QMessageBox.Yes).setText("Editar")
            msgbox.button(QMessageBox.No).setText("Remover")
            msgbox.button(QMessageBox.Cancel).setText("Ignorar")
            msgbox.setIcon(QMessageBox.Warning)
            reply = msgbox.exec()
            
            if reply == QMessageBox.Yes:  # Editar
                # Abrir diálogo de edição
                dlg = WindowConfigDialog(None, dados=jcfg, titulo=f"Editar {nome}")
                if dlg.exec() == QDialog.Accepted:
                    dados = dlg.dados()
                    # Validar template
                    if not os.path.exists(dados["caminho_template"]):
                        QMessageBox.critical(None, "Erro", "Template inválido.")
                        continue
                    # Atualizar config com dados editados
                    self.cfg["janelas"][nome] = {
                        **dados,
                        "pos_x": jcfg.get("pos_x", 0),
                        "pos_y": jcfg.get("pos_y", 0),
                        "z_order": jcfg.get("z_order", 0)
                    }
                    # Tentar carregar a janela corrigida
                    try:
                        self._instanciar(nome, self.cfg["janelas"][nome])
                        janelas_carregadas += 1
                        logger.info(f"{nome} foi editada e carregada com sucesso")
                    except Exception as e2:
                        logger.error(f"Erro ao carregar {nome} após edição: {e2}")
                        QMessageBox.critical(None, "Erro", f"Ainda há problemas ao carregar {nome}:\n{e2}")
                        # Remover se falhou novamente
                        if nome in self.cfg["janelas"]:
                            del self.cfg["janelas"][nome]
            elif reply == QMessageBox.No:  # Remover
                # Remover janela
                if nome in self.cfg["janelas"]:
                    del self.cfg["janelas"][nome]
                    logger.info(f"{nome} foi removida do config")
            else:  # Cancel - Pular
                # Manter na lista de falhadas
                logger.info(f"{nome} não foi removida, será ignorada")
        
        # Salvar config atualizado
        salvar_config(self.cfg)
        logger.info(f"Aplicação iniciada com {janelas_carregadas} janela(s) carregada(s) e {len(janelas_falhadas)} janela(s) processada(s)")

    def _instanciar(self, nome, jcfg):
        w = JanelaComChroma(nome, jcfg)
        self.janelas[nome] = w
        w.show()

    def _proximo_nome(self):
        i = 1
        while True:
            n = f"janela{i}"
            if n not in self.cfg.get("janelas", {}): return n
            i += 1

    def trazer_para_frente(self, janela: JanelaComChroma):
        """Traz janela para frente e atualiza z_order somente se janelas_moviveis for True.
        
        Se janelas_moviveis é False (fixadas), a janela não muda de camada visualmente.
        """
        # Se janelas estão fixadas, não fazer nada - preserva ordem de camadas
        if not self.janelas_moviveis:
            return
        
        # Só executa daqui em diante se janelas_moviveis é True (desfixadas)
        # Encontrar o maior z_order atual
        max_z = max((w.z_order for w in self.janelas.values()), default=0)
        
        # Se a janela já está na frente, não faz nada
        if janela.z_order == max_z and len(self.janelas) > 1:
            return
        
        # Trazer visualmente para frente (só acontece se janelas_moviveis é True)
        janela.raise_()
        
        # Atualizar z_order: janela clicada recebe max+1
        janela.z_order = max_z + 1
        
        # Salvar estado atualizado
        self.salvar_estado(janela)

    def restaurar_z_order(self):
        """Restaura a ordem de camadas visual de acordo com z_order de cada janela.
        Usado quando janelas estão fixadas para desfazer o raise() automático do Windows."""
        # Ordenar janelas por z_order
        janelas_ordenadas = sorted(
            self.janelas.values(),
            key=lambda w: w.z_order
        )
        # Re-aplicar a ordem visual (primeira para trás, última para frente)
        for w in janelas_ordenadas:
            w.lower()  # Coloca para trás
        for w in janelas_ordenadas:
            w.raise_()  # Re-levanta na ordem correta

    # salvar estado de uma
    def salvar_estado(self, w: JanelaComChroma):
        self.cfg["janelas"][w.nome] = w.to_dict()
        salvar_config(self.cfg)

    # criar via diálogo
    def criar_via_dialog(self, base: JanelaComChroma | None = None):
        dados_base = base.to_dict() if base else {}
        dlg = WindowConfigDialog(None, dados=dados_base, titulo="Nova janela")
        if dlg.exec() != QDialog.Accepted:
            return
        dados = dlg.dados()
        if not os.path.exists(dados["caminho_template"]):
            QMessageBox.critical(None, "Erro", "Template inválido.")
            return
        img = Image.open(dados["caminho_template"]).convert("RGBA")
        nome = self._proximo_nome()
        
        # Obter maior z_order atual para colocar nova janela na frente
        max_z = max((w.z_order for w in self.janelas.values()), default=0)
        
        novo = {
            **dados,
            "largura": img.width,
            "altura": img.height,
            "z_order": max_z + 1
        }
        # posição central; se base, desloca
        if base:
            pos = base.pos() + QPoint(40, 40)
            novo["pos_x"] = pos.x(); novo["pos_y"] = pos.y()
        else:
            novo["pos_x"] = 0; novo["pos_y"] = 0

        self.cfg["janelas"][nome] = novo
        salvar_config(self.cfg)
        self._instanciar(nome, novo)

    # editar via diálogo
    def editar_via_dialog(self, w: JanelaComChroma):
        dlg = WindowConfigDialog(None, dados=w.to_dict(), titulo=f"Editar {w.nome}")
        if dlg.exec() != QDialog.Accepted:
            return
        dados = dlg.dados()
        
        if not os.path.exists(dados["caminho_template"]):
            QMessageBox.critical(None, "Erro", "Template inválido.")
            return
        
        # Salvar nome, posição/tamanho e z_order atuais
        nome_janela = w.nome
        pos_x = w.x()
        pos_y = w.y()
        largura = w.width()
        altura = w.height()
        z_order_atual = w.z_order
        
        # Fechar janela antiga
        w.close()
        del self.janelas[nome_janela]
        
        # Criar nova configuração mantendo posição, tamanho e z_order
        novo_config = {
            **dados,
            "pos_x": pos_x,
            "pos_y": pos_y,
            "largura": largura,
            "altura": altura,
            "z_order": z_order_atual
        }
        
        # Atualizar configuração e salvar
        self.cfg["janelas"][nome_janela] = novo_config
        salvar_config(self.cfg)
        
        # Recriar janela com nova configuração
        self._instanciar(nome_janela, novo_config)

    def janela_atual(self) -> JanelaComChroma | None:
        aw = QApplication.activeWindow()
        if isinstance(aw, JanelaComChroma):
            return aw
        # fallback: primeira
        return next(iter(self.janelas.values()), None)

    def editar_atual(self):
        w = self.janela_atual()
        if w: self.editar_via_dialog(w)

    def excluir_atual(self):
        w = self.janela_atual()
        if w: self.excluir_janela(w.nome)

    def excluir_janela(self, nome: str):
        w = self.janelas.get(nome)
        if not w: return
        w.close()
        del self.janelas[nome]
        if nome in self.cfg["janelas"]:
            del self.cfg["janelas"][nome]
            salvar_config(self.cfg)

    def toggle_move_atual(self):
        # Alternar estado global
        self.janelas_moviveis = not self.janelas_moviveis
        # Atualizar texto do menu
        self.act_move.setText("Fixar Janelas" if self.janelas_moviveis else "Desfixar Janelas")
        # Salvar no JSON
        self.cfg["janelas_moviveis"] = self.janelas_moviveis
        salvar_config(self.cfg)

    def show_help(self):
        texto = (
            "<b>Atalhos por janela</b><br>"
            "Ctrl+N: nova janela<br>"
            "Ctrl+E: editar janela atual<br>"
            "Ctrl+Del: excluir janela atual<br>"
            "↑↓←→: mover imagem no chroma<br>"
            "T: alternar transparência do verde<br>"
            "R: manter proporção on/off<br>"
            "+ / - : redimensionar janela + template<br>"
        )
        msg = QMessageBox()
        msg.setWindowTitle("Ajuda - vaporwave_window")
        msg.setTextFormat(Qt.RichText)
        msg.setText(texto)
        msg.exec()

    def show_about(self):
        texto = (
            "<h2>Vaporwave Windows</h2>"
            "<p><b>Versão:</b> 1.0</p>"
            "<p><b>Desenvolvido por:</b> Rafael Neves</p>"
            "<p><a href='https://rafaelneves.dev.br/'>https://rafaelneves.dev.br/</a></p>"
        )
        msg = QMessageBox()
        msg.setWindowTitle("Sobre - Vaporwave Windows")
        msg.setTextFormat(Qt.RichText)
        msg.setText(texto)
        msg.exec()

    def sair(self):
        for w in list(self.janelas.values()):
            self.salvar_estado(w)
        self.app.quit()

# ---------------- main ----------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Não encerrar quando fechar última janela
    manager = AppManager(app)
    sys.exit(app.exec())
