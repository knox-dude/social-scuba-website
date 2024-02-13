import os
from flask import Flask, render_template, request, flash, redirect, session, g, jsonify
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from models import db, connect_db, User, Dive, Divesite, Buddy, Divetype
from forms import UserAddForm, UserEditForm, LoginForm, DiveForm, DiveEditForm, DivesiteForm
from secret import SECRET_KEY, GOOGLE_API_KEY

CURR_USER_KEY = "curr_user"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql:///social-scuba-app')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False

connect_db(app)

with app.app_context():
    db.create_all()

app.config['SECRET_KEY'] = SECRET_KEY

##############################################################################
# User signup/login/logout

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None

def do_login(user):
    """Log in user."""
    session[CURR_USER_KEY] = user.id

def do_logout():
    """Logout user."""
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.

    Create new user and add to DB. Redirect to home page.

    If form not valid, present form.

    If there already is a user with that username: flash message and re-present form.
    """

    form = UserAddForm()

    if form.validate_on_submit():

        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data
            )
            db.session.commit()

        except IntegrityError:
            flash("Username already in use", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)
    
@app.route('/login', methods=["GET", "POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)

@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()
    return redirect("/")

##############################################################################
# API routes and routes for Google Maps integration:

def generate_static_map_url(lat, lng):
    # Gets static map for individual dive
    map_size = '800x400'
    zoom_level = 11

    static_map_url = f'https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom={zoom_level}&size={map_size}&markers={lat},{lng}&key={GOOGLE_API_KEY}'

    return static_map_url

@app.route("/get_dive_sites")
def get_divesites():
    """Returns JSON of divesites in specified map bounds"""

    # Get NE and SW latitude and longitude values from query parameters
    ne_lat = float(request.args.get('ne_lat'))
    ne_lng = float(request.args.get('ne_lng'))
    sw_lat = float(request.args.get('sw_lat'))
    sw_lng = float(request.args.get('sw_lng'))

   # Fetch divesites within the specified bounds from the database
    divesites = Divesite.query.filter(
        Divesite.lat.between(sw_lat, ne_lat),
        Divesite.lng.between(sw_lng, ne_lng)
    ).all()

    json_to_return = []
    for site in divesites:
        json_to_return.append({
            "id":site.id,
            "name":site.name,
            "latitude":site.lat,
            "longitude":site.lng
        })
    return jsonify(json_to_return)

##############################################################################
# General user routes:

@app.route('/search')
def search():
    """Page with listing of either users or divesites.
    Takes a 'category' param to determine which database to search, users or divesites.
    Takes a 'q' param in querystring to search by that divesite/username.
    Takes a 'pagination' param for pagination.
    """
    search = request.args.get('q')
    category = request.args.get('category')

    # Set the page number from the query parameter, default to 1
    page = request.args.get('page', 1, type=int)
    per_page = 12

    if category == "users":
        if not search:
            pagination = User.query.paginate(page=page, per_page=per_page, error_out=False)
        else:
            pagination = User.query.filter(User.username.ilike(f"%{search}%")).paginate(page=page, per_page=per_page, error_out=False)

        return render_template('users/index.html', users=pagination.items, pages=pagination, search=search, category=category)
    
    else:
        if not search:
            pagination = Divesite.query.paginate(page=page, per_page=per_page, error_out=False)
        else:
            pagination = Divesite.query.filter(Divesite.name.ilike(f"%{search}%")).paginate(page=page, per_page=per_page, error_out=False)

        return render_template('divesites/index.html', divesites=pagination.items, pages=pagination, search=search, category=category)

@app.route('/users/<int:user_id>')
def users_show(user_id):
    """Show user profile."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)

    if not user:
        flash("No user found.", "danger")

    max_depth = user.get_max_depth()
    max_bottom_time = user.get_max_bottom_time()
    countries = user.get_unique_country_count()
    continents = user.get_unique_continent_count()

    # TODO remove messages and get dives
    # user.messages won't be in order by default
    dives = (Dive
                .query
                .filter(Dive.user_id == user_id)
                .order_by(Dive.date.desc())
                .limit(100)
                .all()
            )
    
    return render_template(
                'users/show.html',
                user=user, 
                dives=dives, 
                max_depth=max_depth, 
                max_bottom_time=max_bottom_time,
                countries=countries,
                continents=continents
            )

@app.route('/users/delete', methods=["POST"])
def delete_user():
    """Delete user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    do_logout()

    db.session.delete(g.user)
    db.session.commit()

    return redirect("/signup")

@app.route('/users/<int:user_id>/buddies')
def show_buddies(user_id):
    """Show list of people this user has added as buddies."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/buddies.html', user=user)

