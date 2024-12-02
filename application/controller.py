from flask import Flask, render_template, redirect, request, session, flash
from flask import current_app as app
from .models import *
from datetime import datetime


@app.route("/", methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        u_name = request.form.get("u_name").strip()
        pwd = request.form.get("pwd")
        this_user = User.query.filter_by(username = u_name).first() 
        if this_user:
            if this_user.password == pwd:
                session['user_id'] = this_user.id
                if this_user.type == "admin":
                    return redirect('/requests')
                else:
                    return redirect('/books') 
            else:
                return "incorrect Password"
        else:
            return "user does not exist!"
    return render_template('user_login.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u_name = request.form.get("u_name")
        pwd = request.form.get("pwd")
        name = request.form.get("name")
        this_user = User.query.filter_by(username = u_name).first()
        if this_user:
            return "user exist!"
        else:
            new_user = User(username = u_name, password = pwd, name = name)
            print(new_user)
            db.session.add(new_user)
            db.session.commit()
            return redirect("/")
    return render_template("register.html")




@app.route("/add_section", methods = ["GET", "POST"])
def add_section():
    if request.method == "POST":
        s_title = request.form.get("s_title")
        date = request.form.get("date")
        description = request.form.get("description")

        new_section = Section(sec_title=s_title, date=date, description=description)
        db.session.add(new_section)
        db.session.commit()

        return redirect("/section") 
    else:
        return render_template("add_section.html")

#section from which we can add books and section both
@app.route("/section")
def section():
    sections = Section.query.all() 
    return render_template("section.html", sections=sections)


@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    if request.method == "POST":
        b_title = request.form.get("b_title")
        author = request.form.get("author")
        content = request.form.get("content")
        section_title = request.args.get("section_title")

        section = Section.query.filter_by(sec_title=section_title).first()
        if section:
            section_id = section.id
        else:
            return "Section not found"
        
        new_book = Book(b_title=b_title, author=author, content=content, b_section=section_id)
        db.session.add(new_book)
        db.session.commit()

        return redirect("/section")
    else:
        return render_template("add_book.html")
    
@app.route("/sec_books")
def section_books():
    section_title = request.args.get("section_title")
    section = Section.query.filter_by(sec_title=section_title).first()
    if section:
        books = Book.query.filter_by(b_section=section.id).all()
        return render_template("section_books.html", books=books)
    
@app.route("/delete_section/<int:section_id>", methods=['POST'])
def delete_section(section_id):
    section = Section.query.get(section_id)
    books = Book.query.filter_by(b_section=section_id).all()

    # Delete associated books
    for book in books:
        # Delete associated feedback for each book
        feedback = Feedback.query.filter_by(book_id=book.id).all()
        for fb in feedback:
            db.session.delete(fb)
        db.session.delete(book)

    db.session.delete(section)
    db.session.commit()

    flash("Section and associated books deleted successfully.", "success")
    return redirect("/section")



@app.route("/books", methods = ['GET', 'POST'])
def book():
    if request.method == 'POST':
        search_query = request.form.get("search")
        books = Book.query.join(Section).filter((Book.b_title.ilike(f"%{search_query}%")|
                                    Book.author.ilike(f"%{search_query}%")|
                                    Section.sec_title.ilike(f"%{search_query}%"))).all()
        
        return render_template("books.html", books=books)
    else:
        books = Book.query.all()
        return render_template("books.html", books=books)

@app.route("/mybooks", methods=['GET', 'POST'])
def mybooks():
    if request.method == 'POST':
        search_query = request.form.get("search")
        user_id = session.get('user_id')
        # Query the Request model for approved requests associated with the user
        approved_requests = Request.query.join(Book).join(Section).filter(
            Request.user_id == user_id,
            Request.status == 'Approved',
            (Book.b_title.ilike(f"%{search_query}%")) |
            (Book.author.ilike(f"%{search_query}%")) |
            (Section.sec_title.ilike(f"%{search_query}%"))
        ).all()

        # Extract books from approved requests
        issued_books = [req.book for req in approved_requests]

        return render_template("mybook.html", issued_requests=issued_books)

    else:
        user_id = session.get('user_id')
        # Query the Request model for approved requests associated with the user
        approved_requests = Request.query.filter_by(user_id=user_id, status='Approved').all()
        # Extract books from approved requests
        issued_books = [req.book for req in approved_requests]
        return render_template("mybook.html", issued_requests=issued_books)


#for admin to see requests from user and show approved books
@app.route("/requests", methods=['GET', 'POST'])
def requests():
    if request.method == 'POST':
        search_query = request.form.get("search")
        all_requested = Request.query.join(User).join(Book).filter(
            (Book.b_title.ilike(f"%{search_query}%")) |
            (User.name.ilike(f"%{search_query}%"))).all()
        
        # Filter pend_requests and approved_requests based on the filtered results
        pend_requests = [req for req in all_requested if req.status == 'pending']
        approved_requests = [req for req in all_requested if req.status == 'Approved']
    else:
        all_requested = Request.query.all()
        pend_requests = Request.query.filter_by(status='pending').all()
        approved_requests = Request.query.filter_by(status='Approved').all()
    return render_template("requests.html", all_requested=all_requested, approved_requests=approved_requests, pend_requests=pend_requests)
    
@app.route("/request_book/<int:user_id>", methods=['POST'])
def request_book(user_id):
    
    if request.method == 'POST':
        # Check if the user has already requested the maximum number of books
        max_books_allowed = 5  
        user_requests = Request.query.filter_by(user_id=user_id).count()

        if user_requests >= max_books_allowed:
            flash("You have reached the maximum limit for requesting e-books.")
            return redirect('/books')
        
    user_id = request.form.get("user_id")
    book_id = request.form.get("book_id")
    existing_request = Request.query.filter_by(user_id=user_id, book_id=book_id).first()

    if existing_request:
        flash("You have already requested this book.")
        return redirect('/books')
    days_requested = request.form.get("days_requested")
    requested_at = datetime.now()

    new_request = Request(user_id=user_id, book_id=book_id, days_requested=days_requested, requested_at=requested_at)
    db.session.add(new_request)
    db.session.commit()

    return redirect('/mybooks')
    
@app.route("/approve_request", methods=['POST'])
def approve_request():
    if request.method == 'POST':
        request_id = request.form.get("request_id")
        action = request.form.get("action")

        # Find the request by ID
        req = Request.query.get(request_id) 
        if req:
            if action == "approve":
                # Update the status to "Approved"
                req.status = "Approved"
                db.session.commit()
                approved_request = Request.query.filter_by(id=request_id).first()
                if approved_request:

                    db.session.add(approved_request)
                    db.session.commit()

            elif action == "reject":
                # Delete the request from the database
                db.session.delete(req)
                db.session.commit()
            
            elif action == "revoke":
                db.session.delete(req)
                db.session.commit()

            return redirect("/requests")


@app.route("/content/<int:book_id>")
def book_content(book_id):
    # Query the Book model to get the book with the given ID
    book = Book.query.get(book_id)
    if book:
        return render_template("read_book.html", book=book)
    
@app.route("/return_book/<int:book_id>", methods=['GET', 'POST'])
def return_book(book_id):
    if request.method == 'GET':
        book = Book.query.get(book_id)
        request_record = Request.query.filter_by(book_id=book_id).first()
        if request_record:
            db.session.delete(request_record)
            db.session.commit()
            return redirect("/mybooks")
        
@app.route("/delete_book/<int:book_id>", methods=['POST'])
def delete_book(book_id):
    # Query the Book and associated Feedback
    book = Book.query.get(book_id)
    feedback = Feedback.query.filter_by(book_id=book_id).all()

    # Delete the associated feedback
    for fb in feedback:
        db.session.delete(fb)

    # Delete the book
    db.session.delete(book)
    db.session.commit()

    flash("Book deleted successfully.", "success")
    return redirect("/section")
        

@app.route("/user_details/<int:user_id>")
def user_details(user_id):
    user = User.query.get(user_id)
    if user:
        return render_template("details.html", user=user)


@app.route("/submit_feedback/<int:book_id>", methods=['POST'])
def submit_feedback(book_id):
    if request.method == 'POST':
        content = request.form.get("feedback")
        user_id = session.get('user_id')

        new_feedback = Feedback(user_id=user_id, book_id=book_id, content=content)
        db.session.add(new_feedback)
        db.session.commit()

        return redirect(f'/books')
    
@app.route("/feedback/<int:book_id>", methods=['GET'])
def view_feedback(book_id):
    book = Book.query.get(book_id)
    feedbacks = Feedback.query.filter_by(book_id=book_id).all()
    if book:
        return render_template("read_feedback.html", book=book, feedbacks=feedbacks)
    
    
