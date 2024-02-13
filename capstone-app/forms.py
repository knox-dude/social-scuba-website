from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField, FloatField, SelectMultipleField, SelectField, RadioField, widgets, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Length, NumberRange

class DivesiteForm(FlaskForm):
    """Form for adding/editing divesites."""

    name = StringField('Name', validators=[DataRequired()])
    lat = FloatField('Latitude', validators=[DataRequired()])
    lng = FloatField('Longitude', validators=[DataRequired()])
    ocean = StringField('Ocean', validators=[DataRequired()])
    country = SelectField('Country', validators=[DataRequired()])
    continent = SelectField(choices=["Asia", "Africa", "Europe", "South America", "North America", "Oceania"], validators=[DataRequired()])
    location = StringField('Location')

class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class DiveForm(FlaskForm):
    """Form for adding dives."""

    dive_type_choices = [
        ("drysuit", "drysuit"), 
        ("night", "night"), 
        ("cave", "cave"), 
        ("wreck", "wreck"), 
        ("drift", "drift"), 
        ("ice", "ice"), 
        ("deep", "deep"), 
        ("technical", "technical"), 
        ("altitude", "altitude"), 
        ("muck", "muck")
    ]

    date = DateField('Date', validators=[DataRequired()])
    dive_type = MultiCheckboxField('Dive Type (select all that apply)', choices=dive_type_choices)
    rating = SelectField('Rating (1 worst, 10 best)', choices=[str(i) for i in range(1, 11)], validators=[DataRequired()])
    bottom_time = FloatField('Bottom Time (min.)', validators=[DataRequired(),
                                                               NumberRange(min=0, max=600, message='Value must be between 0 and 600')])
    max_depth = FloatField('Max depth', validators=[DataRequired(),
                                                    NumberRange(min=0, max=350, message='Value must be between 0 and 350')])
    depth_units = RadioField('Depth units', choices=['meters', 'feet'], validators=[DataRequired()])
    buddy_id = SelectField('Buddy', coerce=int, validators=[DataRequired()])
    comments = TextAreaField('Comments')

class DiveEditForm(FlaskForm):
    """Form for editing dives"""

    dive_type_choices = [
        ("drysuit", "drysuit"), 
        ("night", "night"), 
        ("cave", "cave"), 
        ("wreck", "wreck"), 
        ("drift", "drift"), 
        ("ice", "ice"), 
        ("deep", "deep"), 
        ("technical", "technical"), 
        ("altitude", "altitude"), 
        ("muck", "muck")
    ]

    date = DateField('Date', validators=[DataRequired()])
    dive_no = IntegerField('Dive Num:')
    dive_type = MultiCheckboxField('Dive Type (select all that apply)', choices=dive_type_choices)
    rating = SelectField('Rating (1 worst, 10 best)', choices=[str(i) for i in range(1, 11)], validators=[DataRequired()])
    bottom_time = FloatField('Bottom Time (min.)', validators=[DataRequired(),
                                                               NumberRange(min=0, max=600, message='Value must be between 0 and 600')])
    max_depth = FloatField('Max depth', validators=[DataRequired(),
                                                    NumberRange(min=0, max=350, message='Value must be between 0 and 350')])
    depth_units = RadioField('Depth units', choices=['meters', 'feet'], validators=[DataRequired()])
    buddy_id = SelectField('Buddy', coerce=int, validators=[DataRequired()])
    comments = TextAreaField('Comments')

class UserAddForm(FlaskForm):
    """Form for adding/editing users."""

    username = StringField('Username', validators=[DataRequired(), Length(min=3)])
    password = PasswordField('Password', validators=[Length(min=6)])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])

class UserEditForm(FlaskForm):
    """Form for editing existing users."""

    username = StringField('Username', validators=[DataRequired()])
    image_url = StringField('Image URL')
    header_image_url = StringField('Image Header URL')
    bio = TextAreaField('Bio')
    password = PasswordField('Enter Password to Confirm')

class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])
