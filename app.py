"""Antarmuka Streamlit. Jalankan: python -m streamlit run app.py."""

from datetime import datetime
from pathlib import Path
import sqlite3
from zoneinfo import ZoneInfo
import altair as alt
import pandas as pd
import streamlit as st
import finance as fin
import accounts
from translations import t

ROOT = Path(__file__).parent
TODAY = datetime.now(ZoneInfo("Asia/Tokyo")).date()
PURPLE, TEAL, BLUE, PINK = "#A05AFF", "#1BCFB4", "#4BCBEB", "#FE9496"
MUTED = "#6B6477"
STORED_LABELS = {
    "Pemasukan": t("収入"),
    "Pengeluaran": t("支出"),
    "Tempat tinggal": t("住居費"),
    "Makanan": t("食費"),
    "Transportasi": t("交通費"),
    "Pendidikan": t("教育費"),
    "Hiburan": t("娯楽費"),
    "Lainnya": t("その他"),
    "Kerja paruh waktu": t("アルバイト"),
    "Beasiswa": t("奨学金"),
    "Kiriman keluarga": t("仕送り"),
}
DEMO_NOTES = {
    "Gaji arubaito": t("アルバイト代"),
    "Beasiswa bulanan": t("毎月の奨学金"),
    "Dukungan keluarga": t("家族からの仕送り"),
    "Sewa tempat tinggal": t("家賃"),
    "Belanja dan makan": t("食料品・外食"),
    "Kartu transportasi": t("交通系ICカード"),
    "Buku dan alat kuliah": t("教科書・学用品"),
    "Waktu bersama teman": t("友人とのお出かけ"),
    "Kebutuhan lain": t("その他の日用品"),
}


def label(value):
    return STORED_LABELS.get(value, value)


def yen(value):
    return f"{('−' if value < 0 else '')}¥{abs(int(value)):,}"


def month_label(value):
    return t("{v0}年{v1}月", v0=value[:4], v1=int(value[5:]))


def notice(message):
    st.session_state["notice"] = message
    st.rerun()


def transaction_form(path, row=None):
    editing = row is not None
    prefix = f"edit_{int(row['id'])}" if editing else "new"
    kind = st.selectbox(
        t("収支区分"),
        list(fin.CATEGORIES),
        index=list(fin.CATEGORIES).index(row["kind"]) if editing else 0,
        format_func=label,
        key=f"{prefix}_kind",
    )
    categories = fin.CATEGORIES[kind]
    with st.form(prefix, clear_on_submit=not editing):
        left, right = st.columns(2)
        day = left.date_input(
            t("日付"),
            value=datetime.fromisoformat(row["date"]).date() if editing else TODAY,
            max_value=TODAY,
            format="YYYY/MM/DD",
        )
        category = right.selectbox(
            t("カテゴリー"),
            categories,
            index=(
                categories.index(row["category"])
                if editing and row["category"] in categories
                else 0
            ),
            format_func=label,
        )
        amount = st.number_input(
            t("金額（円）"),
            min_value=1,
            max_value=fin.MAX_AMOUNT,
            value=int(row["amount"]) if editing else 1000,
            step=100,
        )
        note = st.text_input(
            t("メモ（任意）"), value=row["note"] if editing else "", max_chars=120
        )
        if st.form_submit_button(
            t("変更を保存") if editing else t("記録を追加"),
            type="primary",
            width="stretch",
        ):
            fin.save_transaction(
                path,
                day,
                kind,
                category,
                amount,
                note,
                int(row["id"]) if editing else None,
            )
            notice(t("変更を保存しました。") if editing else t("記録を追加しました。"))


def japanese_table(frame):
    return frame.assign(
        kind=frame["kind"].map(label), category=frame["category"].map(label)
    ).rename(
        columns={
            "date": t("日付"),
            "kind": t("区分"),
            "category": t("カテゴリー"),
            "amount": t("金額（円）"),
            "note": t("メモ"),
        }
    )[
        [t("日付"), t("区分"), t("カテゴリー"), t("メモ"), t("金額（円）")]
    ]


