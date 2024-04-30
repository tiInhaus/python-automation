#uvicorn app_api:app --reload
import pyodbc
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import warnings
import datetime

warnings.filterwarnings('ignore')

#Parâmetros de conexão
server = '10.56.6.56'
database = 'Vista_Replication_PRD'
username ='gpsvista'
password = 'X95Wd@36m*Dz'

app = FastAPI()

@app.get("/")
def read_hello():
    return{"hello":"world"}

#Função pegar URLS passando rasp_id como parâmetro    
@app.get("/get_rasp_url/{rasp_id}")
async def read_item(rasp_id: int):
    query_user = ("select rasp_id, url,ordem,tempo,date_updated from  Vista_Proc.dbo.rasp_urls where rasp_id in (1,{}) order by rasp_id, ordem ".format(rasp_id) )  
    conn = pyodbc.connect ('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    df = pd.read_sql(query_user, conn)
    conn.close()
    df['date_updated'] = df['date_updated'].apply(lambda x: str(x))
    result = df.to_dict('records')
    return JSONResponse(content = result) 

# Função que retorna o número total de tarefas do mês e compara com o mês anterior
@app.get("/alexa_qtd_tarefa/")
async def read_item():
    query_mes = ("select COUNT(Id) as qtd, month(TerminoReal) as mes from dw_vista.dbo.FT_TAREFA ft  where TerminoReal is not null and month(TerminoReal) = month(getdate() ) group by month(TerminoReal)" )  
    query_mes_ant = """select COUNT(Id) AS qtd, month(TerminoReal) as mes from dw_vista.dbo.FT_TAREFA ft  where TerminoReal is not null and TerminoReal BETWEEN DATEADD(MONTH,-1,DATEADD(MONTH, DATEDIFF(MONTH, 1, getdate()), 0)) AND DATEADD(month, -1, getdate()) GROUP BY month(TerminoReal) """
    conn = pyodbc.connect ('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    df = pd.read_sql(query_mes, conn)
    df1 = pd.read_sql(query_mes_ant, conn)
    conn.close()
    total = df['qtd'][0] - df1['qtd'][0]
    df['total'] = round(total*100 / df1['qtd'][0])
    #Compara com o total do mês anterior e calcula a porcentagem de tarefas a mais ou a menos
    result = df.to_dict('records')
    return JSONResponse(content = result) 


#API-ALEXA Lista quantidade total de tarefas abertas no Vista
@app.get("/alexa_qtd_abertas/")
async def read_item():
    query_user = ("select COUNT(Id) as qtd from dw_vista.dbo.FT_TAREFA ft where Id_Status  = 10" )  
    conn = pyodbc.connect ('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    df = pd.read_sql(query_user, conn)
    conn.close()
    result = df.to_dict('records')
    return JSONResponse(content = result) 

# API-ALEXA Resumo por GRUPO_ID, trazendo qtd de finalizadas, abertas, andamento
@app.get("/filter_by_grupo/{grupo_id}")
async def read_item(grupo_id:int):
    query_user = ("select COUNT(CASE WHEN Id_Status = 85 THEN 1 END) as finalizadas, COUNT(CASE WHEN Id_Status = 10 THEN 1 END) as abertas, COUNT(CASE WHEN Id_Status = 25 THEN 1 END) as andamento,  Cliente  from dw_vista.dbo.FT_TAREFA ft inner join DW_Vista.dbo.DM_ESTRUTURA de ON de.Id_Estrutura = ft.Id_Estrutura where LEFT(de.Cliente,6) ={} group by cliente".format(grupo_id) )  
    conn = pyodbc.connect ('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    df = pd.read_sql(query_user, conn)
    conn.close()
    result = df.to_dict('records')
    return JSONResponse(content = result) 

# API-ALEXA Filtro por serviço, passando o id
@app.get("/filter_by_servico/{servico_id}")
async def read_item(servico_id:object):
    query_mes = ("SELECT COUNT(id) as qtd from  dw_vista.dbo.FT_TAREFA   where Id_Servico  = '{}' and  Id_Status = 85 and month(TerminoReal) = month(getdate() )".format(servico_id) )  
    query_mes_anterior = ("select COUNT(Id) AS qtd  from dw_vista.dbo.FT_TAREFA ft  where Id_Servico  = '{}' and TerminoReal is not null and TerminoReal BETWEEN DATEADD(MONTH,-1,DATEADD(MONTH, DATEDIFF(MONTH, 1, getdate()), 0)) AND DATEADD(month, -1, getdate())".format(servico_id) )
    conn = pyodbc.connect ('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    df = pd.read_sql(query_mes, conn)
    df1 = pd.read_sql(query_mes_anterior, conn)
    conn.close()
    total = df['qtd'][0] - df1['qtd'][0]
    #Compara com o total do mês anterior e calcula a porcentagem de tarefas a mais ou a menos
    df['total'] = round(total*100 / df1['qtd'][0])
    result = df.to_dict('records')
    return JSONResponse(content = result) 

@app.get("/filter_by_negocio/{negocio_id}")
async def read_item(negocio_id:object):
    if negocio_id == '0':
        nome = 'SEGURANCA HUMANA'
    elif negocio_id == '1':
        nome =  'LOGISTICA'
    elif negocio_id == '2':
        nome = 'INFRA-SERVICOS'
    elif negocio_id == '3':
        nome = 'ALIMENTACAO'
    query_mes = ("SELECT count(t.id) as qtd FROM Tarefa t WHERE Status = 85 and month(TerminoReal) = month(getdate()) and EstruturaId  IN (SELECT Id_Estrutura FROM DW_Vista.dbo.DM_ESTRUTURA de where Negocio ='{}') ".format(nome) )  
    query_mes_anterior = ("SELECT count(t.id) as qtd FROM Tarefa t WHERE Status = 85 and TerminoReal BETWEEN DATEADD(MONTH,-1,DATEADD(MONTH, DATEDIFF(MONTH, 1, getdate()), 0)) AND DATEADD(month, -1, getdate()) and EstruturaId  IN (SELECT Id_Estrutura FROM DW_Vista.dbo.DM_ESTRUTURA de where Negocio ='{}') ".format(nome) )  
    query_mes_completo_anterior = ("SELECT count(t.id) as qtd FROM Tarefa t WHERE Status = 85 and TerminoReal BETWEEN DATEADD(MONTH,-1,DATEADD(MONTH, DATEDIFF(MONTH, 1, getdate()), 0)) AND DATEADD(MONTH, DATEDIFF(MONTH, 1, getdate()), 0) and EstruturaId  IN (SELECT Id_Estrutura FROM DW_Vista.dbo.DM_ESTRUTURA de where Negocio ='{}') ".format(nome) )  

    conn = pyodbc.connect ('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    df = pd.read_sql(query_mes, conn)
    df1 = pd.read_sql(query_mes_anterior, conn)
    df_mes_total = pd.read_sql(query_mes_completo_anterior, conn)
    conn.close()
    total = df['qtd'][0] - df1['qtd'][0]
    df['total'] = round(total*100 / df1['qtd'][0])
    d = datetime.datetime.now().strftime("%d")
    media = df['qtd'][0] / int(d)
    df['previsto'] = round(30 * media)

    result = df.to_dict('records')
    return JSONResponse(content = result) 
