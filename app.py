import threading
from flask import Flask, request, jsonify
from colorama import init, Fore
from src.config import Config
from src.core.nexus_agent import NexusAgent

init(autoreset=True)

app = Flask(__name__)
nexus = NexusAgent()

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if not data or 'message' not in data:
        return jsonify({"status": "ignored"})

    chat_id = data['message']['chat']['id']
    text = data['message'].get('text', '')
    
    if not text:
        return jsonify({"status": "no text"})

    print(f"{Fore.MAGENTA}[TELEGRAM] Recebido: {text}{Fore.RESET}")

    if text.startswith('/start'):
        nexus._broadcast("🚀 **NEXUS ONLINE.** Mande seu comando tático. (Ex: 'Triagem rápida', 'Notícias', ou 'Resuma o email sobre X')", chat_id)
    else:
        # Repassa o texto livre para o Cérebro Roteador (Intent Parser)
        # Rodamos numa thread para o Telegram não achar que o servidor travou (timeout)
        threading.Thread(target=nexus.process_telegram_command, args=(chat_id, text)).start()

    return jsonify({"status": "ok"})

if __name__ == '__main__':
    print(f"{Fore.GREEN}🚀 Servidor NEXUS-WEBHOOK iniciado na porta {Config.PORT}{Fore.RESET}")
    print(f"{Fore.YELLOW}Não se esqueça de rodar o 'npx localtunnel --port {Config.PORT}' e configurar o Webhook do Telegram!{Fore.RESET}")
    app.run(host='0.0.0.0', port=Config.PORT, debug=Config.DEBUG)
