from io import BytesIO
from PIL import Image, ImageOps
from database import selecao
from datetime import datetime

def processarImagem(arquivo):
    img = Image.open(arquivo)
    img = ImageOps.exif_transpose(img)
    img = img.convert("RGB")
    img = ImageOps.fit(img, (520, 780))
    saida = BytesIO()
    img.save(saida, "JPEG", quality=85, optimize=True)
    return saida.getvalue()

def logEmprestimos(id, condicao):
      campoExclusao = 'BOOKID' if condicao else 'USERID'
      linhas = selecao('EMPRESTIMOS', 'NOME, TITULO, DATAENTREGA, DATADEVOLUCAO, ENTREGUE', campoExclusao, '=', id, True, True, 'LEITORES', 'USERID', '=', 'LEITORES.ID JOIN LIVROS ON BOOKID = LIVROS.ID')
      with open('./logs/emprestimosExcluidos.txt', 'a', encoding='UTF-8') as f:
           for x in linhas:
                f.write(f"Leitor: {x[0]}, Livro: {x[1]}, Retirada: {x[2]}, Devolução: {x[3]}, Entregue? {'Sim' if int(x[4]) else 'Não'}, {datetime.now()} \n")

