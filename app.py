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
MONTHS = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
GREEN, ORANGE = "#17644D", "#B45A31"


def yen(value):
    return f"{'−' if value < 0 else ''}¥{abs(int(value)):,}".replace(",", ".")


def month_label(value):
    return f"{MONTHS[int(value[5:]) - 1]} {value[:4]}"


def notice(message):
    st.session_state["notice"] = message
    st.rerun()


def transaction_form(path, row=None):
    editing = row is not None
    prefix = f"edit_{int(row['id'])}" if editing else "new"
    kind = st.selectbox("Jenis transaksi", list(fin.CATEGORIES),
                        index=list(fin.CATEGORIES).index(row["kind"]) if editing else 0, key=f"{prefix}_kind")
    categories = fin.CATEGORIES[kind]
    with st.form(prefix, clear_on_submit=not editing):
        left, right = st.columns(2)
        day = left.date_input("Tanggal", value=datetime.fromisoformat(row["date"]).date() if editing else TODAY, max_value=TODAY)
        category = right.selectbox("Kategori", categories,
                                   index=categories.index(row["category"]) if editing and row["category"] in categories else 0)
        amount = st.number_input("Nominal (¥)", min_value=1, max_value=fin.MAX_AMOUNT,
                                 value=int(row["amount"]) if editing else 1000, step=100)
        note = st.text_input("Catatan (opsional)", value=row["note"] if editing else "", max_chars=120)
        if st.form_submit_button("Simpan perubahan" if editing else "Tambah transaksi", type="primary", width="stretch"):
            fin.save_transaction(path, day, kind, category, amount, note, int(row["id"]) if editing else None)
            notice("Perubahan tersimpan." if editing else "Transaksi ditambahkan.")


def display_table(frame):
    view = frame.rename(columns={"date": "Tanggal", "kind": "Jenis", "category": "Kategori", "amount": "Nominal (¥)", "note": "Catatan"})
    st.dataframe(view[["Tanggal", "Jenis", "Kategori", "Catatan", "Nominal (¥)"]], hide_index=True, width="stretch",
                 column_config={"Nominal (¥)": st.column_config.NumberColumn(format="¥ %d")})


def overview(frame, selected, month, path):
    income, expenses, balance = fin.totals(selected)
    budget, goal = fin.get_plan(path, month)
    with st.container(key="summary"):
        for column, label, value in zip(st.columns(4),
                                        ["Pemasukan", "Pengeluaran", "Sisa bulan ini", "Rasio surplus"],
                                        [yen(income), yen(expenses), yen(balance), f"{balance / income:.1%}" if income else "—"]):
            column.metric(label, value)
    st.caption("Sisa bulan ini = pemasukan − pengeluaran. Ini bukan saldo rekening atau tabungan aktual.")
    left, right = st.columns([1.7, 1], gap="large")
    with left:
        st.subheader("Perjalanan keuangan")
        st.caption("Pemasukan dan pengeluaran · enam bulan sampai periode terpilih")
        periods = pd.period_range(end=month, periods=6, freq="M").astype(str)
        history = frame.assign(month=frame["date"].str[:7]).groupby(["month", "kind"])["amount"].sum()
        chart_data = pd.DataFrame([
            {"Bulan": period, "Jenis": kind, "Yen": int(history.get((period, kind), 0))}
            for period in periods for kind in ["Pemasukan", "Pengeluaran"]
        ])
        chart = alt.Chart(chart_data).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
            x=alt.X("Bulan:N", title=None, sort=list(periods), axis=alt.Axis(labelAngle=0)),
            y=alt.Y("Yen:Q", title="Yen (¥)", axis=alt.Axis(format=",.0f")), xOffset="Jenis:N",
            color=alt.Color("Jenis:N", scale=alt.Scale(domain=["Pemasukan", "Pengeluaran"], range=[GREEN, ORANGE]), legend=alt.Legend(orient="bottom", title=None)),
            tooltip=["Bulan", "Jenis", alt.Tooltip("Yen:Q", format=",.0f")],
        ).properties(height=270).configure_axis(labelColor="#52685D", titleColor="#52685D").configure_legend(labelColor="#52685D")
        st.altair_chart(chart, width="stretch")
    with right:
        st.subheader("Ruang untuk menabung")
        st.caption("Target surplus untuk bulan terpilih")
        st.metric("Surplus / target", f"{yen(balance)} / {yen(goal)}")
        if goal:
            st.progress(min(max(balance / goal, 0), 1))
            st.write("Target surplus tercapai." if balance >= goal else f"Masih perlu {yen(goal - balance)} untuk mencapai target.")
        else:
            st.info("Atur target di menu Anggaran.")
        st.divider()
        if budget:
            st.write(f"**{yen(abs(budget - expenses))}** {'melewati batas anggaran' if expenses > budget else 'anggaran tersisa'}")
            st.caption(f"Pengeluaran {expenses / budget:.0%} dari batas {yen(budget)}.")
        else:
            st.caption("Batas anggaran belum diatur.")
    left, right = st.columns([1, 1.7], gap="large")
    with left:
        st.subheader("Ke mana uangmu pergi?")
        spending = selected[selected["kind"] == "Pengeluaran"].groupby("category", as_index=False)["amount"].sum().sort_values("amount", ascending=False)
        if spending.empty:
            st.info("Belum ada pengeluaran pada bulan ini.")
        else:
            chart = alt.Chart(spending).mark_bar(cornerRadiusEnd=4, color=GREEN).encode(
                y=alt.Y("category:N", title=None, sort="-x"), x=alt.X("amount:Q", title="Yen (¥)"),
                tooltip=[alt.Tooltip("category:N", title="Kategori"), alt.Tooltip("amount:Q", title="Yen", format=",.0f")],
            ).properties(height=230).configure_axis(labelColor="#52685D", titleColor="#52685D")
            st.altair_chart(chart, width="stretch")
            biggest = spending.iloc[0]
            st.caption(f"{biggest['category']} menyerap {biggest['amount'] / expenses:.0%} pengeluaran bulan ini.")
    with right:
        st.subheader("Transaksi terbaru")
        if selected.empty:
            st.info("Mulai dari menu Transaksi untuk mencatat keuanganmu.")
        else:
            display_table(selected.head(5))
        if expenses > income:
            st.warning(f"Pengeluaran melampaui pemasukan sebesar {yen(expenses - income)}. Tinjau pengeluaran yang bisa ditunda.")
        elif income:
            st.success(f"Surplus bulan ini {yen(balance)}. Sisihkan sesuai prioritasmu sebelum menambah belanja.")
        st.caption("Insight dihitung dari transaksi tercatat; bukan prediksi atau saran keuangan profesional.")


