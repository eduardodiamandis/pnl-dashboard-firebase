import subprocess
import sys

def forcar_sincronizacao_tempo_windows():
    """
    Força a sincronização da hora do sistema Windows usando w32tm.
    Requer privilégios de administrador.
    """
    print("Tentando forçar a sincronização de data e hora do Windows...")

    # Comandos para parar, registrar novamente e iniciar o serviço de horário do Windows, e então ressincronizar
    comandos = [
        ["net", "stop", "w32time"],
        ["w32tm", "/unregister"],
        ["w32tm", "/register"],
        ["net", "start", "w32time"],
        ["w32tm", "/resync", "/force"] # O parâmetro /force é opcional, mas garante a tentativa imediata
    ]

    for comando in comandos:
        try:
            # Executa o comando e captura a saída
            resultado = subprocess.run(comando, capture_output=True, text=True, check=True, shell=True)
            print(f"Comando executado: {' '.join(comando)}")
            print(f"Saída: {resultado.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            print(f"Erro ao executar o comando: {' '.join(comando)}")
            print(f"Erro: {e.stderr.strip()}")
            print("Certifique-se de estar executando o script como ADMINISTRADOR.")
            return False
        except Exception as e:
            print(f"Ocorreu um erro inesperado: {e}")
            return False

    print("Sincronização de data e hora concluída (ou tentada) com sucesso.")
    return True

if __name__ == "__main__":
    if sys.platform != "win32":
        print("Este script é destinado apenas para sistemas Windows.")
    else:
        forcar_sincronizacao_tempo_windows()

