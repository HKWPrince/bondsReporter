from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file
import os
import pandas as pd
from app.dao import DatabaseHandler
import time
import datetime
import requests
import asyncio
import aiohttp

main = Blueprint("main", __name__)

_REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

# 確認Taipei Exchange 檔案狀態

# 單一網址檢查邏輯
async def _fetch_url_status(session, element):
    try:
        async with session.get(element['Url'], timeout=5) as response:
            is_file = response.status == 200 and 'text/html' not in response.headers.get('Content-Type', '')
            element['Status_code'] = '200' if is_file else '404'
            element['Show_download_btn'] = '' if is_file else 'disabled'
            element['Download_btn_class'] = 'success' if is_file else 'Secondary'
    except Exception:
        element['Status_code'] = '404'
        element['Show_download_btn'] = 'disabled'
        element['Download_btn_class'] = 'Secondary'
    return element


async def _check_all_urls_async(data):
    connector = aiohttp.TCPConnector(limit=20, ssl=False)
    async with aiohttp.ClientSession(headers=_REQUEST_HEADERS, connector=connector) as session:
        async def passthrough(el):
            return el

        tasks = [
            _fetch_url_status(session, el) if el["Status_code"] == "Search" else passthrough(el)
            for el in data
        ]
        return await asyncio.gather(*tasks)


def _check_taipei_exchange(data):
    return asyncio.run(_check_all_urls_async(data))


def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]

def _process_csv(filepath):
    with open(filepath, 'r', encoding='cp950') as f:
        lines = f.readlines()
        raw_date = lines[1].split(',')[1].strip()
        raw_date = raw_date.replace('日期:', '').replace('年', '/').replace('月', '/').replace('日', '')
        parts = raw_date.split('/')
        date = str(int(parts[0]) + 1911) + '/' + parts[1] + '/' + parts[2]

    df = pd.read_csv(filepath, encoding='cp950', skiprows=2, header=None)
    df = df.iloc[2:, 1:]

    db = DatabaseHandler()

    if db.check_date_exists(date):
        return False

    success = db.insert_convertible_bond_daily(df, date)
    db.insert_upload_log(date)
    return success


@main.route("/")
def home():
    # 前端年份篩選
    year = request.args.get("year")
    # 取得所有有資料的年份
    filter_year = year if year and year != "all" else None
    
    db = DatabaseHandler()
    recent_status = _check_taipei_exchange(db.query_recent_status(filter_year))
    # 查詢近30天資料狀態 
    # 查詢資料庫資料天數
    # 查詢最近交易日
    # 查詢最近交易日
    return render_template(
        "index.html",
        recent_status=recent_status,
        years=db.get_data_years(),
        selected_year=year,
        dataDaysNum=db.get_data_days_count(),
        tradingDate=db.get_latest_trading_date(),
        date=datetime.datetime.now().strftime("%Y-%m-%d(%A)"),
        latestUpload=db.get_latest_upload_date(),
    )


@main.route("/download")
def download():
    return render_template("download.html")

# **處理上傳檔案**
@main.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        flash("Error: No file part")
        return redirect(url_for("main.home"))

    file = request.files["file"]
    if file.filename == "":
        flash("Error: Please select a file!")
        return redirect(url_for("main.home"))

    if not (file and _allowed_file(file.filename)):
        flash("Error: Invalid file format. Please upload a CSV file!")
        return redirect(url_for("main.home"))

    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], file.filename)
    file.save(filepath)

    if _process_csv(filepath):
        flash("Success: File uploaded and processed successfully!")
    else:
        flash("Error: The data hasn't been uploaded. Please check!")
    return redirect(url_for("main.home"))

# **自動下載並上傳檔案**
@main.route("/autoInsert", methods=["POST"])
def auto_insert():
    date = request.values['Date']
    url = request.values['Url']

    response = requests.get(url, headers=_REQUEST_HEADERS)
    is_file = response.status_code == 200 and response.headers.get('Content-Type') != 'text/html'

    if not is_file:
        filename = date.replace("-", "") + ".csv"
        if response.headers.get('Content-Type') == 'text/html':
            flash(f"Error: Taipei Exchange doesn't provide {filename}")
        else:
            flash(f"Error: {filename} file hasn't been downloaded")
        return redirect(url_for("main.home"))

    filename = date.replace("-", "") + ".csv"
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    try:
        with open(filepath, "wb") as f:
            f.write(response.content)

        if _process_csv(filepath):
            flash(f"Success: {filename} has been downloaded and inserted successfully!")
        else:
            flash(f"Error: {filename} hasn't been uploaded. Please check!")
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

    return redirect(url_for("main.home"))

# **下載檔案**
@main.route("/download_ConvertibleBondDaily", methods=["GET"])
def download_convertible_bond_daily():
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    bond_id = request.args.get('id') or None
    company_name = request.args.get('companyName') or None
    # 日期不為空
    if not start_date or not end_date:
        flash("Error: Please provide start and end date!")
        return render_template("download.html")
    # 日期先後順序
    if time.strptime(start_date, "%Y-%m-%d") > time.strptime(end_date, "%Y-%m-%d"):
        flash("Error: Start date should be earlier than end date!")
        return render_template("download.html")

    db = DatabaseHandler()
    # 判斷下載或是搜尋
    method = request.args.get('method')

    if method == 'search':
        table = db.query_convertible_bond(start_date, end_date, bond_id, company_name)
        hide = "" if table else "hidden"
        return render_template(
            "download.html",
            table=table,
            startDate=start_date,
            endDate=end_date,
            bond_id=bond_id,
            company_name=company_name,
            hide=hide,
        )

    if method == 'download':
        filename = db.download_convertible_bond(start_date, end_date, bond_id, company_name)
        if not filename:
            flash("Error: Data Not Found!")
            return render_template("download.html")
        # 回傳 Excel 檔案給用戶下載
        return send_file(os.path.join(current_app.config["File_FOLDER"], filename), as_attachment=True)
