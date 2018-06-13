import csv


# class Transaction:

class CatBank:
    fmt_str = "#{cmt}\n{date} {desc}\n\t{pos_acct}\t${val}\n\t{neg_acct}\n"

    def credit(row):
        return CatBank.fmt_str.format(
            date=mdy_to_ymd(row['Date']),
            desc=row['Description'],
            pos_acct='Accounts:Checking',
            val=row['Credit'],
            neg_acct='Expenses:Uncategorized',
            cmt='')

    def debit(row):
        return CatBank.fmt_str.format(
            date=mdy_to_ymd(row['Date']),
            desc=row['Description'],
            pos_acct='Accounts:Checking',
            val=row['Debit'],
            neg_acct='Expenses:Uncategorized',
            cmt='')

    def recognize_transaction():
        pass

    def read_account_export(filename):
        with open(filename) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['Type'] == 'CREDIT':
                    print(CatBank.credit(row))
                elif row['Type'] == 'DEBIT':
                    print(CatBank.debit(row))
                else:
                    print('??? Unknown transaction type ???')


def mdy_to_ymd(datestr):
    lst = datestr.split(sep='/')
    year = lst.pop()
    lst.insert(0, year)
    return '/'.join(lst)


known_accts = [
    ("UWM RESTAU MILWAUKEE", "UWM Restaurant Ops", "Expenses:Food:DiningOut"),
    ("EAST GARDE", "East Garden", "Expenses:Food:DiningOut"),
]

CatBank.read_account_export('export.csv')
