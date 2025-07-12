"""
連作データ処理モジュール

連作CSVファイルの読み込み、分離、検出処理を担当
"""

import pandas as pd
import re
from typing import List, Dict, Tuple


class SeriesProcessor:
    """連作データ処理クラス"""
    
    def __init__(self):
        self.processed_data = None
        self.series_info = {}
    
    def process_series_csv(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        連作CSVデータを処理し、個別首に展開する
        
        Args:
            df: 連作CSVから読み込んだDataFrame
            
        Returns:
            展開された個別首のDataFrame
        """
        expanded_rows = []
        series_count = 0
        
        for idx, row in df.iterrows():
            content = row.get('Content', '')
            eiso_count = row.get('Eiso_count', 1)
            title = row.get('Title', '')
            author = row.get('Author', '')
            
            # 連作データかどうかを判定
            if self._is_series_data(content, eiso_count):
                # 連作の場合：個別首に分離
                poems = self._split_series_content(content)
                
                # 首数の検証
                if len(poems) != eiso_count:
                    print(f"警告: {author}の連作「{title}」の首数が不一致 "
                          f"(期待値:{eiso_count}, 実際:{len(poems)})")
                
                series_count += 1
                series_id = f"series_{series_count:03d}"
                
                # 連作情報を記録
                self.series_info[series_id] = {
                    'author': author,
                    'title': title,
                    'eiso_count': eiso_count,
                    'actual_count': len(poems),
                    'original_row': idx
                }
                
                # 各首を個別行として追加
                for i, poem in enumerate(poems):
                    new_row = row.copy()
                    new_row['Content'] = poem.strip()
                    new_row['Series_ID'] = series_id
                    new_row['Series_Index'] = i + 1
                    new_row['Is_Series'] = True
                    new_row['Series_Title'] = title
                    new_row['Total_Count'] = len(poems)
                    expanded_rows.append(new_row)
            else:
                # 単作の場合：そのまま
                new_row = row.copy()
                new_row['Series_ID'] = None
                new_row['Series_Index'] = 1
                new_row['Is_Series'] = False
                new_row['Series_Title'] = ''
                new_row['Total_Count'] = 1
                expanded_rows.append(new_row)
        
        self.processed_data = pd.DataFrame(expanded_rows)
        print(f"処理完了: {len(self.series_info)}作品の連作と"
              f"{len(expanded_rows) - sum(info['actual_count'] for info in self.series_info.values())}作品の単作を処理")
        
        return self.processed_data
    
    def _is_series_data(self, content: str, eiso_count: int) -> bool:
        """連作データかどうかを判定"""
        if eiso_count <= 1:
            return False
        
        # 改行が含まれているかチェック
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        return len(lines) > 1
    
    def _split_series_content(self, content: str) -> List[str]:
        """連作コンテンツを個別首に分離"""
        # 改行で分割し、空行を除去
        poems = [line.strip() for line in content.split('\n') if line.strip()]
        return poems
    
    def group_by_series(self, df: pd.DataFrame = None) -> Dict[str, pd.DataFrame]:
        """連作ごとにグループ化"""
        if df is None:
            df = self.processed_data
        
        if df is None:
            raise ValueError("処理済みデータがありません。先にprocess_series_csv()を実行してください。")
        
        grouped = {}
        
        # 連作のグループ化
        series_df = df[df['Is_Series'] == True]
        for series_id in series_df['Series_ID'].unique():
            if series_id:
                grouped[series_id] = series_df[series_df['Series_ID'] == series_id].copy()
        
        # 単作のグループ化
        single_df = df[df['Is_Series'] == False]
        for idx, row in single_df.iterrows():
            single_id = f"single_{idx}"
            grouped[single_id] = pd.DataFrame([row])
        
        return grouped
    
    def get_series_summary(self) -> Dict:
        """連作処理の要約情報を取得"""
        if not self.series_info:
            return {
                'total_series': 0,
                'min_eiso_count': 0,
                'max_eiso_count': 0,
                'avg_eiso_count': 0,
                'series_details': {},
                'message': "連作データが処理されていません"
            }
        
        eiso_counts = [info['actual_count'] for info in self.series_info.values()]
        
        return {
            'total_series': len(self.series_info),
            'min_eiso_count': min(eiso_counts) if eiso_counts else 0,
            'max_eiso_count': max(eiso_counts) if eiso_counts else 0,
            'avg_eiso_count': sum(eiso_counts) / len(eiso_counts) if eiso_counts else 0,
            'series_details': self.series_info
        }
    
    def generate_series_prompt_content(self, df: pd.DataFrame = None) -> str:
        """連作用のプロンプトコンテンツを生成"""
        if df is None:
            df = self.processed_data
            
        if df is None:
            raise ValueError("処理済みデータがありません。")
        
        prompt_parts = []
        grouped = self.group_by_series(df)
        
        work_number = 1
        
        for group_id, group_df in grouped.items():
            if group_id.startswith('series_'):
                # 連作の場合
                first_row = group_df.iloc[0]
                author = first_row['Author']
                title = first_row['Series_Title']
                total_count = first_row['Total_Count']
                
                prompt_parts.append(f"{work_number}. 【連作】{title}（作者：{author}、{total_count}首）")
                
                for _, row in group_df.iterrows():
                    prompt_parts.append(f"   {row['Series_Index']}首目：{row['Content']}")
                
            else:
                # 単作の場合
                row = group_df.iloc[0]
                author = row['Author']
                content = row['Content']
                
                prompt_parts.append(f"{work_number}. 【単作】{content}（作者：{author}）")
            
            work_number += 1
            prompt_parts.append("")  # 空行追加
        
        return "\n".join(prompt_parts)


def test_series_processor(csv_path: str):
    """連作処理のテスト関数"""
    print(f"=== 連作処理テスト: {csv_path} ===")
    
    # CSVファイル読み込み
    df = pd.read_csv(csv_path)
    print(f"元データ: {len(df)}行")
    
    # 連作処理
    processor = SeriesProcessor()
    processed_df = processor.process_series_csv(df)
    
    print(f"処理後: {len(processed_df)}首")
    
    # 要約情報出力
    summary = processor.get_series_summary()
    print(f"\n=== 処理要約 ===")
    print(f"連作数: {summary['total_series']}")
    if summary['total_series'] > 0:
        print(f"首数範囲: {summary['min_eiso_count']}首 ～ {summary['max_eiso_count']}首")
        print(f"平均首数: {summary['avg_eiso_count']:.1f}首")
    
    # プロンプト生成テスト
    prompt = processor.generate_series_prompt_content()
    print(f"\n=== 生成プロンプト（先頭500文字） ===")
    print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
    
    return processor, processed_df


if __name__ == "__main__":
    # テスト実行
    import sys
    if len(sys.argv) > 1:
        test_series_processor(sys.argv[1])
    else:
        print("使用法: python series_processor.py <csv_path>")