import os
import re

def update_html_links(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Atualiza links href que não começam com http, /, ou ..
    content = re.sub(r'href="(?!http|/|\.\.)([^"]+\.html)"', r'href="/\1"', content)
    
    # Atualiza redirecionamentos JavaScript
    content = re.sub(r'window\.location\.href\s*=\s*[\'"](?!http|/|\.\.)([^"\']+(\.html)?)[\'"]', r'window.location.href = "/\1"', content)
    
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def process_html_files():
    # Caminho para a pasta pages
    pages_dir = os.path.join(os.getcwd(), 'pages')
    
    # Lista todos os arquivos HTML na pasta pages
    html_files = [f for f in os.listdir(pages_dir) if f.endswith('.html')]
    
    # Atualiza cada arquivo
    for html_file in html_files:
        file_path = os.path.join(pages_dir, html_file)
        print(f"Atualizando links em: {html_file}")
        update_html_links(file_path)

if __name__ == '__main__':
    process_html_files()