@app.route('/users/<int:user_id>/buddies-to')
def show_buddies_to(user_id):
    """Show list of users who have added this user as a buddy."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    user = User.query.get_or_404(user_id)
    return render_template('users/buddies_to.html', user=user)

@app.route('/users/add-buddy/<int:buddy_id>', methods=["POST"])
def add_buddy(buddy_id):
    """Adds a user as a buddy."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    followed_user = User.query.get_or_404(buddy_id)
    g.user.buddies.append(followed_user)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/buddies")

@app.route('/users/remove-buddy/<int:buddy_id>', methods=['POST'])
def remove_buddy(buddy_id):
    """Have currently-logged-in-user remove other user from their buddy list."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    buddy_to_remove = User.query.get(buddy_id)
    g.user.buddies.remove(buddy_to_remove)
    db.session.commit()

    return redirect(f"/users/{g.user.id}/buddies")

@app.route('/users/profile', methods=["GET", "POST"])
def profile():
    """Update profile for current user."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    form = UserEditForm(obj=g.user)

    if form.validate_on_submit():

        # checks password field is correct
        current_user = User.authenticate(g.user.username, form.password.data)

        if not current_user:
            flash("Incorrect Password", "danger")
            return redirect("/")
        
        #checks if new username is available
        if form.username.data != g.user.username:
            existing_user = User.query.filter(User.username==form.username.data).all()
            if existing_user:
                flash('Username is already taken', 'warning')
                return redirect("/users/profile")

        g.user.username = form.username.data
        g.user.image_url = form.image_url.data
        g.user.header_image_url = form.header_image_url.data
        g.user.bio = form.bio.data

        db.session.commit()
        flash('Profile successfully updated', 'success')
        return redirect(f"/users/{g.user.id}")

    return render_template("/users/edit.html", form=form)

##############################################################################
# General divesite routes:

@app.route("/divesites/map")
def view_map():
    """Shows map of all divesites"""
    return render_template("divesites/map.html", GOOGLE_API_KEY=GOOGLE_API_KEY)

@app.route('/divesites/new', methods=['GET', 'POST'])
def add_divesite():
    "Add a divesite through POST request, or show form for adding divesite"

    from pycountry import countries
    countries = [country.name for country in countries]

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    form = DivesiteForm()
    form.country.choices = countries

    if form.validate_on_submit():
        divesite = Divesite(
            name = form.name.data,
            lat = form.lat.data,
            lng = form.lng.data,
            ocean = form.ocean.data,
            country = form.country.data,
            continent = form.continent.data,
            location = form.location.data,
            api_id = str(g.user.id)
        )
        db.session.add(divesite)
        db.session.commit()

        return redirect(f"/divesites/{divesite.id}")
    
    return render_template("divesites/new.html", form=form)

@app.route("/divesites/<int:divesite_id>")
def show_divesite(divesite_id):
    """Shows info on a single divesite"""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    divesite = Divesite.query.get_or_404(divesite_id)
    static_map = generate_static_map_url(divesite.lat, divesite.lng)

    return render_template("divesites/show.html", user=g.user, divesite=divesite, static_map=static_map)

@app.route("/divesites/<int:divesite_id>/delete", methods=["POST"])
def delete_divesite(divesite_id):
    """Deletes a divesite. Only works if user originally created the divesite"""

    divesite = Divesite.query.get_or_404(divesite_id)

    if not g.user or divesite.api_id != str(g.user.id):
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    db.session.delete(divesite)
    db.session.commit()

    flash("Divesite deleted.", "warning")
    return redirect("/")

##############################################################################
# General dive routes:

def _create_divetype_dict(data):
    """Creates a dictionary to help create a Divetype object"""
    all_divetypes = set(["drysuit", "night", "cave", "wreck", "drift", "ice", "deep", "technical", "altitude", "muck"])
    types_to_add = set(data)
    types_to_not_add = all_divetypes - types_to_add
    returned_dict = dict()

    for type in types_to_add:
        returned_dict[type] = True

    for type in types_to_not_add:
        returned_dict[type] = False

    return returned_dict

@app.route('/divesites/<int:divesite_id>/new', methods=['GET', 'POST'])
def add_dive(divesite_id):
    "Add a dive, after already choosing divesite"

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    form = DiveForm()

    # Lets users choose one of their buddies, or no buddy
    form.buddy_id.choices = [(-1, 'No buddy')]
    form.buddy_id.choices += [(buddy.id, buddy.username) for buddy in g.user.buddies]

    if form.validate_on_submit():

        # convert meters to feet
        max_depth = form.max_depth.data
        if form.depth_units.data == 'meters':
            max_depth = max_depth * 3.28084

        dive = Dive(
            user_id = g.user.id,
            dive_no=len(g.user.dives)+1,
            divesite_id = divesite_id,
            date = form.date.data,
            rating = form.rating.data,
            bottom_time = form.bottom_time.data,
            max_depth = max_depth,
            buddy_id = form.buddy_id.data,
            comments = form.comments.data
        )
        
        # Make sure "no buddy" gets entered in as null
        if dive.buddy_id == -1:
            dive.buddy_id = None

        db.session.add(dive)
        db.session.commit()

        # Handle dive types (create Divetype obj)
        dive_types_dict = _create_divetype_dict(form.dive_type.data)

        divetype = Divetype(
            dive_id = dive.id,
            drysuit = dive_types_dict["drysuit"],
            night = dive_types_dict["night"],
            cave = dive_types_dict["cave"],
            wreck = dive_types_dict["wreck"],
            drift = dive_types_dict["drift"],
            ice = dive_types_dict["ice"],
            deep = dive_types_dict["deep"],
            technical = dive_types_dict["technical"],
            altitude = dive_types_dict["altitude"],
            muck = dive_types_dict["muck"]
        )

        db.session.add(divetype)
        db.session.commit()

        return redirect(f'/users/{g.user.id}')
    
    return render_template('dives/new.html', form=form)

