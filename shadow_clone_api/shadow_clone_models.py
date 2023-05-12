"""This module contains Alchemy DB Models"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_object("config.DevConfig")
db = SQLAlchemy(app, session_options={"autoflush": False})


class Cohorts(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cohort_id = db.Column(db.String(64), unique=True, nullable=False)
    course = db.Column(db.String(12), unique=False, nullable=False)
    students = db.relationship("Students", backref="cohort")

    def __repr__(self):
        return "<Cohorts %r>" % self.cohort_id


class Students(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cohort_id = db.Column(
        db.String(64),
        db.ForeignKey("cohorts.cohort_id", ondelete="CASCADE", onupdate="CASCADE"),
    )
    github_id = db.Column(db.String(39), unique=False, nullable=False)

    def __repr__(self):
        return "<Students %r>" % self.github_id