def display_table(frame):
    st.dataframe(
        japanese_table(frame),
        hide_index=True,
        width="stretch",
        column_config={t("金額（円）"): st.column_config.NumberColumn(format="¥ %d")},
    )


def overview(frame, selected, month, path):
    income, expenses, balance = fin.totals(selected)
    budget, goal = fin.get_plan(path, month)
    with st.container(key="summary"):
        for column, key, heading, value in zip(
            st.columns(3),
            ["card_income", "card_expenses", "card_balance"],
            [t("収入"), t("支出"), t("今月の収支")],
            [yen(income), yen(expenses), yen(balance)],
        ):
            with column:
                with st.container(key=key):
                    st.metric(heading, value)
                    st.caption(month_label(month))
    st.caption(t("今月の収支＝収入−支出。銀行口座の残高や実際の貯蓄額ではありません。"))

    left, right = st.columns([1.65, 1], gap="medium")
    with left:
        with st.container(key="trend_panel"):
            st.subheader(t("収入・支出の推移"))
            st.caption(t("選択した月までの6か月間"))
            periods = pd.period_range(end=month, periods=6, freq="M").astype(str)
            history = (
                frame.assign(month=frame["date"].str[:7])
                .groupby(["month", "kind"])["amount"]
                .sum()
            )
            chart_data = pd.DataFrame(
                [
                    {
                        t("月"): month_label(period),
                        t("区分"): label(kind),
                        t("金額"): int(history.get((period, kind), 0)),
                    }
                    for period in periods
                    for kind in ["Pemasukan", "Pengeluaran"]
                ]
            )
            chart = (
                alt.Chart(chart_data)
                .mark_bar(size=14, cornerRadiusTopLeft=2, cornerRadiusTopRight=2)
                .encode(
                    x=alt.X(
                        t("月:N"),
                        title=None,
                        sort=[month_label(period) for period in periods],
                        axis=alt.Axis(labelAngle=-25),
                    ),
                    y=alt.Y(
                        t("金額:Q"),
                        title=t("金額（円）"),
                        axis=alt.Axis(format=",.0f", tickCount=5),
                    ),
                    xOffset=t("区分:N"),
                    color=alt.Color(
                        t("区分:N"),
                        scale=alt.Scale(
                            domain=[t("収入"), t("支出")], range=[PURPLE, PINK]
                        ),
                        legend=alt.Legend(orient="bottom", title=None),
                    ),
                    tooltip=[
                        t("月"),
                        t("区分"),
                        alt.Tooltip(t("金額:Q"), format=",.0f"),
                    ],
                )
                .properties(height=245, background="#FFFFFF")
                .configure_axis(labelColor=MUTED, titleColor=MUTED, gridColor="#F0EDF5")
                .configure_legend(labelColor=MUTED)
                .configure_view(stroke=None)
            )
            st.altair_chart(chart, width="stretch", theme=None)

    spending = (
        selected[selected["kind"] == "Pengeluaran"]
        .groupby("category", as_index=False)["amount"]
        .sum()
        .sort_values("amount", ascending=False)
    )
    spending["category"] = spending["category"].map(label)
    with right:
        with st.container(key="category_panel"):
            st.subheader(t("カテゴリー別の支出"))
            if spending.empty:
                st.info(t("この月の支出はまだありません。"))
            else:
                chart = (
                    alt.Chart(spending)
                    .mark_arc(
                        innerRadius=47, outerRadius=77, padAngle=0.025, cornerRadius=2
                    )
                    .encode(
                        theta=alt.Theta("amount:Q", stack=True),
                        color=alt.Color(
                            "category:N",
                            title=None,
                            sort=list(spending["category"]),
                            scale=alt.Scale(
                                range=[TEAL, BLUE, PINK, "#7430B8", "#9E58FF", "#CDB4FF"]
                            ),
                            legend=alt.Legend(
                                orient="bottom",
                                columns=2,
                                symbolType="circle",
                                labelLimit=150,
                            ),
                        ),
                        order=alt.Order("amount:Q", sort="descending"),
                        tooltip=[
                            alt.Tooltip("category:N", title=t("カテゴリー")),
                            alt.Tooltip(
                                "amount:Q", title=t("金額（円）"), format=",.0f"
                            ),
                        ],
                    )
                    .properties(height=245, background="#FFFFFF")
                    .configure_legend(labelColor=MUTED)
                    .configure_view(stroke=None)
                )
                st.altair_chart(chart, width="stretch", theme=None)
                biggest = spending.iloc[0]
                st.caption(
                    t(
                        "{v0}が今月の支出の{v1:.0%}を占めています。",
                        v0=biggest["category"],
                        v1=biggest["amount"] / expenses,
                    )
                )

    left, right = st.columns([1.65, 1], gap="medium")
    with left:
        with st.container(key="records_panel"):
            st.subheader(t("最近の記録"))
            if selected.empty:
                st.info(t("「収支記録」から最初の記録を追加しましょう。"))
            else:
                display_table(selected.head(5))
            if expenses > income:
                st.warning(
                    t(
                        "支出が収入を{v0}上回っています。見直せる支出を確認しましょう。",
                        v0=yen(expenses - income),
                    )
                )
            elif income:
                st.success(
                    t(
                        "今月の黒字は{v0}です。優先順位を考えて計画的に使いましょう。",
                        v0=yen(balance),
                    )
                )
            st.caption(
                t(
                    "表示内容は登録済みの記録に基づきます。将来予測や専門的な金融助言ではありません。"
                )
            )
    with right:
        with st.container(key="target_panel"):
            st.subheader(t("黒字目標への進捗"))
            st.metric(t("黒字率"), f"{balance / income:.1%}" if income else "—")
            st.metric(t("今月の収支 / 黒字目標"), f"{yen(balance)} / {yen(goal)}")
            if goal:
                st.progress(min(max(balance / goal, 0), 1))
                st.write(
                    t("今月の黒字目標を達成しました。")
                    if balance >= goal
                    else t("目標達成まであと{v0}です。", v0=yen(goal - balance))
                )
            else:
                st.info(t("「予算・目標」で黒字目標を設定してください。"))
            st.divider()
            if budget:
                st.write(
                    f"{(t('予算超過') if expenses > budget else t('予算の残り'))}：**{yen(abs(budget - expenses))}**"
                )
                st.caption(
                    t(
                        "予算{v0}のうち{v1:.0%}を使用しています。",
                        v0=yen(budget),
                        v1=expenses / budget,
                    )
                )
            else:
                st.caption(t("支出予算がまだ設定されていません。"))


