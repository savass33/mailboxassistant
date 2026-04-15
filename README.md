# 🧠 Nexus: AI Mailbox Assistant

![Python](https://img.shields.io/badge/Python-3.14-blue?style=flat-square&logo=python)
![Ollama](https://img.shields.io/badge/AI-Ollama%20(Local)-white?style=flat-square&logo=ollama)
![Telegram](https://img.shields.io/badge/Interface-Telegram_Bot-2CA5E0?style=flat-square&logo=telegram)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

**Nexus** é um agente de inteligência artificial autônomo focado na gestão, triagem e extração de inteligência de caixas de entrada do Gmail. 

Desenhado com uma arquitetura **Agentic** (Intent Router) e focado em privacidade, o Nexus roda LLMs inteiramente de forma local (via [Ollama](https://ollama.ai/)) e é controlado via linguagem natural através do Telegram.

---

## 🚀 Principais Features

- **🎯 Intent Router (Roteamento de Intenção):** O agente interpreta mensagens naturais (ex: *"Resume o e-mail do meu chefe"*) e aciona dinamicamente a ferramenta correta no código Python.
- **📋 Protocolo de Triagem (Triage):** Lê os e-mails não lidos e os classifica visualmente em categorias táticas:
  - 🔴 `[CRÍTICO]` Alertas, Empregos (Gupy), Prazos.
  - 🟡 `[AÇÃO]` Tarefas, aprovações pendentes.
  - 🔵 `[FINANCEIRO]` Relatórios de bancos, comprovantes PIX.
  - ⚪ `[NOISE]` Spam, promoções e recibos irrelevantes.
- **🕵️‍♂️ Deep Dive (Raio-X):** Abre e-mails específicos e longos, gerando um relatório profundo com *Contexto*, *Análise Técnica*, *Próximos Passos* e até um *Draft de Resposta*.
- **📰 Destilador de Newsletters:** Ignora anúncios e foca exclusivamente em extrair fatos sobre Inteligência Artificial, Programação e Mercado Financeiro.
- **🧹 Limpeza Autônoma:** Capacidade de marcar e-mails processados como lidos automaticamente (quando instruído).

---

## 🏗️ Arquitetura do Projeto

O código segue princípios **SOLID** e **Clean Architecture**, dividindo responsabilidades em serviços focados:

```text
mailboxassistant/
├── app.py                   # Servidor Flask (Telegram Webhook Entrypoint)
├── nexus_cli.py             # Interface legada para testes via Terminal
├── src/
│   ├── config.py            # Single Source of Truth para variáveis de ambiente
│   ├── core/
│   │   └── nexus_agent.py   # O "Cérebro" Roteador (Intent Parser e Lógica)
│   └── services/
│       ├── gmail_service.py # Interação com a API do Google (Thread-safe)
│       ├── llm_service.py   # Comunicação com o Ollama local
│       └── telegram_service.py # Envio assíncrono de mensagens pro usuário
```

---

## ⚙️ Pré-requisitos

1. **Python 3.10+** (Testado no 3.14)
2. **Ollama** rodando localmente (Recomendado: modelo `llama3.2:3b` ou `hermes3:8b`).
3. **Credenciais do Google Cloud:** Um arquivo `cred.json` com a API do Gmail ativada (Escopo: `https://www.googleapis.com/auth/gmail.modify`).
4. **Token do Telegram:** Um bot criado via `@BotFather`.

---

## 🛠️ Instalação e Uso

### 1. Clonar e Instalar Dependências
```bash
git clone https://github.com/savass33/mailboxassistant.git
cd mailboxassistant
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuração de Variáveis
Copie o template do arquivo de ambiente:
```bash
cp .env.example .env
```
Edite o `.env` com seu `TELEGRAM_BOT_TOKEN`, informações de banco (opcional) e o nome do modelo local. Coloque seu arquivo `cred.json` na raiz do projeto.

### 3. Subir o Motor de IA (Ollama)
Recomenda-se rodar com aceleração Vulkan para GPUs mais antigas (ex: AMD Polaris):
```bash
OLLAMA_VULKAN=1 ollama serve
```

### 4. Rodar o Servidor
```bash
python3 app.py
```
*(No primeiro acesso, o terminal exibirá um link do Google para autorizar a leitura da sua caixa de entrada).*

### 5. Expor o Webhook para o Telegram
Use o Localtunnel ou Pinggy para expor a porta `5000`:
```bash
npx localtunnel --port 5000
```
Configure a URL gerada no seu bot do Telegram:
```bash
curl "https://api.telegram.org/bot<SEU_TOKEN>/setWebhook?url=<URL_GERADA>/webhook"
```

---

## 💬 Exemplos de Uso no Telegram

Envie mensagens em linguagem natural para o seu Bot:

> *"Nexus, faz uma triagem na minha caixa de entrada"*
> 
> *"Tem alguma newsletter interessante hoje? Resume e marca como lido"*
> 
> *"Faça um deepdive no último e-mail do Filipe Deschamps"*

---
Desenvolvido com ☕ e 💻 no Arch Linux.
