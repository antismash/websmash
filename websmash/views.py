from flask import redirect, url_for, request, abort, \
                  render_template, jsonify
from flask.ext.mail import Message
import os
from os import path
from werkzeug import secure_filename
from websmash import app, mail, get_db
from websmash.utils import generate_confirmation_mail
from websmash.models import Job, Notice

@app.route('/', methods=['GET', 'POST'])
def new():
    redis_store = get_db()
    error = None
    results_path = app.config['RESULTS_URL']
    old_email = ''
    try:
        if request.method == 'POST':
            kwargs = {}
            kwargs['ncbi'] = request.form.get('ncbi', '').strip()
            kwargs['email'] = request.form.get('email', '').strip()
            old_email = kwargs['email']
            kwargs['from'] = request.form.get('from', '').strip()
            kwargs['to'] = request.form.get('to', '').strip()
            legacy = request.form.get('legacy', u'off')
            if legacy == u'on':
                raise Exception('Sorry, but running antiSMASH 1 is no longer supported')
            eukaryotic = request.form.get('eukaryotic', u'off')
            all_orfs = request.form.get('all_orfs', u'off')
            smcogs = request.form.get('smcogs', u'off')
            clusterblast = request.form.get('clusterblast', u'off')
            knownclusterblast = request.form.get('knownclusterblast', u'off')
            subclusterblast = request.form.get('subclusterblast', u'off')
            fullhmmer = request.form.get('fullhmmer', u'off')

            kwargs['genefinder'] = request.form.get('genefinder', 'prodigal')
            kwargs['trans_table'] = request.form.get('trans_table', 1, type=int)
            kwargs['gene_length'] = request.form.get('gene_length', 50, type=int)
            kwargs['from'] = request.form.get('from', 0, type=int)
            kwargs['to'] = request.form.get('to', 0, type=int)

            inclusive = request.form.get('inclusive', u'off')
            kwargs['inclusive'] = (inclusive == u'on')
            kwargs['cf_cdsnr'] = request.form.get('cf_cdsnr', 5, type=int)
            kwargs['cf_npfams'] = request.form.get('cf_npfams', 5, type=int)
            kwargs['cf_threshold'] = request.form.get('cf_threshold', 0.6, type=float)

            asf = request.form.get('asf', u'off')
            ecpred = request.form.get('ecpred', u'off')
            kwargs['modeling'] = request.form.get('modeling', u'none')

            # Always predict all sec met types
            kwargs['geneclustertypes'] = "1"

            # given that we only support antismash 3 at the moment, hardcode
            # that jobtype.
            kwargs['jobtype'] = 'antismash3'

            # Use boolean values instead of "on/off" strings
            kwargs['eukaryotic'] = (eukaryotic == u'on')
            kwargs['smcogs'] = (smcogs == u'on')
            kwargs['clusterblast'] = (clusterblast == u'on')
            kwargs['knownclusterblast'] = (knownclusterblast == u'on')
            kwargs['subclusterblast'] = (subclusterblast == u'on')
            kwargs['fullhmm'] = (fullhmmer == u'on')
            kwargs['asf'] = (asf == u'on')
            kwargs['ecpred'] = (ecpred == u'on')
            kwargs['all_orfs'] = (all_orfs == u'on')

            # Never run full-genome blast analysis
            kwargs['fullblast'] = False

            job = Job(**kwargs)
            dirname = path.join(app.config['RESULTS_PATH'], job.uid)
            os.mkdir(dirname)
            upload = None

            if kwargs['ncbi'] != '':
                job.download = kwargs['ncbi']
            else:
                upload = request.files['seq']

                if upload is not None:
                    filename = secure_filename(upload.filename)
                    upload.save(path.join(dirname, filename))
                    if not path.exists(path.join(dirname, filename)):
                        raise Exception("Could not save file!")
                    job.filename = filename
                else:
                    raise Exception("Uploading input file failed!")

            redis_store.hmset(u'job:%s' % job.uid, job.get_dict())
            redis_store.lpush('jobs:queued', job.uid)
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

        redis_store.hmset(u'job:%s' % job.uid, job.get_dict())
        redis_store.lpush('jobs:queued', job.uid)
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

@app.route('/status/<task_id>')
def status(task_id):
    redis_store = get_db()
    res = redis_store.hgetall(u'job:%s' % task_id)
    if res == {}:
        abort(404)
    job = Job(**res)
    if job.status == 'done':
        result_url = "%s/%s" % (app.config['RESULTS_URL'], job.uid)
        if job.jobtype == 'antismash':
            result_url += "/display.xhtml"
        else:
            result_url += "/index.html"
        res['result_url'] = result_url
    res['short_status'] = job.get_short_status()

    return jsonify(res)


@app.route('/server_status')
def server_status():
    redis_store = get_db()
    pending = redis_store.llen('jobs:queued')
    running = redis_store.llen('jobs:running')

    if pending + running > 0:
        status = 'working'
    else:
        status = 'idle'
    return jsonify(status=status, queue_length=pending, running=running)

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