def transaction_page(selected, path, month):
    st.subheader(t("収支の記録"))
    history, add, edit = st.tabs([t("履歴"), t("追加"), t("編集・削除")])
    with history:
        left, right = st.columns(2)
        kind = left.selectbox(
            t("収支で絞り込む"), [t("すべて"), *fin.CATEGORIES], format_func=label
        )
        query = right.text_input(t("メモ・カテゴリーを検索"), max_chars=120)
        filtered = (
            selected if kind == t("すべて") else selected[selected["kind"] == kind]
        )
        if query:
            filtered = filtered[
                filtered["note"].str.contains(query, case=False, regex=False)
                | filtered["category"]
                .map(label)
                .str.contains(query, case=False, regex=False)
            ]
        st.caption(t("{v0} · {v1}件", v0=month_label(month), v1=len(filtered)))
        if filtered.empty:
            st.info(
                t(
                    "該当する記録がありません。条件を変更するか、記録を追加してください。"
                )
            )
        else:
            display_table(filtered)
            exported = japanese_table(filtered)
            for column in [t("メモ"), t("カテゴリー")]:
                exported[column] = exported[column].map(
                    lambda value: (
                        "'" + value
                        if value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r"))
                        else value
                    )
                )
            st.download_button(
                t("CSVをダウンロード"),
                exported.to_csv(index=False).encode("utf-8-sig"),
                file_name=t("収支記録-{v0}.csv", v0=month),
                mime="text/csv",
            )
    with add:
        st.caption(
            t(
                "記録は日付に対応する月に保存されます。別の月を見るには表示月を変更してください。"
            )
        )
        transaction_form(path)
    with edit:
        if selected.empty:
            st.info(t("この月の記録はまだありません。"))
        else:
            records = {int(row["id"]): row for _, row in selected.iterrows()}
            identity = st.selectbox(
                t("編集する記録"),
                list(records),
                format_func=lambda value: f"#{value} · {records[value]['date']} · {label(records[value]['category'])} · {yen(records[value]['amount'])}",
            )
            transaction_form(path, records[identity])
            with st.expander(t("この記録を削除")):
                confirmed = st.checkbox(
                    t("この記録を完全に削除することを確認しました"),
                    key=f"delete_{identity}",
                )
                if st.button(t("完全に削除"), disabled=not confirmed):
                    fin.delete_transaction(path, identity)
                    notice(t("記録を削除しました。"))


