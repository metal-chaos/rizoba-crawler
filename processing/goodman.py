import requests
import re
import settings

class Goodman:

    #salary
    KIND_OF_SALARY = 0
    NUM_OF_SALARY = 1
    SALARY = 2

    HOME_URL = settings.GD_HOME_URL

    def __init__(self, soup, dtlLink):
        self.soup = soup
        self.dtlLink = dtlLink
        self.__urlNum = re.search(r"(\d+)", self.dtlLink)
        self.__strSoup = str(self.soup)

    def title(self):
        return self.soup.title.string

    def place(self):
        place = re.search(r"<dl class=\"conditions\">[\s\S]*?<dt>勤務地<\/dt>[\s\S]*?<dd>([\s\S]*?)・([\s\S]*?)<\/dd>", self.__strSoup)
        return place[1] + " " + place[2]

    def occupation(self):
        return re.search(r"<dl class=\"conditions\">[\s\S]*?<dt>職種<\/dt>[\s\S]*?<dd>([\s\S]*?)<\/dd>", self.__strSoup)[1]

    def term(self):
        return re.search(r"<dl class=\"conditions\">[\s\S]*?<dt>働く期間<\/dt>[\s\S]*?<dd>([\s\S]*?)<\/dd>", self.__strSoup)[1]

    def salary(self, request):
        """Get salaries and process it to classify by type

        Args:
            request (int): type of salary
        Returns:
            mixed: processed salary
        """

        salary = re.search(r"<dl class=\"conditions\">[\s\S]*?<dt>給与<\/dt>[\s\S]*?<dd>([\s\S]*?)<\/dd>", self.__strSoup)
        salaryFigure = re.search(r"[\s\S]*?(\d+)[\s\S]*?", str(salary[1].replace(',', "")))
        salary = (salary[1] if request == Goodman.KIND_OF_SALARY
            else salaryFigure[1] if request == Goodman.NUM_OF_SALARY
            else salary[1] if request ==  Goodman.SALARY
            else NULL)
        return salary

    def dormitory(self):
        return "TRUE" if (re.search(r"<ul class=\"icon\">[\s\S]*?<li><img alt=\"\" src=\"\/images\/icon\/option\/op09\.png\"\/>", self.__strSoup)) else "FALSE"

    def picture(self):
        return re.search(r"<div class=\"photo\">\s*<img[\s\S]*?src=\"([\s\S]*?)\"", self.__strSoup)[1]

    def time(self):
        return re.search(r"<dl class=\"conditions\">[\s\S]*?<dt>勤務時間<\/dt>[\s\S]*?<dd>([\s\S]*?)<\/dd>", self.__strSoup)[1]

    def treatment(self):
        return re.search(r"<dl class=\"conditions\">[\s\S]*?<dt>待遇<\/dt>[\s\S]*?<dd>([\s\S]*?)<\/dd>", self.__strSoup)[1]

    def jobDesc(self):
        return re.search(r"<dl class=\"conditions\">[\s\S]*?<dt>仕事内容<\/dt>[\s\S]*?<dd>([\s\S]*?)<\/dd>", self.__strSoup)[1]

    def permaLink(self):
        return "detail-goodman-" + str(self.__urlNum[1])

    def meal(self):
        return "TRUE" if (re.search(r"<ul class=\"icon\">[\s\S]*?<li><img alt=\"\" src=\"\/images\/icon\/option\/op05\.png\"\/>", self.__strSoup)) else "FALSE"

    def wifi(self):
        return "TRUE" if (re.search(r"<ul class=\"icon\">[\s\S]*?<li><img alt=\"\" src=\"\/images\/icon\/option\/op22\.png\"\/>", self.__strSoup)) else "FALSE"

    def spa(self):
        return "TRUE" if (re.search(r"<ul class=\"icon\">[\s\S]*?<li><img alt=\"\" src=\"\/images\/icon\/option\/op19\.png\"\/>", self.__strSoup)) else "FALSE"

    def transportationFee(self):
        return "TRUE" if (re.search(r"<ul class=\"icon\">[\s\S]*?<li><img alt=\"\" src=\"\/images\/icon\/option\/op07\.png\"\/>", self.__strSoup)) else "FALSE"

    def affiliateLink(self):
        return "https://px.a8.net/svt/ejp?a8mat=2TOVB0+BE7QWA+3OHQ+BW8O2&a8ejpredirect=http%3A%2F%2Fwww.resortbaito.com%2F" + str(self.__urlNum[1])

    def campaign(self):
        return "TRUE"

    def company(self):
        return"goodman"