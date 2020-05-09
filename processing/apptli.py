import requests
import re
import settings

class Apptli:

    #salary
    KIND_OF_SALARY = 0
    NUM_OF_SALARY = 1
    SALARY = 2

    HOME_URL = settings.AP_HOME_URL

    def __init__(self, soup, dtlLink):
        self.soup = soup
        self.dtlLink = dtlLink
        self.__urlNum = re.search(r"(\d+)", self.dtlLink)
        self.__strSoup = str(self.soup)

    def title(self):
        return self.soup.title.string

    def place(self):
        place = re.search(r"<span class=\"heading-list-txt_place\">\s*?<a href=\"[\s\S]*?\">([\s\S]*?)<\/a>\s*?<a href=\"[\s\S]*?\">([\s\S]*?)<\/a>", self.__strSoup)
        return place[1] + " " + place[2]

    def occupation(self):
        return re.search(r"<span class=\"detailJobSummaryList__ttlTxt\">職種<\/span>\s*?<\/dt>\s*?<dd class=\"detailJobSummaryList__desc\">\s*?<span class=\"detailJobSummaryList__descTxt\">\s*?<a href=\"[\s\S]*?\">([\s\S]*?)<\/a>", self.__strSoup)[1]

    def term(self):
        return re.search(r"<span class=\"detailJobSummaryList__ttlTxt\">期間<\/span>\s*?<\/dt>\s*?<dd class=\"detailJobSummaryList__desc\">\s*?<span class=\"detailJobSummaryList__descTxt\">([\s\S]*?)<\/span>", self.__strSoup)[1]

    def salary(self, request):
        """Get salaries and process it to classify by type

        Args:
            request (int): type of salary
        Returns:
            mixed: processed salary
        """

        salary = re.search(r"<span class=\"detailJobSummaryList__ttlTxt\">(時給|日給|月給)<\/span>\s*?<\/dt>\s*?<dd class=\"detailJobSummaryList__desc\">\s*?<span class=\"detailJobSummaryList__descTxt\">([\s\S]*?)(円[\s\S]*?)<\/span>", self.__strSoup)
        salary = (salary[1] if request == Apptli.KIND_OF_SALARY
            else int(salary[2].replace(',', "")) if request == Apptli.NUM_OF_SALARY
            else salary[1] + salary[2] + salary[3] if request == Apptli.SALARY
            else NULL)
        return salary

    def dormitory(self):
        dormitory = re.search(r"<span class=\"detailJobSummaryList__ttlTxt\">寮<\/span>\s*?<\/dt>\s*?<dd class=\"detailJobSummaryList__desc\">\s*?<span class=\"detailJobSummaryList__descTxt\">([\s\S]*?)<\/span>", self.__strSoup)
        return "TRUE" if ("個室" in dormitory[1]) else "FALSE"

    def picture(self):
        picture = re.search(r"<div class=\"list carousel-item\"><img[\s\S]*?src=\"([\s\S]*?)\"", self.__strSoup)
        return Apptli.HOME_URL + picture[1]

    def time(self):
        return re.search(r"<span class=\"detailJobSummaryList__ttlTxt\">勤務時間<\/span>\s*?<\/dt>\s*?<dd class=\"detailJobSummaryList__desc\">\s*?<span class=\"detailJobSummaryList__descTxt\">([\s\S]*?)<\/span>", self.__strSoup)[1]

    def treatment(self):
        return re.search(r"<span class=\"detailJobSummaryList__ttlTxt\">待遇<\/span>\s*?<\/dt>\s*?<dd class=\"detailJobSummaryList__desc\">\s*?<span class=\"detailJobSummaryList__descTxt\">([\s\S]*?)<\/span>", self.__strSoup)[1]

    def jobDesc(self):
        return re.search(r"<span class=\"detailJobContent__txt\">([\s\S]*?)<\/span>", self.__strSoup)[1]

    def permaLink(self):
        return "detail-apptli-" + str(self.__urlNum[1])

    def meal(self):
        return "TRUE" if re.search(r"<span class=\"detailJobSummaryList__descTxt\">[\s\S]*?食事無料[\s\S]*?<div class=\"detailJobDetailOuter\">", self.__strSoup) else "FALSE"

    def wifi(self):
        return "TRUE" if ("<span class=\"detailJobTraitList__txt\">ネット利用可</span>" in self.__strSoup) else "FALSE"

    def spa(self):
        return "TRUE" if ("<span class=\"detailJobTraitList__txt\">温泉利用可</span>" in self.__strSoup) else "FALSE"

    def transportationFee(self):
        return "TRUE" if re.search(r"<span class=\"detailJobSummaryList__descTxt\">[\s\S]*?光熱費無料[\s\S]*?<div class=\"detailJobDetailOuter\">", self.__strSoup) else "FALSE"

    def affiliateLink(self):
        return "https://hataraku.com/work/detail?work_id=" + str(self.__urlNum[1])

    def campaign(self):
        return "TRUE"

    def company(self):
        return "apptli"