def transaction_page(selected, path, month):
    st.subheader("Catatan transaksi")
    history, add, edit = st.tabs(["Riwayat", "Tambah", "Ubah / hapus"])
    with history:
        left, right = st.columns(2)
        kind = left.selectbox("Filter jenis", ["Semua", *fin.CATEGORIES])
        query = right.text_input("Cari catatan atau kategori", max_chars=120)
        filtered = selected if kind == "Semua" else selected[selected["kind"] == kind]
        if query:
            filtered = filtered[filtered["note"].str.contains(query, case=False, regex=False) | filtered["category"].str.contains(query, case=False, regex=False)]
        st.caption(f"{len(filtered)} transaksi · {month_label(month)}")
        if filtered.empty:
            st.info("Tidak ada transaksi yang cocok. Ganti filter atau tambahkan transaksi.")
        else:
            display_table(filtered)
            exported = filtered.drop(columns="id").copy()
            for column in ["note", "category"]:
                exported[column] = exported[column].map(lambda value: "'" + value if value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else value)
            st.download_button("Unduh CSV", exported.to_csv(index=False).encode("utf-8-sig"), file_name=f"transaksi-{month}.csv", mime="text/csv")
    with add:
        st.caption("Tanggal transaksi menentukan bulan pencatatan. Ganti periode untuk melihat bulan lain.")
        transaction_form(path)
    with edit:
        if selected.empty:
            st.info("Belum ada transaksi pada periode ini.")
        else:
            records = {int(row["id"]): row for _, row in selected.iterrows()}
            identity = st.selectbox("Pilih transaksi", list(records), format_func=lambda value: f"#{value} · {records[value]['date']} · {records[value]['category']} · {yen(records[value]['amount'])}")
            transaction_form(path, records[identity])
            with st.expander("Hapus transaksi ini"):
                confirmed = st.checkbox("Saya yakin ingin menghapus transaksi ini", key=f"delete_{identity}")
                if st.button("Hapus permanen", disabled=not confirmed):
                    fin.delete_transaction(path, identity)
                    notice("Transaksi dihapus.")


