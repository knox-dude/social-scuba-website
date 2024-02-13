from flask_sqlalchemy import SQLAlchemy
from datetime import date, time
from sqlalchemy import func
from flask_bcrypt import Bcrypt

from secret import GOOGLE_API_KEY

bcrypt = Bcrypt()
db = SQLAlchemy()

def connect_db(app):
    """Connect to database."""

    db.app = app
    db.init_app(app)

class Buddy(db.Model):
    """Connection of a user to another user as buddies"""

    __tablename__ = "buddies"

    main_user_id=db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        primary_key=True
    )

    buddy_user_id=db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        primary_key=True
    )
    
class Dive(db.Model):
    """A single dive logged by a user"""

    __tablename__ = "dives"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False
    )

    dive_no = db.Column(db.Integer, nullable=False)

    date = db.Column(db.Date, nullable=False, default=date.today())

    divesite_id = db.Column(
        db.Integer,
        db.ForeignKey('divesites.id', ondelete="CASCADE"),
        nullable=False
    )

    rating = db.Column(db.Integer, nullable=False)

    bottom_time = db.Column(db.Float, nullable=False)

    max_depth = db.Column(db.Float, nullable=False)

    comments = db.Column(db.Text)

    buddy_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=True
    )

    diver = db.relationship("User", foreign_keys=[user_id], back_populates="dives")
    buddy = db.relationship("User", foreign_keys=[buddy_id])
    divesite=db.relationship("Divesite", foreign_keys=[divesite_id], back_populates="dives")
    divetypes = db.relationship("Divetype", back_populates="dive", uselist=False)

    def get_divetypes(self):
        """Returns a list of all divetypes associated with a dive."""
        
        all_divetypes = ["drysuit", "night", "cave", "wreck", "drift", "ice", "deep", "technical", "altitude", "muck"]
        return_list = []

        for divetype_name in all_divetypes:
            divetype_val = getattr(self.divetypes, divetype_name)
            
            if divetype_val:
                return_list.append(divetype_name)

        return return_list
    
class Divetype(db.Model):
    """A lookup table storing all possible dive types for one dive."""

    __tablename__ = "divetypes"

    id = db.Column(db.Integer, primary_key=True)

    dive_id = db.Column(
        db.Integer,
        db.ForeignKey('dives.id', ondelete='CASCADE'),
        nullable=False,
        unique=True
    )

    drysuit = db.Column(db.Boolean, nullable=False)

    night = db.Column(db.Boolean, nullable=False)

    cave = db.Column(db.Boolean, nullable=False)

    wreck = db.Column(db.Boolean, nullable=False)

    drift = db.Column(db.Boolean, nullable=False)

    ice = db.Column(db.Boolean, nullable=False)

    deep = db.Column(db.Boolean, nullable=False)

    technical = db.Column(db.Boolean, nullable=False)

    altitude = db.Column(db.Boolean, nullable=False)

    muck = db.Column(db.Boolean, nullable=False)

    dive = db.relationship("Dive", foreign_keys=[dive_id], back_populates='divetypes')

