import json
import boto3
import time
import io
import psutil  
import pandas as pd
from datetime import datetime


# CONFIGURAÇÃO DE AUTENTICAÇÃO AWS 



s3_client = session.client('s3')
bucket_name = 'case-itops-nicole-miranda'


# FUNÇÃO: CAPTURA DE DADOS REAIS DA MÁQUINA

def gerar_dados_reais_da_maquina():
    timestamp_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
  
    status_rede = psutil.net_io_counters()
    bytes_enviados = status_rede.bytes_sent
    bytes_recebidos = status_rede.bytes_recv
    
   
    uso_cpu = int(psutil.cpu_percent(interval=1)) 
    uso_ram = int(psutil.virtual_memory().percent)
  
    conexoes_ativas = len(psutil.net_connections())

  
    dados_antena = {
        "tipo": "antena",
        "ID_antena": "maquina_nicole",  
        "Bytes_Sent": bytes_enviados,
        "Bytes_Recv": bytes_recebidos,
        "Active_conn": conexoes_ativas, 
        "CPU_Usage": uso_cpu,
        "RAM_Usage": uso_ram,
        "timestamp": timestamp_atual
    }


    dados_firewall = {
        "tipo": "firewall",
        "Active_sessions": conexoes_ativas + 5,
        "Dropped_packets": 0,
        "top_blocked_ip": "127.0.0.1",
        "CPU_Usage": uso_cpu,
        "RAM_Usage": uso_ram,
        "Bytes_Sent": bytes_enviados,
        "Bytes_Recv": bytes_recebidos,
        "timestamp": timestamp_atual
    }
    
    return dados_antena, dados_firewall



# PROCESSO 1: CAMADA BRONZE

antena, firewall = gerar_dados_reais_da_maquina()
hora_arquivo = int(time.time())

# Envia o JSON real da antena para a camada Bronze
s3_client.put_object(
    Bucket=bucket_name,
    Key=f"01-bronze/antena_{hora_arquivo}.json",
    Body=json.dumps(antena)
)
print("Dados reais da antena enviados para 01-bronze!")


s3_client.put_object(
    Bucket=bucket_name,
    Key=f"01-bronze/firewall_{hora_arquivo}.json",
    Body=json.dumps(firewall)
)
print("Dados reais do firewall enviados para 01-bronze!")



# PROCESSO 2: CAMADA SILVER 

# Puxa a lista de arquivos de dentro do prefixo 01-bronze/
objetos = s3_client.list_objects_v2(Bucket=bucket_name, Prefix="01-bronze/")
lista_dados = []

for obj in objetos.get('Contents', []):
    chave = obj['Key']
    if chave.endswith(".json"):
        resposta = s3_client.get_object(Bucket=bucket_name, Key=chave)
        conteudo = response_body = resposta['Body'].read().decode('utf-8')
        lista_dados.append(json.loads(conteudo))


df = pd.DataFrame(lista_dados)

def definir_carga(linha):
    if pd.notna(linha.get('Active_conn')) and linha['Active_conn'] > 40:
        return 'alta densidade'
    elif pd.notna(linha.get('CPU_Usage')) and linha['CPU_Usage'] > 80:
        return 'gargalo de processamento'
    elif pd.notna(linha.get('RAM_Usage')) and linha['RAM_Usage'] > 75:
        return 'OOM'
    return 'estavel'


df['status_carga'] = df.apply(definir_carga, axis=1)

csv_buffer = io.StringIO()
df.to_csv(csv_buffer, index=False)

# Envia o arquivo tratado em formato CSV
s3_client.put_object(
    Bucket=bucket_name,
    Key="02-silver/dados_consolidados.csv",
    Body=csv_buffer.getvalue()
)
print("Dados formatados e unificados enviados para 02-silver!")



# PROCESSO 3: CAMADA GOLD (Zonas Mortas)

resposta = s3_client.get_object(Bucket=bucket_name, Key="02-silver/dados_consolidados.csv")
df_silver = pd.read_csv(io.BytesIO(resposta['Body'].read()))

# Filtra apenas o tipo antena
df_antenas = df_silver[df_silver['tipo'] == 'antena']

# Agrupa para identificar o tráfego acumulado (neste caso, a sua máquina física)
relatorio_zonas_mortas = df_antenas.groupby('ID_antena')['Bytes_Sent'].sum().reset_index()
relatorio_zonas_mortas = relatorio_zonas_mortas.sort_values(by='Bytes_Sent', ascending=True)

csv_buffer_gold = io.StringIO()
relatorio_zonas_mortas.to_csv(csv_buffer_gold, index=False)

# Envia o relatório final refinado para a camada Gold
s3_client.put_object(
    Bucket=bucket_name,
    Key="03-gold/relatorio_zonas_mortas.csv",
    Body=csv_buffer_gold.getvalue()
)
print("Relatório de Zonas Mortas gerado com sucesso em 03-gold!")