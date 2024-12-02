from .database import db

class User(db.Model):
    id = db.Column(db.Integer(), primary_key = True)
    username = db.Column(db.String(), nullable = False, unique = True)
    password = db.Column(db.String(), nullable = False)
    name = db.Column(db.String(), nullable = False)
    type = db.Column(db.String(), default = "general")
    

class Section(db.Model):
    id = db.Column(db.Integer(), primary_key = True)
    sec_title = db.Column(db.String(), nullable = False)
    date = db.Column(db.String(), nullable = False)
    description = db.Column(db.Text)

    # one to many relation with book
    books = db.relationship('Book', backref='section', lazy=True)

class Request(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer(), db.ForeignKey('book.id'), nullable=False)
    requested_at = db.Column(db.Date(), nullable=False)
    days_requested = db.Column(db.Integer(), nullable = False)
    status = db.Column(db.String(), default='pending')

    # Define relationships
    user = db.relationship('User', backref=db.backref('requests', lazy=True))
    book = db.relationship('Book', back_populates='book_request')  

class Book(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    b_title = db.Column(db.String(), nullable=False)
    author = db.Column(db.String(), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_issued = db.Column(db.Integer())

    feedback = db.relationship('Feedback', backref='book', lazy=True)

    # Define the foreign key for the many-to-one relationship
    b_section = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False) 
    
    # one-to-many relationship with Request
    book_request = db.relationship('Request', back_populates='book', lazy=True)

class Feedback(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer(), db.ForeignKey('book.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)

    # Define relationship with User model
    user = db.relationship('User', backref=db.backref('feedback', lazy=True))


