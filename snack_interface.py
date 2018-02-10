#!/usr/bin/python
import shutil
from inspect import getargspec
import pdb
import sys
from Tkinter import *
import sqlite3
from time import sleep

# List of SnackBar Tables
tables = {
    'users' : 'users',
    'transactions' : 'transactions',
    'inventory' : 'inventory'
}

# Queries to create tables
CREATE_TABLE_USERS_QUERY = '''
CREATE TABLE {} (
idnum integer PRIMARY KEY AUTOINCREMENT,
netid text NOT NULL UNIQUE,
password text NOT NULL,
email text NOT NULL UNIQUE,
name text NOT NULL,
balance integer DEFAULT 0
);'''.format( tables['users'] )

CREATE_TABLE_TRANS_QUERY = '''
CREATE TABLE {} (
transid integer PRIMARY KEY AUTOINCREMENT,
netid text NOT NULL, 
inventoryid integer NOT NULL,
quantity text NOT NULL,
timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);'''.format( tables['transactions'] )

CREATE_TABLE_INVEN_QUERY = '''
CREATE TABLE {} (
inventoryid integer PRIMARY KEY AUTOINCREMENT,
product text NOT NULL UNIQUE,
cost integer NOT NULL
);'''.format( tables['inventory'] )

# Query to get complete list of inventory items
GET_INVENTORY_LIST_QUERY = '''
SELECT product,cost FROM {}
'''.format( tables['inventory'] )


class SnackBar_Interface:

    def __init__( self, master, db ):
        
        self.master = master

        # Save db
        self.db = db
        
        # Textbox for username
        self.username_entry = Entry( master )
        self.username = ''
        
        # Textbox for password
        self.password_entry = Entry( master, show='*' )
	self.password = ''

        # Log In button
        self.login_button = Button( master, text="Log In", command=self.check_login )

        # Quit Button
        self.quit_button = Button( master, text="Quit", command=master.quit )

        # Init Login interface
        self.login()

        # Submit button
        self.submit_button = Button( master, text="Submit", command=self.submit_order )
        
        # Dictionary to hold orders for products
        self.product_dict = dict()

        # Confirmation Balance Label
        self.balance_str = StringVar()
        self.confirmation_label = Label( master, textvariable=self.balance_str,
                                         justify=CENTER )


    def login( self ):
        # Clear up other widgets
        clear_frame( self.master )
        # Clear any previous login
        self.username = ''
        self.password = ''
        # Display Login widgets
        self.username_entry.pack()
        self.password_entry.pack()
        self.login_button.pack()

    def confirmation( self ):
        # Get user balance
        query = '''
        SELECT balance 
        FROM {}
        WHERE netid='{}'
        '''.format( tables['users'], self.username )
        r = self.db.execute( query ).fetchall()
        if ( r ):
            # Display Balance
            balance = float( r[0][0] )/100.
            if ( balance < 0 ):
                self.balance_str.set('Your New Balance is: -${:1.02f}'.format( abs(balance) ))
            else:
                self.balance_str.set('Your New Balance is: ${:1.02f}'.format( balance ))
                
            self.confirmation_label.pack()
        else:
            # Shouldn't ever get here
            raise Exception( 'Trying to fetch non-existent balance with netid {}'
                             .format( self.username ) )


    def shop( self ):
        # Get inventory items from database
        r = self.db.execute( GET_INVENTORY_LIST_QUERY ).fetchall()

        # Add an entry for each product
        count = 1
        for row in r:
            # Construct Label for Name+Price of Product
            product_label = Label( self.master, text='{}: ${:1.02f}'.
                                   format( row[0], float(row[1])/100. ) )
            # Quantity specifier for order
            product_qty = Spinbox( self.master, from_=0, to=10 )

            # Add label and quantity specifier to page
            product_label.grid( row=count, column=0 )
            product_qty.grid( row=count, column=2 )
            count += 1

            # Add product and order mapping to dictionary
            self.product_dict[row[0]] = (row[1], product_qty)
            
        # Separator between products and submit button
        separator = Frame( height=2, bd=1, relief=SUNKEN )
        separator.grid( row=count, columnspan=3 )
        count += 1
        
        # Pack Submit Button
        self.submit_button.grid( row=count, column=2 )

        pass

    def check_login( self ):
        username = self.username_entry.get()
        password = self.password_entry.get()

        st = verify_cred( self.db, username, password )

        if ( st ):
            self.username = username
            self.password = password
            clear_frame( self.master )
            self.username_entry.delete( 0, END )
            self.password_entry.delete( 0, END )
            self.shop()
            pass
        else:
            self.invalid_login()

    def submit_order( self ):
        # Calculate cost of order 
        total = 0
        for k in self.product_dict:
            # Add (quantity * cost) to total
            total += self.product_dict[k][0] * int(self.product_dict[k][1].get())
            # Submit Each order to transactions table
            query = '''
            INSERT INTO {} (netid, inventoryid, quantity)
            VALUES
            ( '{}', (SELECT inventoryid FROM {} WHERE product='{}'), {} );
            '''.format( tables['transactions'], self.username,
                        tables['inventory'], k, self.product_dict[k][0] )
            self.db.execute( query )
            self.db.connection.commit()

        # Update User Balance
        query = '''
        UPDATE {}
        SET balance = balance - {}
        WHERE netid='{}'
        '''.format( tables['users'], total, self.username )
        self.db.execute( query )
        self.db.connection.commit()
        
        # Clear order dictionary
        for k in self.product_dict:
            self.product_dict[k][1].selection_clear()

        # Remove current display widgets
        clear_frame( self.master )

        # Go to Order Confirmation Page
        self.confirmation()

        # Return to Login Interface
        self.master.after( 3000, self.login )
        #self.login()
        
        
