import time
import threading
from colorama import init, Fore
from src.core.nexus_agent import NexusAgent

init(autoreset=True)

# Inicializa o Agente
nexus = NexusAgent()

def start_polling():
    """Modo Polling: O Bot pergunta ao Telegram se há novas mensagens."""
    print(f"{Fore.GREEN}╔══════════════════════════════════════════════════════════════════════╗{Fore.RESET}")
    print(f"{Fore.GREEN}║ 🚀 NEXUS ONLINE via Long Polling!                                    ║{Fore.RESET}")
    print(f"{Fore.GREEN}║ O servidor agora opera 100% oculto na sua máquina local.             ║{Fore.RESET}")
    print(f"{Fore.YELLOW}║ Feche qualquer túnel do Pinggy ou Localtunnel, você não precisa mais!║{Fore.RESET}")
    print(f"{Fore.GREEN}╚══════════════════════════════════════════════════════════════════════╝{Fore.RESET}\n")
    
    # Para o Polling funcionar, o Webhook deve ser desligado à força no servidor do Telegram
    print(f"{Fore.CYAN}[*] Desativando Webhooks antigos do Telegram...{Fore.RESET}")
    nexus.telegram.delete_webhook()
    
    print(f"{Fore.CYAN}[*] Iniciando escuta tática na caixa do Telegram...{Fore.RESET}")
    last_update_id = None
    
    while True:
        try:
            updates = nexus.telegram.get_updates(offset=last_update_id, timeout=60)
            
            for update in updates:
                last_update_id = update['update_id'] + 1
                
                # Trata cliques nos botões (Callback Queries)
                if 'callback_query' in update:
                    callback = update['callback_query']
                    chat_id = callback['message']['chat']['id']
                    data = callback['data']
                    
                    print(f"\n{Fore.CYAN}[BOTÃO CLICADO] Ação: {data}{Fore.RESET}")
                    
                    if data.startswith('mark_read_'):
                        msg_id = data.split('mark_read_')[1]
                        nexus.gmail.mark_as_read([msg_id])
                        nexus._broadcast("🧹 E-mail marcado como lido com sucesso!", chat_id)
                        
                    elif data.startswith('draft_'):
                        msg_id = data.split('draft_')[1]
                        nexus._broadcast("✍️ Rascunhos via botão exigem instruções em texto. Responda à mensagem dizendo o que quer escrever.", chat_id)
                    continue

                message = update.get('message')
                if not message:
                    continue
                    
                chat_id = message['chat']['id']
                text = message.get('text', '')
                
                if not text:
                    continue
                    
                print(f"\n{Fore.MAGENTA}[TELEGRAM] Recebido de {message['from']['first_name']}: {text}{Fore.RESET}")
                
                if text.startswith('/start'):
                    nexus._broadcast("🚀 **NEXUS ONLINE.** Mande seu comando tático.", chat_id)
                else:
                    # Inicia a orquestração do LLM em uma Thread separada para não travar a escuta de outras mensagens
                    threading.Thread(target=nexus.process_telegram_command, args=(chat_id, text)).start()
                    
        except KeyboardInterrupt:
            print(f"\n{Fore.RED}🛑 Nexus desligado manualmente.{Fore.RESET}")
            break
        except Exception as e:
            print(f"{Fore.RED}❌ Erro no Loop Principal: {e}{Fore.RESET}")
            time.sleep(5) # Pausa de segurança se o Telegram cair

if __name__ == '__main__':
    start_polling()
