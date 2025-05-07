from collections import defaultdict
from socket import SocketIO
import time
import bcrypt
import cv2
from flask import Flask, Response, jsonify, render_template, request, redirect, url_for, session, send_file
import mysql.connector
from mysql.connector import Error
import numpy as np
import pandas as pd
import csv
import io
from flask_socketio import SocketIO, emit

from ultralytics import YOLO
from Test import process_frame, draw_boxes

import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.jinja_env.globals.update(enumerate=enumerate)
socketio = SocketIO(app)
model = YOLO('last_v9.pt')
def create_connection():
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='pbl05',
            user='root',
            password=''
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print("Error while connecting to MySQL", e)
    return None

def validate_user(username, password):
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Account WHERE Account=%s", (username, ))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        if user:
            if check_password(password,user['Password']):
                return True
    return False
def getTypeUser(username):
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT Type FROM account WHERE Account=%s", (username,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        if user:
            if (user['Type'] == "admin") : 
                return 1
            else :
                return 0
    return None

def MyInforFromDatabase(username):
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM infor WHERE Account=%s", (username,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        if user:
            return user
    return None

def ShowOject():
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT DISTINCT ClassName FROM class")
        objects = cursor.fetchall()
        cursor.close()
        connection.close()
        if objects:
            return objects
    return None
def ShowOjectAndID():
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT ClassName, IDClass FROM class")
        objects = cursor.fetchall()
        cursor.close()
        connection.close()
        if objects:
            # Tạo chuỗi IDClass-ClassName cho mỗi lớp và thêm vào danh sách
            formatted_objects = [f"{obj['IDClass']}-{obj['ClassName']}" for obj in objects]
            return formatted_objects
    return None
def ShowOjectAndIDOfTeacher(Account):
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT ClassName, IDClass FROM class where Account = %s", (Account,))
        objects = cursor.fetchall()
        cursor.close()
        connection.close()
        if objects:
            # Tạo chuỗi IDClass-ClassName cho mỗi lớp và thêm vào danh sách
            formatted_objects = [f"{obj['IDClass']}-{obj['ClassName']}" for obj in objects]
            return formatted_objects
    return None

def get_enrollment_info_admin(Object):
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM class WHERE ClassName=%s", (Object,))
        enrollment_info = cursor.fetchall()
        cursor.close()
        connection.close()
        return enrollment_info
    return None

def get_student_infor(name):
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT enrollment.IDClass, enrollment.MSSV, student.Name, student.Class FROM enrollment JOIN student ON enrollment.MSSV = student.MSSV WHERE enrollment.IDClass = %s", (name,))
        student_info = cursor.fetchall()
        cursor.close()
        connection.close()
        return student_info
    return None
def get_data(selected_class):
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)

    # Truy vấn dữ liệu kết hợp từ bảng enrollment, student và status
        cursor.execute('''
        SELECT e.IDenroll, s.MSSV, s.Name, s.Class, st.Status
        FROM enrollment e
        JOIN student s ON e.MSSV = s.MSSV
        LEFT JOIN status st ON e.IDenroll = st.IDEnroll
        WHERE e.IDClass = %s
        ''', (selected_class,))
        data = cursor.fetchall()

        connection.close()
    return data
def CheckAccount(Taikhoan):
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT Account FROM account WHERE Account=%s", (Taikhoan,))
        enrollment_info = cursor.fetchall()
        if enrollment_info:
            return 1
        cursor.close()
        connection.close()
        
    return 0
def GetAccountAndName():
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM infor ")
        enrollment_info = cursor.fetchall()
        cursor.close()
        connection.close()
        if enrollment_info:
            # Tạo chuỗi IDClass-ClassName cho mỗi lớp và thêm vào danh sách
            formatted_enrollment_info = [f"{obj['Account']}-{obj['Name']}" for obj in enrollment_info]
            return formatted_enrollment_info
    return 0
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

# Kiểm tra mật khẩu
def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
def Add_Object(ID,Account, Name, ClassName, Date):
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("INSERT INTO class (IDCLASS ,Account, NameTeacher, ClassName, Date) VALUES (%s, %s, %s, %s, %s)",
                   (ID, Account,Name ,ClassName, Date))
        connection.commit()
        cursor.close()
        connection.close()
        return None
def check_Idclass(IDClass):
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("Select * from class where IDCLASS = %s",
                   (IDClass,))
        check = cursor.fetchall()
        cursor.close()
        connection.close()
        if check :
            return 0
        return 1
