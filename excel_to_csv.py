#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Excel分割変換ツール for Utayomi

複数タブのExcelファイルを、短歌選評システム「Utayomi」用のCSVファイルに変換します。
各タブは個別のCSVファイルとして保存され、ファイル名にはタブ名が使用されます。

使用方法:
    python excel_to_utayomi_csv.py input.xlsx output_directory

作成者: ef_utakata
"""

import os
import argparse
import pandas as pd
import re


def sanitize_filename(name):
    """
    タブ名をファイル名として使用できるように安全な形式に変換する
    
    Args:
        name (str): タブ名
    
    Returns:
        str: 安全なファイル名
    """
    # ファイル名に使えない文字を削除または置換
    sanitized = re.sub(r'[\\/*?:"<>|]', "", name)
    # 空白はアンダースコアに変換
    sanitized = sanitized.replace(' ', '_')
    return sanitized


def detect_content_column(df):
    """
    短歌内容を含む可能性が高い列を検出する
    
    Args:
        df (DataFrame): 元のDataFrame
    
    Returns:
        str: 内容を含む可能性が高い列名、見つからない場合はNone
    """
    # 列名のヒント（優先順位順）
    content_hints = ['短歌', '内容', '本文', 'うた', '歌', 'テキスト', 'text', 'content']
    
    # 完全一致の列名をチェック
    for col in df.columns:
        if col in ['Content']:
            return col
    
    # ヒントを含む列名をチェック
    for hint in content_hints:
        for col in df.columns:
            if isinstance(col, str) and hint in col.lower():
                return col
    
    # 見つからなかった場合は最初の列を返す（ユーザー確認が必要）
    if len(df.columns) > 0:
        return df.columns[0]
    
    return None


def detect_author_column(df):
    """
    作者名を含む可能性が高い列を検出する
    
    Args:
        df (DataFrame): 元のDataFrame
    
    Returns:
        str: 作者名を含む可能性が高い列名、見つからない場合はNone
    """
    # 列名のヒント（優先順位順）
    author_hints = ['作者', '筆者', '著者', '名前', '氏名', 'author', 'name']
    
    # 完全一致の列名をチェック
    for col in df.columns:
        if col in ['Author']:
            return col
    
    # ヒントを含む列名をチェック
    for hint in author_hints:
        for col in df.columns:
            if isinstance(col, str) and hint in col.lower():
                return col
    
    # 見つからなかった場合はNoneを返す
    return None


def detect_comment_column(df):
    """
    作者コメントを含む可能性が高い列を検出する
    
    Args:
        df (DataFrame): 元のDataFrame
    
    Returns:
        str: コメントを含む可能性が高い列名、見つからない場合はNone
    """
    # 列名のヒント（優先順位順）
    comment_hints = ['コメント', '解説', '評', '備考', 'comment', 'note']
    
    # 完全一致の列名をチェック
    for col in df.columns:
        if col in ['Author_comment']:
            return col
    
    # ヒントを含む列名をチェック
    for hint in comment_hints:
        for col in df.columns:
            if isinstance(col, str) and hint in col.lower():
                return col
    
    # 見つからなかった場合はNoneを返す
    return None


def convert_excel_to_utayomi_csv(input_excel, output_dir):
    """
    Excelファイルの各タブを短歌選評システム用のCSVファイルに変換する
    
    Args:
        input_excel (str): 入力Excelファイルのパス
        output_dir (str): 出力先ディレクトリ
    
    Returns:
        list: 生成されたCSVファイルのパスリスト
    """
    # 出力ディレクトリが存在しない場合は作成
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Excelファイルを読み込む
    xl = pd.ExcelFile(input_excel)
    
    output_files = []
    
    # 各シートを処理
    for sheet_name in xl.sheet_names:
        # シートを読み込む
        df = xl.parse(sheet_name)
        
        # 空の行を削除
        df = df.dropna(how='all')
        
        # 列の検出
        content_col = detect_content_column(df)
        author_col = detect_author_column(df)
        comment_col = detect_comment_column(df)
        
        print(f"\n--- シート「{sheet_name}」の列マッピング ---")
        print(f"Content列: {content_col}")
        print(f"Author列: {author_col}")
        print(f"Author_comment列: {comment_col}")
        
        # 必要な列だけを抽出して新しいDataFrameを作成
        utayomi_df = pd.DataFrame()
        
        # No列を生成（1から始まる連番）
        utayomi_df['No'] = range(1, len(df) + 1)
        
        # Content列の設定（必須）
        if content_col:
            utayomi_df['Content'] = df[content_col].fillna("").astype(str)
        else:
            print(f"警告: シート「{sheet_name}」から短歌内容を含む列を特定できませんでした")
            utayomi_df['Content'] = ""
        
        # Author列の設定
        if author_col:
            utayomi_df['Author'] = df[author_col].fillna("").astype(str)
        else:
            utayomi_df['Author'] = ""
        
        # Author_comment列の設定
        if comment_col:
            utayomi_df['Author_comment'] = df[comment_col].fillna("").astype(str)
        else:
            utayomi_df['Author_comment'] = ""
        
        # 改行コードを削除
        utayomi_df['Content'] = utayomi_df['Content'].str.replace('\r', '')
        utayomi_df['Content'] = utayomi_df['Content'].str.replace('\n', '')
        utayomi_df['Author_comment'] = utayomi_df['Author_comment'].str.replace('\r', '')
        utayomi_df['Author_comment'] = utayomi_df['Author_comment'].str.replace('\n', '')
        
        # ファイル名の作成（タブ名を使用、安全な形式に変換）
        safe_name = sanitize_filename(sheet_name)
        output_csv = os.path.join(output_dir, f"{safe_name}.csv")
        
        # CSVファイルとして保存
        utayomi_df.to_csv(output_csv, encoding='utf-8', index=False)
        output_files.append(output_csv)
        
        print(f"変換完了: {output_csv} ({len(utayomi_df)}行)")
    
    return output_files


def main():
    """
    メイン関数
    """
    parser = argparse.ArgumentParser(description="Excelファイルを短歌選評システム用のCSVファイルに変換します")
    parser.add_argument('input', help='入力Excelファイルのパス')
    parser.add_argument('output', help='出力先ディレクトリのパス')
    parser.add_argument('--encoding', default='utf-8', help='CSVファイルのエンコーディング（デフォルト: utf-8）')
    
    args = parser.parse_args()
    
    print(f"Excelファイル「{args.input}」を変換しています...")
    
    # Excelファイルの存在確認
    if not os.path.exists(args.input):
        print(f"エラー: 入力ファイル「{args.input}」が見つかりません")
        return
    
    try:
        output_files = convert_excel_to_utayomi_csv(args.input, args.output)
        
        print(f"\n変換が完了しました！")
        print(f"合計 {len(output_files)} 個のCSVファイルが以下の場所に生成されました:")
        print(f"出力ディレクトリ: {os.path.abspath(args.output)}")
        
        # 出力ファイル一覧と行数を表示
        for f in output_files:
            rows = len(pd.read_csv(f))
            print(f"- {os.path.basename(f)} ({rows}行)")
        
        print("\n以下のコマンドで短歌選評を実行できます:")
        print(f"python selection.py {os.path.join(args.output, '[ファイル名].csv')} [出力先] -i [モデル識別子]")
        
    except Exception as e:
        print(f"エラー: 変換処理中に問題が発生しました: {e}")


if __name__ == "__main__":
    main()
