from flask import Flask, render_template, request, redirect, session, flash
import secrets
from database import iniciarDB, insercao, selecao, atualizar, remocao
from processamentoImagem import processarImagem, logEmprestimos
from PIL import UnidentifiedImageError
import base64
from datetime import date, timedelta
import sqlite3
import requests

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
app.secret_key = secrets.token_hex(32)

def calculoPrazo(fim):
   return (date.fromisoformat(fim)-date.today()).days
def formatDate(iso):
   return date.fromisoformat(iso).strftime("%d/%m/%Y")
@app.context_processor
def funcoes():
   if not session.get("UserID"):
      return {}
   dicionario = {"selecao": selecao, "range": range, "base64": base64, 'formatDate': formatDate, 'calculoPrazo': calculoPrazo}
   if not session.get('admin'):
      dicionario['emprestimos'] = selecao('EMPRESTIMOS', 'DATADEVOLUCAO, DATAENTREGA, TITULO, EMPRESTIMOS.ID' ,'USERID','=', session["UserID"], True, True, 'LIVROS', 'BOOKID', '=', 'LIVROS.ID', condicaoComplementar=True, campoComplemento='ENTREGUE', operacaoComplemento='=', comparacaoComplemento='0')
   else:
      dicionario['livros'] = selecao('LIVROS', 'ID, TITULO, AUTOR, GENERO, QUANTIDADE', condicao=False)
      dicionario['usuarios'] = selecao('LEITORES', 'ID, NOME, EMAIL, SENHA', condicao=False)
      dicionario['emprestimosAtivos'] = selecao('EMPRESTIMOS', 'EMPRESTIMOS.ID, NOME, TITULO, DATAENTREGA, DATADEVOLUCAO', 'ENTREGUE', '=', '0', True, True, 'LIVROS', 'BOOKID', '=', 'LIVROS.ID JOIN LEITORES ON USERID = LEITORES.ID')
   return dicionario




@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
   if session.get('admin'):
      return redirect('/BaseAdmin')
   if session.get('UserID'):
      return redirect('/main')
   if (request.method == "GET"):
    return render_template("cadastro.html")
   if (request.method == "POST"):
      nomeUsuario = request.form["nome"].strip()
      emailUsuario = request.form["email"].strip()
      senhaUsuario = request.form["senha"].strip()
      confirmacaoSenha = request.form["confSenha"]
      if (selecao('LEITORES', 'nome','nome','=', nomeUsuario )):
         return render_template("cadastro.html",erro = 'Nome de usuário em uso.', nome = nomeUsuario, email = emailUsuario)
      if (senhaUsuario!=confirmacaoSenha):
         return render_template("cadastro.html",erro = 'Senhas não correspondentes.', nome = nomeUsuario, email = emailUsuario)
      session.permanent = True
      session["UserID"] = insercao('LEITORES', ('nome', 'email', 'senha'), (nomeUsuario, emailUsuario, senhaUsuario))
      session["UserNAME"] = nomeUsuario
      session["UserEMAIL"] = emailUsuario
      print(session["UserID"])
      return redirect("/main")

@app.route("/main", methods=["GET", "POST"])
def main():
   if session.get('admin'):
      return redirect('/BaseAdmin')
   if not session.get("UserID"):
      return redirect("/")
   return render_template("main.html")
         
@app.route("/saidaLogin", methods = ["POST"])
def saida():
   session.clear()
   return redirect("/")


@app.route("/login", methods=["GET", "POST"])
def login():
   if session.get('admin'):
      return redirect('/BaseAdmin')
   if session.get('UserID'):
      return redirect('/main')
   if (request.method == "GET"):
      return render_template("login.html")
   if (request.method == "POST"):
      nomeLogin = request.form["nome"]
      senhaLogin = request.form["senha"]
      consultaUsuario = (selecao('LEITORES', 'nome, senha, email, ID', 'nome', '=', nomeLogin))
      if consultaUsuario:
         if (senhaLogin!= consultaUsuario[0][1]):
            return render_template("login.html", erro="Senha inválida.", user = nomeLogin)
         else:
            session["UserID"] = consultaUsuario[0][3]
            session["UserNAME"] = consultaUsuario[0][0]
            session["UserEMAIL"] = consultaUsuario[0][2]
            return redirect("/main")
      else:
         return render_template("login.html", erro='Usuário inexistente')

