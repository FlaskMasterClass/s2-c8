import os
import pathlib
import flask
from flask import Flask
from flask import jsonify
from flask import request
from flask import render_template
from flask import redirect
from flask import url_for
from flask import current_app
from flask import flash
import click


from init import db
from init import ModelForm

from flask.cli import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)


from config import ProductionConfig
from config import DevelopmentConfig
from config import TestingConfig


profiles = {
    "development": DevelopmentConfig(),
    "production": ProductionConfig(),
    "testing": TestingConfig(),
}


def flash_errors(form):
    """Flashes form errors"""
    for field, errors in form.errors.items():
        for error in errors:
            flash(
                u"Error in the %s field - %s"
                % (getattr(form, field).label.text, error),
                "error",
            )


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String)


class UserForm(ModelForm):
    class Meta:
        model = User


def create_app(profile):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(profiles[profile])
    app.config.from_pyfile("config.py", silent=True)
    app.config["SECRET_KEY"] = os.urandom(24)

    db.init_app(app)

    if profile != "testing":
        app.config.from_pyfile("config.py", silent=True)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.shell_context_processor
    def shell():
        return {
            "db": db,
        }

    @app.route("/", methods=["GET", "POST"])
    def home():
        # for demo purposes
        try:
            db.create_all()
        except:
            pass 
        
        form = UserForm()
        users = User.query.all()
        if request.method == "POST":

            if form.validate_on_submit():
                u = User(name=form.data["name"])
                db.session.add(u)
                db.session.commit()
                return redirect(url_for("home"))
            else:
                flash_errors(form)
                return redirect(url_for("home"))
        return render_template("home.html", form=form, users=users)

    @app.route("/edit/<int:user_id>", methods=["GET", "POST"])
    def edit(user_id):
        user = User.query.get(user_id)
        form = UserForm(obj=user)
        if request.method == "POST":

            if form.validate_on_submit():
                form.populate_obj(user)
                db.session.commit()
                return redirect(url_for("home"))
            else:
                flash_errors(form)
                return redirect(url_for("home"))
        return render_template("edit.html", form=form, user=user)

    return app


flask_env = os.environ.get("FLASK_ENV", default="development")
app = create_app(flask_env)

if __name__ == "__main__":



    app.run(host="0.0.0.0", port=5011, debug=True, ssl_context='adhoc')
