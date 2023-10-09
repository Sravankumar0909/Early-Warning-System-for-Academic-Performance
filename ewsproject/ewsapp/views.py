from django.shortcuts import render
from django.http import HttpResponse
import sqlite3
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
from email.message import EmailMessage
import ssl
import smtplib
# Create your views here.
import joblib
from io import BytesIO
import re
from django.shortcuts import redirect




def logout(request):
    # Perform any custom logout logic here, if needed
    # For example, you can clear session data, revoke tokens, etc.
    request.session.clear()
    # Then, redirect the user to a specific page
    return redirect('home')  # Redirect to the login page or any other page you prefer



def retrieve():
    global loaded_model
    conn = sqlite3.connect('ews.db')
    try:
        cursor = conn.cursor()
        query = "SELECT model_blob FROM model WHERE model_name = ? AND id = ?"
        cursor.execute(query, ('Random Forest', 1))
        result = cursor.fetchone()

        if result:
            model_binary = result[0]
            model_file = BytesIO(model_binary)
            loaded_model = joblib.load(model_file)
        else:
            print("Model not found in the database.")
    finally:
        cursor.close()
        conn.close()
from django.urls import reverse
def home(request):
    return render(request, 'login.html')
def login(request):
    db_file_path = r'C:\Users\srava\Documents\Python\ews.db'
    conn = sqlite3.connect(db_file_path)
    cursor = conn.cursor()
    retrieve = """select username from users;"""
    cursor.execute(retrieve)
    dbuser = cursor.fetchall()
    retrieve = """select password from users;"""
    cursor.execute(retrieve)
    dbpwd = cursor.fetchall()
    cursor.close()
    conn.close()
    user = request.POST.get('username','')
    pwd = request.POST.get('password','')
    if user==dbuser[0][0] and pwd==dbpwd[0][0]:
        return render(request, 'user.html')
    else:
        return HttpResponse('''<h1 style='text-align:center'>Username or password is wrong<br>Try again logging in.</h1>''')
def predict(request):
    global df
    df = pd.DataFrame()
    retrieve()
    if request.method == 'POST':
        attendance_file = request.FILES['attendance_file']
        try:
            df1 = pd.read_csv(attendance_file)
            df['HallTicket'] = None
            df['HallTicket'].fillna(0, inplace=True)
            df = pd.merge(df1, df, on = 'HallTicket', how = "outer")
            df.fillna(0, inplace=True)

            subject_files = request.FILES.getlist('subject_files')
            for subject_file in subject_files:
                df1 = pd.read_csv(subject_file)
                Internal = df1.filter(regex=re.compile('internal', re.IGNORECASE))
                External = loaded_model.predict(Internal)
                HallTicket = df1.filter(regex=re.compile('HallTicket', re.IGNORECASE))
                Credits = df1['Credits']
                new_df = pd.concat([HallTicket, Internal, Credits, pd.DataFrame({'External':External})], axis = 1)
                new_df['External'+df1.loc[0,'Ref Code']] = new_df['Internal']+new_df['External']
                x = 'External'+df1.loc[0,'Ref Code']
                del new_df['External']
                del new_df['Internal']
                if 'HallTicket' in df.columns:
                    df = pd.merge(df, new_df, on = ['HallTicket'], how= "outer")
                else:
                    df['HallTicket'] = None
                    df = pd.merge(df, new_df, on='HallTicket', how='outer')
                df = df.fillna(0)
                for index, row in df.iterrows():
                    if df.loc[index, x]>40:
                        df.loc[index, 'Credits achieved'] += df.loc[index,'Credits']
                        df.loc[index, 'Total Credits'] += df.loc[index,'Credits']
                    else:
                        df.loc[index, 'Total Credits'] += df.loc[index,'Credits']
                del df['Credits']
                html_data = df.to_html(index=False).strip()
                response = HttpResponse(html_data)
            return render(request, 'mail.html', {'predictions':html_data})
        except Exception:
             return HttpResponse('''<h1 style='text-align:center'>Something went wrong. <br>Please try again uploading files with correct format<h1>''')
    return HttpResponse('''<h1 style='text-align:center'>Upload CSV files<h1>''')
