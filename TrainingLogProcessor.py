from oauth2client.service_account import ServiceAccountCredentials
import gspread

import pandas as pd
import datetime as dt


class TrainingLogProcessor:
    def __init__(self, creds_json):
        # self.df = self.__load_from_gss()  
        self.df = self.__read_spreadsheet(sheet_name="TrainingLog",
                                          crendentitial=creds_json)

    def __load_from_gss(crendentitial, sheet_name="TrainingLog"):
        scope = ["https://spreadsheets.google.com/feeds",
                 "https://www.googleapis.com/auth/drive"]
        # 認証情報を使ってクライアントを作成
        creds = ServiceAccountCredentials.from_json_keyfile_dict(crendentitial, scope)

        client = gspread.authorize(creds)

        # スプレッドシートを開く (スプレッドシートの名前を指定)
        print("a")
        spreadsheet = client.open(sheet_name)
        print("a")

        # シートを選択
        sheet = spreadsheet.sheet1  # 一番目のシートを選択する場合

        # データを読み込む
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        df["日付"] = pd.to_datetime(df["日付"])

        # training_menus = ["バックスクワット", "ベンチプレス", "ダンベルベンチプレス", "コンベンショナルデットリフト"]
        # df = df[df["種目"].isin(training_menus)]
        df["Volume"] = df["重量[kg]"] * df["回数[回]"]

        return df

    def __read_spreadsheet(self, sheet_name:str, 
                           crendential_path:str):
        # スコープの設定
        scope = ["https://spreadsheets.google.com/feeds", 
                 "https://www.googleapis.com/auth/drive"]
        # 認証情報を使ってクライアントを作成
        creds = ServiceAccountCredentials.from_json_keyfile_name(crendential_path, scope)
        client = gspread.authorize(creds)

        # スプレッドシートを開く (スプレッドシートの名前を指定)
        spreadsheet = client.open(sheet_name)

        # シートを選択
        sheet = spreadsheet.sheet1  # 一番目のシートを選択する場合

        # データを読み込む
        data = sheet.get_all_records()
        df = pd.DataFrame(data)
        df["日付"] = pd.to_datetime(df["日付"])
        df["Volume"] = df["重量[kg]"] * df["回数[回]"]

        return df

    def get_latest_volume(self):
        # 各種目の最終日の記録のみ表示する
        # 前回の重量を取得
        total_volume_df = self.df.groupby(["日付", "種目"])["Volume"].sum().reset_index()
        total_volume_df = total_volume_df.rename(columns={"Volume" : "Total Volume"})
        total_volume_df['Pre Volume'] = total_volume_df.groupby('種目')['Total Volume'].shift(1)

        # 各種目の最終日のデータを抽出
        latest_df = total_volume_df.groupby('種目').tail(1)
        latest_df["Delta"] = latest_df["Total Volume"] - latest_df["Pre Volume"]

        latest_df = latest_df.fillna(0)
        latest_df

        return latest_df

    def get_total_volume(self):
        total_volume_df = self.df.groupby(["日付", "種目"])["Volume"].sum().reset_index()
        total_volume_df = total_volume_df.pivot(index="日付",
                                                columns="種目",
                                                values="Volume").reset_index()
        return total_volume_df

    def get_contribution_map(self):
        # 日付のためのdfを作成する
        year = dt.datetime.today().strftime("%Y")
        date_df = pd.DataFrame()

        date_df["date"] = pd.date_range(f'{year}-01-01', f'{year}-12-31')
        date_df["date"] = date_df["date"].dt.floor('D')

        daily_volume_df = self.df.groupby("日付")["Volume"].sum().reset_index()
        daily_volume_df = daily_volume_df.rename(
            columns={"Volume" : "Total Volume"}
        )
        contribution_df = pd.merge(date_df, daily_volume_df, left_on="date",
                                   right_on="日付", how="left")
        contribution_df = contribution_df.fillna(0)
        contribution_df.set_index('date', inplace=True)
        # add data
        contribution_df['weekday'] = pd.to_datetime(contribution_df.index).strftime('%w')
        contribution_df['week'] = pd.to_datetime(contribution_df.index).strftime('%U')

        contribution_map = contribution_df.pivot(index='weekday',
                                                 columns='week',
                                                 values='Total Volume').reset_index()
        contribution_map.drop(['weekday'], axis=1, inplace=True)
        contribution_map.fillna(0, inplace=True)

        return contribution_map
