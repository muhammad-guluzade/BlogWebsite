import os
from datetime import date
from flask import Flask, abort, render_template, redirect, url_for, flash, request, session
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from werkzeug.security import generate_password_hash, check_password_hash
from forms import CreatePostForm, RegisterForm, LoginForm, CommentForm
import sqlite3
import smtplib

from functions import *


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("FLASK_KEY")
ckeditor = CKEditor(app)
Bootstrap5(app)


# For adding profile images to the comment section
gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///posts.db")
app.secret_key = '123'


# Register new users into the User database
@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():

        conn = sqlite3.connect("./instance/posts.db")
        cursor = conn.cursor()

        # Check if user email is already present in the database.
        result = cursor.execute(f" SELECT * FROM users WHERE email='{form.email.data}' ").fetchone()

        if result:
            # User already exists
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))

        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        cursor.execute("INSERT INTO users (email, password, name) VALUES (?, ?, ?)", (form.email.data, hash_and_salted_password, form.name.data))

        conn.commit()

        result = cursor.execute("SELECT * FROM users").fetchall()[-1][0]

        # This line will authenticate the user with Flask-Login
        session['id'] = result
        session.modified = True

        return redirect(url_for("get_all_posts"))
    return render_template("register.html", form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():

        conn = sqlite3.connect("./instance/posts.db")
        cursor = conn.cursor()

        password = form.password.data
        result = cursor.execute(f"SELECT * FROM users WHERE email='{form.email.data}' ").fetchone()
        # Note, email in db is unique so will only have one result.
        # Email doesn't exist
        if not result:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        # Password incorrect
        elif not check_password_hash(result[2], password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            session['id'] = result[0]
            session.modified = True
            return redirect(url_for('get_all_posts'))

    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    session.pop("id")
    session.modified = True
    return redirect(url_for('get_all_posts'))


@app.route('/')
def get_all_posts():

    # print(session['id'])

    conn = sqlite3.connect("./instance/posts.db")
    cursor = conn.cursor()

    posts = cursor.execute("SELECT * FROM blog_posts").fetchall()
    authors = cursor.execute("SELECT * FROM users").fetchall()

    final_posts = []

    for post in posts:
        for author in authors:
            if post[1] == author[0]:
                final_posts.append((post, author[-1]))

    return render_template("index.html", all_posts=final_posts)


@app.route("/encrypt_decrypt_images", methods=["GET", "POST"])
def image_encrypt_decrypt():
    if request.method == "POST":
        image = request.files["image"]

        if "en" in request.form['action']:
            encrypt_image(image, f"./static/user_images/{request.files['image'].filename}", request.form['password'] )
        else:
            decrypt_image(image, request.form['password'], f"./static/user_images/{request.files['image'].filename}")

        return render_template("encrypt_decrypt.html", converted_image=f"./static/user_images/{request.files['image'].filename}")

    return render_template("encrypt_decrypt.html")


# Add a POST method to be able to post comments
@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):

    conn = sqlite3.connect("./instance/posts.db")
    cursor = conn.cursor()

    requested_post = cursor.execute(f"SELECT * FROM blog_posts WHERE id={post_id} ").fetchone()

    author_name = cursor.execute(f"SELECT name FROM users WHERE id={requested_post[1]}").fetchone()[0]

    comments = cursor.execute(f"SELECT * FROM comments WHERE post_id={post_id} ").fetchall()
    authors = cursor.execute(f"SELECT * FROM users").fetchall()

    final_comments = []

    # Add the CommentForm to the route
    comment_form = CommentForm()
    # Only allow logged-in users to comment on posts
    if comment_form.validate_on_submit():
        if 'id' not in session:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))

        cursor.execute("INSERT INTO comments (text, author_id, post_id) VALUES (?, ?, ?)", (comment_form.comment_text.data, session['id'], post_id))

        conn.commit()
        return redirect(f"/post/{post_id}")

    for comment in comments:
        for author in authors:
            if comment[-2] == author[0]:
                final_comments.append((comment[1], author[-1]))

    return render_template("post.html", post_id=post_id, post=requested_post, form=comment_form, author_name=author_name, comments=final_comments)


# Use a decorator so only an admin user can create new posts
@app.route("/new-post", methods=["GET", "POST"])
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():

        conn = sqlite3.connect("./instance/posts.db")
        cursor = conn.cursor()

        if form.img_url.data == "":
            image = "../static/assets/img/post-bg.jpg"
        else:
            image = form.img_url.data

        cursor.execute("INSERT INTO blog_posts (author_id, title, subtitle, date, body, img_url) VALUES (?, ?, ?, ?, ?, ?)", (session['id'], form.title.data, form.subtitle.data, date.today().strftime("%B %d, %Y"), form.body.data, image))
        conn.commit()

        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


# Use a decorator so only an admin user can edit a post
@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
def edit_post(post_id):

    conn = sqlite3.connect("./instance/posts.db")
    cursor = conn.cursor()

    post = cursor.execute(f"SELECT * FROM blog_posts WHERE id={post_id}")

    edit_form = CreatePostForm(

    )
    if edit_form.validate_on_submit():

        cursor.execute(f"UPDATE blog_posts SET title='{edit_form.title.data}', subtitle='{edit_form.subtitle.data}', img_url='{edit_form.img_url.data}', author_id={session['id']}, body='{edit_form.body.data}' WHERE id={post_id}")

        conn.commit()
        return redirect(url_for("show_post", post_id=post_id))
    return render_template("make-post.html", form=edit_form, is_edit=True)


# Use a decorator so only an admin user can delete a post
@app.route("/delete/<int:post_id>")
def delete_post(post_id):

    conn = sqlite3.connect("./instance/posts.db")
    cursor = conn.cursor()

    cursor.execute(f"DELETE FROM blog_posts WHERE id={post_id}")
    cursor.execute(f"DELETE FROM comments WHERE post_id={post_id}")
    conn.commit()

    return redirect(url_for('get_all_posts'))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method.upper() == "POST":
        with open("contact_things.txt", "a") as file:
            file.write(f"Name: {request.form['name']}\nEmail: {request.form['email']}\nPhone: {request.form['phone']}\nMessage: {request.form['message']}\n\n\n")
        flash("Your message was received successfully.")
        return redirect("/contact")

    return render_template("contact.html")



if __name__ == "__main__":
    app.run(debug=True, port=5001)
