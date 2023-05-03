import os
import re
import sqlite3 as sql
from typing import Union, Iterable

class Poll:
    def __init__(self ,id ,title, options : list, creator : "User", vote_counts : list = [], active : bool = 1) -> None:
        self.id = id
        self.title = title
        self.options : list = options
        self.vote_counts : list = vote_counts
        if self.vote_counts == []:
            for i in range(len(self.options)):
                self.vote_counts.append(0)
        self.creator : User = creator
        self.active : bool = active
    
    def vote(self, option_num : int) -> None:
        self.vote_counts[option_num-1] = self.vote_counts[option_num-1] + 1
        db = DatabaseManager()
        db.add_vote(self.id, self.vote_counts)

    def set_active(self, active: bool) -> None:
        self.active = active
        db = DatabaseManager()
        db.set_active(active)

class User:
    def __init__(self, email : str, password : str) -> None:
        self.email = email
        self.password = password
    
    def SignUp(self, email : str, password : str) -> "User":
        db = DatabaseManager()
        CurrentUser = User(email, password)
        db.add_user(CurrentUser)    
        return CurrentUser
    
    def SignIn(self, email: str, password : str) -> "User":
        db = DatabaseManager()
        db.cursor.execute(f"SELECT * FROM users WHERE user_email = '{email}' AND user_password = '{password}'")
        usratrs = db.cursor.fetchall()
        db.db.commit()
        CurrentUser = User(usratrs[0][0], usratrs[0][1])
        return CurrentUser
    
    def add_poll(self, title: str, options : list) -> None:
        db = DatabaseManager()
        db.cursor.execute(f"SELECT poll_id FROM polls")
        ids = db.cursor.fetchall()
        db.db.commit()
        if len(ids) == 0:
            id = 1
            db.add_poll(Poll(id, title, options, self.email))
        else:
            
            id = int(ids.pop()[0]) + 1
            db.add_poll(Poll(id, title, options, self.email))

class DatabaseManager:
    def __init__(self) -> None:
        self.db : sql.Connection = sql.connect('Polls.db')
        self.cursor : sql.Cursor = self.db.cursor() 
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS users 
                (user_email TEXT UNIQUE,
                user_password TEXT)
            """)
        self.cursor.execute("""CREATE TABLE IF NOT EXISTS polls
                (poll_id INT,
                poll_title TEXT,
                poll_options TEXT,
                poll_vote_counts TEXT,
                poll_creator TEXT,
                poll_active INT)
            """)
        self.db.commit()
    
    def add_user(self, user : User) -> None:
        self.cursor.execute("INSERT INTO users VALUES (?,?)", (user.email, user.password))
        self.db.commit()
    
    def add_poll(self, poll : Poll) -> None:
        self.cursor.execute("INSERT INTO polls VALUES (?,?,?,?,?,?)", (poll.id, poll.title, str(poll.options), str(poll.vote_counts), poll.creator, poll.active))
        self.db.commit()

    def add_vote(self, poll_id : int, vote_counts : list) -> None:
        vote_counts = str(vote_counts)
        self.cursor.execute(f"UPDATE polls SET poll_vote_counts='{vote_counts}' WHERE poll_id={poll_id}")
        self.db.commit()

    def get_items(self, table : str) -> list:
        options = ["users", "polls"]
        if table not in options: 
            raise AttributeError("Inavlid Table Name")
        self.cursor.execute(f"SELECT * FROM {table}")
        items = self.cursor.fetchall()
        for i in range(len(items)):
            items[i] = list(items[i])
        final_list = []
        if table == "users":
            for i in items:
                user = User(i[0], i[1])
                final_list.append(user)
        elif table == "polls":
            for i in items:
                poll = Poll(id=i[0], title=i[1], options=eval(i[2]), vote_counts=eval(i[3]), creator=i[4], active=i[5])
                final_list.append(poll)
        return final_list
    
    def get_poll(self, id : int) -> Poll:
        self.cursor.execute(f"SELECT * FROM polls WHERE poll_id={int(id)}")
        items = self.cursor.fetchall()
        items[0] =  list(items[0])
        poll = Poll(id=items[0][0], title=items[0][1], options=eval(items[0][2]), vote_counts=eval(items[0][3]), creator=items[0][4], active=items[0][5])
        return poll
    
    def get_created_polls_by_user(self, creator : str) -> Poll: 
        self.cursor.execute(f"SELECT * FROM polls WHERE poll_creator = '{creator}'")
        items = self.cursor.fetchall()
        self.db.commit()
        for i in range(len(items)):
            items[i] = list(items[i])
        polls = []
        for i in items:
            poll = Poll(id=i[0], title=i[1], options=eval(i[2]), vote_counts=eval(i[3]), creator=i[4], active=i[5])
            polls.append(poll)
        return polls
    
    def set_active(self, id : int, active : bool) -> None:
        active = 1 if active else 0
        self.cursor.execute(f"""UPDATE polls SET poll_active = {active}
                WHERE poll_id = {id}
                """)
        self.db.commit()
    
    def validate_user(self, email : str, password : Union[str, None]) -> bool:  
        email_stat = False
        self.cursor.execute("SELECT user_email FROM users")
        items = self.cursor.fetchall()
        for i in range(len(items)):
            items[i] = items[i][0]
        self.db.commit()
        if email in items: 
            email_stat = True
        if not password:
            return email_stat
        if not email_stat:
            return False
        self.cursor.execute("SELECT user_password FROM users")
        items = self.cursor.fetchall()
        for i in range(len(items)):
            items[i] = items[i][0]
        self.db.commit()
        if password in items:
            return True
        else:
            return False
    
    def delete_poll(self, poll_id:str) -> None:
        self.cursor.execute(f"DELETE FROM polls WHERE poll_id={str(poll_id)}")
        self.db.commit()

    def get_options(self, poll_id:str) -> list:
        self.cursor.execute(f"SELECT poll_options FROM polls WHERE poll_id='{str(poll_id)}'")
        options = eval(self.cursor.fetchall()[0][0])
        self.db.commit()
        return options

class Session:
    def __init__(self) -> None:
        self.current_user : User = User("guest", "guest")
        self.db = DatabaseManager()

    def clear(self) -> None:
        os.system("clear")

    def run(self) -> None:
        while True:
            if self.current_user.email == "guest":
                x = int(input("""1. Signup
