# project: p2
# submitter: zdai38
# partner: none

from zipfile import ZipFile
from io import TextIOWrapper
import csv

class ZippedCSVReader():
    def __init__(self, filename):
        self.filename = filename
        paths = []
        with ZipFile(self.filename) as zf:
            for info in zf.infolist():
                paths.append(info.filename)
        self.paths = sorted(paths)
                
    def __str__(self):
        return self.paths
    
    def lines(self, name):
        with ZipFile(self.filename) as zf:
            with zf.open(name) as f:
                for line in TextIOWrapper(f):
                    yield line
    
    def csv_iter(self, name = None):
        with ZipFile(self.filename) as zf:
            if name == None:
                    for i in self.paths:
                        with zf.open(i, "r") as csvfile:
                            tio1 = TextIOWrapper(csvfile)
                            reader = csv.DictReader(tio1)
                            for row in reader:
                                yield row
            
            else:
                with zf.open(name, "r") as csvfile:
                    tio2 = TextIOWrapper(csvfile)
                    reader = csv.DictReader(tio2)
                    for row in reader:
                        yield row
                   
class Loan:
    def __init__(self, amount, purpose, race, income, decision):
        self.amount = amount
        self.purpose = purpose
        self.race = race
        self.income = income
        self.decision = decision
        self.list = [self.amount,self.purpose,self.race,self.income,self.decision]

    def __repr__(self):
        return f"Loan({self.amount}, '{self.purpose}', '{self.race}', {self.income}, '{self.decision}')"

    def __getitem__(self, lookup):
        if hasattr(self, str(lookup)) == False:
            for i in self.list:
                if lookup == i:
                    return 1
            return 0
        
        else:
            return getattr(self, lookup)
    
    def set_race(self, val):
        self.race = val
        self.list[2] = val
        
def get_bank_names(reader):
    bank_list = []
    for row in reader.csv_iter():
        for i in row:
            if i == "agency_abbr":
                if not row[i] in bank_list:
                    bank_list.append(row[i])
    return sorted(bank_list)
    
class Bank:
    def __init__(self, name, reader):
        self.reader = reader
        self.name = name
    
    def loan_iter(self):
                    
        for row in self.reader.csv_iter():
            if self.name == None:
                if row["action_taken_name"] == "Loan originated":
                    decision = "approve"
                if row["action_taken_name"] != "Loan originated":
                    decision = "deny"
                if row["loan_amount_000s"]=="":
                    amount = 0
                if row["loan_amount_000s"]!="":
                    amount = int(row["loan_amount_000s"])
                if row["applicant_income_000s"] =="":
                    income = 0
                if row["applicant_income_000s"] !="":
                    income = int(row["applicant_income_000s"])

                loan = Loan(amount, row["loan_purpose_name"],row["applicant_race_name_1"],income,decision)
                yield loan
            
            
            for i in row:
                if i == "agency_abbr" and row[i] == self.name:
                    if row["action_taken_name"] == "Loan originated":
                        decision = "approve"
                    if row["action_taken_name"] != "Loan originated":
                        decision = "deny"
                    if row["loan_amount_000s"]=="":
                        amount = 0
                    if row["loan_amount_000s"]!="":
                        amount = int(row["loan_amount_000s"])
                    if row["applicant_income_000s"] =="":
                        income = 0
                    if row["applicant_income_000s"] !="":
                        income = int(row["applicant_income_000s"])
                        
                    loan = Loan(amount, row["loan_purpose_name"],row["applicant_race_name_1"],income,decision)
                    yield loan
    
    def loan_filter(self, loan_min, loan_max, loan_purpose):
        for i in self.loan_iter():
            if i["amount"] >= loan_min and i["amount"] <= loan_max and i["purpose"]==loan_purpose:
                yield i

class SimplePredictor():
    def __init__(self):
        self.approve = 0
        
    def predict(self, loan):
        if loan["purpose"] == "Home improvement":
            self.approve += 1
            return True
        else:
            return False

    def getApproved(self):
        return self.approve

class Node():
    def __init__(self, key, val):
        self.key = key
        self.val = val
        
        self.left = None
        self.right = None
        
class DTree(SimplePredictor):
    def __init__(self):
        self.disapprove = 0
        super().__init__()
        
    def readTree(self, reader, path):
        depth_dict = {}
        lines = [] 
        for row in reader.lines(path):
            parts = row.split("--- ")
            depth = parts[0].count("|")
            content = parts[1]
            lines.append((depth, content))

        for depth, line in lines:
            if "<=" in line:
                content_split = line.split(" <= ")
                
            if "class:" in line:
                content_split = line.split(": ") 
                
            if not ">" in line:
                if depth == 1:
                    root = Node(content_split[0], float(content_split[1].strip()))
                    depth_dict[depth] = root

                elif depth_dict[depth-1].left == None:
                    depth_dict[depth-1].left = Node(content_split[0], float(content_split[1].strip()))
                    depth_dict[depth] = depth_dict[depth-1].left
                else:
                    depth_dict[depth-1].right = Node(content_split[0], float(content_split[1].strip()))
                    depth_dict[depth] = depth_dict[depth-1].right
                    
        self.tree = root
        #return root
    
    def predict(self,data):
        return self.call_predict(data, self.tree)
        
    def call_predict(self, data, node):
        if node.val == 0:
            self.disapprove += 1
            return False
        if node.val == 1:
            self.approve += 1
            return True
        
        if data[node.key] <= node.val:
            if node.left != None:
                return self.call_predict(data,node.left)
        else:
            if node.right != None:
                return self.call_predict(data, node.right)
            
    def getDisapproved(self):
        return self.disapprove

class RandomForest(SimplePredictor):
    def __init__(self, trees):
        self.trees = trees

    def predict(self, loan):
        ones = 0
        count = 0
        for i in self.trees:
            count += 1
            if i.predict(loan)==True:
                ones += 1
        return ones>=(count-ones)

def bias_test(bank, predictor, race_override):
    total = 0
    diff_result = 0
    
    for loan in bank.loan_iter():
        total += 1
        result = predictor.predict(loan)
        loan.set_race(race_override)
        
        new_result = predictor.predict(loan)
        #print(result,new_result)
        if result != new_result:
            diff_result += 1

    return diff_result/total

    return diff_result/total