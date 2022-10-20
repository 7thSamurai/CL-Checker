import sqlite3, os, urllib.parse

class Query:
    def __init__(self, area, section, query, alarm, email, id=-1):
        self.area = area
        self.section = section
        self.query = query
        self.alarm = alarm
        self.email = email
        self.id = id

    def name(self):
        return f'{self.area}/{self.section}/{self.query}'

    # Generate the complete URL
    def url(self):
        params = f'query={urllib.parse.quote(self.query)}'
        return f'https://{self.area}.craigslist.org/search/{Query.sections[self.section]}?{params}'

    # Craigslist sections
    sections = {
        'all': 'sss',
        'antiques': 'ata',
        'appliances': 'ppa',
        'arts+crafts': 'ara',
        'atvs/utvs/snow': 'sna',
        'auto parts': 'pta',
        'auto wheels & tires': 'wta',
        'aviation': 'ava',
        'baby+kids': 'baa',
        'barter': 'bar',
        'beauty+hlth': 'haa',
        'bike parts': 'bip',
        'bikes': 'bia',
        'boat parts': 'bpa',
        'boats': 'boo',
        'books': 'bka',
        'business': 'bfa',
        'cars+trucks': 'cta',
        'cds/dvd/vhs': 'ema',
        'cell phones': 'moa',
        'clothes+acc': 'cla',
        'collectibles': 'cba',
        'computer parts': 'syp',
        'computers': 'sya',
        'electronics': 'ela',
        'farm+garden': 'gra',
        'free stuff': 'zip',
        'furniture': 'fua',
        'garage sales': 'gms',
        'general': 'foa',
        'heavy equipment': 'hva',
        'household': 'hsa',
        'jewerly': 'jwa',
        'materials': 'maa',
        'motorcycle parts': 'mpa',
        'motorcycles': 'mca',
        'music instr': 'msa',
        'photo+video': 'pha',
        'RVs': 'rva',
        'sporting': 'sga',
        'tickets': 'tia',
        'tools': 'tla',
        'toys+games': 'taa',
        'trailers': 'tra',
        'video gaming': 'vga',
        'wanted': 'waa'
    }

class Product:
    def __init__(self, id, name, url, query):
        self.id = id
        self.name = name
        self.url = url
        self.query = query

class DB:
    """
    Connivent wrapper around SQLite for storing all the different product information.
    """

    def __init__(self, path):
        path = os.path.join(os.path.dirname(__file__), path)
        exists = os.path.exists(path)

        try:
            self.conn = sqlite3.connect(path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        except:
            pass # TODO

        # Initial Setup
        if not exists:
            self.conn.execute('''
                CREATE TABLE PRODUCTS
                (ID    INT       NOT NULL PRIMARY KEY,
                 NAME  TEXT      NOT NULL,
                 URL   TEXT      NOT NULL,
                 QUERY TEXT      NOT NULL,
                 FOUND TIMESTAMP NOT NULL,
                 SEEN  TIMESTAMP NOT NULL
                );''')

            self.conn.execute('''
                CREATE TABLE QUERIES
                (ID      INTEGER  PRIMARY KEY,
                 AREA    TEXT NOT NULL,
                 SECTION TEXT NOT NULL,
                 QUERY   TEXT NOT NULL,
                 ALARM   INT  NOT NULL,
                 EMAIL   INT  NOT NULL
                );''')

            self.conn.commit()
            
    def get_queries(self):
        """
        Gets a list of all queries
        """
            
        cursor = self.conn.execute('SELECT * FROM QUERIES ORDER BY ID;')
        queries = []
        
        for row in cursor:
            queries.append(Query(row[1], row[2], row[3], row[4] == 1, row[5] == 1, row[0]))
        
        return queries
            
    def get_query(self, id):
        """
        Grabs a query by it's ID, returning None if it does not exist
        """
    
        cursor = self.conn.execute('SELECT * FROM QUERIES WHERE ID = ?;', [id])

        query = cursor.fetchone()
        if not query:
            return None

        return Query(query[1], query[2], query[3], query[4] == 1, query[5] == 1, query[0])
        
    def add_query(self, query):
        """
        Adds a query to the database, returning it's ID
        """
        
        self.conn.execute(
            'INSERT INTO QUERIES (AREA, SECTION, QUERY, ALARM, EMAIL) VALUES(?, ?, ?, ?, ?);',
            [query.area, query.section, query.query, query.alarm, query.email]
        )

        self.conn.commit()
        
        # Get the ID of the newly inserted record
        cursor = self.conn.execute('SELECT MAX(ID) FROM QUERIES;')
        return cursor.fetchone()[0]
        
    def update_query(self, query):
        """
        Updates a query in the database
        """
        
        self.conn.execute(
            'UPDATE QUERIES SET AREA = ?, SECTION = ?, QUERY = ?, ALARM = ?, EMAIL = ? WHERE ID = ?', 
            [query.area, query.section, query.query, 1 if query.alarm == True else 0, 1 if query.email == True else 0, query.id]
        )
        
        self.conn.commit()
        
    def delete_query(self, id):
        """
        Deletes a query by it's ID
        """
        
        self.conn.execute('DELETE FROM QUERIES WHERE ID = ?;', [id])
        self.conn.commit()
        
    def get_product(self, product):
        """
        Grabs a product by it's ID, returning None if it does not exist
        """
        
        cursor = self.conn.execute('SELECT * FROM PRODUCTS WHERE ID = ?;', [product.id])

        product = cursor.fetchone()
        if not product:
            return None

        return Product(product[0], product[1], product[2], product[3])

    def get_products(self, query_url):
        """
        Grabs a list of all products that were found using a query URL
        """
        
        cursor = self.conn.execute('SELECT * FROM PRODUCTS WHERE QUERY = ? ORDER BY FOUND;', [query_url])
        products = []

        for row in cursor:
            products.append(Product(row[0], row[1], row[2], row[3]))

        return products

    def get_num_products(self, query_url):
        """
        Grabs the number of products that were found using a query URL
        """

        cursor = self.conn.execute('SELECT COUNT(ID) FROM PRODUCTS WHERE QUERY = ?;', [query_url])
        return cursor.fetchone()[0]

    def add_product(self, product):
        """
        Adds a product to the database, or updates it if it already exists
        """
        
        cursor = self.conn.execute('SELECT * FROM PRODUCTS WHERE ID = ?', [product.id])
        
        # First check if the product already exists in the database
        if cursor.fetchone() != None:
            self.conn.execute('UPDATE PRODUCTS SET SEEN = datetime("now") WHERE ID = ?', [product.id])
        else:
            self.conn.execute(
                'INSERT INTO PRODUCTS (ID, NAME, URL, QUERY, FOUND, SEEN) VALUES(?, ?, ?, ?, datetime("now"), datetime("now"));',
                [product.id, product.name, product.url, product.query]
            )

        self.conn.commit()

    def delete_old_products(self):
        """
        Deletes any old products from the database that were last seen over a week ago
        """
        
        self.conn.execute('DELETE FROM PRODUCTS WHERE datetime("now") >= datetime(SEEN, "+7 days");')
        self.conn.commit()
