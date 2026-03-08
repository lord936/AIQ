import csv
import datetime
import sqlite3

class AttendenceDB():
    def __init__(self,db_name="attendence.db"):
        self.conn=sqlite3.connect(db_name)
        self.cursor=self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects(
            subject TEXT PRIMARY KEY,
            attended INTEGER,
            total INTEGER
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS records(
            subject TEXT,
            day TEXT,
            type TEXT
        )
        """)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS timetable(
            subject TEXT,
            day TEXT,
            time TEXT
        )
        """)

        self.conn.commit()


    def add_subject(self,sub,attend=0,total=0):
        
        self.cursor.execute(
            "INSERT OR IGNORE INTO subjects VALUES (?,?,?)",
            (sub,attend,total)
        )
        self.conn.commit()
    




        
    def present_subject(self,sub):
        today=datetime.date.today()

        self.cursor.execute(
            "INSERT OR IGNORE INTO records VALUES(?,?,?)",
            (sub,today,"present")
        )
        self.conn.commit()



    def absent_subject(self,sub):
        today=datetime.date.today()


        self.cursor.execute(
            "INSERT OR IGNORE INTO records VALUES (?,?,?)",
            (sub,today,"absent")
        )
        self.conn.commit()
    
    def get_subject_totals(self,sub):
        
        self.cursor.execute(
            "SELECT attended,total FROM subjects WHERE subject=?",
            (sub,)
        )
        row=self.cursor.fetchone()
        if row is None:
            return 0,0
        a,t=row

        self.cursor.execute(
            "SELECT type FROM records WHERE subject=?",
            (sub,)
        )
        records=self.cursor.fetchall()
        for r in records:
            if r[0]=="present":
                a+=1
            t+=1
        return a,t
    
    def get_overall_totals(self):
        al,tl=0,0
        self.cursor.execute(
            "SELECT attended,total FROM subjects"
        )
        row=self.cursor.fetchall()
        for r in row:
            al+=r[0]
            tl+=r[1]
        
        self.cursor.execute(
            "SELECT type FROM records"
        )

        records=self.cursor.fetchall()

        for r in records:
            if r[0]=="present":
                al+=1
            tl+=1
        return al,tl

    def csv_to_list_of_dicts(self,filename):
        data = []
        try:
            with open(filename, mode='r', newline='', encoding='utf-8') as csvfile:
                # Create a DictReader object
                reader = csv.DictReader(csvfile)
                # Iterate over each row and append to the list
                for row in reader:
                    data.append(row)
        except FileNotFoundError:
            print(f"Error: The file {filename} was not found.")
        except Exception as e:
            print(f"An error occurred: {e}")
        return data
        
    def import_timetable(self,csv):
        if csv[0]=='"' and csv[-1]=='"' :
            csv=csv[1:-1]
        #tim=input('enter time table path')
        df=self.csv_to_list_of_dicts(csv)
        for j in df:
            for i in j.keys():

                if i=="Day":
                    d=j[i]
                else:
                    subjects=self.get_subjects()
                    if j[i] not in ['LIBRARY','SPORTS','NONE'] :
                        if j[i] not in subjects:
                            self.add_subject(j[i])
                            s=j[i]
                        self.cursor.execute(
                            "INSERT INTO timetable VALUES (?,?,?)",
                            (j[i],d,i)
                        )
        self.conn.commit()
        


    def delete_timetable(self,s,d,t):
        self.cursor.execute(
            "DELETE FROM timetable WHERE subject=? AND day=? AND time=?",
            (s,d,t)
        )
        self.conn.commit()

    def overall_percentage(self):
        
        al,tl=self.get_overall_totals()
        
        return al*100/tl if tl!=0 else 0,al,tl
    

    def subject_percentage(self,sub):
        a,t=self.get_subject_totals(sub)

        return a*100/t if t!=0 else 0,a,t
    


    def get_subject_status(self,sub,threshold):
            
        a,t=self.get_subject_totals(sub)
        
        if t!=0:
            per=a*100/t
        if per >=threshold+5:
            return 'safe'
        elif per>=threshold:
            return 'warning'
        else:
            return 'critical'
        

    def get_recovery_classes(self,threshold):
        al,tl=self.get_overall_totals()
        
        per=0
        recovery=0
        if tl !=0:
            per=al*100/tl
            while per<threshold:
                a=al+recovery
                t=tl+recovery
                per=a*100/t
                recovery+=1
        return recovery


    def subject_delete(self,sub):
        
        self.cursor.execute(
            "DELETE FROM subjects WHERE subject=?",
            (sub,)
        )

        self.cursor.execute(
            "DELETE FROM records WHERE subject=?",
            (sub,)
        )

        self.conn.commit()


    def weekly_summary(self):
        today=datetime.date.today()

        start_of_week=today-datetime.timedelta(days=today.weekday())

        end_of_week=start_of_week+datetime.timedelta(days=6)

        a,t,p=0,0,0
        self.cursor.execute(
            "SELECT day,type FROM records"
        )
        records=self.cursor.fetchall()
        for i in records:
            if i[0]>=start_of_week and i[0]<=end_of_week:
                if i[1]=='present':
                    p+=1
                else:
                    a+=1
        t=p+a

        dit={
            "week_start": start_of_week,
            "week_end": end_of_week,
            "total_classes": t,
            "present": p,
            "absent": a
        }

        return dit
    
    def get_timetable(self):
        self.cursor.execute("SELECT * FROM timetable")

        return self.cursor.fetchall()


    def  get_subjects(self):
        self.cursor.execute("SELECT subject FROM subjects")

        return [s[0] for s in self.cursor.fetchall()]
    
    def add_timetable(self, subject, day, time):

        self.cursor.execute(
            "INSERT INTO timetable VALUES (?, ?, ?)",
            (subject, day, time)
        )

        self.conn.commit()


    def get_time_now(self):

        now=datetime.datetime.now()

        day=now.strftime('%A')
        time=now.strftime('%H:%M')

        return day,time
    
    def get_next_class(self):

        day,current_time=self.get_time_now()

        self.cursor.execute(
            "SELECT subject,time FROM timetable WHERE day=? ORDER BY time",
            (day,)
        )
        row=self.cursor.fetchall()

        for s,t in row:
            if t.split("-")[0]>current_time:
                return s,t
        return None,None
    
    def get_countdown(self,time_str):
        
        now = datetime.datetime.now()
        start_time = time_str.split("-")[0]
        print(now,start_time)

        class_time = datetime.datetime.strptime(start_time,"%H:%M")

        class_time = now.replace(
            hour=class_time.hour,
            minute=class_time.minute,
            second=0
        )


        remaining=class_time-now

        return remaining
    
    def get_today_classes(self):

        today=datetime.datetime.now().strftime('%A')

        self.cursor.execute(
            "SELECT subject,time FROM timetable WHERE day=?",
            (today,)
        )
        return self.cursor.fetchall()
    
    def get_finished_clsses(self):

        now=datetime.datetime.now().time()

        classes=self.get_today_classes()

        finished=[]

        for sub,time in classes:
            end_time=datetime.datetime.strptime(time.split('-')[1],'%H:%M').time()

            if now >end_time:
                finished.append(sub)
        return finished
    
    def marked_classes(self):

        
        today=datetime.date.today()

        self.cursor.execute(
            "SELECT subject FROM records WHERE day=?",
            (today,)
        )
        row=self.cursor.fetchall()
        marked=set()
        for r in row:
            marked.add(r[0])

        return marked
    
    def reset(self):
        self.cursor.execute(
            "DELETE FROM subjects"
        )

        self.cursor.execute("DELETE FROM records")

        self.cursor.execute("DELETE FROM timetable")

        self.conn.commit()