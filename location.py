import os

for root, dirs, files in os.walk(r"C:\Users\Lenovo\PycharmProjects"):
    for file in files:
        if file.lower() == "instruments.json":
            print(os.path.join(root, file))