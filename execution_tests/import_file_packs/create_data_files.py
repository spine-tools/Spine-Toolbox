import csv

with open("1.dat", "w", newline="") as out_file:
    writer = csv.writer(out_file)
    writer.writerow(["a", "b", 23])
    writer.writerow(["a", "c", 50])

with open("2.dat", "w", newline="") as out_file:
    writer = csv.writer(out_file)
    writer.writerow(["a", "d", -23])
    writer.writerow(["a", "e", -50])
