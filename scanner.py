import FinanceDataReader as fdr
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

# 1. 구글 스프레드시트 연동 설정
def save_to_google_sheet(df):
    # 깃허브 Secret에 저장된 JSON 키를 불러옵니다.
    json_key = json.loads(os.environ['GSPREAD_KEY'])
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(json_key, scope)
    client = gspread.authorize(creds)
    
    # 'Quant_Scanner_Result'라는 이름의 시트를 엽니다.
    sheet = client.open('Quant_Scanner_Result').sheet1
    
    # 기존 데이터 삭제 후 새 데이터 업데이트
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())

# 2. 퀀트 필터링 로직
def get_quant_screening():
    # 유니버스 구성 (코스피/코스닥 전 종목)
    df_krx = fdr.StockListing('KRX')
    universe = df_krx.sort_values(by='Marcap', ascending=False).head(20) # 테스트를 위해 상위 20개만
    
    results = []
    for i, row in universe.iterrows():
        try:
            df = fdr.DataReader(row['Code'], '2026-01-01')
            df['MA5'] = df['Close'].rolling(window=5).mean()
            df['MA20'] = df['Close'].rolling(window=20).mean()
            
            # [필터 조건] 5일선이 20일선 위에 있는 종목 (정배열)
            if df['MA5'].iloc[-1] > df['MA20'].iloc[-1]:
                results.append({'Code': row['Code'], 'Name': row['Name'], 'Price': df['Close'].iloc[-1]})
        except:
            continue
    return pd.DataFrame(results)

# 3. 메인 실행
if __name__ == "__main__":
    df_result = get_quant_screening()
    if not df_result.empty:
        save_to_google_sheet(df_result)
        print("성공적으로 스프레드시트에 저장되었습니다.")
    else:
        print("조건에 맞는 종목이 없습니다.")