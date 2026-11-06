import sqlite3
def iniciarDB():
    db = sqlite3.connect("./db/bookflow.db")
    db.execute("""
        CREATE TABLE IF NOT EXISTS LEITORES (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL,
        senha TEXT NOT NULL
        )
        """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS LIVROS (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        TITULO TEXT NOT NULL,
        AUTOR TEXT NOT NULL,
        GENERO TEXT NOT NULL,
        QUANTIDADE INTEGER
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS EMPRESTIMOS (
        ID INTEGER PRIMARY KEY AUTOINCREMENT,
        USERID INTEGER NOT NULL,
        BOOKID INTEGER NOT NULL,
        DATADEVOLUCAO DATE NOT NULL,
        DATAENTREGA DATE NOT NULL,
        ENTREGUE INTEGER NOT NULL DEFAULT 0 CHECK (ENTREGUE IN (0,1)),
        FOREIGN KEY (USERID) REFERENCES LEITORES(ID),
        FOREIGN KEY (BOOKID) REFERENCES LIVROS(ID)
        
        )
    """)
    db.commit()
    db.close()

def insercao(nomeTabela, colunas, valores):
    db = sqlite3.connect("./db/bookflow.db")
    db.execute("PRAGMA foreign_keys = ON")
    UserID = db.execute(f"INSERT INTO {nomeTabela} ({', '.join(colunas)}) VALUES ({', '.join('?' * len(valores))})", valores).lastrowid
    db.commit()
    db.close()
    return UserID

def selecao(tabela, coluna, campo='', operacao='', comparacao='', condicao=True, join=False, tabelaJoin = '', campo1Join = '', operacaoJoin = '', campo2Join = '', condicaoComplementar = False, campoComplemento = '', operacaoComplemento = '', comparacaoComplemento = ''):
    db = sqlite3.connect("./db/bookflow.db")
    db.execute("PRAGMA foreign_keys = ON")
    consulta = (f"SELECT {coluna} FROM {tabela}")
    valores = ()
    if join:
        consulta +=(f" JOIN {tabelaJoin} ON {campo1Join} {operacaoJoin} {campo2Join}")
    if condicao:
        consulta+=(f" WHERE {campo} {operacao} ?")
        valores+=(comparacao,)
    if condicaoComplementar:
        consulta+=(f" AND {campoComplemento} {operacaoComplemento} ?")
        valores+=(comparacaoComplemento,)
    resultado = db.execute(consulta, valores).fetchall()
    db.commit()
    db.close()
    return resultado

def atualizar(tabela, colunas, valores, condicaoCampo, condicaoOperacao, condicaoCampo2, contador):
    db = sqlite3.connect("./db/bookflow.db")
    db.execute("PRAGMA foreign_keys = ON")
    consulta = (f"UPDATE {tabela} SET ")
    for i in range (contador):
        if i !=0:
            consulta+=", "
        consulta+=(f"{colunas[i]} = {valores[i]}")
    consulta+=(f" WHERE {condicaoCampo} {condicaoOperacao} {condicaoCampo2}")
    print(consulta)
    db.execute(consulta)
    db.commit()
    db.close()

def remocao(tabela, condicao, valor):
    db = sqlite3.connect('./db/bookflow.db')
    db.execute('PRAGMA foreign_keys = ON')
    consulta = f"DELETE FROM {tabela} WHERE {condicao} ?"
    valores = (valor,)
    db.execute(consulta, valores)
    db.commit()
    db.close()





