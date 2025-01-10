from utils import JsonLoader, JsonReader

import json
import time

json_loader = JsonLoader(database='order.json')
json_reader = JsonReader(database='order.json')

ask = input("\nOption: \n1. monitor\n2. clear\n\n")
if ask == "2" or ask == "clear" or ask == "1" or ask == "monitor":
    if ask == "2" or ask == "clear":
        json_loader.load([])

    while True:
        i = 1
        time.sleep(1) # 每1秒 print一遍
        print("\n\nORDER: \n\n")
        data = json_reader.read()
        for item in data:
            print(f"""Order {i} * {item["OrderTime"]}: \n{item}\n""")
            i = i + 1
else: 
    print("\n\nWrong Option")
        