def Add_Student(Idclass, MSSV):
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("INSERT INTO enrollment (IDCLASS ,MSSV) VALUES (%s, %s)",
                   (Idclass, MSSV))
        connection.commit()
        cursor.close()
        connection.close()
        return None
def ShowObjectOfTeacher(Account):
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("Select IDCLASS, ClassName from class where Account = %s",
                   (Account,))
        check = cursor.fetchall()
        cursor.close()
        connection.close()
        if check:
            checked = [f"{obj['IDCLASS']}-{obj['ClassName']}" for obj in check]
            return checked
        return None
def DeleteClass(IDCLASS):
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("Delete From class where IDCLASS = %s",
                   (IDCLASS, ))
        connection.commit()
        cursor.close()
        connection.close()
        return None
def DeleteStatus(IDCLASS):
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
                    DELETE FROM Status 
                    WHERE IDenroll IN (
                        SELECT IDenroll 
                        FROM enrollment 
                        WHERE IDCLASS = %s
                    )
                """, (IDCLASS, ))
        connection.commit()
        cursor.close()
        connection.close()
        
def DeleteEnrollment(IDCLASS):
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary = True)
        cursor.execute("Delete from enrollment where IDCLASS = %s", (IDCLASS, ))
        connection.commit()
        cursor.close()
        connection.close()
def get_classes():
    connection = create_connection()
    if connection:
        try:
            query = "SELECT IDCLASS, NameTeacher, ClassName FROM class ORDER BY NameTeacher, IDCLASS"
            df = pd.read_sql(query, connection)
            return df
        except Error as e:
            print(f"Error while fetching data: {e}")
            return None
        finally:
            connection.close()
    else:
        print("Failed to create database connection")
        return None
#############################
def get_user_info(username):
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM infor WHERE Account=%s", (username,))
        user_info = cursor.fetchone()
        cursor.close()
        connection.close()
        return user_info
    return None

def get_user_classes(username):
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT IDClass, ClassName, Date FROM class WHERE Account=%s", (username,))
        classes = cursor.fetchall()
        cursor.close()
        connection.close()
        return classes
    return None

def get_enrollment_info(IDClass):
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT MSSV FROM enrollment WHERE IDClass=%s", (IDClass,))
        enrollment_info = cursor.fetchall()
        cursor.close()
        connection.close()
        return enrollment_info
    return None

def update_attendance(mssv, class_id):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        cursor.execute("UPDATE enrollment SET status=%s WHERE MSSV=%s AND IDClass=%s", ('Present', mssv, class_id))
        connection.commit()
        cursor.close()
        connection.close()
        # Gọi hàm cập nhật thông tin điểm danh vào bảng status
        update_attendance_status(mssv, class_id)

def update_attendance_status(mssv, class_id):
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT IDenroll FROM enrollment WHERE MSSV=%s AND IDClass=%s", (mssv, class_id))
        enrollment_info = cursor.fetchone()
        
        if enrollment_info:
            id_enroll = enrollment_info['IDenroll']
            current_time = time.strftime('%Y-%m-%d')
            cursor.execute("INSERT INTO status (IDenroll, Status) VALUES (%s, %s)", (id_enroll, current_time))
            connection.commit()
        cursor.close()
        connection.close()

def generate_frames():
    esp32_url = 'http://192.168.75.196/cam-hi.jpg'  # URL của ESP32
    cap = None
    try:
        while True:
            try:
                response = requests.get(esp32_url)
                if response.status_code == 200:
                    img_array = np.array(bytearray(response.content), dtype=np.uint8)
                    frame = cv2.imdecode(img_array, -1)

                    results = process_frame(frame)
                    frame = draw_boxes(frame, results)

                    ret, buffer = cv2.imencode('.jpg', frame)
                    frame = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                else:
                    print("Failed to get image from ESP32")
            except Exception as e:
                print("Error: ", e)
                break
    finally:
        if cap:
            cap.release()

def get_class_info(class_id):
    connection = create_connection()
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM class WHERE IDClass=%s", (class_id,))
        class_info = cursor.fetchone()
        cursor.close()
        connection.close()
        return class_info
    return None
##### Hải ########

##############
#############################
@app.route('/')
def index():
    if "user_name" not in session:
        return render_template('index.html')
    else:
        session.pop("user_name", None)
        return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    user_name = request.form['taikhoan']
    pass_word = request.form['matkhau']

    if validate_user(user_name, pass_word):
        session["user_name"] = user_name
        if(getTypeUser(user_name) == 0):
            return redirect(url_for('home'))
        else:
            return redirect(url_for('homeAdmin'))
    else:
        return "SAI TAI KHOAN"
##############################
@app.route('/userinfo')
def userinfo():
    if 'user_name' not in session:
        return redirect(url_for('/'))
    user_info = get_user_info(session['user_name'])
    if user_info:
        return render_template('inforuserform.html', content=user_info)
    else:
        return 'User information not found'
@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if 'user_name' not in session:
        return redirect(url_for('index'))
    no_students = False
    enrollment_info = None
    selected_class = None
    class_info = None
    if request.method == 'POST':
        selected_class = request.form.get('classes')
        selected_class_IDClass = selected_class.split('-')[0].strip()
        enrollment_info = get_student_infor(selected_class_IDClass)
        if not enrollment_info:
            no_students = True
        else:
            class_info = get_class_info(selected_class)
    user_classes = get_user_classes(session['user_name'])
    return render_template('attendance.html', username=session['user_name'], classes=user_classes, enrollment_info=enrollment_info, selected_class=selected_class, no_students=no_students, class_info=class_info)

@app.route('/video_feed/<class_id>')
def video_feed(class_id):
    if 'user_name' not in session:
        return redirect(url_for('index'))
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@socketio.on('start_recognition')
def handle_start_recognition(data):
    class_id = data['class_id']
    esp32_url = 'http://192.168.75.196/cam-hi.jpg'  # URL của ESP32
    while True:
        try:
            response = requests.get(esp32_url)
            if response.status_code == 200:
                img_array = np.array(bytearray(response.content), dtype=np.uint8)
                frame = cv2.imdecode(img_array, -1)

                results = process_frame(frame)
                for result in results[0].boxes:
                    x1, y1, x2, y2 = map(int, result.xyxy[0])
                    label = model.names[int(result.cls[0])]

                    if label == "unknown":
                        # Gửi cảnh báo khi nhận diện là "unknown"
                        socketio.emit('unknown_person_detected', {'message': 'Unknown person detected!'})
                    else:
                        # Truy vấn cơ sở dữ liệu để lấy thông tin sinh viên tương ứng với label (MSSV)
                        connection = create_connection()
                        if connection:
                            cursor = connection.cursor(dictionary=True)
                            cursor.execute("SELECT * FROM enrollment WHERE MSSV=%s AND IDClass=%s", (label, class_id))
                            student_info = cursor.fetchone()
                            cursor.close()
                            connection.close()

                            if not student_info:
                                # Gửi cảnh báo khi nhận diện không thuộc lớp
                                socketio.emit('unknown_person_detected', {'message': 'Person not in this class detected!'})
                            else:
                                # Cập nhật trạng thái điểm danh cho sinh viên
                                socketio.emit('face_detected', {'mssv': label, 'class_id': class_id})
            else:
                print("Failed to get image from ESP32")
            time.sleep(3)  # Add a delay of 3 seconds here
        except Exception as e:
            print("Error: ", e)
            break

@app.route('/confirm_attendance', methods=['POST'])
def confirm_attendance():
    data = request.get_json()
    mssv = data.get('mssv')
    class_id = data.get('class_id')
    try:
        update_attendance_status(mssv, class_id)
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/recognize/<class_id>')
def recognize(class_id):
    if 'user_name' not in session:
        return redirect(url_for('index'))
    return render_template('recognize.html', class_id=class_id)



##############################
@app.route('/homeadmin')
def homeAdmin():
    return render_template('mainform.html', content=session['user_name'])


@app.route('/home')
def home():
    return render_template('home.html', content=session['user_name'])


@app.route('/MyInfor')
def MyInfor():
    user_info = MyInforFromDatabase(session["user_name"])
    if user_info:
        return render_template("inforForm.html", content=user_info)

@app.route("/TeacherForm")
def LoadCB():
    objects = ShowOject()
    if objects:
        return render_template("TeacherForm.html", content=objects, username=session["user_name"])

@app.route('/attendanceAdmin', methods=['GET', 'POST'])
def attendanceAdmin():
    if 'user_name' not in session:
        return redirect(url_for('index'))
    no_students = False
    enrollment_info = None
    selected_class = None
    if request.method == 'POST':
        selected_class = request.form.get('object')
        enrollment_info = get_enrollment_info_admin(selected_class)
        if not enrollment_info:
            no_students = True
    contents = ShowOject()
    return render_template('TeacherForm.html', username=session['user_name'], content=contents, enrollment_info=enrollment_info, selected_class=selected_class, no_students=no_students)

@app.route('/student/<name>')
def loadsv(name):
    student = get_student_infor(name)
    if student:
        return render_template("student.html", student=student)
    return "Không tìm thấy sinh viên"
@app.route('/attendancedStudent', methods=['GET', 'POST'])
def index1():
    selected_class = request.form.get('class')  # Lấy IDClass từ form
    classes = ShowOjectAndID()

    data = []
    all_dates = set()
    results = defaultdict(lambda: {'MSSV': '', 'Name': '', 'Class': '', 'Status': defaultdict(lambda: 'Vắng')})

    if selected_class:
        selected_class_id = selected_class.split('-')[0].strip()  # Tách IDClass từ giá trị được chọn
        data = get_data(selected_class_id)
        for row in data:
            if results[row["IDenroll"]]['MSSV'] == '' :
                results[row["IDenroll"]]['MSSV'] = row["MSSV"]
                results[row["IDenroll"]]['Name'] = row["Name"]
                results[row["IDenroll"]]['Class'] = row["Class"]  
            if row["Status"]:
                results[row["IDenroll"]]['Status'][row["Status"]] = row["Status"]
                all_dates.add(row["Status"])
        all_dates = sorted(all_dates)
    return render_template('attendancedStudent.html', classes=classes, selected_class=selected_class, data=results, all_dates=all_dates)

@app.route('/attendancedStudentUser', methods=['GET', 'POST'])
def index2():
    selected_class = request.form.get('class')  # Lấy IDClass từ form
    classes = ShowOjectAndIDOfTeacher(session['user_name'])

    data = []
    all_dates = set()
    results = defaultdict(lambda: {'MSSV': '', 'Name': '', 'Class': '', 'Status': defaultdict(lambda: 'Vắng')})

    if selected_class:
        selected_class_id = selected_class.split('-')[0].strip()  # Tách IDClass từ giá trị được chọn
        data = get_data(selected_class_id)
        for row in data:
            if results[row["IDenroll"]]['MSSV'] == '' :
                results[row["IDenroll"]]['MSSV'] = row["MSSV"]
                results[row["IDenroll"]]['Name'] = row["Name"]
                results[row["IDenroll"]]['Class'] = row["Class"]  
            if row["Status"]:
                results[row["IDenroll"]]['Status'][row["Status"]] = row["Status"]
                all_dates.add(row["Status"])
        all_dates = sorted(all_dates)
    return render_template('attendancedStudentUser.html', classes=classes, selected_class=selected_class, data=results, all_dates=all_dates)
@app.route('/download_csv')
def download_csv():
    selected_class = request.args.get('class')  # Lấy IDClass từ query params
    selected_class_id = selected_class.split('-')[0].strip()
    data = get_data(selected_class_id)
    
    # Chuẩn bị dữ liệu cho CSV
    results = defaultdict(lambda: {'MSSV': '', 'HoTen': '', 'Lop': '', 'Status': defaultdict(lambda: 'Vắng')})
    all_dates = set()
    
    for row in data:
        if results[row["IDenroll"]]['MSSV'] == '' :
            results[row["IDenroll"]]['MSSV'] = row["MSSV"]
            results[row["IDenroll"]]['Name'] = row["Name"]
            results[row["IDenroll"]]['Class'] = row["Class"]  
        if row["Status"]:
            results[row["IDenroll"]]['Status'][row["Status"]] = row["Status"]
            all_dates.add(row["Status"])
    
    all_dates = sorted(all_dates)
    
    # Tạo file CSV trong bộ nhớ
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Viết tiêu đề cột
    header = ['MSSV', 'Name', 'Class'] + all_dates
    writer.writerow(header)
    
    # Viết dữ liệu cho từng hàng
    for id, info in results.items():
        row = [info['MSSV'], info['Name'], info['Class']] + [info['Status'][date] for date in all_dates]
        writer.writerow(row)
    
    # Trả về file CSV
    output.seek(0)
    link_csv = selected_class + '.csv'
    return send_file(io.BytesIO(output.getvalue().encode('utf-8-sig')), 
                     mimetype='text/csv', 
                     download_name=link_csv, 
                     as_attachment=True)
@app.route('/FormAddTeacher')
def redirectAddTeacher():
    return render_template("AddTeacher.html")
@app.route('/register', methods=['GET', 'POST'])
def add_teacher():
    if request.method == 'POST':
        account = request.form['taikhoan']
        if CheckAccount(account):
            return render_template("AddTeacher.html", message="Trùng tài khoản")
        
        password = request.form['matkhau']
        hash_pass = hash_password(password)
        role = request.form['role']
        name = request.form['HoTen']
        age = request.form['Tuoi']
        sdt = request.form['SDT']
        
        connection = create_connection()
        if connection:
            try:
                cursor = connection.cursor()
                # Bắt đầu giao dịch
                connection.start_transaction()
                
                # Chèn vào bảng account
                cursor.execute("""
                    INSERT INTO account (Account, Password, Type)
                    VALUES (%s, %s, %s)
                """, (account, hash_pass, role))
                
                # Chèn vào bảng profile
                cursor.execute("""
                    INSERT INTO infor (Account, Name, Age, PhoneNumber)
                    VALUES (%s, %s, %s, %s)
                """, (account, name, age, sdt))
                
                # Xác nhận giao dịch
                connection.commit()
                cursor.close()
                return render_template("AddTeacher.html", success = "Thêm thành công")
            except mysql.connector.Error as err:
                print(f"Error: {err}")
                # Nếu có lỗi, hủy giao dịch
                connection.rollback()
                return render_template("AddTeacher.html", message="Đã có lỗi xảy ra. Vui lòng thử lại.")
            finally:
                connection.close()
    return render_template("AddTeacher.html", message = "Đã có lỗi xảy ra, xin thử lại")
@app.route('/ControllObject', methods=['GET', 'POST'])
def Controll():
    objectname = GetAccountAndName()
    action = request.form.get('action')
    if action == 'Button1':
        return redirect(url_for('show_teacher'))
    if action == 'Button2':
        selected_class = request.form.get('class')
        if selected_class:
            selected_class_account = selected_class.split('-')[0].strip()
            selected_class_Name = selected_class.split('-')[1].strip()
            return render_template("FormAddOrDel.html", Account = selected_class_account, Name = selected_class_Name,classes = objectname, type = "Add")
    if action == 'Button3':
        selected_class = request.form.get('class')
        if selected_class:
            selected_class_account = selected_class.split('-')[0].strip()
            selected_class_Name = selected_class.split('-')[1].strip()
            combo_box = ShowObjectOfTeacher(selected_class_account)
            return render_template("FormAddOrDel.html", Account = selected_class_account,content = combo_box, Name = selected_class_Name,classes = objectname, type = "Del")
    return render_template("FormAddOrDel.html", classes = objectname)
@app.route('/check_duplicate', methods=['POST'])
def check_duplicate():
    IDmonhoc = request.form['IDmonhoc']
    
    if check_Idclass(IDmonhoc) == 0:
        # Nếu IDmonhoc đã tồn tại, trả về một JSON object với thông báo lỗi
        return jsonify({'status': 'error', 'message': 'Mã môn học đã tồn tại'})
    else:
        # Nếu IDmonhoc không tồn tại, trả về một JSON object với thông báo thành công
        return jsonify({'status': 'successed', 'message': 'Thêm môn học thành công'})
@app.route('/AddObject', methods=['GET', 'POST'])
def add_object():
    account = request.form['taikhoan']
    name = request.form['Name']
    id_mon_hoc = request.form['IDmonhoc']
    ten_mon_hoc = request.form['Namemonhoc']
    time = request.form['Time']
    number_student = int(request.form['numberstudent'])
    mssvs = [request.form[f'mssv{i}'] for i in range(1, number_student + 1)]
    Add_Object(id_mon_hoc, account, name, ten_mon_hoc, time)
    for mssv in mssvs:
        Add_Student(id_mon_hoc,mssv)
    objectname = GetAccountAndName()
    return render_template("FormAddorDel.html", classes = objectname, response = "OK")
@app.route('/DeleteClass', methods=['GET', 'POST'])
def delete_class():
    account = request.form['taikhoan']
    name = request.form['Name']
    selected_class = request.form['class2']
    objectname = GetAccountAndName()
    if selected_class :
        selected_class_ID = selected_class.split('-')[0].strip()
        selected_class_ClassName = selected_class.split('-')[1].strip()
        DeleteClass(selected_class_ID)
        DeleteStatus(selected_class_ID)
        DeleteEnrollment(selected_class_ID)
        return render_template("FormAddorDel.html", classes = objectname, response2 = "OK")
@app.route('/ShowTeacher')
def show_teacher():
    df = get_classes()
    if df is not None:
        grouped_data = df.groupby('NameTeacher').apply(lambda x: x[['IDCLASS', 'ClassName']].to_dict('records')).to_dict()
        return render_template('ShowTeacher.html', data=grouped_data)
    else:
        return "Error fetching data"
if __name__ == "__main__":
    app.run(debug=True)
