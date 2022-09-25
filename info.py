from requests import Session
from bs4 import BeautifulSoup


def createSoup(subdomain, url, session: Session):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.114 YaBrowser/22.9.1.1095 Yowser/2.5 Safari/537.36"
    }
    getInfo = session.post(url=url, data=None, headers=headers)
    soup = BeautifulSoup(getInfo.text, 'lxml')
    return soup


def getInfo(subdomain, session: Session):
    url = f"https://{subdomain}.eljur.ru/journal-user-preferences-action"

    soup = createSoup(subdomain, url, session)
    if "error" in soup:
        return soup

    label = None
    info = {}
    for tag in soup.find_all(["label", "span"], class_=["ej-form-label", "control-label"]):
        if tag.contents[0] == "СНИЛС":
            break

        if tag.name == "label":
            label = tag.contents[0]
            info.update([(label, None)])

        if tag.name == "span":
            info[label] = tag.contents[0]

    return info


def getJournal(subdomain, session: Session):
    url = f"https://{subdomain}.eljur.ru/journal-app"

    soup = createSoup(subdomain, url, session)
    if "error" in soup:
        return soup

    info = {}
    for day in soup.find_all("div", class_="dnevnik-day"):
        title = day.find("div", class_="dnevnik-day__title")
        week, date = title.contents[0].strip().replace("\n", "").split(", ")

        if day.find("div", class_="page-empty"):
            info.update([(week, {"date": date, "isEmpty": True, "comment": "Нет уроков", "lessons": {}})])
            continue

        if day.find("div", class_="dnevnik-day__holiday"):
            info.update([(week, {"date": date, "isEmpty": True, "comment": "Выходной", "lessons": {}})])
            continue

        lessons = day.find_all("div", class_="dnevnik-lesson")
        lessonsDict = {}
        if lessons:
            for lesson in lessons:
                lessonNumber = lesson.find("div", class_="dnevnik-lesson__number")
                if lessonNumber:
                    lessonNumber = lessonNumber.contents[0].replace("\n", "").strip()[:-1]

                lessonName = lesson.find("span", class_="js-rt_licey-dnevnik-subject").contents[0]

                lessonHomeTask = lesson.find("div", class_="dnevnik-lesson__task")
                if lessonHomeTask:
                    lessonHomeTask = lessonHomeTask.contents[2].replace("\n", "").strip()

                lessonMark = lesson.find("div", class_="dnevnik-mark")
                if lessonMark:
                    lessonMark = lessonMark.contents[1].attrs["value"]

                lessonsDict.update([(lessonNumber, {"name": lessonName,
                                                    "hometask": lessonHomeTask,
                                                    "mark": lessonMark})])

            info.update([(week, {"date": date, "isEmpty": False, "comment": "Выходной", "lessons": lessonsDict})])

    return info