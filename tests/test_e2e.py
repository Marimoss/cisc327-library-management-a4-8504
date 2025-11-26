import pytest
from playwright.sync_api import Page, expect  # Install fixtures. 

BASE_URL = "http://localhost:5000"  # All tests can run headless by default for efficiency. 

# -------------------------------------------------------------------------

def test_catalog_display(page: Page):
    '''Automates user flow of visiting the catalog page and verifying that all sample books were loaded correctly.'''
    # Open the site. 
    page.request.get(BASE_URL + "/api/test/reset-db")  # Loads sample books.
    page.goto(BASE_URL)  # Navigate to the flask-based web app catalog (home) page.
    expect(page).to_have_url(BASE_URL + "/catalog")  # Assert we are on the catalog page.

    # Verify page header and subheader description. 
    expect(page.get_by_role("heading", name="📖 Book Catalog")).to_be_visible()
    expect(page.get_by_text("Browse all available books in our library collection.")).to_be_visible()  

    # Check table rows count. 
    # NOTE: for all searches, the first row is always for column names so there should be one extra row than the actual book count.
    expect(page.get_by_role("row")).to_have_count(4)  # 1 header row + 3 sample books. 

    # View all default books in catalog. 
    expect(page.get_by_role("row", name="1 The Great Gatsby")).to_be_visible()  # Assertions for each book. 
    expect(page.get_by_role("row", name="2 To Kill a Mockingbird")).to_be_visible()
    expect(page.get_by_role("row", name="3 1984")).to_be_visible()


def test_add_then_borrow_book(page: Page):
    '''Automates user flow of adding a book through the web interface successfully, then borrowing it successfully.'''
    # Begin in catalog page. 
    page.goto(BASE_URL + "/catalog")
    
    # Add a new book to catalog.
    page.get_by_role("link", name="➕ Add New Book").click()  # Click the add new book button. 
    expect(page).to_have_url(BASE_URL + "/add_book")  # Assert we are on the add book page.

    page.get_by_role("textbox", name="Title *").fill("Detective Chinatown")  # Fill in each required field. 
    page.get_by_role("textbox", name="Author *").fill("Peak")  
    page.get_by_role("textbox", name="ISBN *").fill("8888888888888")  
    page.get_by_role("spinbutton", name="Total Copies *").fill("8")  
    page.get_by_role("button", name="Add Book to Catalog").click() 
    
    # Verify that book appears in catalog. 
    expect(page.get_by_text('Book "Detective Chinatown" has been successfully added to the catalog.')).to_be_visible()
    assert "Detective Chinatown" in page.content()  # MIGHT be wrong. 

    row = page.get_by_role("row", name="4 Detective Chinatown")  # Formatted as “bookID Title". 
    expect(row).to_contain_text("Detective Chinatown")
    expect(row).to_contain_text("Peak")
    expect(row).to_contain_text("8888888888888")
    expect(row).to_contain_text("8/8 Available")  # Assert the book appears correctly. 

    # Navigate back to borrow the book. 
    expect(page).to_have_url(BASE_URL + "/catalog")
    
    # Borrow the book using a patron ID. 
    row.get_by_placeholder("Patron ID (6 digits)").fill("888888")
    row.get_by_role("button", name="Borrow").click()  # Click borrow button.
    
    # Verify that borrow confirmation message appears.
    expect(page.get_by_text('Successfully borrowed "Detective Chinatown".')).to_be_visible()
    expect(row).to_contain_text("7/8 Available")  # Assert that available copies decremented. 


def test_return_borrowed_book_no_fees(page: Page):
    """Automates user flow of returning a previously borrowed book above with no late fees and verifying the copies update."""
    # Begin in catalog page. 
    page.goto(BASE_URL + "/catalog")

    # Go to the return book page. 
    page.get_by_role("link", name="↩️ Return Book").click()  # Click the return book button. 
    expect(page).to_have_url(BASE_URL + "/return")  # Assert we are now on the return book page.

    # Fill in the return form (with the previously used patron ID and book ID).  
    page.get_by_role("textbox", name="Patron ID *").fill("888888")  
    page.get_by_role("spinbutton", name="Book ID *").fill("4")  
    
    # Verify the return confirmation message appears. 
    page.get_by_role("button", name="Process Return").click()  # Click return book button.
    expect(page.get_by_text('Book with id=4 returned successfully. No late fees.')).to_be_visible()
    expect(page).to_have_url(BASE_URL + "/return")  # Still on return page.

    # Verify that available copies incremented back to 8/8. 
    page.get_by_role("link", name="📖 Catalog").click()  # Return to catalog page. 
    row = page.get_by_role("row", name="4 Detective Chinatown")
    expect(row).to_contain_text("8/8 Available")


def test_search_book_by_different_criteria(page: Page): 
    '''Automates user flow of searching for books by different criteria such as partial title, author, and full ISBN.'''
    # Begin in catalog page. 
    page.goto(BASE_URL + "/catalog")

    # Go to the search book page. 
    page.get_by_role("link", name="🔍 Search").click()
    expect(page).to_have_url(BASE_URL + "/search")  # Assert we are on the search book page.

    # Search by a partial title. 
    page.get_by_role("textbox", name="Search Term").fill("Detec") 
    page.get_by_role("button", name="🔍 Search").click()
    expect(page.get_by_role("heading", name="Search Results for \"Detec\" (")).to_be_visible()
    expect(page.get_by_role("row")).to_have_count(2)  # 1 header row + 1 book result. 
    expect(page.get_by_role("row", name="4 Detective Chinatown")).to_be_visible()  # Verify the book appears in results.

    # Search by partial author (not case sensitive). 
    page.get_by_role("textbox", name="Search Term").fill("Pe")
    page.get_by_label("Search Type").select_option("author")
    page.get_by_role("button", name="🔍 Search").click()
    expect(page.get_by_role("heading", name="Search Results for \"Pe\" (")).to_be_visible()
    expect(page.get_by_role("row")).to_have_count(3)  # 1 header row + 2 book results. 
    expect(page.get_by_role("row", name="4 Detective Chinatown")).to_be_visible()
    expect(page.get_by_role("row", name="2 To Kill a Mockingbird")).to_be_visible()  # Harper Lee contains "Pe".

    # Search by full ISBN.
    page.get_by_role("textbox", name="Search Term").fill("8888888888888")
    page.get_by_label("Search Type").select_option("isbn")
    page.get_by_role("button", name="🔍 Search").click()
    expect(page.get_by_role("heading", name="Search Results for \"8888888888888\" (")).to_be_visible()
    expect(page.get_by_role("row")).to_have_count(2)  # 1 header row + 1 book result. 
    expect(page.get_by_role("row", name="4 Detective Chinatown")).to_be_visible()

    # Click to view all books button. 
    page.get_by_role("link", name="View All Books").click()
    expect(page).to_have_url(BASE_URL + "/catalog")  # Assert we were sent back on the catalog page.
    expect(page.get_by_role("row")).to_have_count(5)  # 1 header row + all 4 existing database books. 
