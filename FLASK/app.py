import os
from flask import Flask, json, jsonify, render_template, request, redirect, Response
from flask_sqlalchemy import SQLAlchemy
import datetime
import requests
from sqlalchemy.sql import func
from urllib.parse import quote  
import pandas as pd
import pyodbc
import psycopg2 as pg

import sys
from io import BytesIO



#PARAMETROS DE CONEXÃO AO BANCO
server = '10.56.6.56'
database = 'Vista_Replication_PRD'
username ='gpsvista'
password = 'X95Wd@36m*Dz'

#configurações para insert/update
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mssql+pyodbc://gpsvista:%s@10.56.7.150:1433/Vista_Proc?driver=SQL+Server"  % quote(password)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "msuuuuuuuperkey141Kk42"
db = SQLAlchemy(app)

#### Criação das Classes/Tabelas banco
class RASP_NAMES(db.Model):
    __tablename__ = "RASP_NAMES"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    descricao = db.Column(db.String(200))
    date_updated = db.Column(db.DateTime,default=datetime.datetime.now , onupdate=datetime.datetime.now)

    def __init__(self, name, descricao, date_updated):
        self.name = name
        self.descricao = descricao
        self.date_updated = date_updated

    def __repr__(self):
            return f'{self.name}>'



class RASP_URLS(db.Model):
    __tablename__ = "RASP_URLS"
    id = db.Column(db.Integer, primary_key=True)
    rasp_id = db.Column(db.Integer, db.ForeignKey('RASP_NAMES.id'))
    url = db.Column(db.String(500))
    ordem = db.Column(db.Integer)
    tempo = db.Column(db.Integer)
    date_updated = db.Column(db.DateTime,default=datetime.datetime.now ,onupdate=datetime.datetime.now)

    def __init__(self, rasp_id, url, ordem, tempo, date_update):
        self.rasp_id = rasp_id
        self.url = url
        self.ordem = ordem
        self.tempo = tempo
        self.date_update = date_update

    def __repr__(self):
            return f'{self.rasp_id}>'



class VISTA_SHIFTS(db.Model):
    __tablename__ = "VISTA_SHIFTS"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    shift_description = db.Column(db.String(100))
    init_date = db.Column(db.Time)
    end_date = db.Column(db.TIME)
    sabado = db.Column(db.Boolean)
    domingo = db.Column(db.Boolean)

    def __init__(self, name, shift_description, init_date,end_date, sabado,domingo):
        self.name = name
        self.shift_description = shift_description
        self.init_date = init_date
        self.end_date = end_date
        self.sabado = sabado
        self.domingo = domingo

    def __repr__(self):
            return f'{self.name}>'

class VISTA_USER_ALERTS(db.Model):
    __tablename__ = "VISTA_USER_ALERTS"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    telegram_id = db.Column(db.String(20))
    cr_list = db.Column(db.String(1000))
    alerta1 = db.Column(db.Boolean)
    alerta2 = db.Column(db.Boolean)
    alerta3 = db.Column(db.Boolean)
    alerta4 = db.Column(db.Boolean)
    shift_id = db.Column(db.Integer, db.ForeignKey('VISTA_SHIFTS.id'))
    date_updated = db.Column(db.DateTime,default=datetime.datetime.now , onupdate=datetime.datetime.now)

    def __init__(self, name, telegram_id,alerta1, alerta2,alerta3,alerta4, cr_list,shift_id, date_updated):
        self.name = name
        self.telegram_id = telegram_id
        self.cr_list = cr_list
        self.alerta1 = alerta1
        self.alerta2 = alerta2
        self.alerta3 = alerta3
        self.alerta4 = alerta4
        self.shift_id = shift_id
        self.date_updated = date_updated

    def __repr__(self):
            return f'{self.name}>'
############

def getToken():
    url = f"https://apiprod.gpsvista.com.br/api/auth/login-by-doc"
    header = {
        'Content-Type': "application/json",
    }
    payload = {
        "cpf": "sys",
        "password": "P@ssw0rd$#@"
    }   
    res = requests.post(url, data = json.dumps(payload), headers = header)
    return json.loads(res.content)["authToken"]

def writeLog(logMessage):
    data_formatada = datetime.datetime.now().strftime("%Y-%m-%dT00:00:00.000Z") 

    logText = f"""{data_formatada} - {logMessage}""" 

    with open(os.getcwd() + '\\log.txt', 'a') as f:
        f.write('\n' + logText)

