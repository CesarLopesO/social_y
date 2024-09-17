from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, jsonify, flash
import rethinkdb as r
from werkzeug.utils import secure_filename
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Necessário para usar sessões no Flask

# Configuração para upload de arquivos
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi', 'mkv', 'pdf', 'doc', 'docx', 'ppt', 'pptx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limite de 16MB para uploads

# Verifica se a pasta de uploads existe
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Inicializando a classe RethinkDB
rdb = r.RethinkDB()

# Conectar ao RethinkDB
conn = rdb.connect("localhost", 28015)


# Configuração inicial do banco de dados
def setup_db():
    # Criação das tabelas
    if not rdb.db("mydatabase").table_list().contains("users").run(conn):
        rdb.db("mydatabase").table_create("users").run(conn)
    if not rdb.db("mydatabase").table_list().contains("posts").run(conn):
        rdb.db("mydatabase").table_create("posts").run(conn)
    if not rdb.db("mydatabase").table_list().contains("departments").run(conn):
        rdb.db("mydatabase").table_create("departments").run(conn)
    if not rdb.db("mydatabase").table_list().contains("friend_requests").run(conn):
        rdb.db("mydatabase").table_create("friend_requests").run(conn)

    # Verifica se o admin já existe
    admin_exists = rdb.db("mydatabase").table("users").filter({"username": "adm"}).count().run(conn)
    if admin_exists == 0:
        # Criar o superusuário "adm"
        rdb.db("mydatabase").table("users").insert({
            "username": "adm",
            "password": "123",  # Em um aplicativo real, você deve usar hashing de senhas
            "role": "admin",
            "department": None,
            "profile_pic": None,
            "friends": []  # Lista de amigos
        }).run(conn)

        print("Superusuário 'adm' criado com sucesso.")
@app.route('/add_friend', methods=['POST'])
def add_friend():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Verificar se o usuário a ser adicionado existe
    to_user = request.form['to_user']
    user_cursor = rdb.db("mydatabase").table("users").filter({"username": to_user}).run(conn)
    user = list(user_cursor)

    if not user:
        flash('Usuário não encontrado.')
        return redirect(url_for('profile'))

    # Criar solicitação de amizade
    rdb.db("mydatabase").table("friend_requests").insert({
        "from_user": session['username'],
        "to_user": to_user,
        "status": "pending"
    }).run(conn)

    flash(f'Solicitação de amizade enviada para {to_user}!')
    return redirect(url_for('profile'))



