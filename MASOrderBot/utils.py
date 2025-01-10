import json
import re
from datetime import datetime


# Code
class CodeExtractor:
    def __init__(self, code='json'):
        self.code = code
    
    def extract(self, text):
        # 这里假设了只有一段被反引号包括的文本
        match = re.search(r"```(.*?)```", text, flags=re.DOTALL)

        # debugger
        if not match:
            text = {"error": text, "OrderTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            return text
        code_text = match.group(1).strip()
        
        # json
        if len(code_text) >= 3 and (self.code == 'json'):
            if 'json' in code_text.lower():
                code_text = code_text.replace("json", "").replace("Json", "").replace("\'", "\"").strip()

            code = json.loads(code_text) # 容易报错

            code["OrderTime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            return code
 

class JsonLoader:
    def __init__(self, database=''):
        self.database = database
    def load(self, file):
        with open(self.database, "w") as f:
            json.dump(file, f, indent=4)

class JsonReader:
    def __init__(self, database=''):
        self.database = database
    def read(self):
        with open(self.database, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    



# YES/NO 提取器
class YesNoExtractor:
    def __init__(self):
        pass
    def extract(self, text):
        if "no" in text.lower():
            return 0
        elif "yes" in text.lower():
            return 1
        else:
            return "extract failed"