def mail(request):
    global df
    list_of_students_subjects = []
    list_of_students_attendance = []
    list_of_students_credits = []
    for index, row in df.iterrows():
        list_of_subjects = []
        student_mail = row['Student email']  
        credits_criteria = (df.loc[index, 'Credits achieved']/df.loc[index, 'Total Credits'])*100
        for column in df.columns:
            if 'External' in column and row[column] < 50:
                list_of_subjects.append(column[8:])
                

        if len(list_of_subjects) > 0:
            list_of_students_subjects.append(row['HallTicket'])

        email_receiver = student_mail.strip()
        subject = 'Academic Report'
        if len(list_of_subjects) == 0 and row['Attendance'] > 70 and credits_criteria>60:
            body = """ Maintain the same pace and try to improve more """
        elif len(list_of_subjects) == 0 and row['Attendance'] <= 70 and credits_criteria>60:
            list_of_students_attendance.append(row['HallTicket'])
            body = f"Your attendance percentage is low."
        elif len(list_of_subjects) > 0 and row['Attendance'] <= 70 and credits_criteria>60:
            list_of_students_attendance.append(row['HallTicket'])
            output = '\n'.join(map(str, list_of_subjects))
            body = f"You are weak in the following subjects. Try to improve more in the following subjects:\n{output}\nYour attendance percentage is low. Your current attendance is {row['Attendance']}"
        elif len(list_of_subjects)>0 and row['Attendance'] > 70 and credits_criteria<60:
                list_of_students_credits.append(row['HallTicket'])
                output = '\n'.join(map(str, list_of_subjects))
                body = f"Chances of getting detended if failed in any subjects. Try to improve more in the following subjects:\n{output}"
        elif len(list_of_subjects)>0 and row['Attendance']<=70 and credits_criteria<60:
                list_of_students_attendance.append(row['HallTicket'])
                list_of_students_credits.append(row['HallTicket'])
                output = '\n'.join(map(str,list_of_subjects))
                body = f"Chances of getting detended due to lack of attendance and credits.\nTry to improve more in the following subjects\n{output}\nYour attendance percentage is {row['Attendance']}"
        elif len(list_of_subjects)>0 and row['Attendance']>70 and credits_criteria>60:
                output = '\n'.join(map(str, list_of_subjects))
                body = f"Try to improve more in the following subjects\n{output}"
        else:
                list_of_students_attendance.append(row['HallTicket'])
                body = f"Your attendance percentage is low. Your current attendance is {row['Attendance']}"
        try:
            email_sender = '20eg110103@gmail.com'
            email_password = 'botz cmlr hqsl mcsj'
            em = EmailMessage()
            em['From'] = email_sender
            em['To'] = email_receiver
            em['Subject'] = subject
            em.set_content(body)
            context = ssl.create_default_context()

            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
                    smtp.login(email_sender, email_password)
                    smtp.sendmail(email_sender, email_receiver, em.as_string())
        except Exception:
             return HttpResponse('''<h1 style='text-align:center'>Something went wrong. Please try again<h1>''')
    try:
        subject = "Academic Report"
        output1 = '\n'.join(map(str, list_of_students_attendance))
        output2 = '\n'.join(map(str, list_of_students_subjects))
        output3 = '\n'.join(map(str, list_of_students_credits))
        body = f"The following students are in the list of low attendance with\nHallTicket Numbers \n{output1} \nThe following students are in the list of low marks in subjects\nHallTicket Numbers\n{output2}\nThe following students are having low credits\nHallTicket\n{output3}"
        email_receiver = df.loc[0,'Incharge email']
        em1 = EmailMessage()
        em1['From'] = email_sender
        em1['To'] = df.loc[0,'Incharge email']           #df1.loc[0,'Incharge email']
        em1['Subject'] = subject
        em1.set_content(body)
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
                smtp.login(email_sender, email_password)
                smtp.sendmail(email_sender, df.loc[0,'Incharge email'].strip(), em1.as_string())
    except Exception:
         return HttpResponse('''<h1 style='text-align:center'> Something went wrong. Please try again</h1>''')
    return HttpResponse('''<h1 style='text-align:center'>Sent Mails Successfully</h1>''')