@app.route('/accept_friend/<request_id>', methods=['POST'])
def accept_friend(request_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    # Atualizar o status da solicitação de amizade para 'accepted'
    rdb.db("mydatabase").table("friend_requests").get(request_id).update({
        "status": "accepted"
    }).run(conn)

    # Adicionar os usuários à lista de amigos um do outro
    friend_request = rdb.db("mydatabase").table("friend_requests").get(request_id).run(conn)
    from_user = friend_request['from_user']
    to_user = friend_request['to_user']

    # Adicionar amigo para o usuário atual (to_user)
    rdb.db("mydatabase").table("users").filter({"username": to_user}).update({
        "friends": rdb.row["friends"].default([]).append(from_user)
    }).run(conn)

    # Adicionar amigo para o usuário que enviou a solicitação (from_user)
    rdb.db("mydatabase").table("users").filter({"username": from_user}).update({
        "friends": rdb.row["friends"].default([]).append(to_user)
    }).run(conn)

    flash(f'Você e {from_user} agora são amigos!')
    return redirect(url_for('profile'))


@app.route('/reject_friend/<request_id>', methods=['POST'])
def reject_friend(request_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    # Excluir a solicitação de amizade
    rdb.db("mydatabase").table("friend_requests").get(request_id).delete().run(conn)

    flash('Solicitação de amizade recusada.')
    return redirect(url_for('profile'))


@app.route('/clear_database', methods=['POST'])
def clear_database():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Verificar se o usuário é admin
    user_cursor = rdb.db("mydatabase").table("users").filter({"username": session['username']}).run(conn)
    user = list(user_cursor)[0]

    if not user.get('is_admin'):
        return "Acesso negado.", 403

    # Limpar as tabelas de usuários e posts
    rdb.db("mydatabase").table("users").delete().run(conn)
    rdb.db("mydatabase").table("posts").delete().run(conn)

    # Recriar o superusuário "adm"
    rdb.db("mydatabase").table("users").insert({
        "username": "adm",
        "password": "123",  # Em um aplicativo real, você deve usar hashing de senhas
        "profile_picture": None,
        "is_admin": True
    }).run(conn)

    return redirect(url_for('admin'))



@app.route('/admin')
def admin():
    try:
        if 'username' not in session:
            print("Usuário não logado, redirecionando para login.")
            return redirect(url_for('login'))

        # Verificar se o usuário é admin
        user_cursor = rdb.db("mydatabase").table("users").filter({"username": session['username']}).run(conn)
        user = list(user_cursor)

        if not user:
            print("Usuário não encontrado.")
            return "Usuário não encontrado.", 404

        user = user[0]

        if not user.get('is_admin'):
            print("Acesso negado para o usuário:", user['username'])
            return "Acesso negado. Você não tem permissão para acessar esta página.", 403

        # Obter todos os usuários, posts e departamentos
        users = list(rdb.db("mydatabase").table("users").run(conn))
        posts = list(rdb.db("mydatabase").table("posts").run(conn))
        departments = list(rdb.db("mydatabase").table("departments").run(conn))  # Obter departamentos

        print("Usuário admin acessando a página de administração.")
        return render_template('admin.html', users=users, posts=posts, departments=departments)

    except Exception as e:
        print(f"Erro ao acessar a página de admin: {e}")
        return f"Ocorreu um erro ao tentar acessar a página de administração: {str(e)}", 500



@app.route('/delete_user/<user_id>', methods=['POST'])
def delete_user(user_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    # Verificar se o usuário é admin
    user_cursor = rdb.db("mydatabase").table("users").filter({"username": session['username']}).run(conn)
    user = list(user_cursor)[0]

    if not user.get('is_admin'):
        return "Acesso negado.", 403

    # Impedir a exclusão do próprio admin
    user_to_delete = rdb.db("mydatabase").table("users").get(user_id).run(conn)
    if user_to_delete['username'] == 'adm':
        return "Não é possível excluir o superusuário.", 403

    # Excluir o usuário
    rdb.db("mydatabase").table("users").get(user_id).delete().run(conn)

    return redirect(url_for('admin'))


@app.route('/delete_post/<post_id>', methods=['POST'])
def delete_post(post_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    # Verificar se o usuário é admin
    user_cursor = rdb.db("mydatabase").table("users").filter({"username": session['username']}).run(conn)
    user = list(user_cursor)[0]

    if not user.get('is_admin'):
        return "Acesso negado.", 403

    # Excluir o post
    rdb.db("mydatabase").table("posts").get(post_id).delete().run(conn)

    return redirect(url_for('admin'))


# Função auxiliar para verificar a extensão do arquivo
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def home():
    return redirect(url_for('login'))
@app.route('/test')
def test():
    return render_template('login.html')

def add_department(department_name):
    rdb.db("mydatabase").table("departments").insert({
        'name': department_name
    }).run(conn)
    print(f"Departamento {department_name} inserido com sucesso.")

def get_departments():
    return list(rdb.db("mydatabase").table("departments").run(conn))

@app.route('/admin/departments', methods=['GET', 'POST'])
def admin_departments():
    if request.method == 'POST':
        department_name = request.form['department']
        add_department(department_name)
        flash(f'Departamento {department_name} adicionado com sucesso!')

    departments = get_departments()
    return render_template('admin.html', departments=departments)
@app.route('/delete_department/<department_id>', methods=['POST'])
def delete_department(department_id):
    rdb.db("mydatabase").table("departments").get(department_id).delete().run(conn)
    flash('Departamento excluído com sucesso!')
    return redirect(url_for('admin'))  # Certifique-se de que 'admin' é a função que renderiza a página 'admin.html'




@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            # Verificar se o usuário existe no banco de dados
            user_cursor = rdb.db("mydatabase").table("users").filter({"username": username, "password": password}).run(conn)
            user = list(user_cursor)  # Converte o cursor para uma lista

            if user:  # Se o usuário existir
                session['username'] = username  # Armazena o nome do usuário na sessão
                print(user[0])  # Diagnóstico: verifique o que está sendo retornado para user[0]
                if user[0].get('is_admin'):  # Verifica se o usuário é admin
                    return redirect(url_for('admin'))
                else:
                    return redirect(url_for('feed'))
            else:
                return "Login inválido. Tente novamente."
        except Exception as e:
            print(f"Erro durante o login: {e}")
            return "Ocorreu um erro. Tente novamente mais tarde."

    return render_template('login.html')


import base64

import base64

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    departments = get_departments()  # Obtém todos os departamentos para exibir no dropdown

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        department = request.form['department']
        role = request.form['role']  # Usuário pode escolher apenas entre 'employee' e 'manager'

        # Upload da foto de perfil
        if 'profile_picture' not in request.files:
            flash('Nenhum arquivo de imagem enviado')
            return redirect(request.url)

        file = request.files['profile_picture']

        if file.filename == '':
            flash('Nenhum arquivo selecionado')
            return redirect(request.url)

        if file:
            # Converte a imagem para base64
            image_data = file.read()  # Lê os dados do arquivo
            encoded_image = base64.b64encode(image_data).decode('utf-8')  # Converte para base64

            # Salvar o usuário no banco de dados com a imagem em base64 e cargo
            rdb.db("mydatabase").table("users").insert({
                'username': username,
                'password': password,  # Deve ser hash em um app real
                'department': department,
                'role': role,  # Salva apenas 'employee' ou 'manager'
                'profile_pic': encoded_image  # Salva a imagem como string base64
            }).run(conn)

            flash('Conta criada com sucesso! Faça login para continuar.')
            return redirect(url_for('login'))

    return render_template('signup.html', departments=departments)

@app.route('/feed')
def feed():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Recupera o usuário logado e seu departamento
    user_cursor = rdb.db("mydatabase").table("users").filter({"username": session['username']}).run(conn)
    user = list(user_cursor)[0]
    user_department = user['department']  # Departamento do usuário logado
    user_role = user['role']  # Cargo do usuário (employee, manager, admin)
    friends = user.get("friends", [])  # Lista de amigos do usuário

    # Se o usuário for gerente, ele vê todos os posts, independentemente do departamento
    if user_role == 'manager':
        posts = list(rdb.db("mydatabase").table("posts").order_by(rdb.desc("created_at")).run(conn))

    # Se o usuário for funcionário, ele vê apenas posts de pessoas do mesmo departamento e dos amigos
    elif user_role == 'employee':
        # Posts do mesmo departamento
        department_posts = list(rdb.db("mydatabase").table("posts").filter(
            rdb.row['department'] == user_department
        ).order_by(rdb.desc("created_at")).run(conn))

        # Posts dos amigos
        friend_posts = list(rdb.db("mydatabase").table("posts").filter(
            lambda post: rdb.expr(friends).contains(post['username'])
        ).order_by(rdb.desc("created_at")).run(conn))

        # Combina posts do departamento e posts dos amigos
        posts = department_posts + friend_posts

        # Ordena por data de criação, do mais recente ao mais antigo
        posts = sorted(posts, key=lambda p: p['created_at'], reverse=True)

    return render_template('feed.html', posts=posts)










@app.route('/add_post', methods=['POST'])
def add_post():
    if 'username' in session:
        content = request.form['content']
        file = request.files['file']
        encoded_image = None

        if file and allowed_file(file.filename):
            image_data = file.read()
            encoded_image = base64.b64encode(image_data).decode('utf-8')

        # Recuperar as informações do usuário logado
        user_cursor = rdb.db("mydatabase").table("users").filter({"username": session['username']}).run(conn)
        user = list(user_cursor)[0]
        user_department = user['department']  # Atribuir o departamento do usuário ao post
        profile_picture = user.get('profile_pic', None)

        # Dados do post
        post_data = {
            "username": session['username'],
            "profile_pic": profile_picture,
            "content": content,
            "likes": 0,
            "liked_by": [],
            "comments": [],
            "created_at": datetime.now().isoformat(),
            "department": user_department  # Salva o departamento do usuário no post
        }

        if encoded_image:
            post_data['image'] = encoded_image

        # Inserir o post no banco de dados
        rdb.db("mydatabase").table("posts").insert(post_data).run(conn)

    return redirect(url_for('feed'))


@app.route('/comment_post/<post_id>', methods=['POST'])
def comment_post(post_id):
    if 'username' in session:
        comment_content = request.form['comment']

        # Recuperar a foto de perfil do usuário que está comentando
        user_cursor = rdb.db("mydatabase").table("users").filter({"username": session['username']}).run(conn)
        user = list(user_cursor)[0]
        profile_picture = user.get('profile_pic', None)  # Foto de perfil do usuário que comentou

        # Cria o objeto do comentário
        comment = {
            "username": session['username'],
            "profile_pic": profile_picture,  # Inclui a foto de perfil no comentário
            "content": comment_content,
            "created_at": datetime.now().isoformat()
        }

        # Adiciona o comentário ao post correspondente
        rdb.db("mydatabase").table("posts").get(post_id).update({
            "comments": rdb.row["comments"].append(comment)
        }).run(conn)

        # Renderizar apenas o novo comentário
        return render_template('comment_single.html', comment=comment)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS



@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/like_post/<post_id>', methods=['POST'])
def like_post(post_id):
    if 'username' in session:
        post = rdb.db("mydatabase").table("posts").get(post_id).run(conn)
        liked = session['username'] in post['liked_by']

        if liked:
            # Se o usuário já curtiu, descurtir
            rdb.db("mydatabase").table("posts").get(post_id).update({
                "likes": rdb.row["likes"] - 1,
                "liked_by": rdb.row["liked_by"].difference([session['username']])
            }).run(conn)
            liked = False
        else:
            # Se o usuário ainda não curtiu, curtir
            rdb.db("mydatabase").table("posts").get(post_id).update({
                "likes": rdb.row["likes"] + 1,
                "liked_by": rdb.row["liked_by"].append(session['username'])
            }).run(conn)
            liked = True

        # Retornar o número atualizado de curtidas
        post = rdb.db("mydatabase").table("posts").get(post_id).run(conn)
        return jsonify({"likes": post["likes"], "liked": liked})

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Recuperar o usuário logado do banco de dados
    user_cursor = rdb.db("mydatabase").table("users").filter({"username": session['username']}).run(conn)
    user = list(user_cursor)[0]

    # Recuperar solicitações de amizade pendentes onde o usuário é o destinatário
    friend_requests_cursor = rdb.db("mydatabase").table("friend_requests").filter(
        {"to_user": session['username'], "status": "pending"}
    ).run(conn)
    friend_requests = list(friend_requests_cursor)

    print("Solicitações de amizade pendentes:", friend_requests)  # Verificação

    return render_template('profile.html', user=user, friend_requests=friend_requests)


@app.route('/profile/<username>')
def view_profile(username):
    # Verificar se o usuário está logado
    if 'username' not in session:
        return redirect(url_for('login'))

    # Recuperar as informações do usuário do banco de dados
    user_cursor = rdb.db("mydatabase").table("users").filter({"username": username}).run(conn)
    user = list(user_cursor)

    if not user:
        return "Usuário não encontrado.", 404

    user = user[0]

    return render_template('profile.html', user=user)


if __name__ == '__main__':
    app.run(debug=True)
