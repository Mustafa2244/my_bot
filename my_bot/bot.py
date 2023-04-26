import os.path
import pickle
import shutil
import zipfile
from collections import UserDict
import re
import datetime
from fuzzywuzzy import fuzz


class Field:
    def __init__(self, value=None):
        self.value = None
        self.set_value(value)

    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value


class Name(Field):
    def __init__(self, name):
        super().__init__(name)


class Phone(Field):
    def __init__(self, phone_number=None):
        super().__init__(phone_number)

    def set_value(self, value):
        try:
            self.value = int(value)
        except Exception:
            self.value = None
            return None


class Birthday(Field):
    def __init__(self, birthday_date: str = None):
        super().__init__(birthday_date)

    def set_value(self, value: str):
        if len(value) == 5 and re.match(r'\d\d.\d\d', value):
            try:
                new_value = value + ".24"
                datetime.datetime.strptime(new_value, "%d.%m.%y").date()
            except:
                return None
            self.value = value
        else:
            return None


class Address(Field):
    def __init__(self, address: str = None):
        super().__init__(address)


class Email(Field):
    def __init__(self, email: str = None):
        super().__init__(email)

    def set_value(self, value):
        if re.match(r'^([a-z0-9_-]+\.)*[a-z0-9_-]+@[a-z0-9_-]+(\.[a-z0-9_-]+)*\.[a-z]{2,6}$', value):
            self.value = value
        else:
            self.value = None


class Record:
    def __init__(self, name: Name, phones: list[Phone] = [], address: Address = None, email: Email = None,
                 birthday: Birthday = None):
        self.name = name
        self.phones = phones
        self.address = address
        self.email = email
        self.birthday = birthday

    def add_phone(self, phone: Phone):
        self.phones.append(phone)

    def remove_phone(self, phone_number):
        for my_phone in self.phones:
            if my_phone.get_value() == phone_number:
                self.phones.remove(my_phone)

    def update_phone(self, old_phone, new_phone):
        for my_phone in self.phones:
            if my_phone.get_value() == old_phone:
                my_phone.set_value(new_phone)

    def set_address(self, address: str):
        if self.address:
            self.address.set_value(address)
        else:
            self.address = Address(address)

    def set_birthday(self, birthday: str):
        if self.birthday:
            self.birthday.set_value(birthday)
        else:
            self.birthday = Birthday(birthday)

    def days_to_birthday(self):
        if self.birthday.get_value():
            plus_year = 0
            while True:
                try:
                    birthday = datetime.datetime.strptime(self.birthday.get_value()+".24", "%d.%m.%y").replace(
                        year=datetime.datetime.today().year + plus_year,
                        hour=0,
                        minute=0,
                        second=0,
                        microsecond=0
                    )
                    break
                except:
                    plus_year += 1
            if (birthday - datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)).days < 0:
                new_birthday = datetime.datetime.strptime(
                    self.birthday.get_value(), "%d.%m"
                ).replace(
                    year=datetime.datetime.today().year + 1,
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0
                )
                days = (new_birthday - datetime.datetime.today().replace(
                    hour=0, minute=0, second=0, microsecond=0)).days
            else:
                days = (birthday - datetime.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)).days
            return days
        else:
            return None

    def set_email(self, email: str):
        if self.email:
            self.email.set_value(email)
        else:
            self.email = Email(email)


class AddressBook(UserDict):
    def add_record(self, record: Record):
        self.data[record.name.get_value()] = record

    def del_record(self, name: str):
        self.data.pop(name)

    def iterator(self, n):
        for i in range(0, len(self.data.keys()), n):
            yield [{key: value} for key, value in
                   zip(list(self.data.keys())[i:i + n], list(self.data.values())[i:i + n])]

    def birthday_in_days(self, days: int):
        result = []
        for record in self.data.values():
            if record.days_to_birthday() == days:
                result.append(record)
        return result

    def search(self, search_word: str):
        search_word = search_word.lower()
        result = []
        for record in self.data.values():
            if search_word in record.name.get_value().lower():
                if record not in result:
                    result.append(record)
            for phone in record.phones:
                if search_word in str(phone.get_value()).lower():
                    if record not in result:
                        result.append(record)
            if record.address.get_value():
                if search_word in record.address.get_value().lower():
                    if record not in result:
                        result.append(record)
            if record.email.get_value():
                if search_word in record.email.get_value():
                    if record not in result:
                        result.append(record)
        return result

    def save(self, filepath="address_book.pkl"):
        if not os.path.exists(os.path.expanduser(r"~\bot\saves")):
            os.mkdir(os.path.expanduser(r"~\bot\saves"))
        pickle.dump(
            self.data,
            open(os.path.join(os.path.expanduser(r"~\bot\saves"), filepath), "wb"),
            protocol=pickle.HIGHEST_PROTOCOL
        )

    def load(self, filepath="address_book.pkl"):
        if os.path.exists(os.path.join(os.path.expanduser(r"~\bot\saves"), filepath)):
            self.data = pickle.load(open(os.path.join(os.path.expanduser(r"~\bot\saves"), filepath), "rb"))


