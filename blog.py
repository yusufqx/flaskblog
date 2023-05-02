from flask import *
from flask_mysqldb import *
from wtforms import *
from functools import *
from flask_wtf import *
from itsdangerous import *
from wtforms.validators import *
from flask_mail import *
import hashlib


app=Flask(__name__)


app.secret_key="firstblog"
app.config["MYSQL_HOST"]= "localhost"
app.config["MYSQL_USER"]= "root"
app.config["MYSQL_PASSWORD"]= ""
app.config["MYSQL_DB"]= "firstblog"
app.config["MYSQL_CURSORCLASS"]= "DictCursor"
app.config['SECRET_KEY'] = 'your_secret_key'



mysql=MySQL(app)







    
#kullanıcı girişi decorator'ı
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu Sayfayı Görüntülemek İçin Lütfen Giriş Yapın","danger")
            return redirect(url_for("login"))
    return decorated_function


class RegisterForm(Form):
    name = StringField("İsim Soyisim", [validators.Length(min=4, max=25)])
    username = StringField("Kullanıcı Adı", [validators.Length(min=5, max=32)])
    email = StringField("E-posta Adresi", [validators.Email(message="Lütfen E-posta Adresinizi Kontrol Edin"), validators.DataRequired()])
    password = PasswordField("Parola:", [validators.DataRequired(), validators.EqualTo('confirm', message='Parolanız Uyuşmuyor')])
    confirm = PasswordField("Parola Doğrula")


    
class LoginForm(Form):
    username=StringField("Kullanıcı Adınız:")
    password=PasswordField("Şifreniz:")

 

@app.route("/")

def index():

    information = [
    {"id":1, "name":"python1", "content":"flask1"},
    {"id":2, "name":"python2", "content":"flask2"},
    {"id":3, "name":"python3", "content":"flask3"}
    ]
    return render_template("index.html", information = information)  
    
@app.route("/x-index")
def index2():
    return render_template("x-index.html")

@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles"

    result = cursor.execute(sorgu)

    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html",articles=articles)

    else:
        return render_template("articles.html")

@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "Select * From articles where author=%s"

    result = cursor.execute(sorgu,(session["username"],))

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles=articles)
    else:
        return render_template("dashboard.html")

    return render_template("dashboard.html")    


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = form.password.data
        hashed_password = hashlib.sha256(password.encode()).hexdigest()

        # Check if the username is already taken
        cursor = mysql.connection.cursor()
        sorgu = "SELECT * FROM users WHERE username = %s"
        result = cursor.execute(sorgu, (username,))
        if result > 0:
            flash("Bu kullanıcı adı zaten alınmış, lütfen farklı bir kullanıcı adı seçin", "danger")
            return redirect(url_for("register"))

        sorgu = "INSERT INTO users(name, username, email, password) VALUES (%s, %s, %s, %s)"
        cursor.execute(sorgu, (name, username, email, hashed_password))
        mysql.connection.commit()
        cursor.close()

        flash("Başarıyla Kayıt Oldunuz", "success")
        return redirect(url_for("index"))
    else:
        return render_template("register.html", form=form)

@app.route("/login",methods=["GET","POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():

        username = form.username.data
        password = form.password.data

        cursor = mysql.connection.cursor()

        sorgu = "Select * from users where username = %s"

        result = cursor.execute(sorgu,(username,))
        
        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]
            if form.password.data:
                flash("Başarıyla Giriş Yaptınız..","success")

                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for("index"))
            else:
                flash("Parolanızı Yanlış Girdiniz","danger")
                return redirect(url_for("login"))
        else:
            flash("Böyle Bir Kullanıcı Adı Yok","danger")
            return redirect(url_for("login"))


    return render_template("login.html",form=form)



@app.route("/article/<string:id>")
def article(id):

    cursor = mysql.connection.cursor()

    sorgu = "Select * from articles where id=%s"

    result = cursor.execute(sorgu,(id,))

    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html",article=article)
    else:
        return render_template("article.html")
#çıkış (log out) işlemi

@app.route("/logout")
def logout():
    session.clear()
    flash("Çıkış Yaptınız","danger")
    return redirect(url_for("index"))


@app.route("/addarticle",  methods=["GET","POST"])
def addarticle():
    form = ArticleForm(request.form)
    if request.method=="POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()

        sorgu = "Insert into articles(title,author,content) VALUES(%s,%s,%s)"

        cursor.execute(sorgu,(title,session["username"],content))

        mysql.connection.commit()

        cursor.close()
        flash("Yorum Başarıyla Eklendi","success")

        return redirect(url_for("dashboard"))
    return render_template("addarticle.html", form=form)