def budget_page(selected, path, month):
    budget, goal = fin.get_plan(path, month)
    income, expenses, balance = fin.totals(selected)
    left, right = st.columns([1, 1.4], gap="large")
    with left:
        st.subheader(t("今月の予算と目標"))
        with st.form("plan"):
            new_budget = st.number_input(
                t("月間の支出予算（円）"),
                min_value=0,
                max_value=fin.MAX_AMOUNT,
                value=budget,
                step=1000,
            )
            new_goal = st.number_input(
                t("月間の黒字目標（円）"),
                min_value=0,
                max_value=fin.MAX_AMOUNT,
                value=goal,
                step=1000,
            )
            st.caption(
                t(
                    "0は未設定です。黒字＝収入−支出であり、実際の貯蓄残高ではありません。"
                )
            )
            if st.form_submit_button(t("予算・目標を保存"), type="primary"):
                fin.save_plan(path, month, new_budget, new_goal)
                notice(t("予算と目標を保存しました。"))
    with right:
        st.subheader(t("予算と目標の達成状況"))
        st.metric(t("支出 / 予算"), f"{yen(expenses)} / {yen(budget)}")
        if budget:
            st.progress(min(expenses / budget, 1))
            if expenses > budget:
                st.warning(t("予算を{v0}超過しています。", v0=yen(expenses - budget)))
            else:
                st.write(t("予算の残りは **{v0}** です。", v0=yen(budget - expenses)))
        else:
            st.info(t("支出予算を設定すると進捗が表示されます。"))
        st.divider()
        st.metric(t("今月の収支 / 黒字目標"), f"{yen(balance)} / {yen(goal)}")
        if goal:
            st.progress(min(max(balance / goal, 0), 1))
        if income and budget and (budget + goal > income):
            st.info(t("予算をすべて使うと、現在の収入では黒字目標に届きません。"))


