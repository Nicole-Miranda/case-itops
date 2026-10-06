import boto3
import pandas as pd
import io

s3_client = boto3.client('s3')
bucket_name = 'case-itops-nicole-miranda'


resposta = s3_client.get_object(Bucket=bucket_name, Key="02-silver/dados_consolidados.csv")
df = pd.read_csv(io.BytesIO(resposta['Body'].read()))


df_antenas = df[df['tipo'] == 'antena']

# 3. Agrupa as antenas para ver o total de tráfego enviado (Bytes_Sent)
# O sort_values(ascending=True) coloca os menores consumos no topo (Zonas Mortas)
relatorio_zonas_mortas = df_antenas.groupby('ID_antena')['Bytes_Sent'].sum().reset_index()
relatorio_zonas_mortas = relatorio_zonas_mortas.sort_values(by='Bytes_Sent', ascending=True)


csv_buffer = io.StringIO()
relatorio_zonas_mortas.to_csv(csv_buffer, index=False)

s3_client.put_object(
    Bucket=bucket_name,
    Key="03-gold/relatorio_zonas_mortas.csv",
    Body=csv_buffer.getvalue()
)
print("Relatório de Zonas Mortas gerado com sucesso em 03-gold!")