import boto3
import pandas as pd
import json
import io


s3_client = boto3.client('s3')
bucket_name = 'case-itops-nicole-miranda'

# 1. Puxa a lista de arquivos de dentro do prefixo 01-bronze/
objetos = s3_client.list_objects_v2(Bucket=bucket_name, Prefix="01-bronze/")
lista_dados = []

for obj in objetos.get('Contents', []):
    chave = obj['Key']
    if chave.endswith(".json"):
        # Baixa o conteúdo do arquivo
        resposta = s3_client.get_object(Bucket=bucket_name, Key=chave)
        conteudo = resposta['Body'].read().decode('utf-8')
        lista_dados.append(json.loads(conteudo))

# 2. Transforma em um DataFrame do Pandas
df = pd.DataFrame(lista_dados)

def definir_carga(linha):
    # Se o valor não for vazio, testa as condições pedidas no case
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

s3_client.put_object(
    Bucket=bucket_name,
    Key="02-silver/dados_consolidados.csv",
    Body=csv_buffer.getvalue()
)
print("Dados formatados e unificados enviados para 02-silver!")