class Note:
    def __init__(self, note_name: str, tags: list[str] = []):
        if not os.path.exists(os.path.expanduser(r"~\bot\notes")):
            os.mkdir(os.path.expanduser(r"~\bot\notes"))
        self.name = note_name
        self.tags = None
        self.set_tags(tags)
        self.filepath = os.path.join(os.path.expanduser(r"~\bot\notes"), f"{note_name}.txt")

    def set_tags(self, tags: list[str]):
        self.tags = tags

    def get_tags(self):
        return self.tags

    def write_note(self, lines: list[str]):
        with open(self.filepath, "w", encoding="utf-8") as file:
            file.writelines(lines)

    def read_note(self):
        with open(self.filepath, "r", encoding="utf-8") as file:
            return file.read()

    def change_name(self, new_name):
        self.name = new_name

    def del_note(self):
        os.remove(self.filepath)


class NoteBook(UserDict):
    def add_note(self, note: Note):
        self.data[note.name] = note

    def search(self, search_word: str):
        result = []
        for note in self.data.values():
            if search_word.lower() in " ".join(note.tags):
                if note not in result:
                    result.append(note)
                    continue
            if search_word.lower() in note.read_note().lower():
                if note not in result:
                    result.append(note)
        return result

    def search_by_tags(self, search_word: str):
        result = []
        for note in self.data.values():
            if search_word.lower() in " ".join(note.tags):
                result.append(note)
        return result

    def del_note(self, note_name):
        self.data[note_name].del_note()
        self.data.pop(note_name)

    def save(self, filepath="note_book.pkl"):
        if not os.path.exists(os.path.expanduser(r"~\bot\saves")):
            os.mkdir(os.path.expanduser(r"~\bot\saves"))
        pickle.dump(
            self.data,
            open(os.path.join(os.path.expanduser(r"~\bot\saves"), filepath), "wb"),
            protocol=pickle.HIGHEST_PROTOCOL
        )

    def load(self, filepath="note_book.pkl"):
        if os.path.exists(os.path.join(os.path.expanduser(r"~\bot\saves"), filepath)):
            self.data = pickle.load(open(os.path.join(os.path.expanduser(r"~\bot\saves"), filepath), "rb"))


