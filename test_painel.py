"""
Script de teste para validar a integração do painel
Verifica se todas as importações estão corretas e se não há erros
"""

import os
import sys

# Adicionar caminho do projeto
projeto_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, projeto_path)

print("=" * 60)
print("TESTE DE INTEGRAÇÃO - PAINEL DE CONTROLE")
print("=" * 60)

# Teste 1: Importar módulos
print("\n[1/4] Testando importações...")
try:
    from painel import PainelControle, CartaJanela
    print("    ✓ painel.py importado com sucesso")
except ImportError as e:
    print(f"    ✗ Erro ao importar painel.py: {e}")
    sys.exit(1)

try:
    from animacoes import executar_animacao
    print("    ✓ animacoes.py importado com sucesso")
except ImportError as e:
    print(f"    ✗ Erro ao importar animacoes.py: {e}")
    sys.exit(1)

# Teste 2: Verificar arquivo de configuração
print("\n[2/4] Verificando config.json...")
config_path = os.path.join(projeto_path, "config.json")
if os.path.exists(config_path):
    print(f"    ✓ config.json encontrado: {config_path}")
else:
    print(f"    ✗ config.json não encontrado: {config_path}")
    sys.exit(1)

# Teste 3: Verificar estrutura de pastas
print("\n[3/4] Verificando estrutura de pastas...")
pastas_esperadas = ["data/templates", "data/img1", "data/img2", "data/img3"]
for pasta in pastas_esperadas:
    caminho = os.path.join(projeto_path, pasta)
    if os.path.isdir(caminho):
        print(f"    ✓ {pasta}")
    else:
        print(f"    ⚠ {pasta} não encontrado (opcional)")

# Teste 4: Validar sintaxe dos arquivos principais
print("\n[4/4] Validando sintaxe Python...")
arquivos = ["main.py", "painel.py", "animacoes.py"]
for arquivo in arquivos:
    caminho = os.path.join(projeto_path, arquivo)
    if os.path.exists(caminho):
        try:
            with open(caminho, 'r', encoding='utf-8') as f:
                compile(f.read(), arquivo, 'exec')
            print(f"    ✓ {arquivo} - sem erros de sintaxe")
        except SyntaxError as e:
            print(f"    ✗ {arquivo} - erro de sintaxe: {e}")
            sys.exit(1)
    else:
        print(f"    ✗ {arquivo} não encontrado")
        sys.exit(1)

print("\n" + "=" * 60)
print("✓ TESTES PASSARAM COM SUCESSO!")
print("=" * 60)
print("\nO painel está pronto para uso. Execute main.py para iniciar:")
print("  python main.py")
print("\nOu através do atalho do tray menu clicando em 'Painel'")
print("=" * 60)
