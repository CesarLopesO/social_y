Social Y
Idealização do Projeto

O Social Y é uma rede social corporativa desenvolvida em Flask e RethinkDB. Foi criada para promover a interação entre funcionários de diferentes departamentos de uma empresa, com funcionalidades de amizade, postagens e upload de arquivos. A plataforma possui uma hierarquia de usuários, composta por Administradores, Gerentes e Funcionários, onde cada nível tem permissões e visibilidade distintas.
Funcionalidades Principais:

    Cadastro de usuários: Possibilidade de cadastro de usuários, com seleção de departamentos.
    Sistema de amizade: Adição e aceitação de solicitações de amizade entre usuários.
    Postagens com upload de arquivos: Criação de posts e envio de arquivos, com imagens codificadas em base64.
    Hierarquia de acesso: Três níveis de usuários:
        Administrador: Pode criar departamentos e gerenciar usuários.
        Gerente: Pode ver as postagens de todos os funcionários de seu departamento.
        Funcionário: Pode ver apenas as postagens dos colegas de departamento e do gerente.
    Departamentos: Usuários pertencem a diferentes departamentos, influenciando a interação e visibilidade de posts.

Tecnologias Utilizadas:
Back-end:

    Flask: Framework para criação da API e gerenciamento de rotas.
    RethinkDB: Banco de dados NoSQL utilizado para armazenar as informações de usuários, posts, e pedidos de amizade.

Front-end:

    HTML/CSS: Para estruturar e estilizar as páginas da aplicação.
    JavaScript: Utilizado para interações dinâmicas e manipulação de DOM.
    Bootstrap: Framework CSS para design responsivo.
    jQuery: Para chamadas AJAX e interações do front-end.

Como Executar o Projeto
1-Pré-requisitos:

    Python 3.x
    Pip (gerenciador de pacotes do Python)
    RethinkDB instalado localmente

2-Passo a Passo para Execução

Clone o projeto:

    git clone git@github.com:CesarLopesO/social_y.git
    cd social_y

3-Crie e ative o ambiente virtual:


    python3 -m venv venv
    source venv/bin/activate  # No Windows, use venv\Scripts\activate

4- Instale as dependências:


    pip install -r requirements.txt

5- Configure o banco de dados RethinkDB:

Certifique-se de que o RethinkDB esteja rodando localmente:


    rethinkdb

As tabelas necessárias para o projeto serão criadas automaticamente ao rodar a aplicação, pois o setup do banco de dados está integrado no arquivo app.py.

6- Execute o servidor Flask:

    python3 app.py

7- Acesse a aplicação:

No navegador, vá para http://localhost:5000 para acessar o Social Y.