def clear_frame( frame ):
    for slave in frame.pack_slaves():
        slave.pack_forget()
    for slave in frame.grid_slaves():
        slave.grid_forget()


def add_inventory( db, product, cost ):
    query = '''
    INSERT INTO {} (
    product, cost )
    VALUES ( '{}', '{}' );
    '''.format( tables['inventory'], product, cost )
    r = db.execute( query )
    db.connection.commit()


def add_user( db, username, password, name, email ):
    query = '''
    INSERT INTO {} (
    name, netid, email, password )
    VALUES ( '{}', '{}', '{}', '{}' );
    '''.format( tables['users'], name, username, email, password )
    r = db.execute( query )
    db.connection.commit()


def add_payment( db, username, payment ):
    open( 'failed.tsv', 'w' ).close()
    if ( not get_user( db, username ) ):
        print "Unable to update payment: {}, {}".format( username, payment )
        with open( 'failed.tsv', 'a' ) as fp:
            fp.write( '{}\t{}\n'.format( username, payment ) )
        return False
    query = '''
    UPDATE {}
    SET balance = balance + {}
    WHERE netid='{}'
    '''.format( tables['users'], payment, username )
    r = db.execute( query ).fetchall()
    db.connection.commit()


def update_balances( db, fname ):
    with open( fname, 'r' ) as fp:
        content = [x.split('\t') for x in fp.readlines()]
        payments = [[y[0], int(y[1])] for y in content]
        try:
            shutil.copy2( 'failed.tsv', 'failed.tsv.old' )
        except IOError as e:
            pass

        for i in payments:
            add_payment( db, i[0], i[1] )


def get_user( db, username ):
    query = '''
    SELECT *
    FROM {} 
    WHERE netid='{}'
    LIMIT 1;
    '''.format( tables['users'], username )
    r = db.execute( query ).fetchall()
    if ( r ):
        return True
    else:
        return False


def verify_cred( db, username, password ):
    query = '''
    SELECT *
    FROM {} 
    WHERE netid='{}' AND password='{}'
    LIMIT 1;
    '''.format( tables['users'], username, password )
    r = db.execute( query ).fetchall()
    if ( r ):
        return True
    else:
        return False

def dump_users( db ):
    query = '''
    SELECT * FROM {}
    '''.format( tables['users'] )
    r = db.execute( query ).fetchall()

    print "\n".join( [str(x) for x in r] )

def main( argv ):

    db_file = './snackbar.db'
    # Connect to snackbar database        
    db_conn = sqlite3.connect( db_file )
    db = db_conn.cursor()

    if ( len( argv ) == 2 ):
        update_balances( db, argv[1] )

    # Check if all database tables are setup
    for table_name in tables.values():
        query = '''
        SELECT name 
        FROM sqlite_master 
        WHERE type='table' AND name='{}'
        LIMIT 1;'''.format( table_name )
        db.execute( query )
        r = db.fetchall()
        if ( not r ):
            # Table doesn't exist, create it
            if ( table_name == tables['users'] ):
                db.execute( CREATE_TABLE_USERS_QUERY )
                db.connection.commit()
            elif ( table_name == tables['transactions'] ):
                db.execute( CREATE_TABLE_TRANS_QUERY )
                db.connection.commit()
            elif ( table_name == tables['inventory'] ):
                db.execute( CREATE_TABLE_INVEN_QUERY )
                db.connection.commit()
            else:
                # Should never get here
                raise Exception( 'Trying to create unknown table name {}'
                                 .format( table_name ) )

    update_balances( db, 'py.tsv' )
    pdb.set_trace()
    # Set up window
    win = Tk()
    # Make window fullscreen
    win.attributes('-fullscreen', True)
    # Create Interface 
    interface = SnackBar_Interface( win, db )
    win.mainloop()

if __name__ == "__main__":
    main( sys.argv )
