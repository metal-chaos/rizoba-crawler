import constant

class Main:

    def make_processing(self, processing):
        datas = {}

        # タイトル
        datas['title'] = processing.title()

        # 勤務地
        datas['place'] = processing.place()

        # 職種
        datas['occupation'] = processing.occupation()

        # 勤務期間
        datas['term'] = processing.term()

        # 給与の種類
        datas['kindOfSalary'] = processing.salary(constant.KIND_OF_SALARY)
        # 給与（数値）
        datas['numOfSalary'] = processing.salary(constant.NUM_OF_SALARY)
        # 給与（掲載用）
        datas['salary'] = processing.salary(constant.SALARY)

        # 個室
        datas['dormitory'] = processing.dormitory()

        # 画像
        datas['picture'] = processing.picture()

        # 勤務時間
        datas['time'] = processing.time()

        # 待遇
        datas['treatment'] = processing.treatment()

        # 仕事内容
        datas['jobDesc'] = processing.jobDesc()

        # パーマリンク
        datas['permaLink'] = processing.permaLink()

        # 食事
        datas['meal'] = processing.meal()

        # wifi
        datas['wifi'] = processing.wifi()

        # 温泉
        datas['spa'] = processing.spa()

        # 交通費支給
        datas['transportationFee'] = processing.transportationFee()

        # アフィリエイトリンク付与
        datas['affiliateLink'] = processing.affiliateLink()

        # キャンペーン
        datas['campaign'] = processing.campaign()

        # 会社
        datas['company'] = processing.company()

        return datas