@app.route("/admin", methods=["GET", "POST"])
def administracao():
   if session.get('admin'):
      return redirect('/BaseAdmin')
   if (request.method =="GET"):
      return render_template("admin.html")
   if (request.method=="POST"):
      nomeLogin = request.form['userName']
      senhaLogin = request.form['userPassword']
      consultaUsuario = selecao('LEITORES', 'nome, senha, email, ID, admin', 'nome', '=', nomeLogin)
      if consultaUsuario:
         if consultaUsuario[0][4]:
            if senhaLogin == consultaUsuario[0][1]:
               session["UserID"] = consultaUsuario[0][3]
               session["UserNAME"] = consultaUsuario[0][0]
               session["UserEMAIL"] = consultaUsuario[0][2]
               session["admin"] = consultaUsuario[0][4]
               return redirect('/BaseAdmin')
            else:
               return render_template('admin.html', erro = 'Senha inválida.')
         else:
            return render_template('admin.html', erro = 'Usuário não-administrativo.')
      else:
         return render_template('admin.html', erro = 'Usuário não existente.')

@app.route("/BaseAdmin", methods=["GET", "POST"])
def base():
   if not session.get("UserID") or not session.get("admin"):
         return redirect("/admin")
   return render_template("mainAdmin.html")

@app.route("/cadastroLivro", methods=["GET", "POST"])
def cadastroDeLivros():
   if (request.method == "GET"):
      return render_template("cadastroLivro.html")
   if (request.method == "POST"):
      titulo = request.form["tituloLivro"]
      genero = request.form["generoLivro"]
      autor = request.form["autorLivro"]
      estoque = int(request.form["estoqueLivro"])
      try:
         imagem = processarImagem(request.files["imagemLivro"])
      except UnidentifiedImageError:
         return render_template("cadastroLivro.html", erro ='Imagem inválida.')
      insercao('LIVROS', ('titulo', 'autor', 'genero', 'quantidade', 'imagem'), (titulo, autor, genero, estoque, imagem))
      flash("Livro adicionado com sucesso.")
      return render_template("mainAdmin.html")

@app.route("/livro", methods=["GET", "POST"])
def livraria():
   if not session.get("UserID"):
      return redirect("/")
   return render_template("livro.html")

@app.route("/capa/<int:id>")
def capa(id):
   print(id)
   resultado = selecao('LIVROS', 'imagem', 'ID', '=', id)
   return resultado[0][0], 200, {"Content-Type": "image/jpeg"}

@app.route("/emprestimo", methods=["POST"])
def emprestar():
   if not session.get("UserID"):
      return redirect("/")
   if (request.method=="POST"):
      consultaEmprestimos = selecao('EMPRESTIMOS', 'ID', 'USERID', '=', session['UserID'], condicaoComplementar=True, campoComplemento='ENTREGUE', operacaoComplemento='=', comparacaoComplemento='0')
      if len(consultaEmprestimos) >= 3:
         flash('Limite de três (3) empréstimos atingido. Efetue a devolução de um livro para poder realizar o empréstimo.')
         return redirect("/livro")
      idLivro = request.form["idLivroEmprestimo"]
      dataDevolucao = date.today() + timedelta(int(request.form["dataEmprestimo"]))
      insercao('EMPRESTIMOS', ('userid', 'bookid', 'datadevolucao', 'dataentrega'), (session['UserID'], idLivro, dataDevolucao.isoformat(), date.today().isoformat()))
      atualizar('LIVROS', ('QUANTIDADE',), ('QUANTIDADE - 1',), 'ID', '=', idLivro, 1)
      flash("Empréstimo feito com sucesso.")
      return redirect("/main")

@app.route("/mecanismoPesquisa", methods=["POST"])
def realizarPesquisa():
   if not session.get("UserID"):
      return redirect("/")
   db = sqlite3.connect("./db/bookflow.db")
   dados = request.get_json()
   if not dados.get('tituloLivro'):
      resultado = db.execute('SELECT ID, TITULO, AUTOR, GENERO, QUANTIDADE FROM LIVROS').fetchall() 
   else:
      resultado = db.execute('SELECT ID, TITULO, AUTOR, GENERO, QUANTIDADE FROM LIVROS WHERE TITULO LIKE ?', (f"%{dados.get('tituloLivro')}%",)).fetchall()
   db.commit()
   db.close()
   return resultado

