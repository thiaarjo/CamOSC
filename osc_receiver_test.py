"""
OSC Receiver de Teste — ImgFootball
====================================
Rode este script para VER todas as mensagens OSC que o test_body.py está enviando.
Útil para testar se o envio está correto antes do servidor real existir.

Uso:
    python osc_receiver_test.py

Ele vai escutar na porta 9000 e mostrar tudo que chegar no terminal.
"""

from pythonosc import dispatcher, osc_server
import argparse
import time
import os

# Cores ANSI para o terminal
RED = "\033[91m"
BLUE = "\033[94m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

# Contadores para estatísticas
stats = {
    "total_msgs": 0,
    "start_time": time.time(),
    "last_kick_d": 0,
    "last_kick_e": 0,
}


def colorize_address(addr):
    """Colore o endereço OSC baseado no lado."""
    if "direito" in addr:
        return f"{RED}{addr}{RESET}"
    elif "esquerdo" in addr:
        return f"{BLUE}{addr}{RESET}"
    else:
        return f"{CYAN}{addr}{RESET}"


def handler_default(addr, *args):
    """Handler genérico para qualquer mensagem OSC."""
    stats["total_msgs"] += 1

    # Formata os valores
    values = [f"{v:.4f}" if isinstance(v, float) else str(v) for v in args]
    values_str = "  ".join(values)

    # Destaque especial para chutes
    if "chute" in addr and args and args[0] == 1:
        side = "DIREITO" if "direito" in addr else "ESQUERDO"
        cor = RED if "direito" in addr else BLUE
        print(f"\n{BOLD}{cor}⚽ CHUTE DETECTADO — PÉ {side}!{RESET}\n")
        return

    # Não printa todas as msgs de coordenada para não poluir
    # Só printa a cada 10 mensagens, ou se for algo especial
    if stats["total_msgs"] % 10 == 0 or "chute" in addr or "angulo" in addr or "velocidade" in addr:
        colored_addr = colorize_address(addr)
        print(f"  {colored_addr}  →  {GREEN}{values_str}{RESET}")


def handler_kick(addr, *args):
    """Handler específico para detecção de chute."""
    if args and args[0] == 1:
        side = "DIREITO" if "direito" in addr else "ESQUERDO"
        cor = RED if "direito" in addr else BLUE
        print(f"\n{BOLD}{cor}  ⚽⚽⚽  CHUTE — PÉ {side}  ⚽⚽⚽{RESET}\n")


def handler_side_confirmed(addr, *args):
    """Handler para confirmação de lado."""
    if args:
        val = args[0]
        if val == 1:
            print(f"  {GREEN}✅ Lados confirmados (OK){RESET}")
        elif val == 0:
            print(f"  {RED}⚠️  Lados INVERTIDOS!{RESET}")


def print_stats():
    """Imprime estatísticas periódicas."""
    elapsed = time.time() - stats["start_time"]
    rate = stats["total_msgs"] / max(elapsed, 1)
    print(f"\n{YELLOW}--- Estatísticas ---{RESET}")
    print(f"  Mensagens recebidas: {stats['total_msgs']}")
    print(f"  Taxa: {rate:.0f} msgs/seg")
    print(f"  Tempo ativo: {elapsed:.0f}s")
    print(f"{YELLOW}--------------------{RESET}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Receptor OSC de teste para ImgFootball")
    parser.add_argument("--ip", default="0.0.0.0", help="IP para escutar (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=9000, help="Porta para escutar (default: 9000)")
    args = parser.parse_args()

    # Configura o dispatcher com handlers
    disp = dispatcher.Dispatcher()
    disp.map("/body/direito/chute", handler_kick)
    disp.map("/body/esquerdo/chute", handler_kick)
    disp.map("/body/lado_confirmado", handler_side_confirmed)
    disp.set_default_handler(handler_default)

    # Inicia o servidor OSC
    server = osc_server.ThreadingOSCUDPServer((args.ip, args.port), disp)

    os.system("")  # Habilita cores ANSI no Windows

    print(f"\n{BOLD}{GREEN}{'=' * 55}")
    print(f"  RECEPTOR OSC DE TESTE — ImgFootball")
    print(f"  Escutando em {args.ip}:{args.port}")
    print(f"  Pressione Ctrl+C para parar")
    print(f"{'=' * 55}{RESET}\n")
    print(f"  {RED}● Vermelho = Direito{RESET}")
    print(f"  {BLUE}● Azul = Esquerdo{RESET}")
    print(f"  {GREEN}● Verde = Valores{RESET}")
    print()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print_stats()
        print(f"\n{YELLOW}Servidor encerrado.{RESET}")
        server.server_close()
