# Library Management System

This project is a web application built with Flask for managing a library system. It allows users to manage books, members, and transactions.

## Features

- **Books Management**: CRUD operations for adding, editing, and deleting books.
- **Members Management**: CRUD operations for managing library members.
- **Transactions**: Issue and return books with automated rental fee calculation.
- **API Integration**: Import books data from an external API for easy library collection expansion.

### Importing Books from an API

You can import books data from an external API to populate your library collection. Follow these steps:

1. Click on the "Import Books" link/button in the application.
2. Enter the API URL that provides books data in JSON format.
3. Click on "Import" to fetch and import the books data into the application.

### Managing Books, Members, and Transactions

- **Books**: Add new books, edit existing ones, and delete books from the library.
- **Members**: Manage library members, add new members, edit their details, and remove members.
- **Transactions**: Issue books to members, track return dates, and calculate rental fees automatically based on the borrowing period.

## Technologies Used

- **Backend**: Flask, SQLAlchemy (Python)
- **Frontend**: HTML, CSS (Bootstrap)
- **Database**: PostgreSQL