@app.route('/dives/<int:dive_id>', methods=["GET"])
def dives_show(dive_id):
    """Show a dive."""

    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

    dive = Dive.query.get_or_404(dive_id)
    static_map = generate_static_map_url(dive.divesite.lat, dive.divesite.lng)
    return render_template('dives/show.html', dive=dive, static_map=static_map)

@app.route('/dives/<int:dive_id>/edit', methods=['GET', 'POST'])
def dives_edit(dive_id):
    """Edits a user's dive"""

    dive = Dive.query.get_or_404(dive_id)

    if not g.user or dive.diver.id != g.user.id:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    form = DiveEditForm(obj=dive)

    # Lets users choose one of their buddies, or no buddy
    form.buddy_id.choices = [(-1, 'No buddy')]
    form.buddy_id.choices += [(buddy.id, buddy.username) for buddy in g.user.buddies]

    if form.validate_on_submit():

        # convert meters to feet
        max_depth = form.max_depth.data
        if form.depth_units.data == 'meters':
            max_depth = max_depth * 3.28084

        dive.date = form.date.data
        dive.dive_no = form.dive_no.data
        dive.rating = form.rating.data
        dive.bottom_time = form.bottom_time.data
        dive.max_depth = max_depth
        dive.buddy_id = form.buddy_id.data
        dive.comments = form.comments.data
        
        # Make sure "no buddy" gets entered in as null
        if dive.buddy_id == -1:
            dive.buddy_id = None

        db.session.add(dive)
        db.session.commit()

        # Handle dive types (create Divetype obj)
        dive_types_dict = _create_divetype_dict(form.dive_type.data)

        divetype = dive.divetypes

        divetype.drysuit = dive_types_dict["drysuit"]
        divetype.night = dive_types_dict["night"]
        divetype.cave = dive_types_dict["cave"]
        divetype.wreck = dive_types_dict["wreck"]
        divetype.drift = dive_types_dict["drift"]
        divetype.ice = dive_types_dict["ice"]
        divetype.deep = dive_types_dict["deep"]
        divetype.technical = dive_types_dict["technical"]
        divetype.altitude = dive_types_dict["altitude"]
        divetype.muck = dive_types_dict["muck"]

        db.session.add(divetype)
        db.session.commit()

        flash('Dive successfully updated', 'success')
        return redirect(f"/dives/{dive.id}")

    return render_template("/dives/edit.html", form=form)

@app.route('/dives/<int:dive_id>/delete', methods=['POST'])
def dives_delete(dive_id):
    """Deletes a dive"""

    dive = Dive.query.get_or_404(dive_id)

    if not g.user or dive.diver.id != g.user.id:
        flash("Access unauthorized.", "danger")
        return redirect("/")
    
    divetype = dive.divetypes
    
    db.session.delete(divetype)
    db.session.delete(dive)

    db.session.commit()

    flash("Dive deleted.", "warning")
    return redirect("/")


##############################################################################
# Homepage and error pages

@app.route('/')
def homepage():
    """Show homepage:

    - anon users: no messages
    - logged in: 100 most recent dives and dive photos of buddies

    """

    if g.user:
        self_and_following_ids = [user.id for user in g.user.buddies]
        self_and_following_ids.append(g.user.id)
        dives = (Dive
                    .query
                    .filter(Dive.user_id.in_(self_and_following_ids))
                    .order_by(Dive.date.desc())
                    .limit(100)
                    .all())

        return render_template('home.html', dives=dives)

    else:
        return render_template('home-anon.html')

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

##############################################################################
# Turn off all caching in Flask
#   (useful for dev; in production, this kind of stuff is typically
#   handled elsewhere)
#
# https://stackoverflow.com/questions/34066804/disabling-caching-in-flask

@app.after_request
def add_header(req):
    """Add non-caching headers on every request."""

    req.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    req.headers["Pragma"] = "no-cache"
    req.headers["Expires"] = "0"
    req.headers['Cache-Control'] = 'public, max-age=0'
    return req