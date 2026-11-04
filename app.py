"""Antarmuka Streamlit. Jalankan: python -m streamlit run app.py."""

from datetime import datetime
from pathlib import Path
import sqlite3
from zoneinfo import ZoneInfo

import altair as alt
import pandas as pd
import streamlit as st

import finance as fin

ROOT = Path(__file__).parent
TODAY = datetime.now(ZoneInfo("Asia/Tokyo")).date()
GREEN, ORANGE = "#17644D", "#B45A31"
# Label Jepang untuk nilai tersimpan; skema database yang sudah ada tetap dipakai.
STORED_LABELS = {
    "Pemasukan": "収入", "Pengeluaran": "支出", "Tempat tinggal": "住居費",
    "Makanan": "食費", "Transportasi": "交通費", "Pendidikan": "教育費",
    "Hiburan": "娯楽費", "Lainnya": "その他", "Kerja paruh waktu": "アルバイト",
    "Beasiswa": "奨学金", "Kiriman keluarga": "仕送り",
}
DEMO_NOTES = {
    "Gaji arubaito": "アルバイト代", "Beasiswa bulanan": "毎月の奨学金",
    "Dukungan keluarga": "家族からの仕送り", "Sewa tempat tinggal": "家賃",
    "Belanja dan makan": "食料品・外食", "Kartu transportasi": "交通系ICカード",
    "Buku dan alat kuliah": "教科書・学用品", "Waktu bersama teman": "友人とのお出かけ",
    "Kebutuhan lain": "その他の日用品",
}


def label(value):
    return STORED_LABELS.get(value, value)


def yen(value):
    return f"{'−' if value < 0 else ''}¥{abs(int(value)):,}"


def month_label(value):
    return f"{value[:4]}年{int(value[5:])}月"


def notice(message):
    st.session_state["notice"] = message
    st.rerun()


def transaction_form(path, row=None):
    editing = row is not None
    prefix = f"edit_{int(row['id'])}" if editing else "new"
    kind = st.selectbox("収支区分", list(fin.CATEGORIES),
                        index=list(fin.CATEGORIES).index(row["kind"]) if editing else 0,
                        format_func=label, key=f"{prefix}_kind")
    categories = fin.CATEGORIES[kind]
    with st.form(prefix, clear_on_submit=not editing):
        left, right = st.columns(2)
        day = left.date_input("日付", value=datetime.fromisoformat(row["date"]).date() if editing else TODAY,
                              max_value=TODAY, format="YYYY/MM/DD")
        category = right.selectbox("カテゴリー", categories,
                                   index=categories.index(row["category"]) if editing and row["category"] in categories else 0,
                                   format_func=label)
        amount = st.number_input("金額（円）", min_value=1, max_value=fin.MAX_AMOUNT,
                                 value=int(row["amount"]) if editing else 1000, step=100)
        note = st.text_input("メモ（任意）", value=row["note"] if editing else "", max_chars=120)
        if st.form_submit_button("変更を保存" if editing else "記録を追加", type="primary", width="stretch"):
            fin.save_transaction(path, day, kind, category, amount, note, int(row["id"]) if editing else None)
            notice("変更を保存しました。" if editing else "記録を追加しました。")


def japanese_table(frame):
    return frame.assign(kind=frame["kind"].map(label), category=frame["category"].map(label)).rename(
        columns={"date": "日付", "kind": "区分", "category": "カテゴリー", "amount": "金額（円）", "note": "メモ"}
    )[["日付", "区分", "カテゴリー", "メモ", "金額（円）"]]


def display_table(frame):
    st.dataframe(japanese_table(frame), hide_index=True, width="stretch",
                 column_config={"金額（円）": st.column_config.NumberColumn(format="¥ %d")})