def login_page(account_path):
    def change_language():
        st.session_state["language"] = st.session_state["login_language"]

    st.selectbox(
        t("表示言語"),
        list(accounts.LANGUAGES),
        index=list(accounts.LANGUAGES).index(st.session_state.get("language", "ja")),
        format_func=accounts.LANGUAGES.get,
        key="login_language",
        on_change=change_language,
    )
    left, right = st.columns([1.1, 1], gap="large")
    with left:
        with st.container(key="welcome"):
            st.title(t("学生の家計管理"))
            st.subheader(t("毎日の記録を、あなたの場所に。"))
            st.write(t("自分のアカウントで、収支と目標を管理しましょう。"))
            st.divider()
            st.write(t("同じアカウントなら、言語を変えても家計データは同じです。"))
            st.write(t("登録時もログイン時も、表示言語を自由に選べます。"))
            st.caption(t("このパソコンだけで使う、発表・学習向けのアプリです。"))
    with right:
        login, register = st.tabs([t("ログイン"), t("新規登録")])
        with login:
            with st.form("login", clear_on_submit=True):
                username = st.text_input(t("ユーザー名"), max_chars=32)
                password = st.text_input(
                    t("パスワード"), type="password", max_chars=128
                )
                if st.form_submit_button(
                    t("ログイン"), type="primary", width="stretch"
                ):
                    try:
                        user = accounts.authenticate(account_path, username, password)
                    except ValueError as error:
                        st.error(t(str(error)))
                    else:
                        language = st.session_state.get("language", "ja")
                        accounts.set_language(account_path, user["id"], language)
                        st.session_state.clear()
                        st.session_state.update(
                            user_id=user["id"],
                            language=language,
                            active_mode="personal",
                        )
                        st.rerun()
        with register:
            with st.form("register", clear_on_submit=True):
                display_name = st.text_input(t("表示名"), max_chars=40)
                username = st.text_input(t("ユーザー名"), max_chars=32)
                password = st.text_input(
                    t("パスワード"), type="password", max_chars=128
                )
                confirmation = st.text_input(
                    t("パスワード（確認）"), type="password", max_chars=128
                )
                st.caption(
                    t("ユーザー名：半角英数字・_で3〜32文字。パスワード：12〜128文字。")
                )
                if st.form_submit_button(
                    t("アカウントを作成"), type="primary", width="stretch"
                ):
                    if password != confirmation:
                        st.error(t("確認用パスワードが一致していません。"))
                    else:
                        try:
                            accounts.register(
                                account_path,
                                username,
                                display_name,
                                password,
                                st.session_state.get("language", "ja"),
                            )
                        except ValueError as error:
                            st.error(t(str(error)))
                        else:
                            st.success(
                                t(
                                    "登録が完了しました。「ログイン」からお入りください。"
                                )
                            )


def settings_page(account_path, user):
    st.title(t("設定"))
    st.write(t("表示言語を選んでください。選択はアカウントに保存されます。"))
    with st.form("settings"):
        language = st.selectbox(
            t("表示言語"),
            list(accounts.LANGUAGES),
            index=list(accounts.LANGUAGES).index(user["language"]),
            format_func=accounts.LANGUAGES.get,
        )
        if st.form_submit_button(t("設定を保存"), type="primary"):
            accounts.set_language(account_path, user["id"], language)
            st.session_state["language"] = language
            st.rerun()
    st.caption(
        t("表示言語を変えても、通貨は日本円のままです。入力したメモは翻訳しません。")
    )
    if st.button(t("ダッシュボードに戻る")):
        st.session_state["settings_open"] = False
        st.rerun()


