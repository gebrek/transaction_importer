import csv


class LedgerAcct(object):
    def __init__(self, name, amount=None):
        self.name = name
        self.amount = amount

    def __str__(self):
        if self.amount:
            return "{}  {}".format(self.name, self.amount)
        else:
            return self.name

    def __repr__(self):
        if self.amount:
            return "<{} {}>".format(self.name, self.amount)
        else:
            return "<{}>".format(self.name)


class LedgerEntry:
    """LedgerEntry objects are individual records of transactions. They
should have a date, a description, and a list of accounts. Optionally
a comment. They will be 'recognized' if they have successfully been
checked against set of rules and translated."""

    def __init__(self, date, desc, accts):
        self.date = date
        self.desc = desc
        self.accts = accts
        self.cmt = None
        self.recognized = False

    def __str__(self):
        fmtstr = "{}{}{} {}\n    {}\n"
        return fmtstr.format(self.date, " * " if self.recognized else " ",
                             self.desc, "  ;{}".format(self.cmt)
                             if self.cmt else '', '\n    '.join(
                                 map(str, self.accts)))

    def __repr__(self):
        fmtstr = "<{}>"
        return fmtstr.format(self.desc)

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


class LedgerJournal:
    def __init__(self, entries):
        self.entries = entries


class UWCU:
    rules_file = 'uwcu_rules.csv'
    rules = None

    # The following two functions should be close to generalized
    # already for use in other exporter classes. Should probably make
    # a parent class which all the specialized exporters will inherit from
    def write_rules(rules):
        with open(UWCU.rules_file, 'w') as out:
            csv_out = csv.writer(out)
            csv_out.writerow(['MatchString', 'Description', 'Account'])
            for rule in rules:
                csv_out.writerow(rule)

    def _force_read_rules():
        with open(UWCU.rules_file, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            UWCU.rules = [(row['MatchString'], row['Description'],
                           row['Account']) for row in reader]

    def read_rules():
        # Memoize!
        if UWCU.rules:
            return UWCU.rules
        else:
            UWCU._force_read_rules()
            return UWCU.rules

    def recognize_entry(pri_acct, row):
        le = LedgerEntry(
            mdy_to_ymd(row['Posted Date']),
            row['Description'],
            [LedgerAcct(pri_acct, normalize_cur(row['Amount']))],
        )
        le.recognize(UWCU.read_rules())
        if not le.recognized:
            le.accts.append("Auto:{}".format(row['Category'].replace(' ', '')))
        return le

    def recognize_file(pri_acct, filename):
        with open(filename) as csvfile:
            reader = csv.DictReader(csvfile)
            transactions = [
                UWCU.recognize_entry(pri_acct, row) for row in reader
            ]
            return LedgerJournal(transactions)

    def translate_export(pri_acct, infile, outfile):
        """translate_export is the entry point for reading, and writing from a raw csv
export file to a useful ledger file."""
        journal = UWCU.recognize_file(pri_acct, infile)
        [t.recognize(UWCU.read_rules()) for t in journal.entries]
        with open(outfile, 'w') as fh:
            for t in journal.entries:
                fh.write(str(t))


class AssociatedBank:
    rules_file = 'associated_bank_rules.csv'
    rules = None

    def _force_read_rules():
        with open(AssociatedBank.rules_file, 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            AssociatedBank.rules = [(row['MatchString'], row['Description'],
                                     row['Account']) for row in reader]

    def read_rules():
        # Memoize!
        if AssociatedBank.rules:
            return AssociatedBank.rules
        else:
            AssociatedBank._force_read_rules()
            return AssociatedBank.rules

    def recognize_entry(pri_acct, row):
        le = LedgerEntry(
            mdy_to_ymd(row['Date']), row['Description'],
            [LedgerAcct(pri_acct, "$" + row[row['Type'].title()])])
        le.recognize(AssociatedBank.read_rules())
        if not le.recognized:
            le.accts.append("Auto:Uncategorized")
        return le

    def recognize_file(pri_acct, filename):
        with open(filename) as csvfile:
            reader = csv.DictReader(csvfile)
            transactions = [
                AssociatedBank.recognize_entry(pri_acct, row) for row in reader
            ]
            return LedgerJournal(transactions)

    def translate_export(pri_acct, infile, outfile):
        journal = AssociatedBank.recognize_file(pri_acct, infile)
        [t.recognize(AssociatedBank.read_rules()) for t in journal.entries]
        with open(outfile, 'w') as fh:
            for t in journal.entries:
                fh.write(str(t))


# General utility functions


def mdy_to_ymd(datestr):
    lst = datestr.split(sep='/')
    year = lst.pop()
    lst = list(map(lambda x: x.zfill(2), lst))
    lst.insert(0, year)
    return '/'.join(lst)


def normalize_cur(amount):
    # amount = amount.replace("$", "")
    # print(amount)
    if amount.startswith('('):
        return "-" + amount[1:-1]
    return amount


def detect_cur(amount):
    pass


def norm_usd(val):
    if type(val) == int or type(val) == float:
        return "${}".format(val)


# CatBank.read_account_export('export.csv')
# UWCU.translate_export("Assets:Checking", "History.csv", "auto1.ledger")
# UWCU.translate_export("Assets:Savings", "History-Savings.csv",
#                       "auto1-savings.ledger")
