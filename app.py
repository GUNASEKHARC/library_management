from flask import Flask, render_template, jsonify, request, flash, redirect, url_for
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__, template_folder='template')
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://grady:admin@localhost:5432/library_management"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.secret_key = 'your_secret_key_here'
db = SQLAlchemy(app)

class Book(db.Model):
    __tablename__ = 'books'
    bookid = db.Column(db.String(50), primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    authors = db.Column(db.String(200), nullable=False)
    average_rating = db.Column(db.Float)
    isbn = db.Column(db.String(13), unique=True, nullable=False)
    isbn13 = db.Column(db.String(13))
    language_code = db.Column(db.String(10))
    num_pages = db.Column(db.Integer)
    ratings_count = db.Column(db.Integer)
    text_reviews_count = db.Column(db.Integer)
    publication_date = db.Column(db.Date)
    publisher = db.Column(db.String(200))
    availability = db.Column(db.String(50), nullable=False, default='library')  # New column


class Member(db.Model):
    __tablename__ = 'members'
    memberid = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    phone = db.Column(db.String(15))
    address = db.Column(db.String(200))
    join_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)

class Transaction(db.Model):
    __tablename__ = 'transactions'
    transactionid = db.Column(db.Integer, primary_key=True)
    bookid = db.Column(db.String(50), db.ForeignKey('books.bookid', ondelete='CASCADE'))
    memberid = db.Column(db.String(50), db.ForeignKey('members.memberid', ondelete='CASCADE'))
    issue_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    return_date = db.Column(db.Date)
    rent_fee = db.Column(db.Numeric(10, 2))

# Create tables
with app.app_context():
    db.create_all()

@app.route("/")
def index():
    return render_template('home.html')

@app.route('/books', methods=['GET'])
def books():
    search_query = request.args.get('search', '')
    if search_query:
        search = f"%{search_query}%"
        books = Book.query.filter(
            db.or_(Book.title.ilike(search), Book.authors.ilike(search))
        ).all()
    else:
        books = Book.query.all()
    return render_template('books.html', books=books)

@app.route('/transactions', methods=['GET'])
def transactions():
    transactions = Transaction.query.all()
    return render_template('transaction.html', transactions=transactions)

@app.route('/issue_book', methods=['GET', 'POST'])
def issue_book():
    if request.method == 'POST':
        bookid = request.form['bookid']
        memberid = request.form['memberid']

        book = Book.query.get(bookid)
        if not book:
            flash('Book not found!', 'danger')
            return redirect(url_for('transactions'))

        # Check if the book is available
        if book.availability != 'library':
            flash('Book is not available!', 'danger')
            return redirect(url_for('transactions'))

        # Check if the member's outstanding debt is not more than 500
        transactions = Transaction.query.filter_by(memberid=memberid, return_date=None).all()
        outstanding_debt = sum((datetime.utcnow().date() - t.issue_date).days * 10 for t in transactions)
        if outstanding_debt > 500:
            flash('Member has an outstanding debt of more than 500!', 'danger')
            return redirect(url_for('transactions'))

        # Issue the book
        new_transaction = Transaction(
            bookid=bookid,
            memberid=memberid,
            issue_date=datetime.utcnow().date()
        )
        book.availability = memberid  # Mark the book as borrowed
        db.session.add(new_transaction)
        db.session.commit()
        flash('Book issued successfully!', 'success')
        return redirect(url_for('transactions'))

    available_books = Book.query.filter_by(availability='library').all()
    members = Member.query.all()
    books = Book.query.all()
    return render_template('issue_book.html', available_books=available_books, members=members)


@app.route('/return_book', methods=['GET', 'POST'])
def return_book():
    if request.method == 'POST':
        transactionid = request.form['transactionid']
        
        transaction = Transaction.query.get(transactionid)
        if transaction and transaction.return_date is None:
            days_borrowed = (datetime.utcnow().date() - transaction.issue_date).days
            if days_borrowed == 0:
                days_borrowed = 1  # Ensure at least 10 rupees is charged
            transaction.return_date = datetime.utcnow().date()
            transaction.rent_fee = days_borrowed * 10

            # Mark the book as available again
            book = Book.query.get(transaction.bookid)
            book.availability = 'library'

            db.session.commit()
            flash('Book returned successfully!', 'success')
        else:
            flash('Invalid transaction ID or book already returned.', 'danger')
        return redirect(url_for('transactions'))
    return render_template('return_book.html')



