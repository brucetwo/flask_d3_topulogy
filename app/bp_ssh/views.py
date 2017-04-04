from flask import render_template, redirect, url_for, abort, flash, request, \
    current_app, session
from flask_login import login_required
from . import bp_ssh
from .forms import  EditSSHForm, RegexForm
from .. import db
from ..models import Ssh, RegexSsh
import paramiko

# 执行远程命令
# ssh = paramiko.SSHClient()
# ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# ssh.connect("某IP地址", 22, "用户名", "口令")
# stdin, stdout, stderr = ssh.exec_command("你的命令")
# stdout.readlines()
# ssh.close()

# 上传文件到远程
# t = paramiko.Transport(("某IP地址", 22))
# t.connect(username="用户名", password="口令")
# sftp = paramiko.SFTPClient.from_transport(t)
# remotepath = '/tmp/test.txt'
# localpath = '/tmp/test.txt'
# sftp.put(localpath, remotepath)
# t.close()

# 从远程下载
# t = paramiko.Transport(("某IP地址", 22))
# t.connect(username="用户名", password="口令")
# sftp = paramiko.SFTPClient.from_transport(t)
# remotepath = '/tmp/test.txt'
# localpath = '/tmp/test.txt'
# sftp.get(remotepath, localpath)
# t.close()


@bp_ssh.route('/', methods=['GET', 'POST'])
@login_required
def editssh():
    sshForm = EditSSHForm()
    readLines = None
    if sshForm.validate_on_submit():
        ssh = Ssh(hostname=sshForm.hostname.data, port=sshForm.port.data, username=sshForm.username.data,
                  password=sshForm.password.data,
                  command=sshForm.command.data)
        readLines = Ssh.exec(sshForm.hostname.data, sshForm.port.data, sshForm.username.data, sshForm.password.data,
                             command=sshForm.command.data)
        if readLines:
            db.session.add(ssh)
            db.session.commit()
            session['readLines']=readLines
            return redirect(url_for('.regex', id=ssh.id))
            flash('ssh success')
    return render_template('edit_post.html', sshForm=sshForm)

@bp_ssh.route('/regex/<int:id>')
@login_required
def regexSsh(id):
    regexForm = RegexForm()
    if regexForm.validate_on_submit():
        ssh = Ssh.query.filter_by(id=id).first_or_404()
        return redirect(url_for('topulogy.index'))
        flash('changessh success')

    return render_template('edit_post.html', regexForm=regexForm, readLines=session.get('readLines'))

