# workflow_gemini.py
import re, os, time, json, random, subprocess, ollama, argparse, pandas as pd
from glob import glob
from tqdm import tqdm
from openai import OpenAI
import settings
import uuid
import sys

# 從 settings 模組導入必要的設定與函式
from settings import (
    home_path, response_title, response_folder_path, targetOS, dir_ttp,
    dict_ttp, csv_ttp, csv_ttp_noPr, dir_cti, generate_secure_random_string,
    loadSettings, saveRecord, file_encoding
)

# --- LLM 互動函式 ---

def Llmrequest(messages: list, source: str = settings.source, llm: str = settings.llm):
    """
    根據設定的來源 (OpenAI 或 Ollama) 向大型語言模型發送請求。

    Args:
        messages (list): 包含對話歷史的訊息列表。
        source (str, optional): LLM 來源 ('openai' 或 'ollama')。預設來自 settings。
        llm (str, optional): 使用的 LLM 模型名稱。預設來自 settings。

    Returns:
        str: LLM 的回應內容。
    """
    def gpt_request(llm: str, messages: list):
        """處理 OpenAI API 請求。"""
        api_key = os.getenv("OPENAI_API_KEY")
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=llm,
            messages=messages,
            temperature=0
        )
        return response.choices[0].message.content

    def ollama_request(llm: str, messages: list):
        """處理 Ollama 請求。"""
        response = ollama.chat(
            model=llm,
            messages=messages
        )
        return response['message']['content']

    if source == "openai":
        return gpt_request(llm=llm, messages=messages)
    elif source == "ollama":
        return ollama_request(llm=llm, messages=messages)

def textLoader(txtName: str):
    """
    從 'prompt' 資料夾載入指定的系統提示 (System Prompt) 檔案。

    Args:
        txtName (str): 提示檔案的名稱 (不含 .txt 副檔名)。

    Returns:
        str: 提示檔案的內容。
    """
    prompt_path = os.path.join(os.getcwd(), "prompt", f"{txtName}.txt")
    with open(prompt_path, "r", encoding="utf-8") as file:
        prompt = file.read()
    return prompt

def Llminteraction(dict_input: dict, task: str, outputFormatRegex: str = "", display: bool = False):
    """
    一個與 LLM 互動的通用模板函式。

    Args:
        dict_input (dict): 要傳遞給 LLM 的輸入資料字典。
        task (str): 當前任務的名稱，用於載入對應的系統提示。
        outputFormatRegex (str, optional): 用於從 LLM 回應中提取內容的正規表示式。
                                           預設為空。
        display (bool, optional): 是否顯示發送給 LLM 的訊息。預設為 False。

    Returns:
        str or list: 如果提供了正規表示式，則返回提取的內容；否則返回完整的 LLM 回應。
    """
    print(f"[+] Start {task}.")
    
    # 組合系統提示和使用者輸入
    messages = [
        {"role": "system", "content": textLoader(txtName=f"SystemPrompt_{task}")},
        {"role": "user", "content": "<text>" + str(dict_input) + "</text>"}
    ]
    if display:
        print(messages)
    
    output = Llmrequest(messages)
    print(f"[-] Finish {task}.")

    # 如果需要，使用正規表示式解析輸出
    if outputFormatRegex:
        outputPattern = re.compile(outputFormatRegex, re.DOTALL)
        outputContent = outputPattern.findall(output)
        return outputContent[0] if outputContent else ""
    
    return output

# --- Sigma 規則與查詢生成流程 ---

def workflow_sigmaRule(dict_input: dict):
    """
    完整的 Sigma 規則生成工作流程。
    1. 產生初始 Sigma 規則。
    2. 優化規則。
    3. 組合規則。
    4. 產生 Elasticsearch 查詢。
    5. 儲存結果。

    Args:
        dict_input (dict): 包含攻擊資訊的輸入字典。

    Returns:
        str: 生成的 Elasticsearch 查詢。
    """
    # 步驟 1: 生成初始 Sigma 規則
    sigmarule = Llminteraction(dict_input=dict_input, task="sigmaRuleGeneration")
    
    # 步驟 2: 優化 Sigma 規則
    sigmarule_refined = Llminteraction(
        dict_input={"unrefined_rule": sigmarule, "criteria": "detect by keywords but others"},
        task="sigmaruleRefiner"
    )
    
    # 步驟 3: 組合初始規則與優化後的規則
    result = Llminteraction(
        dict_input={"basic sigma rule": sigmarule, "refined detection rule": sigmarule_refined},
        task="sigmaCombination"
    )
    
    # 產生隨機檔名並儲存 Sigma 規則
    filename = generate_secure_random_string(10)
    with open(os.path.join(os.getcwd(), "response", f"{filename}_sigmarule.yaml"), "w", encoding=file_encoding) as f:
        f.write(result)
        
    # 步驟 4: 產生 Elasticsearch 查詢
    query = Llminteraction(dict_input={"sigma_rule": result}, task="queryGeneration")
    
    # 儲存查詢
    with open(os.path.join(os.getcwd(), "response", f"{filename}_query.yaml"), "w", encoding=file_encoding) as f:
        f.write(query)
        
    return query

# --- Elasticsearch 搜尋 ---

def elsticSearch_search(query, index: str = "sagac1"):
    """
    對 Elasticsearch 執行搜尋。

    Args:
        query (dict): Elasticsearch 查詢物件。
        index (str, optional): 目標索引。預設為 "sagac1"。

    Returns:
        str: 搜尋結果。
    """
    ELASTIC_PASSWORD = os.environ.get('ELASTIC_PASSWORD', '') # 從環境變數讀取密碼
    cmd = [
        "curl", "-u", f"elastic:{ELASTIC_PASSWORD}", "-X", "GET",
        f"https://localhost:9200/{index}/_search?pretty",
        "-H", "Content-Type: application/json", "-d", json.dumps(query),
        "--insecure"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout

# --- 主要工作流程與命令列介面 ---

# ... (workflow1 to workflow10 and WORKFLOWS mapping) ...

def main():
    """
    主函式，用於解析命令列參數並執行對應的工作流程。
    """
    parser = argparse.ArgumentParser(
        description='CLI to execute predefined workflows (1-10)'
    )
    parser.add_argument(
        'workflow',
        choices=WORKFLOWS.keys(),
        help='Workflow number to execute (1-10)'
    )
    args = parser.parse_args()

    # 執行選擇的工作流程
    func = WORKFLOWS[args.workflow]
    func()

if __name__ == '__main__':
    # 如果沒有提供參數，顯示幫助訊息
    if len(sys.argv) == 1:
        print("Please specify a workflow number (1-10).\n")
        parser = argparse.ArgumentParser(
            description='CLI to execute predefined workflows (1-10)'
        )
        parser.print_help()
        sys.exit(1)

    main()