##PÁGINA DE INSERÇÃO DE URL - RASP
#setando a url - diferenciando GET E POST
@app.route('/create', methods = ['GET','POST'])
def create():  
    #quando for GET 
    if request.method =='GET':
        #executa essas duas queries
        rasp_name = RASP_NAMES.query.all()        
        results = db.session.query(RASP_URLS, RASP_NAMES).join(RASP_NAMES).order_by(RASP_URLS.rasp_id.asc(), RASP_URLS.ordem.asc()).all()
        #carrega o arquivo create.html - paassa os parametros para a url
        return render_template('create.html', results=results, rasp_name=rasp_name)
    #quando for POST
    if request.method =='POST':
        try:
            #request.form recebe os valores do POST
            rasp_id = request.form['rasp_id']
            url = request.form['url']
            ordem = request.form['ordem']
            tempo = request.form['tempo']
            #preenche a classe
            rasp_ins = RASP_URLS(
                rasp_id=rasp_id,
                url=url,
                ordem=ordem,
                tempo=tempo,
                date_update= None)
            #insere e commita
            db.session.add(rasp_ins)
            db.session.commit()
        except:
            print("ERRO NO INSERT")
        finally:
            return redirect("/create")

##MÉTODO DE UPDATE recebe o valor passado na url após "/" e seta o valor na variável id
@app.route('/create/<int:id>', methods=['GET','POST'])
def update(id):
    urls_update = RASP_URLS.query.get_or_404(id)
    if request.method =='POST':
        urls_update.rasp_id = request.form['rasp_id']
        urls_update.url = request.form['url']
        urls_update.ordem = request.form['ordem']
        urls_update.tempo = request.form['tempo']
    try:
        db.session.commit()
        return redirect("/create")
    except:
        return 'O UPDATE FALHOU'

#MÉTODO DE DELETE
@app.route('/create/delete/<int:id>', methods=['GET','POST'])
def delete(id):
    urls_delete = RASP_URLS.query.get_or_404(id)
    try:
        db.session.delete(urls_delete)
        db.session.commit()
        return redirect("/create")
    except:
        return 'O DELETE FALHOU'


#PÁGINA E FUNÇÃO DE CRIAÇÃO DE NOVA RASP
@app.route('/add_rasp', methods = ['GET','POST'])
def add_rasp():  
    if request.method =='GET':
        rasp_name = RASP_NAMES.query.all()        
        return render_template('add_rasp.html', rasp_name = rasp_name)
    if request.method =='POST':
        name = request.form['name']
        descricao = request.form['descricao']
        rasp_names = RASP_NAMES(
            name=name,
            descricao=descricao,
            date_updated= None)
        db.session.add(rasp_names)
        db.session.commit()
        return redirect("/add_rasp")


#FUNÇÃO DE DELETE <int:id> recebe a variável como inteiro e seta valor na variável int
@app.route('/add_rasp/delete/<int:id>', methods=['GET','POST'])
def add_rasp_delete(id):
    urls_delete = RASP_NAMES.query.get_or_404(id)
    try:
        db.session.delete(urls_delete)
        db.session.commit()
        return redirect("/add_rasp")
    except:
        return 'O DELETE FALHOU'
    
#PAGINA DE CRIAÇÃO DO CHAMADO
@app.route('/chamado/novo_chamado/<string:nome>/<string:id>', methods=['GET','POST'])
def add_chamado_globo(id, nome=""):
    try:       
        if request.method =='GET':      

            return render_template("add_chamado_globo.html",nome = nome, id = id)
        if request.method =='POST':
            data = request.json
            data_id = data['data_id']  
            limpeza = data['limpeza']
            obs = data['obs']
            # Formatando para o formato desejado
            diferenca = datetime.timedelta(hours=-3)
            fuso_horario = datetime.timezone(diferenca)
            data_formatada = datetime.datetime.now().astimezone(fuso_horario).strftime("%Y-%m-%dT%H:%M:%S.000Z")
            print(data_formatada)
            token = f"Bearer {getToken()}"
            header = {
                'Content-Type': "application/json",
                'Authorization': token,
            }     
            url = "https://apiprod.gpsvista.com.br/api/planejamento/tarefa/adicionar-tarefa-integracao"        
            payload = {
                "rotinaId": f"""{data_id}""",            
                "data": f"""{data_formatada}""",
                "descricao": f"""Solicitação: {limpeza} \nObservação: {obs}"""
            }
            response = requests.post(url, json=payload, headers=header)
            writeLog(f'rotina: {data_id} - tarefa criada para data {data_formatada}')  
            return jsonify({'message': 'Tarefa adicionada com sucesso!'})
        return response.text.replace('"','')
    except Exception as e:
        writeLog("Erro: " + e.args[0] + " - Rotina: " + id)
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        writeLog(f'Add task error {e}: {exc_type, fname, exc_tb.tb_lineno}')       
    return render_template("add_chamado_globo.html",nome = nome, id = id)


