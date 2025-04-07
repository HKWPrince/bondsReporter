from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_file, jsonify
import os
import pandas as pd
from app.dao import DatabaseHandler
import time
import datetime

# 建立 Blueprint
main = Blueprint("main", __name__)

# 查詢近30天資料狀態 
def query_recent_status():
    db = DatabaseHandler()
    recent_status = db.query_recent_status()
    return recent_status
# 查詢資料庫資料天數
def get_dataDaysNum():
    db = DatabaseHandler()
    dataDaysNum = db.get_dataDaysNum()
    return dataDaysNum
# 查詢最近交易日
def get_TradingDate():
    db = DatabaseHandler()
    tradingDate = db.get_TradingDate()
    return tradingDate

# 查詢最近交易日
def get_LatestUpload():
    db = DatabaseHandler()
    latestUpload = db.get_LatestUpload()
    return latestUpload

@main.route("/")
def home():
    recent_status=query_recent_status()
    dataDaysNum = get_dataDaysNum()
    tradingDate = get_TradingDate()
    date = datetime.datetime.now().strftime("%Y-%m-%d(%A)")
    latestUpload = get_LatestUpload()
    return render_template("index.html", recent_status = recent_status, dataDaysNum=dataDaysNum , tradingDate= tradingDate, date=date , latestUpload=latestUpload)

@main.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@main.route("/tables")
def tables():
    return render_template("tables.html")

@main.route("/billing")
def billing():
    return render_template("billing.html")

@main.route("/virtual_reality")
def virtual_reality():
    return render_template("virtual-reality.html")

@main.route("/rtl")
def rtl():
    return render_template("rtl.html")

@main.route("/notifications")
def notifications():
    return render_template("notifications.html")

@main.route("/profile")
def profile():
    return render_template("profile.html")

@main.route("/sign_in")
def sign_in():
    return render_template("sign-in.html")

@main.route("/sign_up")
def sign_up():
    return render_template("sign-up.html")

@main.route("/download")
def download():
    return render_template("download.html", hide = "hidden")

# 確保上傳資料夾存在
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# 檢查檔案格式
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]

# **處理 excel 並存入 SQL Server**
def process_excel(filename):
    df_file = pd.read_csv(filename, encoding='cp950',skiprows=2, header=None)
    # 確認日期
    with open(filename, 'r', encoding='cp950') as f:
        lines = f.readlines()
        date = lines[1].split(',')[1].strip()
        date = date.replace('日期:','').replace('年','/').replace('月','/').replace('日','')
        date_list = date.split('/')
        year=str(int(date_list[0])+1911)
        date = year+'/'+date_list[1]+'/'+date_list[2]

    df_file = df_file.iloc[2:,1:]
    

    # 儲存到資料庫x
    db = DatabaseHandler()

    # 確認是否重複上傳
    date_exist = db.check_convertible_bond_daily_exist(date)

    if date_exist:
        return not date_exist
    
    # 匯入SQL Server
    success = db.insert_convertible_bond_daily(df_file,date)

    # 記錄最後一筆上傳日期
    db.insert_convertible_bond_daily_upload_log(date)

    return success

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

    if file and allowed_file(file.filename):
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], file.filename)
        file.save(filepath)  # 存檔案到 uploads 資料夾

        # 處理 CSV 並存入 SQL Server
        if process_excel(filepath):
            flash("Success: File uploaded and processed successfully!")
            return redirect(url_for("main.home"))
        else:
            flash("Error: The data hasn't been uploaded. Please check!")
            return redirect(url_for("main.home"))
    else:
        flash("Error:Invalid file format. Please upload a Excel file!")
        return redirect(url_for("main.home"))
    
# **下載檔案**
@main.route("/download_ConvertibleBondDaily", methods = ["GET"])
def download_ConvertibleBondDaily():
    table = ""
    hide = "hidden"
    # 參數
    startDate = request.args.get('startDate')  # 格式: YYYY-MM-DD
    endDate = request.args.get('endDate')      # 格式: YYYY-MM-DD
    id = request.args.get('id', None)
    companyName = request.args.get('companyName', None)
    # 日期不為空
    if not startDate or not endDate:
        flash("Error: Please provide start and end date!")
        return render_template("download.html")
    # 日期先後順序
    if time.strptime(startDate, "%Y-%m-%d") > time.strptime(endDate, "%Y-%m-%d") :
        flash("Error: Start date should be earlier than end date!")
        return render_template("download.html")
    db = DatabaseHandler()
    # 判斷下載或是搜尋
    method = request.args.get('method')

    if method == 'search':
        table = db.query_convertible_bond(startDate, endDate, id, companyName)
        if len(table)>0:
            hide = ""
        return render_template("download.html", table = table, startDate = startDate, endDate=endDate, id=id, companyName=companyName, hide=hide)

    elif method == 'download':
        
        filename = db.download_convertible_bond(startDate, endDate, id, companyName)

        if filename:
            filename = os.path.join(current_app.config["File_FOLDER"], filename)
        else:
            flash("Error: Data Not Found!")
            return render_template("download.html")

        # 回傳 Excel 檔案給用戶下載
        return send_file(filename, as_attachment=True)

