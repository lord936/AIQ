from kivy.app import App
from kivy.uix.label import Clock, Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.screenmanager import Screen,ScreenManager
from kivy.properties import StringProperty, NumericProperty
import pandas as pd
import datetime
import database
from kivy.lang import Builder
from kivy.uix.popup import Popup
from kivy.core.window import Window
Window.size = (360,640)


class Dashboardscreen(Screen):
    pass

class Addsubjectscreen(Screen):
    pass

class Timetablescreen(Screen):
    pass

class Settingscreen(Screen):
    pass

class Manager(ScreenManager):
    overall_percentage_value = NumericProperty(0)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db=database.AttendenceDB()
        Clock.schedule_once(self.refresh_subjects)
        Clock.schedule_once(self.update_timetable)

        self.start_timer()
        self.popup_shown =False
        self.marked_today=self.db.marked_classes()
        self.finished=self.db.get_finished_clsses()
        Clock.schedule_interval(self.check_classes,1)
        
        
    

    def attendance_popup(self, subject):

        layout = BoxLayout(orientation="vertical", spacing=10, padding=10)

        label = Label(text=f"Did you attend {subject}?")

        buttons = BoxLayout(size_hint_y=0.4)

        present_btn = Button(text="Present")
        absent_btn = Button(text="Absent")

        buttons.add_widget(present_btn)
        buttons.add_widget(absent_btn)

        layout.add_widget(label)
        layout.add_widget(buttons)

        popup = Popup(
            title="Attendance",
            content=layout,
            size_hint=(0.6,0.4)
        )

        present_btn.bind(on_press=lambda x:self.mark_present(subject,popup))
        absent_btn.bind(on_press=lambda x:self.mark_absent(subject,popup))

        popup.open()


    def mark_present(self, subject, popup):

        self.db.present_subject(subject)

        popup.dismiss()

        self.refresh_subjects()


    def mark_absent(self, subject, popup):

        self.db.absent_subject(subject)

        popup.dismiss()

        self.refresh_subjects()


    def start_timer(self):
        Clock.schedule_interval(self.update_class,1)
        


    def add_subject(self, sub, attend=0, total=0):
        if attend=='':
            attend=0
        if total=='':
            total=0
        try:
            self.db.add_subject(sub,attend,total)
        except Exception as e:
            self.show_error(str(e))
        subjects = self.db.get_subjects()

        if sub in subjects:
            self.show_error("Subject already exists")
            return
        self.refresh_subjects()

    

    

        
    def present_subject(self,sub):
        self.db.present_subject(sub)
        self.refresh_subjects()



    def absent_subject(self,sub):
        self.db.absent_subject(sub)
        self.refresh_subjects()


  

    
    def import_timetable(self,csv):
        
        self.db.import_timetable(csv)
        
        self.update_timetable()


    def update_timetable(self,*args):
        container = self.get_screen("time_table").ids.timetable_container
        container.clear_widgets()
        timetable=self.db.get_timetable()
        for sub in timetable:
            card=BoxLayout(
                    orientation="vertical",
                    padding=10,
                    spacing=5,
                    size_hint_y=None,
                    height=140
                )

            title = Label(
                    text=sub[0],
                    font_size=20
                )
            day = Label(
                    text=sub[1],
                    font_size=20
            )
            time = Label(
                    text=sub[2],
                    font_size=20
                )
            buttons=BoxLayout(
                    size_hint_y=None,
                    height=40,
                    spacing=10

                )
            delete=Button(text="Delete")
            delete.bind(on_press=lambda x,s=sub[0],d=sub[1],t=sub[2]: self.delete_card(s,d,t))

            buttons.add_widget(delete)

            card.add_widget(title)
            card.add_widget(day)
            card.add_widget(time)
            card.add_widget(buttons)
            

            container.add_widget(card)




    def delete_card(self,s,d,t):
        self.db.delete_timetable(s,d,t)
        self.update_timetable()

        

    


    def subject_delete(self,sub):
        self.db.subject_delete(sub)
        self.refresh_subjects()



    def refresh_subjects(self,*args):

        container = self.get_screen("dashboard").ids.subject_container
        container.clear_widgets()

        subjects=self.db.get_subjects()

        for sub in subjects:

            a,t=self.db.get_subject_totals(sub)

            per = (a * 100 / t) if t != 0 else 0

            text = f"{sub}   {a}/{t}   {per:.1f}%"

            card=BoxLayout(
                orientation="vertical",
                padding=10,
                spacing=5,
                size_hint_y=None,
                height=140
            )

            title = Label(
                text=sub,
                font_size=20
            )


            bar = ProgressBar(
                max=100,
                value=per
            )
            stats = Label(
                text=f"{a}/{t}   {per:.1f}%"
            )
            buttons=BoxLayout(
                size_hint_y=None,
                height=40,
                spacing=10

            )

            present=Button(text="Present")
            absent=Button(text="Absent")
            delete=Button(text="Delete")

            present.bind(on_press=lambda x,s=sub:self.present_subject(s))
            absent.bind(on_press=lambda x,s=sub:self.absent_subject(s))
            delete.bind(on_press= lambda x,s=sub:self.subject_delete(s))

            buttons.add_widget(present)
            buttons.add_widget(absent)
            buttons.add_widget(delete)

            card.add_widget(title)
            card.add_widget(bar)
            card.add_widget(stats)
            card.add_widget(buttons)

            container.add_widget(card)
            self.update_overall()

    def update_overall(self,*args):

        container = self.get_screen("dashboard").ids.Overall_container
        container.clear_widgets()
        self.overall_percentage_value, a, t = self.db.overall_percentage()
        self.overall_text = f"{self.overall_percentage_value:.1f}% ({a}/{t})"

        container.add_widget(Label(
                text=self.overall_text,
                size_hint_y=None,
                height=80
            ))
        

    def update_class(self,dt):

        subject,time=self.db.get_next_class()

        if subject is None:
            text="no more classes today"

        else:
            countdown=self.db.get_countdown(time)
            seconds = countdown.total_seconds()

            # show popup when class started or after 5 minutes
            if -300 <= seconds <= 0 and not self.popup_shown:

                self.attendance_popup(subject)

                self.popup_shown = True

            text=f'Next: {subject} at {time} ({countdown})'

        Label=self.get_screen("dashboard").ids.next_class

        Label.text=text

    def add_time_table(self,s,d,st,et):
        if not self.valid_time(st):
            self.show_error("Invalid start time")
            return
        if not self.valid_time(et):
            self.show_error("Invalid End time")
            return
        time=st+'-'+et
        self.db.add_timetable(s,d,time)
        self.update_timetable()

    def check_classes(self,dt):
        
        for subject in self.finished:
           
            if subject not in self.marked_today:
                self.attendance_popup(subject)

                self.marked_today.add(subject)
    def reset_data(self):
        self.db.reset()
        self.refresh_subjects()
        self.update_timetable()
        self.update_overall()
        self.update_class(1)

    def show_error(self,message):

        Popup(
            title="Error",
            content=Label(text=message),
            size_hint=(0.6,0.4)
        ).open()
        
    def valid_time(self,t):
        try:
            datetime.datetime.strptime(t,'%H:%M')
            return True
        except:
            return False
        
    def report_issue(self):

        Popup(
            title="Feedback",
            content=Label(text="Tell Lord what is issue"),
            size_hint=(0.6,0.4)
        ).open()

kv = Builder.load_file("aiq.kv")

class AIQapp(App):
    def build(self):
        return kv
AIQapp().run()
