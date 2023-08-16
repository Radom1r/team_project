import sqlalchemy as sq
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Profile_link(Base):
    __tablename__ = 'Profile_link'
    profile_link_id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    profile_link = sq.Column(sq.String(length=100), nullable=False, unique=True)

class Name(Base):
    __tablename__ = 'Name'
    name_id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    name_and_surname = sq.Column(sq.String(length=100), nullable=False)
    profile_link_id = sq.Column(sq.Integer, sq.ForeignKey('Profile_link.profile_link_id'), nullable=False)
    names = relationship('Profile_link', backref='Name')

class Photo_links(Base):
    __tablename__ = 'Photo_links'
    photo_link_id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    photo_link = sq.Column(sq.String(length=100), nullable=False, unique=True)
    profile_link_id = sq.Column(sq.Integer, sq.ForeignKey('Profile_link.profile_link_id'), nullable=False)
    names = relationship('Profile_link', backref='Photo_links')

def create_tables(eng):
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)