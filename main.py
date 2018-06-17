import csv
import pickle


class LedgerEntry:
    def __init__(self, date, desc, accts, cmt):
        self.date = date
        self.desc = desc
        self.accts = accts
        self.cmt = cmt
        self.recognized = False

    def __str__(self):
        def prn_acct(acct):
            """Expects either a tuple form (str, num) representing the account and
transaction amount, or a str representing the transaction. An entry's
list of accounts should be at most one str, and the rest tuples."""
            if type(acct) == tuple:
                ac, v = acct
                return "    {}  {}".format(ac, v)
            elif type(acct) == str:
                return "    " + acct
            else:
                return ''

        if self.cmt is '':
            return "{date} {desc}\n{accts}\n".format(
                date=self.date,
                desc=self.desc,
                accts='\n'.join(list(map(prn_acct, self.accts))))
        else:
            return "\n{date} * {desc}\n    ; {cmt}\n{accts}\n".format(
                cmt=self.cmt,
                date=self.date,
                desc=self.desc,
                accts='\n'.join(list(map(prn_acct, self.accts))))

    def recognize(self, rules):
        if self.recognized is True:
            return
        for rex, desc, acct in rules:
            if rex in self.desc:
                self.cmt = self.desc
                self.desc = desc
                self.accts.append(acct)
                self.recognized = True
                break


class UWCU:
    fmt_str = "{date} {desc}\n    {pri_acct}  {val}\n    {sec_acct}\n"

    def write_rules(rules):
        with open('uwcu_rules.csv', 'w') as out:
            csv_out = csv.writer(out)
            csv_out.writerow(['MatchString', 'Description', 'Account'])
            for rule in rules:
                csv_out.writerow(rule)

    def read_rules():
        with open('uwcu_rules.csv', 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            return [(row['MatchString'], row['Description'], row['Account'])
                    for row in reader]

    def load_rules():
        with open('uwcu.pickle', 'rb') as f:
            return pickle.load(f)

    def recognize_entry(pri_acct, row):
        le = LedgerEntry(
            mdy_to_ymd(row['Posted Date']),
            row['Description'],
            [(pri_acct, norm_neg(row['Amount']))
             # "Auto:{}".format(row['Category'].replace(' ', '')),
             ],
            '',
        )
        le.recognize(UWCU.load_rules())
        if not le.recognized:
            le.accts.append("Auto:{}".format(row['Category'].replace(' ', '')))
        return le

    def recognize_file(pri_acct, filename):
        with open(filename) as csvfile:
            reader = csv.DictReader(csvfile)
            transactions = [
                UWCU.recognize_entry(pri_acct, row) for row in reader
            ]
            return transactions

    def translate_export(pri_acct, infile, outfile):
        transactions = UWCU.recognize_file(pri_acct, infile)
        [t.recognize(UWCU.load_rules()) for t in transactions]
        with open(outfile, 'w') as fh:
            for t in transactions:
                fh.write(str(t))

    def read_account_export(filename):
        with open(filename) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                print(
                    UWCU.fmt_str.format(
                        date=mdy_to_ymd(row['Posted Date']),
                        desc=row['Description'],  # [:15],
                        pri_acct='Assets:Checking',
                        val=norm_neg(row['Amount']),
                        sec_acct="Auto:" + row['Category'].replace(' ', '')))


def norm_neg(amount):
    if amount.startswith('('):
        return "-" + amount[1:-1]
    return amount


def norm_usd(val):
    if type(val) == int or type(val) == float:
        return "${}".format(val)


#     elif type(val) == str:


class CatBank:
    fmt_str = "\n{date} {desc}\n    {pos_acct}  ${val}\n    {neg_acct}\n"

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
    lst = list(map(lambda x: x.zfill(2), lst))
    lst.insert(0, year)
    return '/'.join(lst)


known_accts = [
    ("UWM RESTAU MILWAUKEE", "UWM Restaurant Ops", "Expenses:Food:DiningOut"),
    ("EAST GARDE", "East Garden", "Expenses:Food:DiningOut"),
]

# CatBank.read_account_export('export.csv')
UWCU.translate_export("Assets:Checking", "History.csv", "auto.ledger")
UWCU.translate_export("Assets:Savings", "History-Savings.csv",
                      "auto-savings.ledger")
