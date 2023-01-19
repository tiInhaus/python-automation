import requests
import pandas as pd
import pyodbc
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')
#select do banco
def exec_query(query): 
    server = '10.56.6.56'
    database = 'Vista_Replication_PRD'
    username ='gpsvista_alertas'
    password = 'X95Wd@36m*Dz'

    conn = pyodbc.connect ('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    df_result = pd.read_sql(query, conn)
    conn.close()
    return df_result

    #select do banco
def exec_query_rasp(query): 
    server = '10.56.7.150'
    database = 'Vista_Proc'
    username ='gpsvista_rasp'
    password = 'bUdtoY3ofXsKt!'

    conn = pyodbc.connect ('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    df_result = pd.read_sql(query, conn)
    conn.close()
    return df_result


#token do bot
token = '5637733761:AAGJ9JYb_Ftl9PkAv2oJY_5ti_iG8uG8bC4'

# função de envio de mensagem
def send_message(token, chat_id, msg):
    try:
        data = {"chat_id": chat_id, "text": msg}
        url = "https://api.telegram.org/bot{}/sendMessage".format(token)
        requests.post(url, data)
    except Exception as e:
        print("Erro no sendMessage:", e)


#MENSAGEM PARA ENVIAR   -- passar variavel dentro de {}
message = """TAREFAS EM ALERTA PRAZO 

Cliente: {cliente}

CR: {cr} {cr_resto}

{categoria}:  {qtd} tarefas em alerta.
 """
if datetime.now().isoweekday() == 6:
    query_crs_alerta = 'SELECT name, telegram_id , cr_list, alerta1 FROM Vista_Proc.dbo.VISTA_USER_ALERTS where alerta2 = 1 and shift_id in (select Id from Vista_Proc.dbo.VISTA_SHIFTS where sabado = 1 and ((init_date > end_date AND (CONVERT(TIME, GETDATE()) >= DATEADD(MINUTE,-5,init_date) OR CONVERT(TIME, GETDATE()) <= DATEADD(MINUTE,5,end_date))) or init_date < end_date and (CONVERT(TIME, GETDATE()) BETWEEN DATEADD(MINUTE,-5,init_date) and DATEADD(MINUTE,5,end_date) )))'
elif datetime.now().isoweekday() == 7:
    query_crs_alerta = 'SELECT name, telegram_id , cr_list, alerta1 FROM Vista_Proc.dbo.VISTA_USER_ALERTS where alerta2 = 1 and shift_id in (select Id from Vista_Proc.dbo.VISTA_SHIFTS where domingo = 1 and ((init_date > end_date AND (CONVERT(TIME, GETDATE()) >= DATEADD(MINUTE,-5,init_date) OR CONVERT(TIME, GETDATE()) <= DATEADD(MINUTE,5,end_date))) or init_date < end_date and (CONVERT(TIME, GETDATE()) BETWEEN DATEADD(MINUTE,-5,init_date) and DATEADD(MINUTE,5,end_date) )))'
else:
    query_crs_alerta = 'SELECT name, telegram_id , cr_list, alerta1 FROM Vista_Proc.dbo.VISTA_USER_ALERTS where alerta2 = 1 and shift_id in (select Id from Vista_Proc.dbo.VISTA_SHIFTS where (init_date > end_date AND (CONVERT(TIME, GETDATE()) >= DATEADD(MINUTE,-5,init_date) OR CONVERT(TIME, GETDATE()) <= DATEADD(MINUTE,5,end_date))) or init_date < end_date and (CONVERT(TIME, GETDATE()) BETWEEN DATEADD(MINUTE,-5,init_date) and DATEADD(MINUTE,5,end_date) ))'
df_crs = exec_query_rasp(query_crs_alerta)
df_crs
if df_crs.empty:
    exit()

crs_list = df_crs['cr_list'].tolist()
crs_list_string = ','.join(crs_list)

#query
query = """select COUNT(Id) as qtd, ServicoDescricao, tr.EstruturaGrupo, Nivel_03 as CR from Tarefa tr 
inner join DW_Vista.dbo.DM_ESTRUTURA de on de.Id_Estrutura = tr.EstruturaId 
where TRY_CAST(LEFT(Nivel_03,6) AS INT) IN ({}) and  InicioReal  is NULL and Prazo BETWEEN getdate() AND DATEADD(hour, 1, getdate()) 
group by ServicoDescricao, EstruturaGrupo, Nivel_03""".format(crs_list_string)
df_result = exec_query(query)
if df_result.empty:
    print("saiu")
    exit()

## formatando a coluna EstruturaGrupo
df_result[['GRUPO_ID', 'GRUPO_NOME']] = df_result['EstruturaGrupo'].str.split('-', 1, expand=True)
df_result[['CR_ID', 'CR_RESTO']] = df_result['CR'].str.split(' -', 1, expand=True)

df_result.sort_values(by=['CR_ID','ServicoDescricao'],inplace=True,ignore_index=True)
i=0
#  Loop para preencher variáveis de mensagem
while i < len(df_result):
    formated_message = message.format(cliente = df_result.loc[i,'GRUPO_NOME'], qtd=df_result.loc[i, 'qtd'], cr=df_result.loc[i, 'CR_ID'], cr_resto=df_result.loc[i, 'CR_RESTO'],  categoria = df_result.loc[i, 'ServicoDescricao'])
#   Se possuir mais que um valor para ServicoDescricao concatena mensagem
    while i+1 < len(df_result) and df_result.loc[i, "CR_ID"] == df_result.loc[i+1, "CR_ID"]:
        formated_message += str("""\n{categoria}:  {qtd} tarefas fora do prazo.\n""").format(categoria=df_result.loc[i+1, 'ServicoDescricao'], qtd=df_result.loc[i+1, 'qtd'])
        i+=1
    df_new_loop = df_crs[df_crs['cr_list'].str.contains(df_result.loc[i, 'CR_ID'])]['telegram_id']
#   Envia para cada id_telegram daquele CR
    for id_teleg in df_new_loop:     
        send_message(token, id_teleg, formated_message)       
    i+=1