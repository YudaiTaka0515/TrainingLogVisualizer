from TrainingLogProcessor import TrainingLogProcessor
import streamlit as st
# import plotly.express as px
import plotly.graph_objects as go
import datetime as dt
import pandas as pd



class TrainingLogVisualizer:
    def __init__(self):
        creds_json = st.secrets["gcp_service_account"]

        self.logs = TrainingLogProcessor(creds_json)
        self.target_menu = ['バックスクワット',
                            'ベンチプレス',
                            'コンベンショナルデッドリフト',
                            'ダンベルベンチプレス'
                            ]

        self.total_volume_df = self.logs.get_total_volume()
        self.rows, self.cols = 2, 2

    def visualize_volume(self):
        latest_df = self.logs.get_latest_volume()
        for r in range(0, self.rows):
            columns = st.columns(self.cols)
            for c in range(0, self.cols):
                idx = c + r * self.cols
                if idx >= len(self.target_menu):
                    break
                menu_name = self.target_menu[idx]
                target_rec = latest_df[latest_df["種目"] == menu_name].iloc[0]
                with columns[c]:
                    # カードビューの描画
                    st.metric(label=target_rec["種目"],
                              value=f'{target_rec["Total Volume"]}kg',
                              delta=f'{target_rec["Delta"]}kg')
                    # TotalVolumeの推移を出力
                    self.__plot_target_volume(menu_name=menu_name)

    def __plot_target_volume(self, menu_name):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=self.total_volume_df["日付"],
                                 y=self.total_volume_df[menu_name],
                                 connectgaps=True))

        fig.update_xaxes(rangeslider={"visible" : True})  # X軸に range slider を表示（下図参照）
        fig.update_layout(title=menu_name)  # グラフタイトルを設定
        fig.update_layout(font={"family" : "Meiryo", "size" : 15})
        # fig.u

        displayed_day = 14
        print(dt.datetime.today() - dt.timedelta(displayed_day))
        fig.update_layout(template="seaborn",
                          xaxis_title="Date",
                          yaxis_title="Total Volume[kg]",
                          width=800,
                          height=600,
                          xaxis=dict(
                              range=[dt.datetime.today() -
                                     dt.timedelta(days=displayed_day),
                                     dt.datetime.today()]))
        st.plotly_chart(fig, use_container_width=True)

    def plot_contribution_map(self):
        contribution_map = self.logs.get_contribution_map()

        fig = go.Figure(data=go.Heatmap(
                z=contribution_map.values,  # ヒートマップの値
                xgap=4,  # X方向のグリッド間のギャップ
                ygap=4,  # Y方向のグリッド間のギャップ
                colorscale='Greens', # カラースケール
                showscale=False  # カラーバーを非表示（GitHub風に）
            ))

        # x軸ラベルとして使用する月ごとのマーカー位置（週番号）
        year = dt.datetime.today().strftime("%Y")
        dates = pd.date_range(f'{year}-01-01', f'{year}-12-31')
        weeks = dates.strftime("%U").astype(int) + 1
        month_start_weeks = weeks[dates.is_month_start]
        month_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        # x軸のカスタマイズ
        fig.update_layout(
            width=1200,
            height=200,
            template="seaborn",
            xaxis=dict(
                tickvals=month_start_weeks,  # ラベルを表示するxの値（週番号）
                ticktext=month_labels,  # 表示する月の名前
                tickmode='array',  # ラベルを手動設定
                scaleanchor="y",   # y軸に対してx軸をスケール固定
                showgrid=False,    # グリッド線を非表示
                constrain="domain"  # レイアウト全体に対してx軸のサイズを固定
            ),
            yaxis=dict(
                showgrid=False,    # グリッド線を非表示
                scaleanchor="x",   # x軸に対してy軸をスケール固定
                tickvals=[0, 1, 2, 3, 4, 5, 6],
                ticktext=['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],  # x軸ラベル
                tickmode='array',  # ラベルを手動設定
                constrain="domain"  # レイアウト全体に対してx軸のサイズを固定
            ),
            margin=dict(l=20, r=0, t=0, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    st.markdown("# TrainingLogVisualizer")
    obj = TrainingLogVisualizer()
    st.markdown("## Contribution Map")
    obj.plot_contribution_map()
    st.markdown("## Recent Volume")
    obj.visualize_volume()