#FUNÇÃO DE UPDATE <int:id> recebe a variável como inteiro e seta valor na variável int
@app.route('/add_rasp/<int:id>', methods=['GET','POST'])
def update_rasp(id):
    rasp_update = RASP_NAMES.query.get_or_404(id)
    if request.method =='POST':
        rasp_update.name = request.form['name']
        rasp_update.descricao = request.form['descricao']
    try:
        db.session.commit()
        return redirect("/add_rasp")
    except:
        return 'o update falhou'

#PAGINA DE INSERÇÃO DE ALERTA POR USUÁRIO
@app.route('/add_user_alert', methods = ['GET','POST'])
def user_alert_add():
    if request.method =='GET':
        shifts_type = VISTA_SHIFTS.query.all()      
        results = db.session.query(VISTA_USER_ALERTS, VISTA_SHIFTS).join(VISTA_SHIFTS).all()
#       RENDERIZA A PÁGINA add_user_alert E CARREGA AS VARIÁVEIS results e shifts_type
        return render_template('add_user_alert.html', results=results, shifts_type=shifts_type)
    if request.method =='POST': 
        #request.form Recebe valor do POST
        name = request.form['name']
        telegram_id = request.form['telegram_id']
        cr_list = request.form['cr_list']
        shift_id = request.form['shift_id']
        #setando todos alertas como Falso se não forem escolhidos
        alerta1=False
        alerta2=False
        alerta3=False
        alerta4=False
        #Se o alerta for selecionado no checkbox definir como True
        if request.form['alerta1'] == 'on':
            alerta1 = True
        if request.form['alerta2'] == 'on':
            alerta2 = True
        if request.form['alerta3'] == 'on':
            alerta3 = True
        if request.form['alerta4'] == 'on':
            alerta4 = True
        try:
            vista_users = VISTA_USER_ALERTS(
                name=name,
                telegram_id=telegram_id,
                cr_list=cr_list,
                alerta1=alerta1,
                alerta2=alerta2,
                alerta3=alerta3,
                alerta4=alerta4,
                shift_id=shift_id,
                date_updated= None)
            db.session.add(vista_users)
            db.session.commit()
            return redirect("/add_user_alert")
        except Exception as e:
            print("ERRO NO INSERT -- " + e)
        finally:
            return redirect("/add_user_alert")

#       FUNÇÃO DE DELETE DE USUÁRIO PARA O ALERTA 
@app.route('/add_user_alert/delete/<int:id>', methods=['GET','POST'])
def user_alert_delete(id):
    urls_delete = VISTA_USER_ALERTS.query.get_or_404(id)
    try:
        db.session.delete(urls_delete)
        db.session.commit()
        return redirect("/add_user_alert")
    except:
        return 'O DELETE FALHOU'

#FUNÇÃO DE UPDATE ALERTA USUÁRIO
@app.route('/add_user_alert/<int:id>', methods=['GET', 'POST'])
def update_user_alert(id):
    vista_users = VISTA_USER_ALERTS.query.get_or_404(id)
    print('============ ja definiu vusta users ============', vista_users.id)
    if request.method =='POST':
        vista_users.alerta1 = False
        vista_users.alerta2 = False
        vista_users.alerta3 = False
        vista_users.alerta4 = False
        vista_users.name = request.form['name']
        vista_users.shift_id = request.form['shift_id']
        vista_users.telegram_id = request.form['telegram_id']
        vista_users.cr_list = request.form['cr_list']
        if request.form['alerta1'] == 'on':
            vista_users.alerta1 = True
        if request.form['alerta2'] == 'on':
            vista_users.alerta2 = True
        if request.form['alerta3'] == 'on':
            vista_users.alerta3 = True
        if request.form['alerta4'] == 'on':
            vista_users.alerta4 = True
    try:
        print('======== dentro do try ========', vista_users.alerta1, vista_users.alerta2, vista_users.alerta3, vista_users.alerta4,vista_users.name, vista_users.shift_id,vista_users.telegram_id, vista_users.cr_list)
        db.session.commit()
        print('======== session.commit feito ========')
    except Exception as e:
        return 'o update falhou ', e
    finally:
        return redirect("/add_user_alert")

        
#   PÁGINA DE CRIAÇÃO DE TURNOS
@app.route('/add_shift', methods = ['GET','POST'])
def add_shift():  
    if request.method =='GET':
        vista_shift = VISTA_SHIFTS.query.all()        
        return render_template('add_shift.html', vista_shift = vista_shift)
    if request.method =='POST':
        name = request.form['name']
        shift_description = request.form['shift_description']
        init_date = request.form['init_date']
        end_date = request.form['end_date']
        sabado=False
        domingo=False
        if request.form['sabado'] == 'on':
            sabado = True
        if request.form['domingo'] == 'on':
            domingo = True
        vista_shift = VISTA_SHIFTS(
            name=name,
            shift_description=shift_description,
            init_date= init_date,
            end_date = end_date,
            sabado = sabado,
            domingo = domingo
            )
        db.session.add(vista_shift)
        db.session.commit()
        return redirect("/add_shift")

