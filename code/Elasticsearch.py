import subprocess
import json
import os

def queryTranslator():
    """
    將指定的 Sigma 規則檔案轉換為 Elasticsearch ESQL 查詢。
    使用 'sigma' command-line tool 進行轉換。

    Returns:
        str: 轉換後的 ESQL 查詢字串。
    """
    # 定義 Sigma 規則檔案的路徑
    sigma_file = os.path.join(os.getcwd(), "response", "UCoXqAi7TN_sigmarule")
    # 建立並執行 sigma 轉換命令
    cmd = ["sigma", "convert", "-t", "esql", "--without-pipeline", sigma_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    query = result.stdout
    return query

def elsticSearch_search(query, index="sagac1"):
    """
    使用 cURL 命令對指定的 Elasticsearch 索引執行搜尋。

    Args:
        query (str): 要執行的 Elasticsearch 查詢 (JSON 格式字串)。
        index (str, optional): 目標 Elasticsearch 索引。預設為 "sagac1"。

    Returns:
        str: cURL 命令的標準輸出，其中包含搜尋結果。
    """
    # 建立並執行 cURL 命令以搜尋 Elasticsearch
    cmd = ["curl", "-u", "elastic:1eqJXNpXocyu9EHg1*hO", "-X", "GET", f"https://localhost:9200/{index}/_search?pretty", "-H", "Content-Type: application/json", "-d", query, "--insecure"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout

# 範例查詢
query = {
    "query": {
        "match": {
            "user.name": "root"
        }
    }
}

if __name__ == "__main__":
    # 主要執行區塊，用於測試
    index = "sagac1"  # 您的索引名稱

    # 將查詢物件轉換為 JSON 字串
    query_json = json.dumps(query)
    
    # 如果需要，可以取消註解以下行來使用 queryTranslator
    # query_json = f'''{json.dumps({"query": queryTranslator()})}'''
    
    print("執行的查詢:")
    print(query_json)
    print("\n搜尋結果:")
    print(elsticSearch_search(query_json, index))