2. Login
Enter your option: """))
                if x == 1:
                    while True:
                        email=input("email: ")
                        password = input("password: ")
                        retyped_pass = input("retype password: ")
                        password_pattern = r'^(?=.*[A-Z])(?=.*[\W_])(?=.*[0-9a-z]).{8,}$'
                        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                        if not self.db.validate_user(email, None) and password == retyped_pass and re.match(password_pattern, password) and re.match(email_pattern, email):
                            self.current_user = self.current_user.SignUp(email, password)
                            print("Signed up successfully.")
                            break
                        else:
                            self.clear()
                            print("This email is registered or isn't in correct pattern or your password dont match or isnt strong")
                            if input("Continue? ").lower() == "yes":
                                continue
                            else:
                                self.clear()
                                break
                elif x == 2:
                    while True:
                        self.clear()
                        username = input("Enter your email: ")
                        password = input("Enter your password: ")
                        if self.db.validate_user(username, password):
                            self.current_user = self.current_user.SignIn(username, password)
                            break
                        else:
                            self.clear()
                            print("Your username or password are incorrect.")
                            if input("Continue? ").lower() == "yes":
                                continue
                            else:
                                self.clear()
                                break
            else:
                self.clear()
                while True:
                    x = int(input("""1. Create a new poll
2. List of polls
3. Participate in a poll
4. Delete your poll
5. Activate or deactivate your poll
6. Poll results
7. List of your polls
8. Exit\n"""))
                    if x == 1:
                        self.clear()
                        title = input("Title :")
                        optionsnum = int(input("Number of options :"))
                        options = []
                        for i in range(optionsnum):
                            options.append(input(f"option {i+1}: "))
                        self.current_user.add_poll(title, options)
                        print("Created")
                        self.clear()

                    elif x == 2:
                        self.clear()
                        polls : Iterable[Poll]= self.db.get_items("polls")
                        for i in polls:
                            print(f"{i.id} : {i.title}")
                        y = input()
                        self.clear()
                    
                    elif x == 3:
                        self.clear()
                        id = int(input("Enter poll id: "))
                        options = self.db.get_options(id)
                        for i in range(len(options)):
                            print(f"{i+1}. {options[i]}")
                        vote = int(input("Your vote: "))
                        poll = self.db.get_poll(id)
                        poll.vote(vote)
                        input("submitted.")
                        self.clear()

                    elif x == 4:
                        self.clear()
                        id = input("Enter your poll id: ")
                        poll = self.db.get_poll(id)
                        if self.current_user.email == poll.creator:
                            self.db.delete_poll(id)
                            print('Deleted')
                            input()
                            self.clear()
                        else:
                            print("This poll isnt yours.")
                            input()
                            self.clear()

                    elif x == 5:
                        self.clear()
                        id = input("Enter your poll id: ")
                        poll = self.db.get_poll(id)
                        if self.current_user.email == poll.creator:
                            if poll.active:
                                self.db.set_active(id, False)
                                print('Deactivated')
                            else:
                                self.db.set_active(id, True)
                                print('Activated')
                            input()
                            self.clear()
                        else:
                            print("This poll isnt yours.")
                            input()
                            self.clear()

                    elif x == 6:
                        self.clear()
                        id = input("Enter your poll id: ")
                        poll = self.db.get_poll(id)
                        for i in range(len(poll.options)):
                            print(f"{i+1}. {poll.options[i]} ---> {str(poll.vote_counts[i])}")
                        input()
                        self.clear()

                    elif x == 7:
                        self.clear()
                        polls = self.db.get_created_polls_by_user(self.current_user.email)
                        for i in polls:
                            active_stat = "active" if i.active else "deactive"
                            print(f"{i.id}. {i.title} ({active_stat})")
                        input()
                        self.clear()

                    elif x == 8:
                        self.clear()
                        exit()


                    
if __name__=="__main__":
    session = Session()
    session.run()