#       FUNÇÃO DE DELETE DE TURNOS
@app.route('/add_shift/delete/<int:id>', methods=['GET','POST'])
def add_shift_delete(id):
    vista_shift = VISTA_SHIFTS.query.get_or_404(id)
    try:
        db.session.delete(vista_shift)
        db.session.commit()
        return redirect("/add_shift")
    except:
        return 'O DELETE FALHOU'

#       Função de UPDATE TURNO
@app.route('/add_shift/<int:id>', methods=['GET','POST'])
def update_shift(id):
    vista_shift = VISTA_SHIFTS.query.get_or_404(id)
    if request.method =='POST':
        vista_shift.name = request.form['name']
        vista_shift.shift_description = request.form['shift_description']
        vista_shift.init_date = request.form['init_date']
        vista_shift.end_date = request.form['end_date']
        vista_shift.sabado=False
        vista_shift.domingo=False
        if request.form['sabado'] == 'on':
            vista_shift.sabado = True
        if request.form['domingo'] == 'on':
            vista_shift.domingo = True
    try:
        db.session.commit()
        return redirect("/add_shift")
    except:
        return 'o update falhou'

#PASSANDO QUAIS URLS VÃO DIRECIONAR PARA A FUNÇÃO
#<data> é a variável que vai receber o parâmetro passado na url
@app.route('/projeto_king_vista/<data>', methods = ['GET'])
@app.route('/projeto_king_vista/', methods = ['GET'])
#FUNÇÃO DO PROJETO BURGUER KING
def projeto_king_vista(data=None):
    if request.method =='GET':
        # SE NÃO INFORMAR DATA 
        if data == None:
            query_user = ("""  select  t.numero  ,t.Nome as rotina , e.HierarquiaDescricao  as "HierarquiaDescricao",format(inicio,'dd/MM/yyyy HH:mm') as inicio,format(InicioReal,'dd/MM/yyyy HH:mm') as inicio_real,   r.Nome,  CASE WHEN t.Status = 85 and (ep.Conteudo ='SUPERVISÃO' or ep.Conteudo ='SUPERVISAO') then 80 WHEN t.Status = 85 and ep.Conteudo = 'EQUIPE DO CONTRATO' then 85  WHEN t.Status = 10 AND DATEADD(HH, -3, GETDATE()) < t.Termino THEN 10 else 15 END AS Status, t.Id  from Vista_Replication_PRD.dbo.Tarefa t inner join Vista_Replication_PRD.dbo.Estrutura e on e.Id = t.EstruturaId  left join Vista_Replication_PRD.dbo.Execucao e2 on e2.TarefaId = t.Id and e2.Status = 85 left join Vista_Replication_PRD.dbo.Recurso r on r.CodigoHash  = e2.CriadoPorHash  left join Vista_Replication_PRD.dbo.Execucao ep on ep.TarefaId = t.Id and ep.PerguntaId = 'B5CC42F8-885C-409C-8AC3-08DAB5B08DDF' where FORMAT(Disponibilizacao, 'dd/MM/yyyy') = FORMAT(DATEADD(HH, -3, GETDATE()), 'dd/MM/yyyy') and (t.Nome = 'TAREFA INICIAL BK' OR t.Nome ='TAREFA INICIAL REPOSIÇÃO BK' OR t.Nome ='RELATO SUPERVISÃO BK' OR t.Nome ='NOVA TAREFA INICIAL' OR t.Nome ='VERIFICAÇÃO IRIS BK')    order by numero desc      """)  
       #  SE INFORMAR DATA
        else:
            query_user = ("""  select  t.numero  ,t.Nome as rotina , e.HierarquiaDescricao  as "HierarquiaDescricao",format(inicio,'dd/MM/yyyy HH:mm') as inicio,format(InicioReal,'dd/MM/yyyy HH:mm') as inicio_real,   r.Nome,  CASE WHEN t.Status = 85 and (ep.Conteudo ='SUPERVISÃO' or ep.Conteudo ='SUPERVISAO') then 80 WHEN t.Status = 85 and ep.Conteudo = 'EQUIPE DO CONTRATO' then 85  WHEN t.Status = 10 AND DATEADD(HH, -3, GETDATE()) < t.Termino THEN 10 else 15 END AS Status, t.Id  from Vista_Replication_PRD.dbo.Tarefa t inner join Vista_Replication_PRD.dbo.Estrutura e on e.Id = t.EstruturaId  left join Vista_Replication_PRD.dbo.Execucao e2 on e2.TarefaId = t.Id and e2.Status = 85 left join Vista_Replication_PRD.dbo.Recurso r on r.CodigoHash  = e2.CriadoPorHash  left join Vista_Replication_PRD.dbo.Execucao ep on ep.TarefaId = t.Id and ep.PerguntaId = 'B5CC42F8-885C-409C-8AC3-08DAB5B08DDF' where FORMAT(Disponibilizacao, 'dd-MM-yyyy') = '{data}' and (t.Nome = 'TAREFA INICIAL BK' OR t.Nome ='TAREFA INICIAL REPOSIÇÃO BK' OR t.Nome ='RELATO SUPERVISÃO BK' OR t.Nome ='NOVA TAREFA INICIAL' OR t.Nome ='VERIFICAÇÃO IRIS BK')    order by numero desc      """)  
        #PASSA PARAMETROS DE CONEXÃO
        conn = pyodbc.connect ('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
        df = pd.read_sql(query_user, conn)
        conn.close()
        if not df.empty:
            df['local'] = df['HierarquiaDescricao'].str.split('/',3,  expand=True)[3]
            df = df.fillna('-')

        return render_template('exemplo_teste.html',  df = df.values.tolist())

#Função da página de drill, recebendo o id da tarefa
@app.route('/projeto_king_vista_by_id/<string:id>', methods = ['GET'])
def projeto_king_vista_find(id):
    if request.method =='GET':
        # EXECUTA CONSULTA
        query_user = ("""select p.Descricao as Pergunta, e.Conteudo as Resposta from Vista_Replication_PRD.dbo.Execucao e  inner join Pergunta p on p.Id = e.PerguntaId where TarefaId = '{}' order by Criado """).format(id)  
        conn = pyodbc.connect ('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
        df = pd.read_sql(query_user, conn)
        conn.close()
        # PREENCHE OS CAMPOS NULOS COM -
        df = df.fillna('-')
        # RENDERIZA E PASSA VALORES DA CONSULTA PRA PÁGINA
        return render_template('exemplo_teste_find.html',  df = df.values.tolist())



@app.route('/gpsvista_tarefas/', methods = ['GET'])
def gpsvista_tarefas(data=None):
    if request.method =='GET':       
        query_user = ("""  select  count(1) Id  from Vista_Replication_PRD.dbo.Tarefa  
        where status = 85 and expirada = 0 and TerminoReal >= datefromparts(year(DATEADD(HH, -3, GETDATE()) ), month(DATEADD(HH, -3, GETDATE()) ), 1)
        and TerminoReal < dateadd(month, 1, datefromparts(year(DATEADD(HH, -3, GETDATE()) ), month(DATEADD(HH, -3, GETDATE()) ), 1)) """)
        query_all_months = ("""
        WITH Meses AS (
        SELECT 1 AS Mes
        UNION ALL
        SELECT 2 AS Mes
        UNION ALL
        SELECT 3 AS Mes
        UNION ALL
        SELECT 4 AS Mes
        UNION ALL
        SELECT 5 AS Mes
        UNION ALL
        SELECT 6 AS Mes
        UNION ALL
        SELECT 7 AS Mes
        UNION ALL
        SELECT 8 AS Mes
        UNION ALL
        SELECT 9 AS Mes
        UNION ALL
        SELECT 10 AS Mes
        UNION ALL
        SELECT 11 AS Mes
        UNION ALL
        SELECT 12 AS Mes
    ),
    Tarefas AS (
        SELECT 
            MONTH(TerminoReal) AS Mes,
            COUNT(1) AS TotalTarefas
        FROM 
            Tarefa  
        WHERE 
            status = 85 
            AND expirada = 0
            AND TerminoReal >= DATEFROMPARTS(YEAR(DATEADD(HH, -3, GETDATE())), 1, 1) -- Primeiro dia do ano atual
            AND TerminoReal < DATEADD(YEAR, 1, DATEFROMPARTS(YEAR(DATEADD(HH, -3, GETDATE())), 1, 1)) -- Primeiro dia do próximo ano
        GROUP BY 
            MONTH(TerminoReal)
    )
    SELECT 
        m.Mes,
        CASE WHEN m.Mes <= MONTH(GETDATE()) THEN COALESCE(t.TotalTarefas, 0) ELSE 0 END AS TotalTarefas
    FROM 
        Meses m
    LEFT JOIN 
        Tarefas t ON m.Mes = t.Mes
    ORDER BY 
        m.Mes;
        """)  

        #PASSA PARAMETROS DE CONEXÃO
        conn = pyodbc.connect ('DRIVER={SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
        meses = []  
        df = pd.read_sql(query_user, conn)
        df_meses = pd.read_sql(query_all_months, conn)
        mes_atual = df.head().values[0][0]
        acumulado = 0
        try:
                if df_meses.values[0][1] > 0:
                    acumulado = df_meses.values[0][1]
                    janeiro = '{:,.0f}'.format(acumulado).replace(',', '.')
                str_1 = 'jan' 
        except IndexError:
            janeiro = 0
            
        try:
                if df_meses.values[1][1] > 0:
                    acumulado = acumulado + df_meses.values[1][1]
                    fevereiro = '{:,.0f}'.format(acumulado).replace(',', '.')
                else:
                     fevereiro = 0
                str_2 = 'fev'
        except IndexError:
            fevereiro = 0
        try:
                if df_meses.values[2][1] > 0:
                    acumulado = acumulado + df_meses.values[2][1]
                    marco = '{:,.0f}'.format(acumulado).replace(',', '.')
                else:
                     marco = 0                    
                str_3 = 'mar' 
        except IndexError:
            marco = 0
        try:
                if df_meses.values[3][1] > 0:
                    acumulado = acumulado + df_meses.values[3][1]
                    abril = '{:,.0f}'.format(acumulado).replace(',', '.')
                else:
                     abril = 0                    
                str_4 = 'abr' 
        except IndexError:
            abril = 0 
        try:
                if df_meses.values[4][1] > 0:
                    acumulado = acumulado + df_meses.values[4][1]
                    maio = '{:,.0f}'.format(acumulado).replace(',', '.')
                else:
                     maio = 0  
                str_5 = 'mai'
        except IndexError:
            maio = 0
        try:
                if df_meses.values[5][1] > 0:
                    acumulado = acumulado + df_meses.values[5][1]
                    junho = '{:,.0f}'.format(acumulado).replace(',', '.')
                else:
                     junho = 0  
                str_6 = 'jun' 
        except IndexError:
            junho = 0 
        try:
                if df_meses.values[6][1] > 0:
                    acumulado = acumulado + df_meses.values[6][1]
                    julho = '{:,.0f}'.format(acumulado).replace(',', '.')
                else:
                     julho = 0  
                str_7 = 'jul' 
        except IndexError:
            julho = 0
        try:
                if df_meses.values[7][1] > 0:
                    acumulado = acumulado + df_meses.values[7][1]
                    agosto = '{:,.0f}'.format(acumulado).replace(',', '.')
                else:
                     agosto = 0  
                str_8 = 'ago' 
        except IndexError:
            agosto = 0
        try:
                if df_meses.values[8][1] > 0:
                    acumulado = acumulado + df_meses.values[8][1]
                    setembro = '{:,.0f}'.format(acumulado).replace(',', '.')
                else:
                     setembro = 0  
                str_9 = 'set' 
        except IndexError:
            setembro = 0
        try:
                if df_meses.values[9][1] > 0:
                    acumulado = acumulado + df_meses.values[9][1]
                    outubro = '{:,.0f}'.format(acumulado).replace(',', '.')
                else:
                     outubro = 0  
                str_10 = 'out' 
        except IndexError:
            outubro = 0
        try:
                if df_meses.values[10][1] > 0:
                    acumulado = acumulado + df_meses.values[10][1]
                    novembro = '{:,.0f}'.format(acumulado).replace(',', '.')
                else:
                     novembro = 0  
                str_11 = 'nov' 
        except IndexError:
            novembro = 0 
        try:
                if df_meses.values[11][1] > 0:
                    acumulado = acumulado + df_meses.values[11][1]
                    dezembro = '{:,.0f}'.format(acumulado).replace(',', '.')
                else:
                     dezembro = 0 
                str_12 = 'dez' 
        except IndexError:
            dezembro = 0 
            str_12 = 'dez'
        conn.close() 
        return render_template('cont_tarefas.html', count=mes_atual,jan=janeiro,
                               fev=fevereiro,mar=marco,abr=abril,mai=maio,
                               jun=junho,jul=julho,ago=agosto,set=setembro,
                               out=outubro,nov=novembro,dez=dezembro,
                               mes_1=str_1,mes_2=str_2,mes_3=str_3,mes_4=str_4,
                               mes_5=str_5,mes_6=str_6,mes_7=str_7,mes_8=str_8,
                               mes_9=str_9,mes_10=str_10,mes_11=str_11,mes_12=str_12)


#Página para carregar informações Smart_delta
@app.route('/smart_delta')
def smart_delta():
    initial = request.args.get('init_date')
    final = request.args.get('end_date')
    return render_template('smartdelta.html', ini=initial, fin=final)
    # return render_template('smartdelta.html' ,  df = df.values.tolist(), col = df.columns.to_list(), ini=initial, fin=final, file=file)

#Ação do botão para baixar csv de missões aplicando filtro selecionado
@app.route('/smart_delta/download')
def smart_delta_download():
    try:
        initial = request.args.get('init_date')
        final = request.args.get('end_date')
        query = f""" select m.id  Mission_id, case when f.edited_flight ->> 'category' is not null  then f.edited_flight ->> 'category' else category end as mission_category, case when f.edited_flight ->> 'operation_type' is not null  then f.edited_flight ->> 'operation_type' else operation_type end as mission_type, case when f.edited_flight ->> 'airline_company' is not null  then f.edited_flight ->> 'airline_company' else airline_company end as flight_company, case when f.edited_flight ->> 'number' is not null  then f.edited_flight ->> 'number' else f.number end as flight_number, case when f.edited_flight ->> 'prefix' is not null then f.edited_flight ->> 'prefix' else prefix end as aircraft, case when f.edited_flight ->> 'origin' is not null  then f.edited_flight ->> 'origin' else f.origin end as origin, case when f.edited_flight ->> 'destiny' is not null  then f.edited_flight ->> 'destiny' else f.destiny end as destiny, d.requester as mission_dispatcher, deltas."name" as delta, number_of_pax as delta_pax, to_char(d.start_time, 'DD/MM/YYYY HH24:mi') as mission_start_time, to_char(d.finish_time,'DD/MM/YYYY HH24:mi') as mission_finish_time, case when f.edited_flight ->> 'responsable' is not null  then f.edited_flight ->> 'responsable' else f.responsable end as responsable, to_char(finish_time, 'DD') as dia, to_char(finish_time, 'MM') as mes, to_char(finish_time, 'YYYY') as ano, to_char(finish_time - start_time, 'HH24:MI:SS') as tempo_missao, to_char(mission_end - mission_start, 'HH24:MI:SS') as tempo_total_missao from missions m inner join flights f on f.id = m.flight_id inner join dispatches d on d.mission_id = m.id inner join deltas on deltas.id = d.delta_id where finish_time >= to_date('{initial}', 'YYYY-MM-dd') AND finish_time < (to_date('{final}', 'YYYY-MM-dd') + '1 day'::interval) order by finish_time asc """ 
        engine = pg.connect("dbname='postgres' user='le_mongo' host='optpax-dev-rds.c6cxy1r8mq9z.us-east-1.rds.amazonaws.com' port='5432' password='cGg1oqFgjJK77H1231v'")
        df = pd.read_sql(query, con=engine)
               
        bio = BytesIO()
        df.to_excel(bio,index=False)
        bio.seek(0) 
        return Response(bio, mimetype="application/vnd.ms-excel")
        # return Response(df.to_csv(index=False), mimetype="text/csv")
    except:
        return redirect("/smart_delta")
        
#Página para carregar informações Smart_delta_new
@app.route('/smart_delta_v2')
def smart_delta_v2():
    initial = request.args.get('init_date')
    final = request.args.get('end_date')
    return render_template('smartdelta_v2.html', ini=initial, fin=final)
    # return render_template('smartdelta.html' ,  df = df.values.tolist(), col = df.columns.to_list(), ini=initial, fin=final, file=file)

#Ação do botão para baixar csv de missões aplicando filtro selecionado
@app.route('/smart_delta_v2/download_v2')
def smart_delta_download_v2():
    try:
        initial = request.args.get('init_date')
        final = request.args.get('end_date')
        #query = f""" select m.id  Mission_id, case when f.edited_flight ->> 'category' is not null  then f.edited_flight ->> 'category' else category end as mission_category, case when f.edited_flight ->> 'operation_type' is not null  then f.edited_flight ->> 'operation_type' else operation_type end as mission_type, case when f.edited_flight ->> 'airline_company' is not null  then f.edited_flight ->> 'airline_company' else airline_company end as flight_company, case when f.edited_flight ->> 'number' is not null  then f.edited_flight ->> 'number' else f.number end as flight_number, case when f.edited_flight ->> 'prefix' is not null then f.edited_flight ->> 'prefix' else prefix end as aircraft, case when f.edited_flight ->> 'origin' is not null  then f.edited_flight ->> 'origin' else f.origin end as origin, case when f.edited_flight ->> 'destiny' is not null  then f.edited_flight ->> 'destiny' else f.destiny end as destiny, d.requester as mission_dispatcher, deltas."name" as delta, number_of_pax as delta_pax, to_char(d.start_time, 'DD/MM/YYYY HH24:mi') as mission_start_time, to_char(d.finish_time,'DD/MM/YYYY HH24:mi') as mission_finish_time, case when f.edited_flight ->> 'responsable' is not null  then f.edited_flight ->> 'responsable' else f.responsable end as responsable, to_char(finish_time, 'DD') as dia, to_char(finish_time, 'MM') as mes, to_char(finish_time, 'YYYY') as ano, to_char(finish_time - start_time, 'HH24:MI:SS') as tempo_missao, to_char(mission_end - mission_start, 'HH24:MI:SS') as tempo_total_missao, cast(f.chock_schedule_datetime as timestamp) as horario_calco,cast(d.request_date as timestamp) as solicitado,cast(d.gate_arrival_time as timestamp) as chegada_portao,cast(d.cia_start_time as timestamp) as inicio_cia,cast(d.passengers_start_time as timestamp) as saida_portao,cast(d.passengers_end_time as timestamp) as delta_livre from missions m inner join flights f on f.id = m.flight_id inner join dispatches d on d.mission_id = m.id inner join deltas on deltas.id = d.delta_id where finish_time >= to_date('{initial}', 'YYYY-MM-dd') AND finish_time < (to_date('{final}', 'YYYY-MM-dd') + '1 day'::interval) order by finish_time asc """ 
        query = f""" select m.id  Mission_id, 
case when f.edited_flight ->> 'category' is not null  then f.edited_flight ->> 'category' else category end as mission_category, 
case when f.edited_flight ->> 'operation_type' is not null  then f.edited_flight ->> 'operation_type' else operation_type end as mission_type, 
case when f.edited_flight ->> 'airline_company' is not null  then f.edited_flight ->> 'airline_company' else airline_company end as flight_company, 
case when f.edited_flight ->> 'number' is not null  then f.edited_flight ->> 'number' else f.number end as flight_number, 
case when f.edited_flight ->> 'prefix' is not null then f.edited_flight ->> 'prefix' else prefix end as aircraft, 
case when f.edited_flight ->> 'origin' is not null  then f.edited_flight ->> 'origin' else f.origin end as origin, 
case when f.edited_flight ->> 'destiny' is not null  then f.edited_flight ->> 'destiny' else f.destiny end as destiny, 
d.requester as mission_dispatcher, 
deltas."name" as delta, 
number_of_pax as delta_pax, 
to_char(d.start_time - interval '3 hours', 'DD/MM/YYYY HH24:mi') as mission_start_time, 
to_char(d.finish_time - interval '3 hours','DD/MM/YYYY HH24:mi') as mission_finish_time, 
case when f.edited_flight ->> 'responsable' is not null  then f.edited_flight ->> 'responsable' else f.responsable end as responsable, 
to_char(finish_time, 'DD') as dia, 
to_char(finish_time, 'MM') as mes, 
to_char(finish_time, 'YYYY') as ano, 
to_char(finish_time - start_time, 'HH24:MI:SS') as tempo_missao, 
to_char(mission_end - mission_start, 'HH24:MI:SS') as tempo_total_missao, 
to_char(f.chock_schedule_datetime - interval '3 hours', 'DD/MM/YYYY HH24:mi') as horario_calco, 
to_char(d.request_date - interval '3 hours', 'DD/MM/YYYY HH24:mi') as solicitado, 
to_char(m.requested_dispatch - interval '3 hours', 'DD/MM/YYYY HH24:mi') as solicitado_despachante, 
to_char(d.gate_arrival_time - interval '3 hours', 'DD/MM/YYYY HH24:mi') as chegada_portao,
to_char(d.cia_start_time - interval '3 hours', 'DD/MM/YYYY HH24:mi') as inicio_cia,
to_char(d.passengers_start_time - interval '3 hours', 'DD/MM/YYYY HH24:mi') as saida_portao,
to_char(d.passengers_end_time - interval '3 hours', 'DD/MM/YYYY HH24:mi') as delta_livre,
to_char(estimated_datetime - interval '3 hours', 'DD/MM/YYYY HH24:mi') as ETD_ETA
from missions m 
inner join flights f on f.id = m.flight_id 
inner join dispatches d on d.mission_id = m.id 
inner join deltas on deltas.id = d.delta_id
where finish_time >= to_date('{initial}', 'YYYY-MM-dd') AND finish_time < (to_date('{final}', 'YYYY-MM-dd') + '1 day'::interval) order by finish_time asc """
        engine = pg.connect("dbname='postgres' user='le_mongo' host='optpax-dev-rds.c6cxy1r8mq9z.us-east-1.rds.amazonaws.com' port='5432' password='cGg1oqFgjJK77H1231v'")
        df = pd.read_sql(query, con=engine)
               
        bio = BytesIO()
        df.to_excel(bio,index=False)
        bio.seek(0) 
        return Response(bio, mimetype="application/vnd.ms-excel")
        # return Response(df.to_csv(index=False), mimetype="text/csv")
    except:
        return redirect("/smart_delta_v2")


@app.route('/')
def inic():
    #db.create_all() 
    return 'hello'

if __name__ == "__main__":
    #descomentar a linha de baixo quando precisar criar uma nova tabela no banco ou recriar as existentes
    #db.create_all()
    app.run(host="0.0.0.0", port=5050)