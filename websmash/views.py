from flask import redirect, url_for, request, abort, \
                  render_template, jsonify
from flask.ext.mail import Message
import os
from os import path
from websmash import app, mail, get_db
from websmash.utils import generate_confirmation_mail, dispatch_job, _submit_job
from websmash.models import Job, Notice


@app.route('/', methods=['GET', 'POST'])
def new():
    error = None
    results_path = app.config['RESULTS_URL']
    old_email = ''
    try:
        if request.method == 'POST':
            job = dispatch_job()
            return redirect(url_for('.display', task_id=job.uid))
    except Exception, e:
        error = unicode(e)
    return render_template('new.html', error=error,
                           old_email=old_email,
                           results_path=results_path)

@app.route('/protein', methods=['GET', 'POST'])
def protein():
    redis_store = get_db()
    error = None
    results_path = app.config['RESULTS_URL']
    old_sequence = ''
    old_email = ''
    if request.method == 'GET':
        return render_template('new.html', error=error,
                               old_email=old_email,
                               old_sequence=old_sequence,
                               switch_to='prot',
                               results_path=results_path)

    try:
        kwargs = {}
        kwargs['prot-ncbi'] = request.form.get('prot-ncbi', '').strip()
        kwargs['email'] = request.form.get('email', '').strip()
        old_email = kwargs['email']
        # We always run all sec met types for the protein search
        kwargs['geneclustertypes'] = "1"
        # And we always run antiSMASH3 jobs for this
        kwargs['jobtype'] = 'antismash3'
        # And of course this is protein input
        kwargs['molecule'] = 'prot'

        smcogs = request.form.get('smcogs', u'off')
        asf = request.form.get('asf', u'off')
        kwargs['smcogs'] = (smcogs == u'on')
        kwargs['asf'] = (asf == u'on')

        job = Job(**kwargs)
        dirname = path.join(app.config['RESULTS_PATH'], job.uid)
        os.mkdir(dirname)

        if kwargs['prot-ncbi'] != '':
            job.download = kwargs['prot-ncbi']
        else:
            sequence = request.form.get('sequence', '').strip()
            old_sequence = sequence

            if len(sequence) == 0:
                raise Exception("No sequence specified")

            if sequence.count('>') < 1:
                raise Exception("No FASTA headers found")

            if sequence.count('\n') < 1:
                raise Exception("No newline between FASTA header and sequence")

            filename = path.join(dirname, 'protein_input.fa')
            with open(filename, 'w') as handle:
                handle.write(sequence)
            job.filename = 'protein_input.fa'

        _submit_job(redis_store, job)
        return redirect(url_for('.display', task_id=job.uid))

    except Exception, e:
        error = unicode(e)
    return render_template('new.html', error=error,
                           old_email=old_email,
                           old_sequence=old_sequence,
                           switch_to='prot',
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

@app.route('/display/<task_id>')
def display(task_id):
    redis_store = get_db()
    results_path = app.config['RESULTS_URL']
    res = redis_store.hgetall(u'job:%s' % task_id)
    if res == {}:
        abort(404)
    else:
        job = Job(**res)
    return render_template('display.html', job=job, results_path=results_path)

@app.route('/display')
def display_tab():
    return render_template('new.html',
                           sec_met_types=sec_met_types,
                           switch_to='job',
                           results_path=app.config['RESULTS_URL'])


@app.route('/current_notices')
def current_notices():
    "Display current notices"
    redis_store = get_db()
    rets = redis_store.keys('notice:*')
    notices = [ redis_store.hgetall(n) for n in rets]
    return jsonify(notices=notices)

@app.route('/show_notices')
def show_notices():
    "Show current notices"
    redis_store = get_db()
    rets = redis_store.keys('notice:*')
    notices = [Notice(**redis_store.hgetall(i)) for i in rets]
    return render_template('notices.html', notices=notices, skip_notices=True)
