# CamOSC — Body Tracking + OSC para ImgFootball ⚽

Sistema de captura de movimentos corporais via câmera com envio de coordenadas em tempo real via **OSC (Open Sound Control)**.

Foco na detecção detalhada de **pernas e pés** (com suporte a sapatos), ideal para projetos de futebol interativo.

## 🎯 Funcionalidades

- **Detecção de corpo inteiro** com foco detalhado da cintura para baixo
- **Identificação precisa de lados**: 🔴 Vermelho = Direito | 🔵 Azul = Esquerdo
- **Confirmação de lados via mãos** usando detector de mãos do MediaPipe
- **Zona do sapato**: área expandida de detecção que compensa o uso de calçados
- **Detecção de chute**: identifica movimentos rápidos dos pés automaticamente
- **Ângulo dos joelhos**: calcula flexão em tempo real (útil para mecânica de chute)
- **Envio OSC constante**: ~22 mensagens por frame, todos os pontos do corpo
- **Suavização de coordenadas**: filtro configurável para reduzir tremulação
- **Logging para arquivo**: grava sessões em JSON para replay e debug
- **Configuração centralizada**: tudo ajustável pelo `config.ini`

## 📋 Requisitos

- Python 3.11 (recomendado)
- Webcam USB ou integrada

## ⚡ Instalação Rápida

```bash
# Crie um ambiente virtual com Python 3.11
py -3.11 -m venv venv

# Ative o ambiente
venv\Scripts\activate         # Windows
# source venv/bin/activate    # Linux/Mac

# Instale as dependências
pip install opencv-python mediapipe==0.10.9 cvzone numpy python-osc
```

> ⚠️ **Importante**: Use `mediapipe==0.10.9`. Versões mais recentes (0.10.30+) removeram o módulo `solutions` e são incompatíveis com o `cvzone`.

## 🚀 Como Usar

### 1. Configurar
Edite o `config.ini` para ajustar câmera, porta OSC, sensibilidade, etc.

### 2. Rodar o Body Tracker
```bash
python test_body.py
```

### 3. (Opcional) Testar as mensagens OSC
Abra **dois terminais**:
```bash
# Terminal 1 — Receptor de teste
python osc_receiver_test.py

# Terminal 2 — Body Tracker
python test_body.py
```

O receptor mostra todas as mensagens OSC chegando em tempo real.

## 📁 Estrutura do Projeto

| Arquivo | Descrição |
|---|---|
| `test_body.py` | Script principal — captura + detecção + envio OSC |
| `config.ini` | Configurações (câmera, OSC, detecção, suavização, logging) |
| `osc_receiver_test.py` | Receptor de teste para validar mensagens OSC |
| `osc_protocol.md` | Documentação completa do protocolo OSC |
| `test_camera.py` | Script auxiliar para testar detecção de mãos |
| `find_camera.py` | Utilitário para descobrir o índice da sua câmera |

## 📡 Protocolo OSC (Resumo)

Coordenadas normalizadas (0.0 a 1.0). Documentação completa em [`osc_protocol.md`](osc_protocol.md).

| Endereço | Valores | Descrição |
|---|---|---|
| `/body/direito/pe` | `x y vis` | Ponta do pé direito |
| `/body/esquerdo/pe` | `x y vis` | Ponta do pé esquerdo |
| `/body/direito/joelho_angulo` | `graus` | Ângulo do joelho direito |
| `/body/direito/chute` | `0 ou 1` | Flag de chute detectado |
| `/body/direito/sapato_centro` | `x y` | Centro da zona do sapato |
| `/body/lado_confirmado` | `1/0/-1` | Status de confirmação dos lados |

*(+ 16 outros endereços para todos os pontos do corpo)*

## 🎮 Controles

- **`q`** — Fechar o programa
- Mostre as **duas mãos** no início para confirmar os lados (esquerdo/direito)

## 👥 Equipe

Desenvolvido para o projeto **ImgFootball**.

## 📄 Licença

Open-source. Modifique e melhore conforme necessário.
