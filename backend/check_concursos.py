from sqlalchemy import create_engine, text

engine = create_engine('sqlite:///petcloud_new.db')
with engine.connect() as conn:
    result = conn.execute(text('SELECT * FROM concursos'))
    rows = result.fetchall()
    
    print('\n=== Registros na tabela concursos ===')
    if rows:
        for row in rows:
            print(f'ID: {row[0]}, Pet ID: {row[1]}, User ID: {row[2]}, Imagem: {row[3]}')
    else:
        print('Nenhum registro encontrado')
    print(f'\nTotal: {len(rows)} registro(s)\n')
