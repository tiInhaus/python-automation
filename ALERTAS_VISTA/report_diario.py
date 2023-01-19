from inspect import formatannotation
import requests
import pandas as pd
import pyodbc
import numpy as np
import warnings
from datetime import datetime
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

def insert_send(telegram_id):    
    server = '10.56.7.150'
    database = 'Vista_Proc'
    username ='gpsvista_rasp'
    password = 'bUdtoY3ofXsKt!'
    conn = pyodbc.connect  ('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    cursor = conn.cursor()
    cursor.execute('''
                    INSERT INTO Vista_Proc.dbo.ALERTS_REGISTRY
                    VALUES
                    ({},3,GETDATE())
                    '''.format(telegram_id))
    conn.commit()
    conn.close()

#token do bot
token = '5726920603:AAHC8mrerKSJYGxPog2obS9YDMmnzDEs8gQ'

# função de envio de mensagem
def send_message(token, chat_id, msg):
    try:
        data = {"chat_id": chat_id, "text": msg}
        url = "https://api.telegram.org/bot{}/sendMessage".format(token)
        requests.post(url, data)
    except Exception as e:
        print("Erro no sendMessage:", e)


#MENSAGEM PARA ENVIAR   -- passar variavel dentro de {}
message = """REPORT DIÁRIO

Cliente: {cliente}

CR: {cr} {cr_resto}

Total Geral: {{total_finalizadas}} tarefas finalizadas, {{total_abertas}} tarefas abertas atrasadas.

{categoria}:  {qtd_finalizadas} tarefas finalizadas , {porcentagem}% finalizadas dentro do prazo e possui {qtd_abertas} tarefas abertas atrasadas. 
 """
#   SE FOR SÁBADO
if datetime.now().isoweekday() == 6:
    query_crs_alerta = """SELECT name, telegram_id , cr_list FROM Vista_Proc.dbo.VISTA_USER_ALERTS where alerta3 = 1 and shift_id in (select id from Vista_Proc.dbo.VISTA_SHIFTS vs where sabado = 1 and CONVERT(TIME, GETDATE()) BETWEEN DATEADD(MINUTE,-30,init_date) and DATEADD(MINUTE,30,end_date))"""
#   SE FOR DOMINGO
elif datetime.now().isoweekday() == 7:
    query_crs_alerta = """SELECT name, telegram_id , cr_list FROM Vista_Proc.dbo.VISTA_USER_ALERTS where alerta3 = 1 and shift_id in (select id from Vista_Proc.dbo.VISTA_SHIFTS vs where domingo = 1 and CONVERT(TIME, GETDATE()) BETWEEN DATEADD(MINUTE,-30,init_date) and DATEADD(MINUTE,30,end_date))"""
else:
    query_crs_alerta = """SELECT name, telegram_id , cr_list FROM Vista_Proc.dbo.VISTA_USER_ALERTS where alerta3 = 1 and shift_id in (select id from Vista_Proc.dbo.VISTA_SHIFTS vs where CONVERT(TIME, GETDATE()) BETWEEN DATEADD(MINUTE,-30,init_date) and DATEADD(MINUTE,30,end_date))"""
df_crs = exec_query_rasp(query_crs_alerta)
df_crs
if df_crs.empty:
    exit()

#   Identifica os turnos que o início é igual ao horário atual (30 min de tolerancia) 
query_crs_alerta = """SELECT name, telegram_id , cr_list FROM Vista_Proc.dbo.VISTA_USER_ALERTS where alerta3 = 1 and shift_id in (select id from Vista_Proc.dbo.VISTA_SHIFTS vs where CONVERT(TIME, GETDATE()) BETWEEN DATEADD(MINUTE,-30,init_date) and DATEADD(MINUTE,30,end_date))"""
# query_crs_alerta = 'SELECT name, telegram_id , cr_list, alerta1 FROM Vista_Proc.dbo.VISTA_USER_ALERTS where alerta3 = 1 and shift_id in (select Id from Vista_Proc.dbo.VISTA_SHIFTS where CONVERT(TIME, GETDATE()) BETWEEN DATEADD(MINUTE,-5,init_date) and DATEADD(MINUTE,5,end_date) )'
df_crs = exec_query_rasp(query_crs_alerta)
crs_list = df_crs['cr_list'].tolist()
crs_list_string = ','.join(crs_list)
# 
query = """select  ft.Id, CR_DESC as 'CR', ds.Servico  as 'ServicoDescricao', Cliente as 'EstruturaGrupo'
 ,Id_Status,ft.Status, Disponibilizacao,  Prazo, TerminoReal
 from DW_Vista.dbo.FT_TAREFA ft inner join DW_Vista.dbo.DM_ESTRUTURA de on de.Id_Estrutura = ft.Id_Estrutura 
 inner join DW_Vista.dbo.DM_SERVICO ds on ds.Id_Servico  = ft.Id_Servico 
where (TerminoReal BETWEEN DATEADD(DAY, DATEDIFF(day, 1, getdate()), 0) AND   DATEADD(DAY, DATEDIFF(day, 0, getdate()), 0) 
OR Disponibilizacao < GETDATE() and Prazo < GETDATE() AND TerminoReal IS NULL)
AND TRY_CAST(LEFT(CR_DESC ,5) AS INT) IN ({})""".format(crs_list_string)
df_result = exec_query(query)



## formatando a coluna EstruturaGrupo
df_result[['CR_ID', 'CR_RESTO']] = df_result['CR'].str.split(' -', 1, expand=True)
i=0



df_aberta = df_result[df_result['Id_Status'] == 10]
df_finalizada = df_result[df_result['Id_Status'] == 85]
df_finalizada_qtd = df_finalizada[['Id','CR_ID', 'CR_RESTO', 'ServicoDescricao', 'EstruturaGrupo']]


df_finalizada['NoPrazo'] = np.where(df_finalizada['Prazo'] > df_finalizada['TerminoReal'] , True, False)
df_finalizada = df_finalizada.groupby(['CR_ID', 'CR_RESTO', 'ServicoDescricao', 'EstruturaGrupo','NoPrazo'])['Id'].count().to_frame(name='finalizadas').reset_index()
df_finalizada['porcentagem'] = round(100 * df_finalizada['finalizadas'] / df_finalizada.groupby(['CR_ID'])['finalizadas'].transform('sum'))
df_finalizada_prazo = df_finalizada[df_finalizada['NoPrazo']==True]
df_finalizada_qtd = df_finalizada_qtd.groupby(['CR_ID', 'CR_RESTO', 'ServicoDescricao', 'EstruturaGrupo'])['Id'].count().to_frame(name='qtd_finalizada').reset_index()
df_f = pd.merge(df_finalizada_qtd,df_finalizada[df_finalizada['NoPrazo'] == True].drop(['finalizadas','EstruturaGrupo','CR_RESTO', 'NoPrazo'], axis = 1), on=('CR_ID','ServicoDescricao'), how='left').fillna(100)
df_result = pd.merge(   df_aberta.groupby(['CR_ID', 'CR_RESTO', 'ServicoDescricao', 'EstruturaGrupo'])['Id'].count().to_frame(name='qtd_abertas').reset_index(),
df_f, on=('CR_ID','CR_RESTO','ServicoDescricao','EstruturaGrupo') ,how='outer').fillna(0)
df_result[['GRUPO_ID', 'GRUPO_NOME']] = df_result['EstruturaGrupo'].str.split('-', 1, expand=True)
df_result.sort_values(by=['CR_ID','ServicoDescricao'],inplace=True,ignore_index=True)


i=0
#  Loop para preencher variáveis de mensagem
while i < len(df_result):
    total_finalizadas = df_result.loc[i, 'qtd_finalizada']
    total_abertas = df_result.loc[i, 'qtd_abertas']
    formated_message = message.format(qtd_finalizadas=int(df_result.loc[i, 'qtd_finalizada']),porcentagem=int(df_result.loc[i, 'porcentagem']) ,qtd_abertas =int(df_result.loc[i, 'qtd_abertas']), cliente = df_result.loc[i,'GRUPO_NOME'],cr_resto=df_result.loc[i, 'CR_RESTO'],  cr=df_result.loc[i, 'CR_ID'], categoria = df_result.loc[i, 'ServicoDescricao'])
#   Se possuir mais que um valor para ServicoDescricao concatena mensagem
    while i+1 < len(df_result) and df_result.loc[i, "CR_ID"] == df_result.loc[i+1, "CR_ID"]:
        formated_message += str("""\n{categoria}:  {qtd_finalizadas} tarefas finalizadas , {porcentagem}% finalizadas dentro do prazo e possui {qtd_abertas} tarefas abertas atrasadas.
        \n""").format(categoria=df_result.loc[i+1, 'ServicoDescricao'],qtd_finalizadas=int(df_result.loc[i, 'qtd_finalizada']),porcentagem=int(df_result.loc[i, 'porcentagem']) ,qtd_abertas =int(df_result.loc[i, 'qtd_abertas']))
        i+=1
        total_finalizadas += df_result.loc[i, 'qtd_finalizada']
        total_abertas += df_result.loc[i, 'qtd_abertas']

    df_new_loop = df_crs[df_crs['cr_list'].str.contains(df_result.loc[i, 'CR_ID'])]['telegram_id']
    print(df_new_loop)
#   Envia para cada id_telegram daquele CR
    for id_teleg in df_new_loop:
        # if id_teleg == '1091068460':
          formated_message = formated_message.format(total_finalizadas=int(total_finalizadas), total_abertas = int(total_abertas))
          send_message(token, id_teleg, formated_message)
          insert_send(id_teleg)
    i+=1