@app.route("/devolucao", methods=["POST"])
def realizarDevolucao():
   if not session.get("UserID"):
      return redirect("/")
   idEmprestimo = request.form['idEmprestimo']
   atualizar('EMPRESTIMOS', ('ENTREGUE',),('1',), 'ID', '=', idEmprestimo, 1)
   return redirect("/main")

@app.route("/gerenciamentoEmprestimo", methods=["GET","POST"])
def gerenciamentoLivros():
   if not session.get("UserID") or not session.get("admin"):
      return redirect("/admin")
   if (request.method == "GET"):
      return render_template("emprestimosAdmin.html") 

@app.route("/gerenciamentoLivro", methods=["GET"])
def y():
   if not session.get("UserID") or not session.get("admin"):
      return redirect("/admin")
   return render_template('livrosAdmin.html')

@app.route("/exclusaoLivro", methods=["POST"])
def x():
   if not session.get("UserID") or not session.get("admin"):
      return redirect("/admin")
   idLivro = request.form['idLivro']
   logEmprestimos(idLivro, True)
   remocao('EMPRESTIMOS', 'BOOKID = ', idLivro)
   remocao('LIVROS', 'ID = ', idLivro)
   flash("Exclusão bem-sucedida")
   return redirect("/gerenciamentoLivro")

@app.route("/edicaoLivro", methods=['POST'])
def w():
   if not session.get("UserID") or not session.get("admin"):
      return redirect("/admin")
   id = request.form['idLivro']
   titulo = request.form['tituloLivro']
   autor = request.form['autorLivro']
   genero = request.form['generoLivro']
   estoque = request.form['estoqueLivro']
   atualizar('LIVROS', ('TITULO', 'AUTOR', 'GENERO', 'QUANTIDADE'), (f"'{titulo}'", f"'{autor}'", f"'{genero}'", f"'{estoque}'"), 'ID', '=', id, 4)
   flash('Edição bem-sucedida.')
   return redirect("/gerenciamentoLivro")

@app.route("/criacaoConta", methods=["GET", "POST"])
def a():
   if not session.get("UserID") or not session.get("admin"):
      return redirect("/admin")
   if (request.method == "GET"):
      return render_template("criacaoContas.html")
   if (request.method == "POST"):
      nome = request.form['nomeUsuario']
      email = request.form['emailUsuario']
      senha = request.form['senhaUsuario']
      if selecao('LEITORES', 'NOME', 'NOME', '=', nome):
         return render_template('criacaoContas.html', erro='Já existe um usuário com esse nome.')
      insercao('LEITORES', ('NOME', 'EMAIL', 'SENHA'), (nome, email, senha))
      flash('Usuário criado com sucesso.')
      return redirect('/criacaoConta')


@app.route("/gerenciamentoConta", methods=["GET"])
def b():
   if not session.get("UserID") or not session.get("admin"):
      return redirect("/admin")
   return render_template('contasAdmin.html')

@app.route("/exclusaoConta", methods=["POST"])
def c(): 
   if not session.get("UserID") or not session.get("admin"):
      return redirect("/admin")
   idConta = request.form['idConta']
   logEmprestimos(idConta, False)
   remocao('EMPRESTIMOS', 'USERID = ', idConta)
   remocao('LEITORES', 'ID =', idConta)
   flash('Exclusão bem-sucedida.')
   return redirect('/gerenciamentoConta')

@app.route("/edicaoConta", methods=["POST"])
def d():
   if not session.get("UserID") or not session.get("admin"):
      return redirect("/admin")
   id = request.form['idConta']
   nome = request.form['nomeConta']
   email = request.form['emailConta'] 
   senha = request.form['senhaConta']
   selecaoRepeticao = selecao('LEITORES', 'NOME, ID', 'NOME', '=', nome)
   if selecaoRepeticao and selecaoRepeticao[0][1] != int(id):
      flash('Nome de usuário já existente.')
      return redirect('/gerenciamentoConta')
   atualizar('LEITORES', ('NOME', 'EMAIL', 'SENHA'), (f"'{nome}'", f"'{email}'", f"'{senha}'"), 'ID', '=', id, 3)  
   flash('Edição bem-sucedida.')
   return redirect('/gerenciamentoConta')
if __name__ == "__main__":
    iniciarDB()
    app.run(debug=True) 