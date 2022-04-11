from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,  BooleanField, PasswordField
from wtforms.validators import DataRequired, URL
from flask_ckeditor import CKEditorField


##WTForm
class CreateForm(FlaskForm):

    plant_name = StringField("Plant Name", validators=[DataRequired()])
    price = StringField("Price", validators=[DataRequired()])
    img_url = StringField("Image URL", validators=[DataRequired(), URL()])
    title = StringField("Title", validators=[DataRequired(),])
    details = StringField('Details', [DataRequired(),])
    quantity = StringField('Quantity', [DataRequired(),])
    care_guide_code = StringField("Care Guide Code", validators=[DataRequired()])
    submit = SubmitField()


class CareGuideForm(FlaskForm):
    care_guide_code = StringField("Care Guide Code", validators=[DataRequired()])
    guide_detail = CKEditorField("Care Guide Details", validators=[DataRequired()])
    submit = SubmitField()


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    name = StringField("Name", validators=[DataRequired()])
    submit = SubmitField("Sign Me Up!")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Let Me In!")


class CommentForm(FlaskForm):
    comment_text = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Submit Comment")
