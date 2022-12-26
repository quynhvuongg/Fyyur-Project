# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import logging
import sys
from logging import Formatter, FileHandler

import babel
import dateutil.parser
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy

import config
from forms import *

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

# connect to a local postgresql database
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

migrate = Migrate(app, db)


# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship('Show', backref='venue', lazy=True)

    def __repr__(self):
        return f'<Venue {self.id} {self.name}>'


class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship('Show', backref='artist', lazy=True)

    def __repr__(self):
        return f'<Artist {self.id} {self.name}>'


class Show(db.Model):
    __tablename__ = 'show'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey("artist.id"), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey("venue.id"), nullable=False)

    def __repr__(self):
        return f'<Show {self.id} {self.artist_id} {self.venue_id} {self.start_time}>'


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    areas = []
    data = Venue.query.order_by('city', 'state', 'name').all()
    for venue in data:
        area_item = {}
        pos_area = -1
        if len(areas) == 0:
            pos_area = 0
            area_item = {
                "city": venue.city,
                "state": venue.state,
                "venues": []
            }
            areas.append(area_item)
        else:
            for i, area in enumerate(areas):
                if area['city'] == venue.city and area['state'] == venue.state:
                    pos_area = i
                    break
            if pos_area < 0:
                area_item = {
                    "city": venue.city,
                    "state": venue.state,
                    "venues": []
                }
                areas.append(area_item)
                pos_area = len(areas) - 1
            else:
                area_item = areas[pos_area]
        v = {
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": 4
        }
        area_item['venues'].append(v)
        areas[pos_area] = area_item
    return render_template('pages/venues.html', areas=areas)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term')
    search = "%{}%".format(search_term.replace(" ", "\ "))
    data = Venue.query.filter(Venue.name.match(search)).order_by('name').all()
    items = []
    for row in data:
        aux = {
            "id": row.id,
            "name": row.name,
            "num_upcoming_shows": len(row.shows)
        }
        items.append(aux)

    response = {
        "count": len(items),
        "data": items
    }
    return render_template('pages/search_venues.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    data = Venue.query.filter_by(id=venue_id).first()
    data.genres = json.loads(data.genres)

    upcoming_shows = []
    past_shows = []
    for show in data.shows:
        if show.date > datetime.now():
            upcoming_shows.append(show)
        else:
            past_shows.append(show)
    data.upcoming_shows = upcoming_shows
    data.past_shows = past_shows
    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    request_data = request.get_json()
    try:
        name = request_data['name']
        city = request_data['city']
        state = request_data['state']
        phone = request_data['phone']
        address = request_data['address']
        genres = json.dumps(request_data['genres'])
        facebook_link = request_data['facebook_link']
        image_link = request_data['image_link']
        website = request_data['website']

        venue = Venue(name=name, city=city, state=state, phone=phone, address=address, genres=genres,
                      facebook_link=facebook_link, image_link=image_link, website=website)
        db.session.add(venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be added')
    finally:
        db.session.close()
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        Venue.query.filter(Venue.id == venue_id).delete()
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return render_template('pages/home.html')


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    response = Artist.query.all()
    return render_template('pages/artists.html', artists=response)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', '')
    result = db.session.query(Artist).filter(Artist.name.ilike(f'%{search_term}%')).all()
    count = len(result)
    response = {
        "count": count,
        "data": result
    }
    return render_template('pages/search_artists.html', results=response,
                           search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    data = Artist.query.filter_by(id=artist_id).first()
    data.genres = json.loads(data.genres)

    upcoming_shows = []
    past_shows = []
    for show in data.shows:
        if show.date > datetime.now():
            upcoming_shows.append(show)
        else:
            past_shows.append(show)
    data.upcoming_shows = upcoming_shows
    data.past_shows = past_shows
    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.filter_by(id=artist_id).first()

    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.facebook_link.data = artist.facebook_link
    form.website.data = artist.website
    form.image_link.data = artist.image_link
    form.genres.data = json.loads(artist.genres)
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    request_data = request.get_json()
    try:
        artist = Artist.query.filter_by(id=artist_id).first()
        artist.name = request_data['name']
        artist.city = request_data['city']
        artist.state = request_data['state']
        artist.phone = request_data['phone']
        artist.genres = json.dumps(request_data['genres'])
        artist.facebook_link = request_data['facebook_link']
        artist.website = request_data['website']
        artist.image_link = request_data['image_link']

        db.session.add(artist)
        db.session.commit()
    except:
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.filter_by(id=venue_id).first()

    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.phone.data = venue.phone
    form.address.data = venue.address
    form.facebook_link.data = venue.facebook_link
    form.website.data = venue.website
    form.image_link.data = venue.image_link
    form.genres.data = json.loads(venue.genres)
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    request_data = request.get_json()

    try:
        venue = Venue.query.filter_by(id=venue_id).first()
        venue.name = request_data['name']
        venue.city = request_data['city']
        venue.state = request_data['state']
        venue.phone = request_data['phone']
        venue.address = request_data['address']
        venue.genres = json.dumps(request_data['genres'])
        venue.facebook_link = request_data['facebook_link']
        venue.website = request_data['website']
        venue.image_link = request_data['image_link']

        db.session.add(venue)
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    request_data = request.get_json()
    try:
        name = request_data['name']
        city = request_data['city']
        state = request_data['state']
        phone = request_data['phone']
        genres = json.dumps(request_data['genres'])
        facebook_link = request_data['facebook_link']
        website = request_data['website']
        image_link = request_data['image_link']

        artist = Artist(name=name, city=city, state=state, phone=phone, genres=genres, facebook_link=facebook_link,
                        image_link=image_link, website=website)
        db.session.add(artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
        db.session.rollback()
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
        print(sys.exc_info())
    finally:
        db.session.close()
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    rows = db.session.query(Show, Artist, Venue).join(Artist).join(Venue).filter(Show.date > datetime.now()).order_by(
        'date').all()
    data = []
    for row in rows:
        item = {
            'venue_id': row.Venue.id,
            'artist_id': row.Artist.id,
            'venue_name': row.Venue.name,
            'artist_name': row.Artist.name,
            'artist_image_link': row.Artist.image_link,
            'start_time': row.Show.date.strftime('%Y-%m-%d %H:%I')
        }
        data.append(item)
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    request_data = request.get_json()
    try:
        artist_id = request_data['artist_id']
        venue_id = request_data['venue_id']
        start_time = request_data['start_time']

        show = Show(artist_id=artist_id, venue_id=venue_id, date=start_time)
        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed!')
    except:
        db.session.rollback()
        flash('An error occurred. Show could not be listed.')
        print(sys.exc_info())
    finally:
        db.session.close()
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
