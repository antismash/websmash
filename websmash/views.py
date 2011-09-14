from flask import redirect, url_for, request, session, g, abort, \
                  render_template, flash, jsonify
from flaskext.mail import Message
import os
from os import path
from sqlalchemy import or_
from datetime import datetime
from werkzeug import secure_filename
from websmash import app, db, mail, dl
from websmash.utils import generate_confirmation_mail
from websmash.models import Job, Notice

# Supported sec met cluster types. List of descriptions, the clusters
# are specified by a number in antismash.py
sec_met_types = ["all", "polyketides (type I)", "polyketides (type II)",
                 "polyketides (type III)", "nonribosomal peptides", "terpenes",
                 "lantibiotics", "bacteriocins", "beta-lactams",
                 "aminoglycosides / aminocyclitols", "aminocoumarins",
                 "siderophores", "ectoines", "butyrolactones", "indoles",
                 "nucleosides", "phosphoglycolipids", "melanins", "others"]

@app.route('/', methods=['GET', 'POST'])
def new():
    error = None
    results_path = app.config['RESULTS_URL']
    try:
        if request.method == 'POST':
            kwargs = {}
            kwargs['ncbi'] = request.form.get('ncbi', '').strip()
            kwargs['email'] = request.form.get('email', '').strip()
            kwargs['from'] = request.form.get('from', '').strip()
            kwargs['to'] = request.form.get('to', '').strip()
            eukaryotic = request.form.get('eukaryotic', u'off')
            smcogs = request.form.get('smcogs', u'off')
            clusterblast = request.form.get('clusterblast', u'off')
            fullblast = request.form.get('fullblast', u'off')
            fullhmmer = request.form.get('fullhmmer', u'off')
            kwargs['trans_table'] = request.form.get('trans_table', 1, type=int)
            kwargs['gene_length'] = request.form.get('gene_length', 50, type=int)
            i = 1
            clusters = []
            while(i < len(sec_met_types) + 1):
                if request.form.get("cluster_%s" % i, u'off') == u'on':
                    clusters.append(str(i))
                    if i == 1:
                        break
                i += 1
            if len(clusters) == 0:
                error_message  = "No gene cluster types specified. "
                error_message += "Please select the type of secondary "
                error_message += "metabolites to look for."
                raise Exception(error_message)
            kwargs['geneclustertypes'] = ",".join(clusters)

            # Use boolean values instead of "on/off" strings
            kwargs['eukaryotic'] = (eukaryotic == u'on')
            kwargs['smcogs'] = (smcogs == u'on')
            kwargs['clusterblast'] = (clusterblast == u'on')
            kwargs['fullblast'] = (fullblast == u'on')
            kwargs['fullhmm'] = (fullhmmer == u'on')

            job = Job(**kwargs)
            dirname = path.join(app.config['RESULTS_PATH'], job.uid)
            os.mkdir(dirname)
            upload = None

            if kwargs['ncbi'] != '':
                ncbi =  kwargs['ncbi']
                if kwargs['email'] != '':
                    email = kwargs['email']
                else:
                    email = app.config['DEFAULT_MAIL_SENDER']

                url = app.config['NCBI_URL'] % (email, ncbi)
                upload = dl.download(str(url))
                if upload is not None:
                    upload.filename = '%s.gbk' % ncbi
            else:
                upload = request.files['seq']

            if upload is not None:
                filename = secure_filename(upload.filename)
                upload.save(path.join(dirname, filename))
                job.filename = filename
            else:
                raise Exception("Downloading or uploading input file failed!")

            db.session.add(job)
            db.session.commit()
            return redirect(url_for('.display', task_id=job.uid))
    except Exception, e:
        error = unicode(e)
    return render_template('new.html', error=error,
                           sec_met_types=sec_met_types,
                           results_path=results_path)

@app.route('/about')
@app.route('/about.html')
def about():
    return render_template('about.html')

@app.route('/help')
@app.route('/help.html')
def help():
    return render_template('help.html')

@app.route('/download')
@app.route('/download.html')
def download():
    return render_template('download.html')

@app.route('/contact', methods=['GET', 'POST'])
@app.route('/contact.html', methods=['GET', 'POST'])
def contact():
    error = None
    email = ''
    message = ''
    try:
        if request.method == 'POST':
            email = request.form.get('email', '')
            message = request.form.get('body', '')
            if email == '':
                raise Exception("Please specify an email address")
            if message == '':
                raise Exception("No message specified. Please specify a message")

            contact_msg = Message(subject='antiSMASH feedback',
                                  recipients=app.config['DEFAULT_RECIPIENTS'],
                                  body=message, sender=email)
            mail.send(contact_msg)
            confirmation_msg = Message(subject='antiSMASH feedback received',
                                       recipients=[email],
                                       body=generate_confirmation_mail(message))
            mail.send(confirmation_msg)

            return render_template('message_sent.html', message=message)
    except Exception, e:
        error = unicode(e)
    return render_template('contact_form.html', error=error, email=email, message=message)

@app.route('/status.php')
def compat_status():
    """Allow to resolve old-style job status URLs"""
    task_id = request.args.get('user', '')
    return display(task_id)

@app.route('/display/<task_id>')
def display(task_id):
    results_path = app.config['RESULTS_URL']
    res = Job.query.filter_by(uid=task_id).first_or_404()
    return render_template('display.html', job=res, results_path=results_path)

@app.route('/server_status')
def server_status():
    jobcount = Job.query.filter(or_(Job.status.like('running%'),
                    Job.status == 'pending')).count()

    if jobcount > 0:
        status = 'working'
    else:
        status = 'idle'
    return jsonify(status=status, queue_length=jobcount)

@app.route('/current_notices')
def current_notices():
    "Display current notices"
    now = datetime.utcnow()
    notices = Notice.query.filter(Notice.show_from<=now).filter(Notice.show_until>=now).order_by(Notice.added).all()
    ret = [i.json for i in notices]
    return jsonify(notices=ret)
