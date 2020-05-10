import requests
import re
import settings

class Aresort:

    #salary
    KIND_OF_SALARY = 0
    NUM_OF_SALARY = 1
    SALARY = 2

    HOME_URL = settings.AR_HOME_URL

    def __init__(self, soup, dtlLink):
        self.soup = soup
        self.dtlLink = dtlLink
        self.__urlNum = re.search(r"(\d+)", self.dtlLink)
        self.__strSoup = str(self.soup)

    def title(self):
        return self.soup.title.string

    def place(self):
        return re.search(r"<th>勤務地<\/th>\s*<td>([\s\S]*?)<\/td>", self.__strSoup)[1]

    def occupation(self):
        return re.search(r"<h3>([\s\S]*?)<\/h3>", self.__strSoup)[1]

    def term(self):
        return re.search(r"<th>期間<\/th>\s*<td>([\s\S]*?)<\/td>", self.__strSoup)[1]

    def salary(self, request):
        """Get salaries and process it to classify by type

        Args:
            request (int): type of salary
        Returns:
            mixed: processed salary
        """

        salary = re.search(r"<th>給与<\/th>\s*<td>([\s\S]*?)(円[\s\S]*?)<\/td>", self.__strSoup)
        salary = ("KindOfSalary無し" if request == Aresort.KIND_OF_SALARY
            else int(salary[1].replace(',', "")) if request == Aresort.NUM_OF_SALARY
            else "時給" + salary[1] + salary[2] if request == Aresort.SALARY
            else NULL)
        return salary

    def dormitory(self):
        return "TRUE" if ("/assets/resort/pc/images/page/resort/view/kodawari_icon2.jpg" in self.__strSoup) else "FALSE"

    def picture(self):
        picture = re.search(r"<div id=\"fv\">\s*<img[\s\S]*?src=\"([\s\S]*?)\"", self.__strSoup)
        return Aresort.HOME_URL + picture[1]

    def time(self):
        return self.__normalization(self.__get_time())

    def treatment(self):
        return self.__normalization(self.__get_treatment_info())

    def jobDesc(self):
        return re.search(r"<th>仕事内容<\/th>\s*<td colspan=\"3\">([\s\S]*?)<\/td>", self.__strSoup)[1]

    def permaLink(self):
        return "detail-alpha-" + str(self.__urlNum[1])

    def meal(self):
        return self.__normalization(self.__get_meal_info())

    def wifi(self):
        return "TRUE" if ("/assets/resort/pc/images/page/resort/view/kodawari_icon8.jpg" in self.__strSoup) else "FALSE"

    def spa(self):
        return "TRUE" if ("/assets/resort/pc/images/page/resort/view/kodawari_icon6.jpg" in self.__strSoup) else "FALSE"

    def transportationFee(self):
        return "TRUE" if ("交通費支給" in self.__strSoup) else "FALSE"

    def affiliateLink(self):
        return "https://px.a8.net/svt/ejp?a8mat=2HQA4W+4NAW2Y+39C6+BW8O2&a8ejpredirect=https%3A%2F%2Fwww.a-resort.jp%2Fresort%2Fankens%2Fview%2F%3Fid%3D" + str(self.__urlNum[1])

    def campaign(self):
        return "TRUE"

    def company(self):
        return "a-resort"

    def __get_time(self):
        """Get information from 'お仕事詳細情報'

        Returns:
            str: information of the time for working
        """

        # 勤務時間があるか検索
        targetValue = ""
        kindOfElement = "勤務時間"
        headElement = "<tr>\s*?<th rowspan=\"([0-9]*?)\" scope=\"row\">" + kindOfElement + "<\/th>\s*?<td (class=)?([\s\S]*?)colspan=\"[0-9]*?\">\s*?([\s\S]*?)<\/td>\s*?<\/tr>"
        addElement = "\s*?<tr>\s*?<td (class=)?([\s\S]*?)colspan=\"[0-9]*?\">\s*?([\s\S]*?)<\/td>\s*?<\/tr>"
        getDataElement = "<td [class=]?[\s\S]*colspan=\"[0-9]*\">\s*([\s\S]*)<\/td>"
        newLine = "[\s\S]*"
        result = re.search(r"<tr>\s*?<th rowspan=\"([0-9]*?)\" scope=\"row\">" + kindOfElement + r"<\/th>\s*?<td (class=)?([\s\S]*?)colspan=\"[0-9]*?\">\s*?([\s\S]*?)<\/td>\s*?<\/tr>", self.__strSoup)

        if (result):
            addCountForHead = addCountForData = addCountForValue = int(result[1]) - 1
            entireElement = headElement
            getAllDataElement = getDataElement

            # （rowspanの数-1）分の正規表現を足す
            while addCountForHead > 0:
                addCountForHead += -1
                entireElement += addElement

            # 仕事内容の中身を取得
            getArrayValues = re.search(r"" + entireElement + r"", self.__strSoup)
            getValue = getArrayValues[0]

            # （rowspanの数-1）分の正規表現を足す
            while addCountForData > 0:
                addCountForData += -1
                getAllDataElement += newLine + getDataElement
            dataValues = re.search(r"" + getAllDataElement + r"", getValue)

            targetValue = dataValues.group(1)
            # （rowspanの数-1）分のマッチオブジェクトがあれば<br>で繋ぐ
            if (addCountForValue > 0):
                while addCountForValue > 0:
                    targetValue += "<br>" + dataValues.group(addCountForValue + 1)
                    addCountForValue += -1
        return targetValue

    def __get_treatment_info(self):
        """Get information from '福利厚生'

        Returns:
            str: description of welfare
        """

        targetValue = ""
        elementName = []
        elementNames = ["交通費", "社会保険", "特典"]

        # searchして取得した各属性をtargetValueに格納
        for elementName in elementNames:
            getElement = r"<th scope=\"row\">" + elementName + r"<\/th>\s*?<td>\s*?([\s\S]*?)<\/td>"
            result = re.search(getElement, self.__strSoup)
            if (result):
                targetValue += elementName + "：" + result.group(1)
        return targetValue

    def __get_meal_info(self):
        """Get information of '食事支給'
        ①「有」で数字が「1」の場合はTRUE
        ② 「有」で数字が「2」の場合かつ「備考」に「円」が含まれていない場合はTRUE
        ③それ以外はFALSE
        """

        targetValue = "FALSE"
        headElement = "<th rowspan=\"([0-9]*?)\" scope=\"row\">食事支給<\/th>\s*?<td( class=\"text-center br_dot\")?( style=\"width: 30px;\")?>\s*?([\s\S]*?)\s*?<\/td>"
        addElement = "[\s\S]*?<td class=\"br_dot\">備考<\/td>\s*?<td colspan=\"[0-9]*?\">([\s\S]*?)<\/td>[\s\S]*?ネット環境"
        remarksElement = headElement + addElement

        # 取得
        headResult = re.search(headElement, self.__strSoup)
        remarksResult = re.search(remarksElement, self.__strSoup)

        if ((headResult.group(1).strip() == 1 and headResult.group(4).strip() == "有"
            or int(headResult.group(1).strip()) >= 2 and headResult.group(4).strip() == "有" and not ("円" in remarksResult.group(5).strip()))):
            return "TRUE"
        else:
            return "FALSE"

    def __normalization(self, text):
        """
        Do some texts to normalize

        Args:
            text (str): scraped texts
        Returns:
            str: normalized texts
        """

        # Add regex when it needs
        regexs = ['<span>|</span>', '\s{2,}', '^\n']
        for regex in regexs:
            text = re.sub(regex, '', text)
        return text