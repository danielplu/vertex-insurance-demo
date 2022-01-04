import csv
from faker import Faker

fake = Faker()


with open('/Users/dplu/Downloads/insurance.csv','r') as csvinput:
    with open('/Users/dplu/Downloads/insurance_pii.csv', 'w') as csvoutput:
        writer = csv.writer(csvoutput, lineterminator='\n')
        reader = csv.reader(csvinput)

        all = []
        row = next(reader)
        row.append('SSN')
        row.append('Phone Number')
        all.append(row)

        for row in reader:
            row.append(fake.ssn())
            row.append(fake.phone_number())
            all.append(row)

        writer.writerows(all)