import os
import argparse

def split_file_by_size(input_path: str, output_prefix: str, chunk_size_mb: int = 500):
    """
    將指定的輸入檔案按大小切割成多個較小的檔案。

    Args:
        input_path (str): 要切割的來源檔案路徑。
        output_prefix (str): 輸出檔案的前綴名稱 (包含副檔名)。
                             例如: "chunk.jsonl"。
        chunk_size_mb (int, optional): 每個切割檔案的大小上限 (單位 MB)。
                                       預設為 500MB。
    """
    chunk_size = chunk_size_mb * 1024 * 1024  # 將 MB 轉換為 bytes
    base_name, ext = os.path.splitext(output_prefix)

    with open(input_path, 'rb') as infile:
        file_index = 0
        current_size = 0
        outfile = None

        for line in infile:
            # 如果尚未開啟輸出檔，或目前行加入後會超過大小限制，則建立新檔案
            if outfile is None or current_size + len(line) > chunk_size:
                if outfile:
                    outfile.close()
                # 格式化輸出檔名，例如: chunk_00.jsonl, chunk_01.jsonl
                out_name = f"{base_name}_{file_index:02d}{ext}"
                outfile = open(out_name, 'wb')
                print(f"[+] 正在建立 {out_name}")
                file_index += 1
                current_size = 0

            outfile.write(line)
            current_size += len(line)

        if outfile:
            outfile.close()
    print("[*] 檔案切割完成。")

if __name__ == "__main__":
    # 命令列參數解析
    parser = argparse.ArgumentParser(
        description="將大型檔案切割成多個小於指定大小的檔案。"
    )
    parser.add_argument("input_file", help="要切割的輸入檔案路徑。")
    parser.add_argument("output_prefix",
                        help="輸出檔案的前綴名稱 (含副檔名)，例如: chunk.jsonl。")
    parser.add_argument("--size", type=int, default=500,
                        help="每個檔案的大小上限 (MB)，預設為 500MB。")
    args = parser.parse_args()

    # 執行檔案切割
    split_file_by_size(args.input_file, args.output_prefix, args.size)