class Sorter:
    def __init__(self):
        self.filepath = ""
        self.lat_letters = "abcdefghijklmnopqrstuvwxyz1234567890"
        self.translit = {
            "а": "a",
            "б": "b",
            "в": "v",
            "г": "g",
            "д": "d",
            "е": "e",
            "ё": "yo",
            "ж": "zh",
            "з": "z",
            "и": "i",
            "й": "j",
            "к": "k",
            "л": "l",
            "м": "m",
            "н": "n",
            "о": "o",
            "п": "p",
            "р": "r",
            "с": "s",
            "т": "t",
            "у": "u",
            "ф": "f",
            "х": "h",
            "ц": "ts",
            "ч": "ch",
            "ш": "sh",
            "щ": "sch",
            "ь": "'",
            "ъ": "''",
            "ы": "y",
            "э": "e",
            "ю": "yu",
            "я": "ya"
        }
        self.files_groups = {
            "images": [],
            "video": [],
            "documents": [],
            "audio": [],
            "archives": [],
            "others": []
        }
        self.known_extensions = {
            "images": ["jpeg", "png", "jpg", "svg"],
            "video": ["avi", "mp4", "mov", "mkv"],
            "documents": ["doc", "docx", "txt", "pdf", "xlsx", "pptx"],
            "audio": ["mp3", "ogg", "wav", "amr"],
            "archives": ["zip", "gz", "tar"]
        }
        self.white_list_dir = ["images", "video", "documents", "audio", "archives"]
        self.known_extensions_in_folder = []
        self.unknown_extensions_in_folder = []

    def check_folder(self, path: str):
        if path.split("\\")[-1] not in self.white_list_dir:
            for item in os.listdir(path):
                if os.path.isfile(os.path.join(path, item)):
                    if item.split(".")[-1] in self.known_extensions["images"]:
                        if item.split(".")[-1] not in self.known_extensions_in_folder:
                            self.known_extensions_in_folder.append(item.split(".")[-1])
                        self.files_groups["images"].append(os.path.join(path, item))
                    elif item.split(".")[-1] in self.known_extensions["video"]:
                        if item.split(".")[-1] not in self.known_extensions_in_folder:
                            self.known_extensions_in_folder.append(item.split(".")[-1])
                        self.files_groups["video"].append(os.path.join(path, item))
                    elif item.split(".")[-1] in self.known_extensions["documents"]:
                        if item.split(".")[-1] not in self.known_extensions_in_folder:
                            self.known_extensions_in_folder.append(item.split(".")[-1])
                        self.files_groups["documents"].append(os.path.join(path, item))
                    elif item.split(".")[-1] in self.known_extensions["audio"]:
                        if item.split(".")[-1] not in self.known_extensions_in_folder:
                            self.known_extensions_in_folder.append(item.split(".")[-1])
                        self.files_groups["audio"].append(os.path.join(path, item))
                    elif item.split(".")[-1] in self.known_extensions["archives"]:
                        if item.split(".")[-1] not in self.known_extensions_in_folder:
                            self.known_extensions_in_folder.append(item.split(".")[-1])
                        self.files_groups["archives"].append(os.path.join(path, item))
                    else:
                        if item.split(".")[-1] not in self.unknown_extensions_in_folder:
                            self.unknown_extensions_in_folder.append(item.split(".")[-1])
                        self.files_groups["others"].append(os.path.join(path, item))
                else:
                    self.check_folder(os.path.join(path, item))

    def normalize(self, filename):
        translit_filename = ""
        for letter in "".join(filename.split(".")[:-1]):
            if letter.lower() in self.translit.keys():
                if letter.islower():
                    cur_letter = self.translit[letter]
                else:
                    cur_letter = self.translit[letter.lower()].upper()
            elif letter.lower() not in self.lat_letters:
                cur_letter = "_"
            else:
                cur_letter = letter
            translit_filename += cur_letter
        translit_filename += "." + filename.split(".")[-1]
        return translit_filename

    def images(self, imgs):
        for img in imgs:
            new_filename = self.normalize(img.split("\\")[-1])
            if not os.path.exists(os.path.join(self.filepath, "images")):
                os.mkdir(os.path.join(self.filepath, "images"))
            shutil.move(img, os.path.join(self.filepath, "images", new_filename))

    def documents(self, docs):
        for doc in docs:
            new_filename = self.normalize(doc.split("\\")[-1])
            if not os.path.exists(os.path.join(self.filepath, "documents")):
                os.mkdir(os.path.join(self.filepath, "documents"))
            shutil.move(doc, os.path.join(self.filepath, "documents", new_filename))

    def audio(self, musics):
        for music in musics:
            new_filename = self.normalize(music.split("\\")[-1])
            if not os.path.exists(os.path.join(self.filepath, "audio")):
                os.mkdir(os.path.join(self.filepath, "audio"))
            shutil.move(music, os.path.join(self.filepath, "audio", new_filename))

    def video(self, videos):
        for vid in videos:
            new_filename = self.normalize(vid.split("\\")[-1])
            if not os.path.exists(os.path.join(self.filepath, "video")):
                os.mkdir(os.path.join(self.filepath, "video"))
            shutil.move(vid, os.path.join(self.filepath, "video", new_filename))

    def archives(self, archive):
        for arc in archive:
            new_filename = self.normalize(arc.split("\\")[-1])
            new_filename = "".join(new_filename.split(".")[:-1])
            zip_file = zipfile.ZipFile(arc)
            if not os.path.exists(os.path.join(self.filepath, "archives")):
                os.mkdir(os.path.join(self.filepath, "archives"))
            zip_file.extractall(os.path.join(self.filepath, "archives", new_filename))

    def sort(self, filepath: str):
        result = ""
        self.filepath = filepath
        self.check_folder(self.filepath)
        result += "Known extension in folder:\n"
        result += "     " + ", ".join(self.known_extensions_in_folder) + "\n"
        result += "Unknown extension in folder:\n"
        result += "     " + ", ".join(self.unknown_extensions_in_folder) + "\n"
        self.images(self.files_groups["images"])
        self.documents(self.files_groups["documents"])
        self.audio(self.files_groups["audio"])
        self.video(self.files_groups["video"])
        self.archives(self.files_groups["archives"])
        result += "Files was sorted successfully"
        return result


