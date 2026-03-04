import sqlite3
conn = sqlite3.connect('gestao.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY, nome TEXT, preco REAL, qtd INTEGER, min INTEGER)''')
produtos = [('Limão', 1.50, 100, 20), ('Laranja', 2.00, 150, 30), ('Âncora', 250.00, 5, 2), ('Viagra', 45.00, 30, 5), ('Siringa', 1.20, 500, 100), ('Poper', 60.00, 15, 3), ('Delivery', 10.00, 9999, 0), ('Pera', 3.50, 80, 15), ('Bong', 180.00, 10, 2), ('Pipe', 40.00, 25, 5)]
c.executemany("INSERT INTO produtos (nome, preco, qtd, min) VALUES (?, ?, ?, ?)", produtos)
conn.commit()
conn.close()
print("✅ Banco populado!")
