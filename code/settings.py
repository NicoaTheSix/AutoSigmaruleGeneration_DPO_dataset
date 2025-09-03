import os
import time
import json
import secrets
import string

# --- 全域設定 ---

# 檔案編碼
file_encoding = "utf-8"

# LLM 來源與模型設定
source = "openai"  # 可選 "ollama"
llm = "gpt-4o-mini"  # 可選 "llama3.2"

# --- 路徑設定 ---
# 專案根目錄
home_path = os.getcwd()
# 回應檔案的標題，以時間命名
response_title = time.strftime("%Y%m%d%H%M", time.localtime())
# 存放生成結果的資料夾路徑
response_folder_path = os.path.join(home_path, "response")
# 目標作業系統
targetOS = "Windows 11"

# --- 資料集路徑 ---
# TTP 相關資料路徑
dir_ttp = os.path.join(home_path, "ttp_with_procedure")
dict_ttp = os.path.join(home_path, "dict_technique.json")
csv_ttp = os.path.join(home_path, "techniques.csv")
csv_ttp_noPr = os.path.join(home_path, "techniques_noPr.csv")
# 載入技術字典
with open(dict_ttp, 'r', encoding=file_encoding) as Json:
    dictionary_technique = json.load(Json)

# CTI 報告目錄 (使用者需自行設定)
dir_cti = os.path.join("D:\\", "all_CTI_report")

# --- 目錄結構 ---
# 定義專案應有的目錄結構
dir_struct = {
    'response': {
        'tasks': {},
    }
}

# --- 執行紀錄 ---
# 全域變數，用於記錄程式執行過程中的各項資訊
JsonRecord = {
    "Error": [],
    "Settings": {
        "source": source,
        "llm": llm,
        "title of the Response": response_title
    },
    "Input": {},
    "Code review": {},
    "Debug": {},
    "Main code review": {},
    "Responce": {}
}

# --- 自訂例外 ---
class ProjectEnvironmentSettingError(Exception):
    """當環境設定不正確時拋出的例外。"""
    def __init__(self, message="There's something wrong in setting.\nPlease check setting.py once more."):
        self.message = message
        super().__init__(self.message)

# --- 輔助函式 ---

def UI_initiate():
    """顯示專案標題 UI。"""
    title_ = f'''
=======================================
Automatic-Malware-Generation-Using-LLMs
--from AntLab in NTUST-----------------
=======================================
'''
    print(title_)

def generate_secure_random_string(length):
    """
    產生指定長度的安全隨機字串。

    Args:
        length (int): 隨機字串的長度。

    Returns:
        str: 產生的隨機字串。
    """
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

def create_dir(homePath: str, dirStruct: dict):
    """
    遞迴地建立專案所需的目錄結構。

    Args:
        homePath (str): 當前路徑。
        dirStruct (dict): 要建立的目錄結構字典。
    """
    for directory, subStructure in dirStruct.items():
        path = os.path.join(homePath, directory)
        os.makedirs(path, exist_ok=True)  # 如果目錄不存在則建立
        create_dir(path, subStructure)  # 遞迴建立子目錄

def namestr(obj):
    """取得變數的原始名稱字串。"""
    try:
        namespace = globals()
        return [name for name in namespace if namespace[name] is obj]
    except:
        namespace = locals()
        return [name for name in namespace if namespace[name] is obj]

def split_line(bool_display: bool = False):
    """顯示分隔線。"""
    split_line = "================================="
    if bool_display:
        print("{:>38} {:<30}".format(split_line, ""))

def saveRecord(filename_jsonRecord: str, path: str = ""):
    """
    將執行紀錄 (JsonRecord) 儲存至指定的 JSON 檔案。

    Args:
        filename_jsonRecord (str): 儲存紀錄的檔名。
        path (str, optional): 儲存路徑。預設為 response_folder_path。
    """
    if path == "":
        path = response_folder_path
    
    with open(os.path.join(path, filename_jsonRecord), mode='w', encoding=file_encoding) as LogFile:
        json.dump(JsonRecord, LogFile, indent=4)

def loadSettings(bool_display: bool = False):
    """
    初始化並檢查專案環境設定。
    - 建立目錄結構
    - 檢查必要的檔案與路徑是否存在
    - 檢查 API 金鑰

    Args:
        bool_display (bool, optional): 是否顯示詳細的檢查過程。預設為 False。
    """
    # ... (內部輔助函式) ...
    try:
        UI_initiate()
        create_dir(homePath=home_path, dirStruct=dir_struct)
        print("[+] Creating directory structure")
        # ... (其餘檢查邏輯) ...
        print("[-] Directory checking Finish")
    except Exception as e:
        # 捕捉到任何錯誤，拋出自訂的設定例外
        raise ProjectEnvironmentSettingError()

# --- 測試區塊 ---
if __name__ == "__main__":
    
    loadSettings(bool_display=True)

