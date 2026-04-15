import argparse
import sys
from colorama import init, Fore, Style
from src.core.nexus_agent import NexusAgent

def print_banner():
    banner = f"""{Fore.MAGENTA}
 _   _  _______  ___   _  _____ 
| \\ | || ____\\ \\/ / | | |/ ____|
|  \\| ||  _|  \\  /| | | |\\___ \\ 
| |\\  || |___ /  \\| |_| | ___) |
|_| \\_||_____/_/\\_\\\\___/ |____/ 
                                
[ Mega Assistente de E-mail Local - CLI Edition ]
{Style.RESET_ALL}"""
    print(banner)

def main():
    init(autoreset=True)
    
    parser = argparse.ArgumentParser(
        description="Nexus - Otimização de tempo e extração de inteligência em E-mails.",
        usage="python3 nexus_cli.py [comando] [--query 'string']"
    )
    
    parser.add_argument('command', choices=['triage', 'deepdive', 'news'], help="Comando executável")
    parser.add_argument('--query', type=str, help="Necessário para 'deepdive'. Passar id do e-mail ou nome de remetente (Ex: 'from:chefe')", default="")

    # Se chamou sem args, printa o help
    if len(sys.argv) == 1:
        print_banner()
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()
    print_banner()
    
    # Inicializa o Agente Orquestrador
    agent = NexusAgent()

    if args.command == 'triage':
        agent.triage_unread()
        
    elif args.command == 'deepdive':
        if not args.query:
            print(f"{Fore.RED}❌ ERROR: O comando 'deepdive' exige o argumento '--query'.{Fore.RESET}")
            print(f"Exemplo: python3 nexus_cli.py deepdive --query 'from:amazon'")
            sys.exit(1)
        agent.deep_dive(args.query)
        
    elif args.command == 'news':
        agent.process_newsletters()

if __name__ == "__main__":
    main()