def main():
    commands = [
        "hello",
        "add record",
        "show all telephones",
        "birthday in days",
        "search record",
        "update record",
        "delete record",
        "add note",
        "search note",
        "delete note",
        "sort",
        "exit",
        "close",
        "good bye"
    ]

    if not os.path.exists(os.path.expanduser(r"~\bot")):
        os.mkdir(os.path.expanduser(r"~\bot"))
    address_book = AddressBook()
    note_book = NoteBook()
    sorter = Sorter()
    address_book.load()
    note_book.load()
    while True:
        command = input().lower()
        try:
            if command == "hello":
                print("How can I help you?")
            elif command == "add record":
                print("Enter Name")
                name = input()
                print("Enter Phone numbers (if there are more than 1 number enter through space)")
                phones = []
                while not phones:
                    phone_numbers = input().split(" ")
                    for phone in phone_numbers:
                        my_phone = Phone(phone)
                        if my_phone.get_value():
                            phones.append(my_phone)
                        else:
                            print(f"Phone number: {phone} is incorrect. Please enter numbers again.")
                            break
                print("Enter Address (optional)")
                address = input()
                print("Enter Email (optional)")
                email = None
                while email is None:
                    my_email = input()
                    if Email(my_email).get_value() or my_email == '':
                        email = Email(my_email)
                    else:
                        print(f"Email: {my_email} is incorrect. Please enter email again")
                print("Enter Birthday (dd.mm) (optional)")
                birthday = None
                while birthday is None:
                    my_birthday = input()
                    if Birthday(my_birthday).get_value() or my_birthday == '':
                        birthday = Birthday(my_birthday)
                    else:
                        print(f"Birthday: {my_birthday} is incorrect. Please enter birthday again")
                address_book.add_record(Record(
                    Name(name),
                    phones,
                    Address(address),
                    email,
                    birthday
                ))
                print("Record was added successfully")
            elif command == "show all telephones":
                for record in address_book.values():
                    print(
                        f"{record.name.get_value()}:\n"
                        f"{'_'*40}\n"
                        f"Phone numbers: {', '.join([str(phone.get_value()) for phone in record.phones])}\n"
                        f"Address: {record.address.get_value()}\n"
                        f"Email: {record.email.get_value()}\n"
                        f"Birthday: {record.birthday.get_value()}\n"
                        f"{'_'*40}"
                    )
            elif command == "birthday in days":
                print("Enter count of days")
                days = int(input())
                for record in address_book.birthday_in_days(days):
                    print(
                        f"{record.name.get_value()}:\n"
                        f"{'_' * 40}\n"
                        f"Phone numbers: {', '.join([str(phone.get_value()) for phone in record.phones])}\n"
                        f"Address: {record.address.get_value()}\n"
                        f"Email: {record.email.get_value()}\n"
                        f"Birthday: {record.birthday.get_value()}\n"
                        f"{'_' * 40}"
                    )
            elif " ".join(command.split(" ")[:2]) == "search record":
                print("Enter search request: ")
                request = " ".join(command.split(" ")[2:])
                for record in address_book.search(request):
                    print(
                        f"{record.name.get_value()}:\n"
                        f"{'_' * 40}\n"
                        f"Phone numbers: {', '.join([str(phone.get_value()) for phone in record.phones])}\n"
                        f"Address: {record.address.get_value()}\n"
                        f"Email: {record.email.get_value()}\n"
                        f"Birthday: {record.birthday.get_value()}\n"
                        f"{'_' * 40}"
                    )
            elif command == "update record":
                print("Now you has this contacts in address book:")
                for name in address_book:
                    print(name)
                print("Enter which contact you want to update (enter name)")
                contact_name = ""
                try:
                    contact_name = input()
                    record = address_book[contact_name]
                except KeyError:
                    print(f"No contact with name: {contact_name}")
                    continue
                print(
                    f"{record.name.get_value()}:\n"
                    f"{'_' * 40}\n"
                    f"Phone numbers: {', '.join([str(phone.get_value()) for phone in record.phones])}\n"
                    f"Address: {record.address.get_value()}\n"
                    f"Email: {record.email.get_value()}\n"
                    f"Birthday: {record.birthday.get_value()}\n"
                    f"{'_' * 40}"
                )
                print("Which field do you want to change: ")
                print("1. Phone numbers")
                print("2. Address")
                print("3. Email")
                print("4. Birthday")
                print("5. Exit")
                while True:
                    field = input()
                    try:
                        if int(field) not in range(1, 6):
                            print("Please choose option")
                        else:
                            field = int(field)
                            break
                    except:
                        print("Enter number of option")
                if field == 1:
                    print("Enter number that you want to change")
                    for i, number in enumerate(record.phones, start=1):
                        print(f"{i}. {number.get_value()}")
                    number = int(input())
                    print("Enter new number")
                    new_number = None
                    while new_number is None:
                        num = input()
                        if Phone(num).get_value():
                            new_number = num
                            record.update_phone(record.phones[number - 1].get_value(), new_number)
                        else:
                            if num == "":
                                record.remove_phone(record.phones[number - 1].get_value())
                                break
                            else:
                                print(f"Phone number: {num} is incorrect. Please enter number again.")
                elif field == 2:
                    print("Enter new address: ")
                    address = input()
                    record.set_address(address)
                elif field == 3:
                    print("Enter new email")
                    email = None
                    while email is None:
                        my_email = input()
                        if Email(my_email).get_value() or my_email == '':
                            email = my_email
                        else:
                            print(f"Email: {my_email} is incorrect. Please enter email again")
                    record.set_email(email)
                elif field == 4:
                    print("Enter new birthday")
                    birthday = None
                    while birthday is None:
                        my_birthday = input()
                        if Birthday(my_birthday).get_value() or my_birthday == '':
                            birthday = my_birthday
                        else:
                            print(f"Birthday: {my_birthday} is incorrect. Please enter birthday again")
                    record.set_birthday(birthday)
                elif field == 5:
                    continue
                print("Record was successfully updated")
            elif command == "delete record":
                print("Now you has this contacts in address book:")
                for name in address_book:
                    print(name)
                print("Enter which contact you want to delete (enter name)")
                contact_name = ""
                try:
                    contact_name = input()
                    _ = address_book[contact_name]
                except KeyError:
                    print(f"No contact with name: {contact_name}")
                    continue
                address_book.del_record(contact_name)
                print("Record wos successfully deleted")
            elif command == "add note":
                print("Enter name of note")
                note_name = input()
                print("Enter tags of note through space (optional)")
                tags = input()
                if tags:
                    tags = tags.split(" ")
                    my_note = Note(note_name, tags)
                else:
                    my_note = Note(note_name)
                print("Enter text of note (to finish typing click enter on new line)")
                my_lines = []
                while True:
                    line = input()
                    if not line:
                        break
                    my_lines.append(line + "\n")
                my_note.write_note(my_lines)
                note_book.add_note(my_note)
                print("Note was successfully written")
            elif " ".join(command.split(" ")[:2]) == "search note":
                search = note_book.search(" ".join(command.split(" ")[2:]))
                for note in search:
                    print(
                        f"{'#' * 40}\n"
                        f"Note name: {note.name}\n"
                        f"Tags: {', '.join(note.tags)}\n"
                        f"Text:\n"
                        f"{'_' * 40}\n"
                        f"{note.read_note()}"
                        f"{'_' * 40}"
                    )
            elif command == "delete note":
                print("Now you has this notes in note book:")
                for note in note_book:
                    print(note)
                print("Enter which contact you want to delete (enter note name)")
                note_name = ""
                try:
                    note_name = input()
                    _ = note_book[note_name]
                except KeyError:
                    print(f"No note with name: {note_name}")
                    continue
                note_book.del_note(note_name)
            elif command.split(" ")[0] == "sort":
                print(sorter.sort(command.split(" ")[1]))
            elif command == "exit" or command == "close" or command == "good bye" or command == ".":
                print("Good bye!")
                break
            else:
                last_per = 0
                last_command = ""
                for comm in commands:
                    if fuzz.WRatio(comm, command) > last_per:
                        last_per = fuzz.WRatio(comm, command)
                        last_command = comm
                print(f"Command *{command}* not found. Maybe you mean *{last_command}*")
        except:
            print("Something wrong!")
    address_book.save()
    note_book.save()
