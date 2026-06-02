# Protocolo OSC — ImgFootball
## Especificação para Integração com Servidor

> **Versão:** 1.0  
> **Última atualização:** 02/06/2026  
> **Porta padrão:** 9000  
> **IP padrão:** 127.0.0.1

---

## Formato Geral

Todas as coordenadas são **normalizadas de 0.0 a 1.0** (relativas à resolução da câmera).
- `x = 0.0` → borda esquerda da câmera
- `x = 1.0` → borda direita da câmera
- `y = 0.0` → topo da câmera
- `y = 1.0` → base da câmera

> ⚠️ A imagem já é espelhada (flip horizontal). O lado "direito" do jogador
> aparece no lado direito da tela.

---

## Endereços OSC — Coordenadas do Corpo

### Parte Superior (Básica)

| Endereço | Argumentos | Tipo | Descrição |
|---|---|---|---|
| `/body/direito/ombro` | `x y vis` | float float float | Ombro direito |
| `/body/esquerdo/ombro` | `x y vis` | float float float | Ombro esquerdo |
| `/body/direito/cotovelo` | `x y vis` | float float float | Cotovelo direito |
| `/body/esquerdo/cotovelo` | `x y vis` | float float float | Cotovelo esquerdo |
| `/body/direito/pulso` | `x y vis` | float float float | Pulso direito |
| `/body/esquerdo/pulso` | `x y vis` | float float float | Pulso esquerdo |

### Parte Inferior (Detalhada)

| Endereço | Argumentos | Tipo | Descrição |
|---|---|---|---|
| `/body/direito/quadril` | `x y vis` | float float float | Quadril direito |
| `/body/esquerdo/quadril` | `x y vis` | float float float | Quadril esquerdo |
| `/body/direito/joelho` | `x y vis` | float float float | Joelho direito |
| `/body/esquerdo/joelho` | `x y vis` | float float float | Joelho esquerdo |
| `/body/direito/tornozelo` | `x y vis` | float float float | Tornozelo direito |
| `/body/esquerdo/tornozelo` | `x y vis` | float float float | Tornozelo esquerdo |
| `/body/direito/calcanhar` | `x y vis` | float float float | Calcanhar direito |
| `/body/esquerdo/calcanhar` | `x y vis` | float float float | Calcanhar esquerdo |
| `/body/direito/pe` | `x y vis` | float float float | Ponta do pé direito |
| `/body/esquerdo/pe` | `x y vis` | float float float | Ponta do pé esquerdo |

> `vis` = visibilidade (0.0 a 1.0). Valores abaixo de 0.3 são considerados
> não confiáveis e não são enviados.

---

## Endereços OSC — Dados Calculados

| Endereço | Argumentos | Tipo | Descrição |
|---|---|---|---|
| `/body/direito/joelho_angulo` | `graus` | float | Ângulo de flexão do joelho direito (0-180°) |
| `/body/esquerdo/joelho_angulo` | `graus` | float | Ângulo de flexão do joelho esquerdo (0-180°) |
| `/body/direito/pe_velocidade` | `vel` | float | Velocidade do pé direito (pixels/frame) |
| `/body/esquerdo/pe_velocidade` | `vel` | float | Velocidade do pé esquerdo (pixels/frame) |
| `/body/direito/sapato_centro` | `x y` | float float | Centro da zona do sapato direito (normalizado) |
| `/body/esquerdo/sapato_centro` | `x y` | float float | Centro da zona do sapato esquerdo (normalizado) |
| `/body/direito/chute` | `flag` | int | 1 = chute detectado, 0 = sem chute |
| `/body/esquerdo/chute` | `flag` | int | 1 = chute detectado, 0 = sem chute |

---

## Endereços OSC — Mãos e Status

| Endereço | Argumentos | Tipo | Descrição |
|---|---|---|---|
| `/body/direito/mao` | `x y` | float float | Centro da mão direita (normalizado) |
| `/body/esquerdo/mao` | `x y` | float float | Centro da mão esquerda (normalizado) |
| `/body/lado_confirmado` | `status` | int | 1 = lados OK, 0 = invertidos, -1 = não confirmado |

---

## Detecção de Chute

Um "chute" é detectado quando a **velocidade do pé** ultrapassa o limiar configurável
(padrão: 40 pixels/frame). O limiar pode ser ajustado no `config.ini`:

```ini
[detection]
kick_speed_threshold = 40
```

### Valores de Referência de Velocidade:
- **0 - 5**: Pé parado
- **5 - 20**: Caminhando / movimento lento
- **20 - 40**: Movimento moderado
- **40+**: Chute / movimento rápido → envia `/body/[lado]/chute 1`

---

## Taxa de Envio

- As coordenadas são enviadas **a cada frame da câmera** (~30 FPS dependendo do hardware)
- Total de mensagens por frame: ~22 mensagens OSC
- Taxa total estimada: ~660 mensagens/segundo

---

## Exemplo de Integração (Python)

```python
from pythonosc import dispatcher, osc_server

def on_kick(addr, flag):
    if flag == 1:
        side = "direito" if "direito" in addr else "esquerdo"
        print(f"Chute detectado com o pé {side}!")

def on_foot(addr, x, y, vis):
    print(f"Pé em ({x}, {y}) - visibilidade: {vis}")

disp = dispatcher.Dispatcher()
disp.map("/body/direito/chute", on_kick)
disp.map("/body/esquerdo/chute", on_kick)
disp.map("/body/direito/pe", on_foot)
disp.map("/body/esquerdo/pe", on_foot)

server = osc_server.ThreadingOSCUDPServer(("0.0.0.0", 9000), disp)
server.serve_forever()
```

---

## Arquivos do Projeto

| Arquivo | Descrição |
|---|---|
| `test_body.py` | Script principal — captura + detecção + envio OSC |
| `config.ini` | Configurações (câmera, OSC, detecção, suavização) |
| `osc_receiver_test.py` | Receptor de teste para validar mensagens |
| `osc_protocol.md` | Este documento |

---

## Notas para o Desenvolvedor do Servidor

1. **Coordenadas são espelhadas**: A imagem é invertida horizontalmente (modo espelho).
   O lado "direito" do jogador já está do lado direito da tela.

2. **Sapatos**: O sistema usa uma "zona do sapato" que engloba tornozelo + calcanhar + 
   ponta do pé com margem extra. Use `sapato_centro` para uma posição mais estável do pé.

3. **Confirmação de lados**: Sempre verifique `/body/lado_confirmado` no início. 
   Se retornar -1, peça ao jogador para mostrar as mãos brevemente.

4. **Visibilidade**: Só confie em coordenadas com `vis > 0.3`. Abaixo disso, o 
   MediaPipe está "chutando" a posição.

5. **Suavização**: As coordenadas já podem ser suavizadas pelo client (configurável 
   no `config.ini`). Se o servidor precisar de dados brutos, desative a suavização.
