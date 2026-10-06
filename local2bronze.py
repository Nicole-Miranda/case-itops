import json
import boto3
import random
import time
from datetime import datetime


session = boto3.Session(


)

s3_client = boto3.client('s3')
bucket_name = 'case-itops-nicole-miranda'

def gerar_dados_simulados():
    timestamp_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    dados_antena = {
        "tipo": "antena",
        "ID_antena": "ap01",
        "Bytes_Sent": random.randint(1000, 5000),
        "Bytes_Recv": random.randint(1000, 5000),
        "Active_conn": random.randint(10, 60), 
        "CPU_Usage": random.randint(30, 90),
        "RAM_Usage": random.randint(40, 90),
        "timestamp": timestamp_atual
    }

    dados_firewall = {
        "tipo": "firewall",
        "Active_sessions": random.randint(100, 500),
        "Dropped_packets": random.randint(0, 50),
        "top_blocked_ip": "192.168.1.100",
        "CPU_Usage": random.randint(20, 85),
        "RAM_Usage": random.randint(30, 80),
        "Bytes_Sent": random.randint(10000, 50000),
        "Bytes_Recv": random.randint(10000, 50000),
        "timestamp": timestamp_atual
    }
    
    return dados_antena, dados_firewall

# Gera os arquivos e faz o upload pro S3
antena, firewall = gerar_dados_simulados()
hora_arquivo = int(time.time())

# Envia o JSON da antena para a camada Bronze
s3_client.put_object(
    Bucket=bucket_name,
    Key=f"01-bronze/antena_{hora_arquivo}.json",
    Body=json.dumps(antena)
)
print("Dados da antena enviados para 01-bronze!")

# Envia o JSON do firewall para a camada Bronze
s3_client.put_object(
    Bucket=bucket_name,
    Key=f"01-bronze/firewall_{hora_arquivo}.json",
    Body=json.dumps(firewall)
)
print("Dados do firewall enviados para 01-bronze!")