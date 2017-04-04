from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, \
    SubmitField, IntegerField
from wtforms.validators import Length, IPAddress, DataRequired


class EditSSHForm(FlaskForm):
    hostname = StringField('hostname', validators=[IPAddress(), DataRequired()])
    port = IntegerField('port', validators=[DataRequired()])
    username = StringField('username', validators=[Length(0, 64)])
    password = StringField('password', validators=[Length(0, 64)])
    command = StringField('command', validators=[Length(0, 64)])
    submit = SubmitField('Submit')


class RegexForm(FlaskForm):
    pattern = StringField('pattern', validators=[IPAddress(), DataRequired()])
    # state,type,output,alias,pos_x,pos_y
    alias = SelectField('名称',
                        choices=[('group1', 1), ('group2', 2), ('group3', 3), ('group4', 4),
                                 ('group5', 5)])
    State = SelectField('状态',
                        choices=[('group1', 1), ('group2', 2), ('group3', 3), ('group4', 4),
                                 ('group5', 5)])
    pos_x = SelectField('节点x',
                        choices=[('group1', 1), ('group2', 2), ('group3', 3), ('group4', 4),
                                 ('group5', 5)])
    pos_y = SelectField('节点y',
                        choices=[('group1', 1), ('group2', 2), ('group3', 3), ('group4', 4),
                                 ('group5', 5)])
    output = SelectField('节点info',
                         choices=[('group1', 1), ('group2', 2), ('group3', 3), ('group4', 4),
                                  ('group5', 5)])

    submit = SubmitField('Submit')
