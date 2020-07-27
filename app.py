import json
import os
from datetime import datetime

from flask import (Flask, request, jsonify)
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS


app = Flask(__name__)

CORS(app)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_FILE_PATH = os.path.join(BASE_DIR, 'db.sqlite')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DB_FILE_PATH
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_title = db.Column(db.String(255))
    company_url = db.Column(db.String(512))
    job_url = db.Column(db.String(512))
    job_posting_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, job_title, company_url, job_url):
        self.job_title = job_title
        self.company_url = company_url
        self.job_url = job_url


@app.cli.command('db_create')
def db_create():
    db.create_all()
    db.session.commit()
    print('Database created!')


@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    db.session.commit()
    print('Database dropped!')


@app.cli.command('db_seed')
def db_seed():
    cwd = os.getcwd()
    for root, dirs, files in os.walk(cwd):
        for _file in files:
            if _file.endswith(".json"):
                with open(_file) as json_file:
                    jobs = json.load(json_file)
                    for job_ in jobs:
                        job = Job(job_['job_title'], job_['company_url'], job_['job_url'])
                        db.session.add(job)

    db.session.commit()
    print('Database seeded!')


class JobSchema(ma.Schema):
    class Meta:
        fields = ('id', 'job_title', 'company_url', 'job_url', 'job_posting_date',)


job_schema = JobSchema()
jobs_schema = JobSchema(many=True)


@app.route('/job', methods=['POST'])
def add_job():
    job_title = request.json['job_title']
    company_url = request.json['company_url']
    job_url = request.json['job_url']

    job = Job(job_title, company_url, job_url)

    db.session.add(job)
    db.session.commit()

    return job_schema.jsonify(job), 201


@app.route('/job', methods=['GET'])
def get_jobs():
    jobs = Job.query.all()
    resp = jsonify(jobs_schema.dump(jobs))

    return resp


@app.route('/job/<id>', methods=['GET'])
def get_job(id):
    job = Job.query.get(id)
    resp = job_schema.jsonify(job)

    return resp


@app.route('/job/<id>', methods=['PUT'])
def update_job(id):
    job = Job.query.get(id)

    job.job_title = request.json['job_title']
    job.company_url = request.json['company_url']
    job.job_url = request.json['job_url']

    db.session.commit()

    resp = job_schema.jsonify(job)

    return resp


@app.route('/job/<id>', methods=['DELETE'])
def delete_job(id):
    job = Job.query.get(id)

    db.session.delete(job)
    db.session.commit()

    resp = job_schema.jsonify(job)

    return resp


if __name__ == '__main__':
    app.run(debug=True)