def main():
    st.set_page_config(
        page_title=t("学生の家計管理"),
        page_icon=":material/account_balance_wallet:",
        layout="wide",
    )
    st.markdown(
        f"<style>{(ROOT / 'style.css').read_text(encoding='utf-8')}</style>",
        unsafe_allow_html=True,
    )
    account_path = ROOT / "data" / "private" / "accounts.sqlite3"
    accounts.initialize(account_path)
    user = accounts.get_user(account_path, st.session_state.get("user_id"))
    if user is None:
        login_page(account_path)
        return
    with st.container(key="topbar"):
        brand, profile = st.columns([3, 1])
        brand.caption(t("学生の家計管理"))
        profile.caption(user["display_name"])
    with st.sidebar:
        st.title(t("学生の家計管理"))
        st.caption(t("小さな習慣から、未来のゆとりへ。"))
        st.write(user["display_name"])
        mode_labels = {"demo": t("デモデータ"), "personal": t("自分のデータ")}
        page_labels = {
            "overview": t("ダッシュボード"),
            "transactions": t("収支記録"),
            "budget": t("予算・目標"),
        }
        mode = st.radio(
            t("データの種類"),
            list(mode_labels),
            format_func=mode_labels.get,
            index=list(mode_labels).index(st.session_state.get("active_mode", "demo")),
            key=f"data_mode_{st.session_state.get('language', 'ja')}",
        )
        st.session_state["active_mode"] = mode
        page = st.radio(
            t("メニュー"),
            list(page_labels),
            format_func=page_labels.get,
            index=list(page_labels).index(
                st.session_state.get("active_page", "overview")
            ),
            key=f"page_{st.session_state.get('language', 'ja')}",
            label_visibility="collapsed",
        )
        st.session_state["active_page"] = page
        if st.button(t("設定"), icon=":material/settings:", width="stretch"):
            st.session_state["settings_open"] = True
        if st.button(t("ログアウト"), icon=":material/logout:", width="stretch"):
            language = st.session_state.get("language", "ja")
            st.session_state.clear()
            st.session_state["language"] = language
            st.rerun()
        st.divider()
        st.caption(t("通貨：日本円（JPY）\n\nデータはこのパソコンに保存されます。"))
        if mode == "demo":
            st.info(
                t(
                    "発表用のサンプルデータです。デモの変更は自分のデータに影響しません。"
                )
            )
        else:
            st.caption(
                t(
                    "保存データは暗号化されていません。ご自身のWindowsアカウントでご利用ください。"
                )
            )
    if st.session_state.get("settings_open"):
        settings_page(account_path, user)
        return
    path = (
        ROOT
        / "data"
        / "private"
        / "users"
        / str(user["id"])
        / ("demo.sqlite3" if mode == "demo" else "finance.sqlite3")
    )
    fin.initialize(path)
    if mode == "demo":
        fin.seed_demo(path, TODAY)
    frame = fin.transactions(path)
    if mode == "demo":
        frame["note"] = frame["note"].replace(DEMO_NOTES)
    current = TODAY.strftime("%Y-%m")
    periods = sorted(
        set(pd.period_range(end=current, periods=24, freq="M").astype(str))
        | set(frame["date"].str[:7]),
        reverse=True,
    )
    title, period = st.columns([3, 1])
    with title:
        st.title(
            {
                "overview": t("ダッシュボード"),
                "transactions": t("日々の収支を、ていねいに。"),
                "budget": t("目標に向けて、ゆとりある計画を。"),
            }[page]
        )
        st.write(t("毎日の記録から、これからの暮らしを整えましょう。"))
    with period:
        month_labels = {value: month_label(value) for value in periods}
        month = st.selectbox(
            t("表示月"),
            periods,
            format_func=month_labels.get,
            index=periods.index(current),
            key=f"month_{mode}_{st.session_state.get('language', 'ja')}",
        )
    st.caption(
        t(
            "{v0} · {v1} · {v2} （日本時間）",
            v0=month_label(month),
            v1=t("サンプルデータ") if mode == "demo" else t("個人データ"),
            v2=TODAY.strftime(t("%Y年%m月%d日")),
        )
    )
    if "notice" in st.session_state:
        st.success(st.session_state.pop("notice"))
    selected = fin.month_data(frame, month)
    if page == "overview":
        overview(frame, selected, month, path)
    elif page == "transactions":
        transaction_page(selected, path, month)
    else:
        budget_page(selected, path, month)
    st.divider()
    st.caption(
        t(
            "学生の家計管理 · Python・Streamlitで開発 · データはパソコン内に保存されます。"
        )
    )


if __name__ == "__main__":
    try:
        main()
    except (sqlite3.Error, OSError, ValueError) as error:
        st.error(
            t(
                "処理できませんでした：{v0} 入力内容と保存先へのアクセス権を確認し、再読み込みしてください。",
                v0=t(str(error)),
            )
        )
        st.stop()
