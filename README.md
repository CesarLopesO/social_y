Social Y

Social Y é uma rede social desenvolvida com o framework Flask e o banco de dados RethinkDB. Este projeto oferece funcionalidades de cadastro de usuários, envio de solicitações de amizade, compartilhamento de posts com suporte para upload de arquivos, e administração de usuários e departamentos.
Funcionalidades Principais

    Cadastro de Usuários: Permite que novos usuários se registrem com seus dados e departamentos.
    Sistema de Amizades: Adicione amigos pelo nome de usuário e envie solicitações de amizade.
    Posts: Os usuários podem compartilhar textos e fazer upload de arquivos, como imagens, que são codificadas em base64 e armazenadas no banco de dados.
    Departamentos: Os usuários são organizados por departamentos, e as permissões de visualização de posts são determinadas pela hierarquia de departamentos.
    Gerenciamento de Departamentos: Administradores podem adicionar novos departamentos diretamente pelo painel de administração.
    Hierarquia de Usuários:
        Administrador: Pode gerenciar todos os aspectos da rede social, incluindo usuários e departamentos.
        Gerente: Pode visualizar posts de todos os funcionários sob sua gerência e de outros departamentos.
        Funcionários: Podem visualizar posts apenas de usuários do mesmo departamento e de seu gerente.
    Sistema de Exclusão Mútua: Gerenciamento eficiente de acessos simultâneos em um arquivo central.

Estrutura do Banco de Dados

A Social Y utiliza o RethinkDB como banco de dados NoSQL, onde os dados são organizados em "tabelas". Alguns exemplos de tabelas utilizadas no projeto incluem:

    users: Armazena informações dos usuários, como nome, departamento e amigos.
    posts: Armazena os posts, incluindo os arquivos codificados em base64.
    friend_requests: Armazena as solicitações de amizade pendentes entre os usuários.
    departments: Armazena a estrutura hierárquica dos departamentos.

Tecnologias Utilizadas

    Backend: Flask (Python)
    Banco de Dados: RethinkDB
    Frontend: HTML5, CSS3, JavaScript
    Outras: Base64 (para codificação de arquivos de imagem), Sistema de Exclusão Mútua Distribuído

Como Executar o Projeto

    Clonar o repositório:

    bash

git clone https://github.com/seu-usuario/social-y.git
cd social-y

Instalar dependências:

Certifique-se de ter o Python e o RethinkDB instalados em sua máquina. Depois, instale as dependências do projeto:

bash

pip install -r requirements.txt

Iniciar o RethinkDB:

Inicie o servidor do RethinkDB:

bash

rethinkdb

O servidor será executado por padrão em http://localhost:8080.

Configurar as tabelas:

No console do RethinkDB, execute os seguintes comandos para configurar as tabelas:

javascript

r.db('test').tableCreate('users');
r.db('test').tableCreate('posts');
r.db('test').tableCreate('friend_requests');
r.db('test').tableCreate('departments');

Executar o projeto:

Execute o servidor Flask:

bash

flask run

A aplicação estará disponível em http://localhost:5000.