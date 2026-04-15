import time
import threading
import queue
from colorama import init, Fore
from src.core.nexus_agent import NexusAgent

init(autoreset=True)

# Inicializa o Agente
nexus = NexusAgent()

# Fila de tarefas global
task_queue = queue.Queue()

def nexus_worker():
    """Worker em background que processa uma mensagem por vez da fila, protegendo a RAM/CPU."""
    while True:
        try:
            # Pega a próxima tarefa (trava a thread até ter algo)
            chat_id, text = task_queue.get()
            
            print(f"{Fore.YELLOW}[WORKER] Iniciando processamento da fila para a tarefa solicitada.{Fore.RESET}")
            # Roda o cérebro
            nexus.process_telegram_command(chat_id, text)
            
            # Marca como concluída
            task_queue.task_done()
            print(f"{Fore.GREEN}[WORKER] Tarefa concluída. Aguardando próxima...{Fore.RESET}")
        except Exception as e:
            print(f"{Fore.RED}❌ Erro crítico no Worker: {e}{Fore.RESET}")

def start_polling():
    """Modo Polling: O Bot pergunta ao Telegram se há novas mensagens."""
    print(f"{Fore.GREEN}╔══════════════════════════════════════════════════════════════════════╗{Fore.RESET}")
    print(f"{Fore.GREEN}║ 🚀 NEXUS ONLINE via Long Polling (com Fila Assíncrona)!              ║{Fore.RESET}")
    print(f"{Fore.GREEN}║ O servidor agora opera 100% oculto na sua máquina local.             ║{Fore.RESET}")
    print(f"{Fore.YELLOW}║ Sistema protegido contra sobrecarga (Fila ativada).                  ║{Fore.RESET}")
    print(f"{Fore.GREEN}╚══════════════════════════════════════════════════════════════════════╝{Fore.RESET}\n")
    
    # Para o Polling funcionar, o Webhook deve ser desligado à força no servidor do Telegram
    print(f"{Fore.CYAN}[*] Desativando Webhooks antigos do Telegram...{Fore.RESET}")
    nexus.telegram.delete_webhook()
    
    # Liga o operário (Worker) que vai ficar lendo a fila para sempre
    threading.Thread(target=nexus_worker, daemon=True).start()
    print(f"{Fore.CYAN}[*] Operário de Fila (Worker) iniciado com sucesso.{Fore.RESET}")
    
    print(f"{Fore.CYAN}[*] Iniciando escuta tática na caixa do Telegram...{Fore.RESET}")
    last_update_id = None
    
    while True:
        try:
            # O timeout=60 faz o código "dormir" esperando o Telegram mandar algo. 
            # Isso gasta 0% de CPU.
            updates = nexus.telegram.get_updates(offset=last_update_id, timeout=60)
            
            for update in updates:
                # Marca a mensagem atual como "lida" pelo bot
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
                        
                    elif data.startswith('delete_'):
                        msg_id = data.split('delete_')[1]
                        nexus.gmail.trash_emails([msg_id])
                        nexus._broadcast("🗑️ **E-mail movido para a lixeira com segurança!**", chat_id)
                        
                    elif data == 'cancel_delete':
                        nexus._broadcast("✅ Ação de exclusão cancelada pelo usuário. E-mail mantido a salvo.", chat_id)
                        
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
                    # EM VEZ DE RODAR IMEDIATAMENTE (QUEBRANDO A RAM), COLOCA NA FILA:
                    posicao = task_queue.qsize() + 1
                    if posicao > 1:
                        nexus._broadcast(f"⏳ **Comando na Fila:** Você é o número {posicao} da fila. O Nexus está processando a tarefa anterior.", chat_id)
                    
                    task_queue.put((chat_id, text))
                    
        except KeyboardInterrupt:
            print(f"\n{Fore.RED}🛑 Nexus desligado manualmente.{Fore.RESET}")
            break
        except Exception as e:
            print(f"{Fore.RED}❌ Erro no Loop Principal: {e}{Fore.RESET}")
            time.sleep(5) # Pausa de segurança se o Telegram cair

if __name__ == '__main__':
    start_polling()