def overview(frame, selected, month, path):
    income, expenses, balance = fin.totals(selected)
    budget, goal = fin.get_plan(path, month)
    with st.container(key="summary"):
        for column, heading, value in zip(st.columns(4),
                                        ["収入", "支出", "今月の収支", "黒字率"],
                                        [yen(income), yen(expenses), yen(balance), f"{balance / income:.1%}" if income else "—"]):
            column.metric(heading, value)
    st.caption("今月の収支＝収入−支出。銀行口座の残高や実際の貯蓄額ではありません。")
    left, right = st.columns([1.7, 1], gap="large")
    with left:
        st.subheader("収入・支出の推移")
        st.caption("選択した月までの6か月間")
        periods = pd.period_range(end=month, periods=6, freq="M").astype(str)
        history = frame.assign(month=frame["date"].str[:7]).groupby(["month", "kind"])["amount"].sum()
        chart_data = pd.DataFrame([
            {"月": month_label(period), "区分": label(kind), "金額": int(history.get((period, kind), 0))}
            for period in periods for kind in ["Pemasukan", "Pengeluaran"]
        ])
        chart = alt.Chart(chart_data).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
            x=alt.X("月:N", title=None, sort=[month_label(period) for period in periods], axis=alt.Axis(labelAngle=-30)),
            y=alt.Y("金額:Q", title="金額（円）", axis=alt.Axis(format=",.0f")), xOffset="区分:N",
            color=alt.Color("区分:N", scale=alt.Scale(domain=["収入", "支出"], range=[GREEN, ORANGE]), legend=alt.Legend(orient="bottom", title=None)),
            tooltip=["月", "区分", alt.Tooltip("金額:Q", format=",.0f")],
        ).properties(height=270).configure_axis(labelColor="#52685D", titleColor="#52685D").configure_legend(labelColor="#52685D")
        st.altair_chart(chart, width="stretch")
    with right:
        st.subheader("黒字目標への進捗")
        st.caption("選択した月の目標を確認しましょう")
        st.metric("今月の収支 / 黒字目標", f"{yen(balance)} / {yen(goal)}")
        if goal:
            st.progress(min(max(balance / goal, 0), 1))
            st.write("今月の黒字目標を達成しました。" if balance >= goal else f"目標達成まであと{yen(goal - balance)}です。")
        else:
            st.info("「予算・目標」で黒字目標を設定してください。")
        st.divider()
        if budget:
            st.write(f"{'予算超過' if expenses > budget else '予算の残り'}：**{yen(abs(budget - expenses))}**")
            st.caption(f"予算{yen(budget)}のうち{expenses / budget:.0%}を使用しています。")
        else:
            st.caption("支出予算がまだ設定されていません。")
    left, right = st.columns([1, 1.7], gap="large")
    with left:
        st.subheader("カテゴリー別の支出")
        spending = selected[selected["kind"] == "Pengeluaran"].groupby("category", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
        spending["category"] = spending["category"].map(label)
        if spending.empty:
            st.info("この月の支出はまだありません。")
        else:
            chart = alt.Chart(spending).mark_bar(cornerRadiusEnd=4, color=GREEN).encode(
                y=alt.Y("category:N", title=None, sort="-x"), x=alt.X("amount:Q", title="金額（円）"),
                tooltip=[alt.Tooltip("category:N", title="カテゴリー"), alt.Tooltip("amount:Q", title="金額（円）", format=",.0f")],
            ).properties(height=230).configure_axis(labelColor="#52685D", titleColor="#52685D")
            st.altair_chart(chart, width="stretch")
            biggest = spending.iloc[0]
            st.caption(f"{biggest['category']}が今月の支出の{biggest['amount'] / expenses:.0%}を占めています。")
    with right:
        st.subheader("最近の記録")
        if selected.empty:
            st.info("「収支記録」から最初の記録を追加しましょう。")
        else:
            display_table(selected.head(5))
        if expenses > income:
            st.warning(f"支出が収入を{yen(expenses - income)}上回っています。見直せる支出を確認しましょう。")
        elif income:
            st.success(f"今月の黒字は{yen(balance)}です。優先順位を考えて計画的に使いましょう。")
        st.caption("表示内容は登録済みの記録に基づきます。将来予測や専門的な金融助言ではありません。")


def transaction_page(selected, path, month):
    st.subheader("収支の記録")
    history, add, edit = st.tabs(["履歴", "追加", "編集・削除"])
    with history:
        left, right = st.columns(2)
        kind = left.selectbox("収支で絞り込む", ["すべて", *fin.CATEGORIES], format_func=label)
        query = right.text_input("メモ・カテゴリーを検索", max_chars=120)
        filtered = selected if kind == "すべて" else selected[selected["kind"] == kind]
        if query:
            filtered = filtered[filtered["note"].str.contains(query, case=False, regex=False) | filtered["category"].map(label).str.contains(query, case=False, regex=False)]
        st.caption(f"{month_label(month)} · {len(filtered)}件")
        if filtered.empty:
            st.info("該当する記録がありません。条件を変更するか、記録を追加してください。")
        else:
            display_table(filtered)
            exported = japanese_table(filtered)
            for column in ["メモ", "カテゴリー"]:
                exported[column] = exported[column].map(lambda value: "'" + value if value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else value)
            st.download_button("CSVをダウンロード", exported.to_csv(index=False).encode("utf-8-sig"), file_name=f"収支記録-{month}.csv", mime="text/csv")
    with add:
        st.caption("記録は日付に対応する月に保存されます。別の月を見るには表示月を変更してください。")
        transaction_form(path)
    with edit:
        if selected.empty:
            st.info("この月の記録はまだありません。")
        else:
            records = {int(row["id"]): row for _, row in selected.iterrows()}
            identity = st.selectbox("編集する記録", list(records), format_func=lambda value: f"#{value} · {records[value]['date']} · {label(records[value]['category'])} · {yen(records[value]['amount'])}")
            transaction_form(path, records[identity])
            with st.expander("この記録を削除"):
                confirmed = st.checkbox("この記録を完全に削除することを確認しました", key=f"delete_{identity}")
                if st.button("完全に削除", disabled=not confirmed):
                    fin.delete_transaction(path, identity)
                    notice("記録を削除しました。")


def budget_page(selected, path, month):
    budget, goal = fin.get_plan(path, month)
    income, expenses, balance = fin.totals(selected)
    left, right = st.columns([1, 1.4], gap="large")
    with left:
        st.subheader("今月の予算と目標")
        with st.form("plan"):
            new_budget = st.number_input("月間の支出予算（円）", min_value=0, max_value=fin.MAX_AMOUNT, value=budget, step=1000)
            new_goal = st.number_input("月間の黒字目標（円）", min_value=0, max_value=fin.MAX_AMOUNT, value=goal, step=1000)
            st.caption("0は未設定です。黒字＝収入−支出であり、実際の貯蓄残高ではありません。")
            if st.form_submit_button("予算・目標を保存", type="primary"):
                fin.save_plan(path, month, new_budget, new_goal)
                notice("予算と目標を保存しました。")
    with right:
        st.subheader("予算と目標の達成状況")
        st.metric("支出 / 予算", f"{yen(expenses)} / {yen(budget)}")
        if budget:
            st.progress(min(expenses / budget, 1))
            if expenses > budget:
                st.warning(f"予算を{yen(expenses - budget)}超過しています。")
            else:
                st.write(f"予算の残りは **{yen(budget - expenses)}** です。")
        else:
            st.info("支出予算を設定すると進捗が表示されます。")
        st.divider()
        st.metric("今月の収支 / 黒字目標", f"{yen(balance)} / {yen(goal)}")
        if goal:
            st.progress(min(max(balance / goal, 0), 1))
        if income and budget and budget + goal > income:
            st.info("予算をすべて使うと、現在の収入では黒字目標に届きません。")


def main():
    st.set_page_config(page_title="学生の家計管理", page_icon=":material/account_balance_wallet:", layout="wide")
    st.markdown(f"<style>{(ROOT / 'style.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    with st.sidebar:
        st.title("学生の家計管理")
        st.caption("小さな習慣から、未来のゆとりへ。")
        mode = st.radio("データの種類", ["デモデータ", "自分のデータ"], key="data_mode")
        page = st.radio("メニュー", ["ダッシュボード", "収支記録", "予算・目標"], label_visibility="collapsed")
        st.divider()
        st.caption("通貨：日本円（JPY）\n\nデータはこのパソコンに保存されます。")
        if mode == "デモデータ":
            st.info("発表用のサンプルデータです。デモの変更は自分のデータに影響しません。")
        else:
            st.caption("保存データは暗号化されていません。ご自身のWindowsアカウントでご利用ください。")
    path = ROOT / "data" / "private" / ("demo.sqlite3" if mode == "デモデータ" else "finance.sqlite3")
    fin.initialize(path)
    if mode == "デモデータ":
        fin.seed_demo(path, TODAY)
    frame = fin.transactions(path)
    if mode == "デモデータ":
        frame["note"] = frame["note"].replace(DEMO_NOTES)
    current = TODAY.strftime("%Y-%m")
    periods = sorted(set(pd.period_range(end=current, periods=24, freq="M").astype(str)) | set(frame["date"].str[:7]), reverse=True)
    title, period = st.columns([3, 1])
    with title:
        st.title({"ダッシュボード": "お金の流れを、もっと見やすく。", "収支記録": "日々の収支を、ていねいに。", "予算・目標": "目標に向けて、ゆとりある計画を。"}[page])
        st.write("毎日の記録から、これからの暮らしを整えましょう。")
    with period:
        month = st.selectbox("表示月", periods, format_func=month_label, index=periods.index(current), key=f"month_{mode}")
    st.caption(f"{month_label(month)} · {'サンプルデータ' if mode == 'デモデータ' else '個人データ'} · {TODAY.strftime('%Y年%m月%d日')} （日本時間）")
    if "notice" in st.session_state:
        st.success(st.session_state.pop("notice"))
    selected = fin.month_data(frame, month)
    if page == "ダッシュボード":
        overview(frame, selected, month, path)
    elif page == "収支記録":
        transaction_page(selected, path, month)
    else:
        budget_page(selected, path, month)
    st.divider()
    st.caption("学生の家計管理 · Python・Streamlitで開発 · データはパソコン内に保存されます。")


if __name__ == "__main__":
    try:
        main()
    except (sqlite3.Error, OSError, ValueError) as error:
        st.error(f"処理できませんでした：{error} 入力内容と保存先へのアクセス権を確認し、再読み込みしてください。")
        st.stop()