class User(db.Model):
    """User in the system."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username=db.Column(db.Text, nullable=False, unique=True)

    image_url=db.Column(db.Text, default="/static/images/diver-prof-photo-612x612.jpeg")

    first_name=db.Column(db.Text, nullable=False)

    last_name=db.Column(db.Text, nullable=False)

    password=db.Column(db.Text, nullable=False)

    header_image_url = db.Column(db.Text, default="/static/images/anon-diver-hero.png")

    bio = db.Column(db.Text)

    buddies_to = db.relationship(
        "User",
        secondary="buddies",
        primaryjoin=(Buddy.main_user_id == id),
        secondaryjoin=(Buddy.buddy_user_id == id)
    )

    buddies = db.relationship(
        "User",
        secondary="buddies",
        primaryjoin=(Buddy.buddy_user_id == id),
        secondaryjoin=(Buddy.main_user_id == id)
    )
    dives = db.relationship("Dive", foreign_keys=[Dive.user_id], back_populates="diver")

    def __repr__(self) -> str:
        return f"User {self.username}, aka {self.first_name} {self.last_name}"

    def get_unique_continent_count(self):
        """Returns the number of continents user has dove in"""
        continent_count =  (
            db.session.query(func.count(func.distinct(Divesite.continent)))
            .join(Dive)
            .filter(Dive.user_id == self.id, Divesite.continent != None)
            .scalar()
        )
        
        if continent_count:
            return str(continent_count)
        
        return "0"

    def get_unique_country_count(self):
        """Returns the number of countries user has dove in"""
        country_count =  (
            db.session.query(func.count(func.distinct(Divesite.country)))
            .join(Dive)
            .filter(Dive.user_id == self.id, Divesite.country != None)
            .scalar()
        )

        if country_count:
            return str(country_count)
        
        return str(max(int(self.get_unique_continent_count()), 0))
    
    def get_max_depth(self):
        """Gets the max depth the user has dove from all their dives"""
        max_depth =  (
            db.session.query(func.max(Dive.max_depth))
            .filter(Dive.user_id == self.id)
            .scalar()
        ) 

        if max_depth:
            return "{:.2f}".format(max_depth)
        
        return "0"
    
    def get_max_bottom_time(self):
        """Gets the max bottom_time the user has dove from all their dives"""
        max_bottom_time = (
            db.session.query(func.max(Dive.bottom_time))
            .filter(Dive.user_id == self.id)
            .scalar()
        )

        if max_bottom_time:
            return "{:.1f}".format(max_bottom_time)
        
        return "0"
    
    def leaderboard_max_bottom_time(self):
        """Returns data about this user and buddies, in order of who dived longest"""
        
        unsorted = []
        unsorted.append([self.get_max_bottom_time(), self, "min"])

        for user in self.buddies:
            unsorted.append([user.get_max_bottom_time(), user, "min"])
        
        sorted_data = sorted(unsorted, key=lambda x: float(x[0]), reverse=True)

        if len(sorted_data) > 5:
            sorted_data = sorted_data[0:5]

        return sorted_data
    
    def leaderboard_max_depth(self):
        """Returns data about this user and buddies, in order of who dived lowest"""
        
        unsorted = []
        unsorted.append([self.get_max_depth(), self, "ft"])

        for user in self.buddies:
            unsorted.append([user.get_max_depth(), user, "ft"])
        
        sorted_data = sorted(unsorted, key=lambda x: float(x[0]), reverse=True)

        if len(sorted_data) > 5:
            sorted_data = sorted_data[0:5]

        return sorted_data

    def leaderboard_num_dives(self):
        """Returns a list of usernames and number of dives that user and buddies have
        
        Assuming users have less than 20 buddies, we can leave it as is. Otherwise I would've used a heap
        """
        
        unsorted = []
        unsorted.append([self.get_num_dives(), self, "dives"])

        for user in self.buddies:
            unsorted.append([user.get_num_dives(), user, "dives"])
        
        sorted_data = sorted(unsorted, key=lambda x: float(x[0]), reverse=True)

        if len(sorted_data) > 5:
            sorted_data = sorted_data[0:5]

        return sorted_data

    def get_num_dives(self):
        """Get the amount of dives the user has completed"""
        num_dives = (
            db.session.query(func.count(Dive.dive_no))
            .filter(Dive.user_id==self.id)
            .scalar()
        )

        if num_dives:
            return str(num_dives)
        
        return "0"

    def is_buddies(self, other_user):
        """Is this user buddies with `other_user`?"""

        found_user_list = [user for user in self.buddies if user == other_user]
        return len(found_user_list) == 1
    
    def is_buddies_to(self, other_user):
        """Has other_user added this user as a buddy?"""

        found_user_list = [user for user in self.buddies_to if user == other_user]
        return len(found_user_list) == 1

    @classmethod
    def signup(cls, username, password, first_name, last_name):
        """Sign up user.

        Hashes password and adds user to system.
        """

        if username == "":
            username=None

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            password=hashed_pwd,
            first_name=first_name,
            last_name=last_name,
            image_url=User.image_url.default.arg,
            bio="No bio yet!",
            header_image_url=User.header_image_url.default.arg
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False

class Divesite(db.Model):
    """An individual dive site"""

    __tablename__ = 'divesites'

    id=db.Column(db.Integer, primary_key=True)

    name=db.Column(db.Text, nullable=False)

    region=db.Column(db.Text)

    lat=db.Column(db.Float)

    lng=db.Column(db.Float)

    ocean=db.Column(db.Text)

    location=db.Column(db.Text)

    api_id = db.Column(db.Text)

    country = db.Column(db.Text)

    continent = db.Column(db.Text)

    dives = db.relationship("Dive", back_populates="divesite")

    def __repr__(self) -> str:
        return f"Divesite {self.name}, in {self.region}"
    
    def average_rating(self):
        """Gets the average rating of a divesite based on all recorded dives"""
        avg_rating = (
            db.session.query(func.avg(Dive.rating))
            .filter(Dive.divesite_id == self.id)
            .scalar()
        )

        if avg_rating:
            return "{:.2f}".format(avg_rating)
        
        return "No Ratings"
    
    def static_map(self, zoom_level=11):
        """Generates a static map for use in showing divesites"""
        map_size = '600x400'

        static_map_url = f'https://maps.googleapis.com/maps/api/staticmap?center={self.lat},{self.lng}&zoom={zoom_level}&size={map_size}&markers={self.lat},{self.lng}&key={GOOGLE_API_KEY}'

        return static_map_url