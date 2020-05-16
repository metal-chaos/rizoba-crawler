import requests
import re

class Humanic:

    # private room
    NO_PRIVATE_ROOM = "FALSE"
    PRIVATE_ROOM = "TRUE"

    #salary
    KIND_OF_SALARY = 0
    NUM_OF_SALARY = 1
    SALARY = 2

    def __init__(self, soup, dtlLink):
        self.soup = soup
        self.dtlLink = dtlLink
        self.__urlNum = re.search(r"(\d+)", self.dtlLink)
        self.__strSoup = str(self.soup)

    def title(self):
        return self.soup.title.string

    def place(self):
        return re.search(r"<dt class=\"item_info_term\">\s*勤務地\s*<\/dt>\s*<dd class=\"item_info_description\">\s*(.*)\s*<\/dd>", self.__strSoup)[1]

    def term(self):
        return re.search(r"<dt class=\"item_info_term\">\s*期間\s*<\/dt>\s*<dd class=\"item_info_description\">\s*(.*)\s*<\/dd>", self.__strSoup)[1]

    def occupation(self):
        return re.search(r"<dt class=\"item_info_term\">\s*職種\s*<\/dt>\s*<dd class=\"item_info_description\">\s*<span class=\"selector_job\">\s*(.*)\s*<\/span>", self.__strSoup)[1]

    def dormitory(self):
        dormitory = re.search(r"<dt class=\"item_info_term\">\s*寮の種類\s*<\/dt>\s*<dd class=\"item_info_description\">\s*(.*)\s*<\/dd>", self.__strSoup)
        return Humanic.PRIVATE_ROOM if ("個室" in dormitory[1]) else Humanic.NO_PRIVATE_ROOM

    def salary(self, request):
        """Get salaries and process it to classify by type

        Args:
            request (int): type of salary
        Returns:
            mixed: processed salary
        """

        salary = re.search(r"<dt class=\"item_info_term\">\s*(時給|日給|月給)\s*<\/dt>\s*<dd class=\"item_info_description\">\s*(.*)(円)\s*<\/dd>", self.__strSoup)
        salary = (salary[1] if request == Humanic.KIND_OF_SALARY
            else salary[2] if request == Humanic.NUM_OF_SALARY
            else salary[1] + salary[2] + "円" if request == Humanic.SALARY
            else NULL)
        return salary

    def picture(self):
        return re.search(r"<span class=\"item_slide_image\">\s*<img alt=\"[\s\S]*?\" src=\"([\s\S]*?)\"", self.__strSoup)[1]

    def time(self):
        return re.search(r"<dd class=\"item_info_description work_time_unit\">\s*([\s\S]*?)\s*<\/dd>", self.__strSoup)[1]

    def treatment(self):
        return re.search(r"<dt class=\"item_info_term\">\s*福利厚生\s*<\/dt>\s*<dd class=\"item_info_description\">\s*([\s\S]*?)\s*<\/dd>", self.__strSoup)[1]

    def jobDesc(self):
        return re.search(r"<dt class=\"item_info_lead_term\">\s*仕事内容\s*<\/dt>\s*<dd class=\"item_info_lead_description\">\s*([\s\S]*?)\s*<\/dd>", self.__strSoup)[1]

    def permaLink(self):
        return "detail-humanic-" + str(self.__urlNum[1])

    def meal(self):
        return "TRUE" if ("食費無料" in self.__strSoup) else "FALSE"

    def wifi(self):
        return "TRUE" if ("食費無料" in self.__strSoup) else "FALSE"

    def spa(self):
        return "TRUE" if ("item_merit skin_merit_m2_16" in self.__strSoup) else "FALSE"

    def transportationFee(self):
        return "TRUE" if ("交通費支給" in self.__strSoup) else "FALSE"

    def affiliateLink(self):
        return "https://px.a8.net/svt/ejp?a8mat=2ZJJHC+5VYEGA+42GS+BW8O2&a8ejpredirect=https%3A%2F%2Fwww.rizoba.com%2Fwork%2F" + str(self.__urlNum[1]) + "%2F"

    def campaign(self):
        return "FALSE"

    def company(self):
        return "humanic"