from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, jsonify
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
    if not rdb.db_list().contains("mydatabase").run(conn):
        rdb.db_create("mydatabase").run(conn)
    if not rdb.db("mydatabase").table_list().contains("users").run(conn):
        rdb.db("mydatabase").table_create("users").run(conn)
    if not rdb.db("mydatabase").table_list().contains("posts").run(conn):
        rdb.db("mydatabase").table_create("posts").run(conn)

    admin_exists = rdb.db("mydatabase").table("users").filter({"username": "adm"}).count().run(conn)
    if admin_exists == 0:
        # Criar o superusuário "adm"
        rdb.db("mydatabase").table("users").insert({
            "username": "adm",
            "password": "123",  # Em um aplicativo real, você deve usar hashing de senhas
            "profile_picture": None,
            "is_admin": True
        }).run(conn)
        print("Superusuário 'adm' criado com sucesso.")


setup_db()


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

        # Obter todos os usuários e posts
        users = list(rdb.db("mydatabase").table("users").run(conn))
        posts = list(rdb.db("mydatabase").table("posts").run(conn))

        print("Usuário admin acessando a página de administração.")
        return render_template('admin.html', users=users, posts=posts)

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



@app.route('/signup', methods=['GET', 'POST'])
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        file = request.files['profile_picture']
        profile_picture = None

        if file and allowed_file(file.filename):
            profile_picture = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], profile_picture))

        # Verificar se o usuário já existe
        existing_user_cursor = rdb.db("mydatabase").table("users").filter({"username": username}).run(conn)
        if list(existing_user_cursor):
            return "Usuário já existe. Tente outro nome."

        # Criar um novo usuário com foto de perfil
        rdb.db("mydatabase").table("users").insert({
            "username": username,
            "password": password,
            "profile_picture": profile_picture  # Armazena o caminho da foto de perfil
        }).run(conn)

        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/feed')
def feed():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Ordenar os posts pelo campo "created_at" em ordem decrescente
    posts = list(rdb.db("mydatabase").table("posts").order_by(rdb.desc("created_at")).run(conn))

    return render_template('feed.html', posts=posts)




@app.route('/add_post', methods=['POST'])
def add_post():
    if 'username' in session:
        content = request.form['content']
        file = request.files['file']
        filename = None
        filetype = None

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_extension = filename.rsplit('.', 1)[1].lower()

            if file_extension in {'png', 'jpg', 'jpeg', 'gif'}:
                filetype = 'image'
            elif file_extension in {'mp4', 'mov', 'avi', 'mkv'}:
                filetype = 'video'
            else:
                filetype = 'document'

            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Recuperar a foto de perfil do usuário
        user_cursor = rdb.db("mydatabase").table("users").filter({"username": session['username']}).run(conn)
        user = list(user_cursor)[0]
        profile_picture = user.get('profile_picture', None)

        post_data = {
            "username": session['username'],
            "profile_picture": profile_picture,  # Armazena a foto de perfil no post
            "content": content,
            "likes": 0,
            "liked_by": [],
            "comments": [],
            "created_at": datetime.now().isoformat()
        }

        if filetype == 'image':
            post_data['image'] = filename
        elif filetype == 'video':
            post_data['video'] = filename
        elif filetype == 'document':
            post_data['document'] = filename

        rdb.db("mydatabase").table("posts").insert(post_data).run(conn)

    return redirect(url_for('feed'))



@app.route('/comment_post/<post_id>', methods=['POST'])
def comment_post(post_id):
    if 'username' in session:
        comment_content = request.form['comment']

        # Recuperar a foto de perfil do usuário
        user_cursor = rdb.db("mydatabase").table("users").filter({"username": session['username']}).run(conn)
        user = list(user_cursor)[0]
        profile_picture = user.get('profile_picture', None)

        comment = {
            "username": session['username'],
            "profile_picture": profile_picture,
            "content": comment_content,
            "created_at": datetime.now().isoformat()
        }

        # Adicionar o comentário ao post correspondente
        rdb.db("mydatabase").table("posts").get(post_id).update({
            "comments": rdb.row["comments"].append(comment)
        }).run(conn)

        # Renderizar apenas o novo comentário
        return render_template('comment_single.html', comment=comment)




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

    return render_template('profile.html', user=user)


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
