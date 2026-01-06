import sqlite3

# Database create karein aur sample data insert karein
def setup_database():
    conn = sqlite3.connect('data.db')
    cursor = conn.cursor()
    
    # Products table create karein
    cursor.execute('''CREATE TABLE IF NOT EXISTS products
                     (id INTEGER PRIMARY KEY, 
                     name TEXT, 
                     price INTEGER, 
                     stock INTEGER)''')
    
    # Sample products insert karein
    sample_products = [
        ('iPhone 15', 79900, 10),
        ('Samsung S23', 69900, 5),
        ('OnePlus 11', 54900, 8)
    ]
    
    cursor.executemany("INSERT INTO products (name, price, stock) VALUES (?, ?, ?)", sample_products)
    
    # FAQs table create karein
    cursor.execute('''CREATE TABLE IF NOT EXISTS faqs
                     (id INTEGER PRIMARY KEY,
                     question TEXT,
                     answer TEXT)''')
    
    # Sample FAQs insert karein
    sample_faqs = [
        ('Delivery time?', '3-5 working days'),
        ('Return policy?', '10 days return policy'),
        ('Warranty?', '1 year manufacturer warranty')
    ]
    
    cursor.executemany("INSERT INTO faqs (question, answer) VALUES (?, ?)", sample_faqs)
    
    conn.commit()
    conn.close()

setup_database()