#arama 

@app.route("/search",methods=["GET","POST"])
def search():
    if request.method == "GET":
        return redirect(url_for("index"))
    else:
        keyword = request.form.get("keyword")

        
        cursor = mysql.connection.cursor()

        sorgu = "Select * from articles where title like '%" + keyword + "%' "

        result = cursor.execute(sorgu)

        if result == 0:
            flash("Böyle Bir Makale Bulunmuyor","warning")
            return redirect(url_for("articles"))
        else:
            articles = cursor.fetchall()

            return render_template("articles.html",articles=articles)


#makale değiştirme

@app.route("/edit/<string:id>", methods=["GET", "POST"])
@login_required
def update(id):
    if request.method== "GET":

        cursor = mysql.connection.cursor()
        
        sorgu = "Select * from articles where id=%s and author=%s"
        result = cursor.execute(sorgu,(id, session["username"]))

        if result == 0:
            flash("Böyle Bir Makale veya Buna Yetkiniz Yok","danger")
            return redirect(url_for("index"))
            
        else:
            article = cursor.fetchone()
            form = ArticleForm()

            form.title.data = article["title"]
            form.content.data = article["content"]
            return render_template("update.html",form=form)
    else:
        form = ArticleForm(request.form)

        newTitle = form.title.data
        newContent = form.content.data

        sorgu2 = "Update articles set title=%s, content=%s where id=%s"

        cursor = mysql.connection.cursor()

        cursor.execute(sorgu2,(newTitle,newContent,id))

        mysql.connection.commit()

        flash("Makale Başarıyla Güncellendi","success")

        return redirect(url_for("dashboard"))
        


#makale silme

@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()
    sorgu = "Select * from articles where author=%s and id=%s"
    result = cursor.execute(sorgu,(session["username"],id))
    if result > 0:
        sorgu2= "Delete from articles where id=%s"
        cursor.execute(sorgu2,(id,))

        mysql.connection.commit()
        flash("Makale Başarıyla Silindi","success")
        return redirect(url_for("dashboard"))

    else:
        flash("Böyle Bir Makale veya Bu İşleme Yetkiniz Yok","danger")
        return redirect(url_for("dashboard"))
class ArticleForm(Form):
    title = StringField("Makale Başlığı",validators=[
        validators.Length(min=5, max=100)
    ])

    content = TextAreaField("Makale İçeriği",validators=[
        validators.Length(min=10)
    ])

"""
def send_reset_email(user):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    token = serializer.dumps(user.email, salt='password-reset')

    message = Message('Şifre Sıfırlama İsteği - [Uygulama Adı]', sender='noreply@example.com', recipients=[user.email])
    message.body = f'''Merhaba {user.username},

Aşağıdaki bağlantıya tıklayarak şifrenizi sıfırlayabilirsiniz:
{url_for('new_password', token=token, _external=True)}

Eğer şifrenizi hatırlıyorsanız bu e-postayı görmezden gelebilirsiniz.

Saygılarımla,
[Breka]'''

    mail.send(message)

"********************************************************************************"


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Şifre', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Şifreyi Doğrula', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Şifreyi Yenile')
    

class NewPasswordForm(FlaskForm):
    password = PasswordField('Yeni Şifre', validators=[
        DataRequired(),
        Length(min=8),
        EqualTo('confirm', message='Şifreler Eşleşmiyor')
    ])
    confirm = PasswordField('Şifre Tekrarı', validators=[DataRequired()])
    submit = SubmitField('Şifre Değiştir')


def generate_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECURITY_PASSWORD_SALT'])


def send_reset_email(user):
    token = generate_token(user.email)
    msg = Message('Şifre Sıfırlama Bağlantısı', recipients=[user.email])
    reset_url = url_for('new_password', token=token, _external=True)
    msg.body = f'''Merhaba {user.username},
    
    Şifrenizi sıfırlamak için aşağıdaki bağlantıya tıklayın:
    {reset_url}
    
    Eğer şifre sıfırlama işlemi yapmak istemediyseniz, bu e-postayı dikkate almayabilirsiniz.
    '''
    mail.send(msg)
"""


"********************************************************************************"


"********************************************************************************"


if __name__=="__main__":
    app.run(debug=True)