with open("input_file.txt") as ifile:
    lines = ifile.readlines()
print(" ".join(lines).strip())
with open("output_file.txt", "w") as ofile:
    ofile.writelines(lines + ["World!"])
