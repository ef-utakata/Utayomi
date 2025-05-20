"""
Common CLI utilities for Utayomi scripts.
"""
import argparse
import datetime
import yaml
import subprocess
import colorama
from colorama import Fore

def get_common_parser(description: str, default_config: str) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('input', help='入力短歌一覧のパス(csv形式で入力)')
    parser.add_argument('output', help='出力先ディレクトリのパス(csv形式で出力)')
    parser.add_argument('-c', '--config', default=default_config,
                        help='利用モデルの入力設定ファイル(yaml形式)')
    parser.add_argument('-i', '--identifier',
                        help='入力設定ファイル内の設定識別子(--listで一覧を確認可能)')
    parser.add_argument('-t', '--theme',
                        help='お題(入力がない場合自由詠)', default=0)
    parser.add_argument('--list', action='store_true',
                        help='-cで指定した入力設定ファイルの一覧を表示')
    parser.add_argument('-V', '--version', action='store_true',
                        help='バージョン情報の表示')
    return parser

def handle_version(args: argparse.Namespace, ver: str) -> None:
    if args.version:
        print(ver)
        exit()

def handle_list(args: argparse.Namespace) -> None:
    if args.list:
        print("[MESSAGE]: 現在、以下のモデルが利用可能です。-i に各モデルの識別子を入力して切り替え可能です。")
        with open(args.config, 'r') as yml_file:
            conf = yaml.safe_load(yml_file)
            for key in conf.keys():
                print(key)
        print("\n[MESSAGE]: 現在、以下のモデルがキャッシュされています。キャッシュされていないモデルは初回実行時に自動でダウンロードされます。")
        subprocess.run('huggingface-cli scan-cache', shell=True)
        subprocess.run('find ./models -name "*.gguf"', shell=True)
        exit()

def load_config(config_path: str, identifier: str) -> dict:
    with open(config_path, 'r') as yml_file:
        conf = yaml.safe_load(yml_file)
    if identifier not in conf:
        print(Fore.RED + f"[ERROR]: identifier [{identifier}] は入力設定ファイルに登録されていません。"
                        + " --listで出力される一覧と-i で入力した識別子を確認してください。\n"
                        + Fore.RESET)
        exit()
    print(Fore.YELLOW + f"[MESSAGE]:入力設定ファイルを読み込んでいます...\n\tmodel: {identifier}"
          + Fore.RESET)
    for elem in conf[identifier]:
        print(Fore.YELLOW + f"\t{elem}:{conf[identifier][elem]}" + Fore.RESET)
    return conf