@app.route('/import_books', methods=['GET','POST'])
def import_books():
    url = "https://frappe.io/api/method/frappe-library?page=2&title=and"
    response = requests.get(url)
    books = response.json().get('message', [])
    new_books_count = 0

    for book in books:
        book_id = book.get('bookID')
        title = book.get('title')
        authors = book.get('authors')
        average_rating = float(book.get('average_rating', 0))
        isbn = book.get('isbn')
        isbn13 = book.get('isbn13')
        language_code = book.get('language_code')
        num_pages = int(book.get('  num_pages', 0))
        ratings_count = int(book.get('ratings_count', 0))
        text_reviews_count = int(book.get('text_reviews_count', 0))
        publication_date = datetime.strptime(book.get('publication_date'), '%m/%d/%Y').date()
        publisher = book.get('publisher')

        # Check if book already exists
        existing_book = Book.query.filter_by(bookid=book_id).first()
        if not existing_book:
            new_book = Book(
                bookid=book_id,
                title=title,
                authors=authors,
                average_rating=average_rating,
                isbn=isbn,
                isbn13=isbn13,
                language_code=language_code,
                num_pages=num_pages,
                ratings_count=ratings_count,
                text_reviews_count=text_reviews_count,
                publication_date=publication_date,
                publisher=publisher
            )
            db.session.add(new_book)
            new_books_count += 1

    db.session.commit()
    flash(f'{new_books_count} books imported successfully!', 'success')
    return redirect(url_for('index'))

@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        bookid = request.form['bookid']
        title = request.form['title']
        authors = request.form['authors']
        average_rating = float(request.form['average_rating'])
        isbn = request.form['isbn']
        isbn13 = request.form['isbn13']
        language_code = request.form['language_code']
        num_pages = int(request.form['num_pages'])
        ratings_count = int(request.form['ratings_count'])
        text_reviews_count = int(request.form['text_reviews_count'])
        publication_date = datetime.strptime(request.form['publication_date'], '%Y-%m-%d').date()
        publisher = request.form['publisher']

        new_book = Book(
            bookid=bookid,
            title=title,
            authors=authors,
            average_rating=average_rating,
            isbn=isbn,
            isbn13=isbn13,
            language_code=language_code,
            num_pages=num_pages,
            ratings_count=ratings_count,
            text_reviews_count=text_reviews_count,
            publication_date=publication_date,
            publisher=publisher
        )

        db.session.add(new_book)
        db.session.commit()
        flash('Book added successfully!', 'success')
        return redirect(url_for('books'))
    return render_template('add_book.html')

@app.route('/edit_book/<string:book_id>', methods=['GET', 'POST'])
def edit_book(book_id):
    book = Book.query.get(book_id)
    if request.method == 'POST':
        book.title = request.form['title']
        book.authors = request.form['authors']
        book.average_rating = float(request.form['average_rating'])
        book.isbn = request.form['isbn']
        book.isbn13 = request.form['isbn13']
        book.language_code = request.form['language_code']
        book.num_pages = int(request.form['num_pages'])
        book.ratings_count = int(request.form['ratings_count'])
        book.text_reviews_count = int(request.form['text_reviews_count'])
        book.publication_date = datetime.strptime(request.form['publication_date'], '%Y-%m-%d').date()
        book.publisher = request.form['publisher']

        db.session.commit()
        flash('Book updated successfully!', 'success')
        return redirect(url_for('books'))
    return render_template('edit_book.html', book=book)

@app.route('/delete_book/<string:book_id>', methods=['GET', 'POST'])
def delete_book(book_id):
    book = Book.query.get(book_id)
    db.session.delete(book)
    db.session.commit()
    flash('Book deleted successfully!', 'success')
    return redirect(url_for('books'))

@app.route('/members', methods=['GET'])
def members():
    members = Member.query.all()
    return render_template('members.html', members=members)

@app.route('/add_member', methods=['GET', 'POST'])
def add_member():
    if request.method == 'POST':
        memberid = request.form['memberid']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        address = request.form['address']
        join_date = datetime.strptime(request.form['join_date'], '%Y-%m-%d').date()

        new_member = Member(
            memberid=memberid,
            name=name,
            email=email,
            phone=phone,
            address=address,
            join_date=join_date
        )

        db.session.add(new_member)
        db.session.commit()
        flash('Member added successfully!', 'success')
        return redirect(url_for('members'))
    return render_template('add_member.html')

@app.route('/edit_member/<string:member_id>', methods=['GET', 'POST'])
def edit_member(member_id):
    member = Member.query.get(member_id)
    if request.method == 'POST':
        member.name = request.form['name']
        member.email = request.form['email']
        member.phone = request.form['phone']
        member.address = request.form['address']
        member.join_date = datetime.strptime(request.form['join_date'], '%Y-%m-%d').date()

        db.session.commit()
        flash('Member updated successfully!', 'success')
        return redirect(url_for('members'))
    return render_template('edit_member.html', member=member)

@app.route('/delete_member/<string:member_id>', methods=['GET', 'POST'])
def delete_member(member_id):
    member = Member.query.get(member_id)
    db.session.delete(member)
    db.session.commit()
    flash('Member deleted successfully!', 'success')
    return redirect(url_for('members'))

if __name__ == "__main__":
    app.run(debug=True)
