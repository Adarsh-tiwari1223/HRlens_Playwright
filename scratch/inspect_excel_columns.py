import openpyxl

path = "testdata/static/Originator-Salary-April'2026.xlsx"
wb = openpyxl.load_workbook(path, data_only=True)
sheet = wb["APR'26"]

print("Row 4:", [cell.value for cell in sheet[4]])
print("Row 5:", [cell.value for cell in sheet[5]])
print("Row 6:", [cell.value for cell in sheet[6]])
print("Row 7:", [cell.value for cell in sheet[7]])
print("Row 8:", [cell.value for cell in sheet[8]])
