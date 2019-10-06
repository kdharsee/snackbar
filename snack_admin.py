#!/usr/bin/python
import datetime
import argparse
import shutil
from inspect import getargspec
from pdb import set_trace as pdb
import sys
import sqlite3
from time import sleep

DEBUG=1

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


def add_inventory( db, product, cost ):
    query = '''
    INSERT INTO {} (
    product, cost )
    VALUES ( '{}', '{}' );
    '''.format( tables['inventory'], product, cost )
    r = db.execute( query )
    db.connection.commit()

def rm_user( db, username ):
    netid = search_name( db, username )
    if ( not username ):
        print('FAILED to remove user "{}". No match in database'.format(username))

    else:
        query = '''
        DELETE FROM {} 
        WHERE netid='{}';
        '''.format( tables['users'], netid )
        r = db.execute( query )
        pdb()
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

    if ( not get_user( db, username ) ):
        print('Unable to update payment: {}, {}'.format( username, payment ))
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
        payments = []
        for line in fp:
            content = [x for x in filter( bool, line.rstrip().split('\t') )]
            payments.append( [content[0], int(content[1])] )

        try:
            shutil.copy2( 'failed.tsv', 'failed.tsv.old' )
        except IOError as e:
            pass

        for i in payments:
            add_payment( db, i[0], i[1] )

def get_email_from_dbrow( row ):
    return row[3]
def get_balance_from_dbrow( row ):
    return row[5]
            
def get_balances( db, fname=None ):

    if not fname:
        fname = 'balances{}.tsv'.format(datetime.date.today().strftime("%Y%m%d"))

    query = '''
    SELECT * FROM {}
    '''.format( tables['users'] )
    r = db.execute( query ).fetchall()

    FORMAT = "%s\t%d\n"

    with open( fname, 'w' ) as fp:
        for row in r:
            email = get_email_from_dbrow( row )
            balance = get_balance_from_dbrow( row )

            fp.write( FORMAT % (email, balance) )
            

def search_name( db, name ):
    FAIL = False

    query = '''
    SELECT *
    FROM {}
    WHERE name LIKE '%{}%'
    '''.format( tables['users'], name )
    r = db.execute( query ).fetchall()
    if ( len(r) == 1 ):
        return r[0][1]
    if ( len(r) > 1 ):
        print('Conflict trying to match name like: [{}]'.format( name ))
        for match in r:
            print('[CONFLICT] {}'.format( match ))
        return False


    query = '''
    SELECT *
    FROM {}
    WHERE email LIKE '%{}%'
    '''.format( tables['users'], name )
    r = db.execute( query ).fetchall()
    if ( len(r) == 1 ):
        return r[0][1]
    if ( len(r) > 1 ):
        print('Conflict trying to match email like: [{}]'.format( name ))
        for match in r:
            print('[CONFLICT] {}'.format( match ))
            return False

    query = '''
    SELECT *
    FROM {}
    WHERE netid LIKE '%{}%'
    '''.format( tables['users'], name )
    r = db.execute( query ).fetchall()
    if ( len(r) == 1 ):
        return r[0][1]
    if ( len(r) > 1 ):
        print('Conflict trying to match netid like: [{}]'.format( name ))
        for match in r:
            print('[CONFLICT] {}'.format( match ))
            return False
    

    print('Unable to match user with name/id like: [{}]'.format( name ))
    return False
    

def names_to_ids( db, fname ):
    FAIL = False
    
    with open( fname, 'r' ) as fp:
        payments = []
        for line in fp:
            content = [x for x in filter( bool, line.rstrip().split('\t') )]
            if ( not content ):
                print('Bad line: [{}]'.format( str(content )))
                FAIL = True
                break
            print('[DEBUG] content: {}'.format( str( content  )))
            payments.append( [content[0], int(content[1])] )

        for i in payments:
            netid = search_name( db, i[0] )
            if netid: 
                i[0] = netid
            else:
                FAIL = True
                print('UNKNOWN ID: *{}*'.format(i[0]))
                continue

        if ( not FAIL ):
            outfile = 'payments{}.tsv'.format(datetime.date.today().strftime("%Y%m%d"))
            print('Matched all names to IDs! Output to {}'.format( outfile ))
            with open( outfile, 'w' ) as fp:
                for i in payments:
                    fp.write( '{}\t{}\n'.format( i[0], i[1] ) )
            return outfile
        else:
            print('FAILED to match all names to IDs')
            return None
            

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

    print('\n'.join( [str(x) for x in r] ))

def main( argv ):

    parser = argparse.ArgumentParser()
    parser.add_argument('--dump', '-d', action='store_true', help='print(all user information')
    parser.add_argument('--adduser', '-u', nargs=4, help='Add a user', metavar=('<username>', '<password>', '<name>', '<email>'))
    parser.add_argument('--rmuser', '-r', nargs=1, help='Delete a user', metavar=('<username>'))
    parser.add_argument('--addinventory', '-i', nargs=2, help='Add an inventory item', metavar=('<product>', '<cost (in cents)>'))
    parser.add_argument('--addpayment', '-p', nargs=2, help='Add a payment', metavar=('<username>', '<amount (in cents)>'))
    parser.add_argument('--batchpayments', '-b', nargs=1, help='Update balances from payments file', metavar='<batchfile>')
    args = parser.parse_args()
    
    db_file = './snackbar.db'
    # Connect to snackbar database        
    db_conn = sqlite3.connect( db_file )
    db = db_conn.cursor()

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
                raise Exception( 'Table "{}" is not set up!'
                                 .format( table_name ) )
            

    if args.dump:
        print('All Users:')
        dump_users(db)
    elif args.adduser:
        print('Adding User...')
        add_user(db, args.adduser[0], args.adduser[1], args.adduser[2], args.adduser[3])
    elif args.rmuser:
        print('Deleting User...')
        rm_user(db, args.rmuser[0])
    elif args.addinventory:
        print('Adding to Inventory...')
        add_inventory(db, args.addinventory[0], args.addinventory[1])
    elif args.addpayment:
        print('Adding Payment...')
        add_payment(db, args.addpayment[0], args.addpayment[1])
    elif args.batchpayments:
        print('Adding Batch Payments...')
        payments_file = names_to_ids(db, args.batchpayments[0])
        if not payments_file:
            print("Aborting...")
            return
        print('Payments to be applied written to: {}'.format(payments_file))
        balance_file = '_balances{}.tsv'.format(datetime.date.today().strftime("%Y%m%d"))
        get_balances(db, fname=balance_file)
        print('Balances pre-payment written to: {}'.format(balance_file))
        update_balances(db, payments_file)
        balance_file = 'balances{}.tsv'.format(datetime.date.today().strftime("%Y%m%d"))
        get_balances(db, fname=balance_file)
        print('Balances post-payment written to: {}'.format(balance_file))
    else:
        parser.print_help()
        
if __name__ == "__main__":
    main( sys.argv )