def budget_page(selected, path, month):
    budget, goal = fin.get_plan(path, month)
    income, expenses, balance = fin.totals(selected)
    left, right = st.columns([1, 1.4], gap="large")
    with left:
        st.subheader("Rencana bulan ini")
        with st.form("plan"):
            new_budget = st.number_input("Batas pengeluaran bulanan (¥)", min_value=0, max_value=fin.MAX_AMOUNT, value=budget, step=1000)
            new_goal = st.number_input("Target surplus bulanan (¥)", min_value=0, max_value=fin.MAX_AMOUNT, value=goal, step=1000)
            st.caption("Nilai 0 berarti belum diatur. Target surplus = pemasukan − pengeluaran, bukan saldo tabungan.")
            if st.form_submit_button("Simpan rencana", type="primary"):
                fin.save_plan(path, month, new_budget, new_goal)
                notice("Rencana bulanan tersimpan.")
    with right:
        st.subheader("Posisi terhadap rencana")
        st.metric("Pengeluaran / anggaran", f"{yen(expenses)} / {yen(budget)}")
        if budget:
            st.progress(min(expenses / budget, 1))
            if expenses > budget:
                st.warning(f"Melewati anggaran {yen(expenses - budget)}.")
            else:
                st.write(f"Masih tersedia **{yen(budget - expenses)}** dalam anggaran.")
        else:
            st.info("Tetapkan batas pengeluaran untuk melihat progres.")
        st.divider()
        st.metric("Surplus / target", f"{yen(balance)} / {yen(goal)}")
        if goal:
            st.progress(min(max(balance / goal, 0), 1))
        if income and budget and budget + goal > income:
            st.info("Jika seluruh anggaran dipakai, pemasukan saat ini belum cukup untuk memenuhi target surplus.")


def main():
    st.set_page_config(page_title="Student Finance", page_icon=":material/account_balance_wallet:", layout="wide")
    st.markdown(f"<style>{(ROOT / 'style.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    with st.sidebar:
        st.title("Student Finance")
        st.caption("Kebiasaan kecil. Rencana lebih besar.")
        mode = st.radio("Sumber data", ["Demo presentasi", "Data pribadi"], key="data_mode")
        page = st.radio("Navigasi", ["Ringkasan", "Transaksi", "Anggaran"], label_visibility="collapsed")
        st.divider()
        st.caption("Mata uang · Yen Jepang (JPY)\n\nData tersimpan di komputer ini.")
        if mode == "Demo presentasi":
            st.info("Data simulasi untuk presentasi. Perubahan demo tidak memengaruhi data pribadi.")
        else:
            st.caption("Catatan lokal belum terenkripsi. Gunakan pada akun Windows pribadimu.")
    path = ROOT / "data" / "private" / ("demo.sqlite3" if mode == "Demo presentasi" else "finance.sqlite3")
    fin.initialize(path)
    if mode == "Demo presentasi":
        fin.seed_demo(path, TODAY)
    frame = fin.transactions(path)
    current = TODAY.strftime("%Y-%m")
    periods = sorted(set(pd.period_range(end=current, periods=24, freq="M").astype(str)) | set(frame["date"].str[:7]), reverse=True)
    title, period = st.columns([3, 1])
    with title:
        st.title({"Ringkasan": "Keuanganmu, lebih terarah.", "Transaksi": "Setiap yen punya cerita.", "Anggaran": "Beri ruang untuk rencanamu."}[page])
        st.write("Lihat kebiasaanmu hari ini, siapkan langkah untuk esok.")
    with period:
        month = st.selectbox("Periode", periods, format_func=month_label, index=periods.index(current), key=f"month_{mode}")
    st.caption(f"{month_label(month)} · {'DATA DEMO / SIMULASI' if mode == 'Demo presentasi' else 'DATA PRIBADI'} · {TODAY.strftime('%d/%m/%Y')} (Jepang)")
    if "notice" in st.session_state:
        st.success(st.session_state.pop("notice"))
    selected = fin.month_data(frame, month)
    if page == "Ringkasan":
        overview(frame, selected, month, path)
    elif page == "Transaksi":
        transaction_page(selected, path, month)
    else:
        budget_page(selected, path, month)
    st.divider()
    st.caption("Student Finance · Dibangun dengan Python & Streamlit · Data milikmu, tersimpan lokal.")


if __name__ == "__main__":
    try:
        main()
    except (sqlite3.Error, OSError, ValueError) as error:
        st.error(f"Perubahan belum berhasil: {error}. Periksa input dan izin folder data, lalu muat ulang.")
        st.stop()
