"""
Módulo de Animações para Vaporwave Windows
Contém todas as animações de transição de imagens
"""

from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QRect


def _criar_animacao_wipe(janela, caminho, direcao):
    """Helper para criar animações wipe em diferentes direções.
    
    Direções:
    - 'top': desaparece de cima para baixo
    - 'bottom': desaparece de baixo para cima
    - 'left': desaparece da esquerda para direita
    - 'right': desaparece da direita para esquerda
    """
    x0, y0, x1, y1 = janela.area_chroma
    largura_orig = x1 - x0
    altura_orig = y1 - y0

    # Determinar valores iniciais e finais baseado na direção
    if direcao == 'top':
        # Desaparece de cima para baixo
        rect_inicio = QRect(x0, y0, largura_orig, altura_orig)
        rect_fim = QRect(x0, y1, largura_orig, 0)
        rect_reload = QRect(x0, y1, largura_orig, 0)
        rect_in_inicio = QRect(x0, y1, largura_orig, 0)
        rect_in_fim = QRect(x0, y0, largura_orig, altura_orig)
    elif direcao == 'bottom':
        # Desaparece de baixo para cima
        rect_inicio = QRect(x0, y0, largura_orig, altura_orig)
        rect_fim = QRect(x0, y0, largura_orig, 0)
        rect_reload = QRect(x0, y0, largura_orig, altura_orig)
        rect_in_inicio = QRect(x0, y0, largura_orig, 0)
        rect_in_fim = QRect(x0, y0, largura_orig, altura_orig)
    elif direcao == 'left':
        # Desaparece da esquerda para direita
        rect_inicio = QRect(x0, y0, largura_orig, altura_orig)
        rect_fim = QRect(x1, y0, 0, altura_orig)
        rect_reload = QRect(x0, y0, largura_orig, altura_orig)
        rect_in_inicio = QRect(x0, y0, 0, altura_orig)
        rect_in_fim = QRect(x0, y0, largura_orig, altura_orig)
    else:  # 'right'
        # Desaparece da direita para esquerda
        rect_inicio = QRect(x0, y0, largura_orig, altura_orig)
        rect_fim = QRect(x0, y0, 0, altura_orig)
        rect_reload = QRect(x0, y0, largura_orig, altura_orig)
        rect_in_inicio = QRect(x1, y0, 0, altura_orig)
        rect_in_fim = QRect(x0, y0, largura_orig, altura_orig)

    # Wipe out
    anim_wipe_out = QPropertyAnimation(janela.label_overlay, b"geometry", janela)
    anim_wipe_out.setDuration(600)
    anim_wipe_out.setStartValue(rect_inicio)
    anim_wipe_out.setEndValue(rect_fim)
    anim_wipe_out.setEasingCurve(QEasingCurve.InQuad)

    # Fade out
    anim_out = QPropertyAnimation(janela.opacity_effect, b"opacity", janela)
    anim_out.setDuration(600)
    anim_out.setStartValue(1.0)
    anim_out.setEndValue(0.0)
    anim_out.setEasingCurve(QEasingCurve.InQuad)

    def after_out():
        janela._carregar_fonte(caminho)
        janela.label_overlay.setGeometry(rect_reload)

        # Wipe in
        anim_wipe_in = QPropertyAnimation(janela.label_overlay, b"geometry", janela)
        anim_wipe_in.setDuration(600)
        anim_wipe_in.setStartValue(rect_in_inicio)
        anim_wipe_in.setEndValue(rect_in_fim)
        anim_wipe_in.setEasingCurve(QEasingCurve.OutQuad)

        # Fade in
        anim_in = QPropertyAnimation(janela.opacity_effect, b"opacity", janela)
        anim_in.setDuration(600)
        anim_in.setStartValue(0.0)
        anim_in.setEndValue(1.0)
        anim_in.setEasingCurve(QEasingCurve.OutQuad)

        anim_wipe_in.start()
        anim_in.start()

    anim_out.finished.connect(after_out)
    anim_wipe_out.start()
    anim_out.start()


def animar_fade(janela, caminho):
    """Fade: desvanece até 20%, volta ao normal."""
    anim_out = QPropertyAnimation(janela.opacity_effect, b"opacity", janela)
    anim_out.setDuration(800)
    anim_out.setStartValue(1.0)
    anim_out.setEndValue(0.2)
    anim_out.setEasingCurve(QEasingCurve.InOutQuad)

    def after_out():
        janela._carregar_fonte(caminho)
        anim_in = QPropertyAnimation(janela.opacity_effect, b"opacity", janela)
        anim_in.setDuration(600)
        anim_in.setStartValue(0.2)
        anim_in.setEndValue(1.0)
        anim_in.setEasingCurve(QEasingCurve.InOutQuad)
        anim_in.start()

    anim_out.finished.connect(after_out)
    anim_out.start()


def animar_slide(janela, caminho):
    """Slide: fade rápido (300ms out/in)."""
    anim_out = QPropertyAnimation(janela.opacity_effect, b"opacity", janela)
    anim_out.setDuration(300)
    anim_out.setStartValue(1.0)
    anim_out.setEndValue(0.0)
    anim_out.setEasingCurve(QEasingCurve.InQuad)

    def after_out():
        janela._carregar_fonte(caminho)
        anim_in = QPropertyAnimation(janela.opacity_effect, b"opacity", janela)
        anim_in.setDuration(300)
        anim_in.setStartValue(0.0)
        anim_in.setEndValue(1.0)
        anim_in.setEasingCurve(QEasingCurve.OutQuad)
        anim_in.start()

    anim_out.finished.connect(after_out)
    anim_out.start()

def animar_wipe_top(janela, caminho):
    """Wipe Top: desaparece de cima para baixo."""
    _criar_animacao_wipe(janela, caminho, 'top')


def animar_wipe_bottom(janela, caminho):
    """Wipe Bottom: desaparece de baixo para cima."""
    _criar_animacao_wipe(janela, caminho, 'bottom')


def animar_wipe_left(janela, caminho):
    """Wipe Left: desaparece da esquerda para direita."""
    _criar_animacao_wipe(janela, caminho, 'left')


def animar_wipe_right(janela, caminho):
    """Wipe Right: desaparece da direita para esquerda."""
    _criar_animacao_wipe(janela, caminho, 'right')


# Dicionário para mapeamento de nomes para funções
ANIMACOES = {
    "fade": animar_fade,
    "slide": animar_slide,

    "wipe_top": animar_wipe_top,
    "wipe_bottom": animar_wipe_bottom,
    "wipe_left": animar_wipe_left,
    "wipe_right": animar_wipe_right,
}


def executar_animacao(tipo_animacao, janela, caminho):
    """Executa a animação correspondente ao tipo."""
    if tipo_animacao in ANIMACOES:
        ANIMACOES[tipo_animacao](janela, caminho)
    else:
        # Fallback para fade se animação não existir
        animar_fade(janela, caminho)
