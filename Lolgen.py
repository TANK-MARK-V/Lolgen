import random as rn
import pymorphy3

import sys
import io
import sqlite3
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow

import designs

# Импортируем нужные библиотеки

morph = pymorphy3.MorphAnalyzer()  # Создаём представитель класса pymorthy для анализа и склонения слов


def getting():  # Функция для считывания слов из БД
    con = sqlite3.connect("DataBase.sqlite")
    cur = con.cursor()
    pril = cur.execute('''SELECT word FROM Massive
                                  WHERE part in (
                                      SELECT id FROM Part
                                          WHERE speech = 'прил') AND standart in (
                                              SELECT num FROM test)''').fetchall()
    sus = cur.execute('''SELECT word FROM Massive
                                 WHERE part in (
                                     SELECT id FROM Part
                                         WHERE speech = 'сущ') AND standart in (
                                             SELECT num FROM test)''').fetchall()
    glag = cur.execute('''SELECT word FROM Massive
                                  WHERE part in (
                                      SELECT id FROM Part
                                          WHERE speech = 'глаг') AND standart in (
                                              SELECT num FROM test)''').fetchall()
    con.commit()
    con.close()
    commands = {
        'сущ': [i[0] for i in sus],
        'прил': [i[0] for i in pril],
        'глаг': [i[0] for i in glag]
    }
    return commands


commands = getting()


def taking(order):  # Выбор случайных слов
    global commands
    commands = getting()
    ad = [rn.choice(commands[slovo]) if slovo in commands else slovo for slovo in
          order.split()]
    return ad


def sc(word, padej='nomn', pol='masc', odu='inan', dont=0):  # Функция для склонения слов
    prs = morph.parse(word)[0]
    if word in commands['сущ']:
        return prs.inflect({'sing', padej}).word
    elif word in commands['прил']:
        if pol == 'masc':
            if prs.inflect({pol, 'sing', padej}).tag.animacy is not None:
                return prs.inflect({odu, pol, 'sing', padej}).word
            else:
                return prs.inflect({pol, 'sing', padej}).word
        else:
            return prs.inflect({pol, 'sing', padej}).word
    elif word == 'который' or (word in commands['глаг'] and dont == 1):
        return prs.inflect({'sing', pol}).word
    elif word in commands['глаг']:
        if '1per' in prs.tag or '2per' in prs.tag or '3per' in prs.tag:
            return prs.inflect({'sing', pol, '3per'}).word
        return prs.inflect({'sing', pol}).word


def brain(order):  # Изначально lolgen был этой функцией. Если в кратце, то это главный алгоритм склонения
    pol = 'masc'
    padej = 'nomn'
    odu = 'inan'
    flag_s = 0
    global commands
    commands = getting()
    sus = commands['сущ']
    pril = commands['прил']
    glag = commands['глаг']

    ad = taking(order)

    for i in range(len(ad)):  # Цикл, проходящий по всем словам, и склоняющий их
        if ad[i] in glag:
            if flag_s == 1:
                ad[i] = sc('который', pol=pol, dont=1) + ' ' + sc(ad[i], pol=pol)
                ad[i - 1] += ','  # Добавление слова "который" если до этого идёт существительное
            padej = 'accs'
        elif ad[i] in sus:
            ad[i] = sc(ad[i], padej)
            pol = morph.parse(ad[i])[0].tag.gender
            odu = morph.parse(ad[i])[0].tag.animacy  # Следующие слова будут зависимы от этого
            flag_s = 1
        elif ad[i] in pril:
            for j in range(i + 1, len(ad)):
                if ad[j] in sus:
                    pol = morph.parse(ad[j])[0].tag.gender
                    odu = morph.parse(ad[j])[0].tag.animacy
                    break
                    # Получение признаков существительного для склонения прилагательного, которое стоит до
            ad[i] = sc(ad[i], padej, pol, odu)
    return ' '.join(ad).capitalize()


def trying(word, speech):  # Проверка на то, подхордит ли новое слово под критерии (по сути просто смесь brain() и sc())
    pol = 'masc'
    padej = 'accs'
    odu = 'inan'
    prs = morph.parse(word)[0]
    if speech == 'VERB':
        if '1per' in prs.tag or '2per' in prs.tag or '3per' in prs.tag:
            word = prs.inflect({'sing', pol, '3per'}).word
        else:
            try:
                word = prs.inflect({'sing', pol}).word
            except Exception:
                return True
    elif speech == 'NOUN':
        try:
            word = prs.inflect({'sing', padej}).word
        except Exception:
            return True
    elif speech == 'ADJF':
        if prs.inflect({pol, 'sing', padej}).tag.animacy is not None:
            try:
                word = prs.inflect({odu, pol, 'sing', padej}).word
            except Exception:
                return True
        else:
            try:
                word = prs.inflect({pol, 'sing', padej}).word
            except Exception:
                return True
    return False


class Lolgen(QMainWindow):  # Главное окно
    def __init__(self):
        super().__init__()
        uic.loadUi(io.StringIO(designs.design), self)
        self.initUI()

    def initUI(self):
        self.do_lol.clicked.connect(self.lolgen)
        self.neword.clicked.connect(self.newword)

    def lolgen(self):
        order = self.input.text()
        words = int(self.standart.isChecked())
        con = sqlite3.connect("DataBase.sqlite")  # Изменение БД с зависимости от галочки
        cur = con.cursor()
        cur.execute("""UPDATE test
                           SET num = ?""", (words,)).fetchall()
        con.commit()
        con.close()
        self.output.setText(brain(order))  # Вывод сгенерированного предложения

    def newword(self):  # Открытие второй формы
        self.new = Dialog()
        self.new.show()


class Dialog(QMainWindow):  # Вторая форма служит для добавления новых слов в БД
    def __init__(self):
        super().__init__()
        uic.loadUi(io.StringIO(designs.designed), self)
        self.initUI()

    def initUI(self):
        self.part.addItems(["Прилагательное", "Существительное", "Глагол"])
        self.saving.accepted.connect(self.adding)

    def adding(self):
        word = self.input.text().lower()
        speech = self.part.currentText()
        con = sqlite3.connect("DataBase.sqlite")
        cur = con.cursor()
        dct = {"Прилагательное": (1, commands['прил'], 'ADJF'), "Существительное": (2, commands['сущ'], 'NOUN'),
               "Глагол": (3, commands['глаг'], 'VERB')}
        if word.lower() in dct[speech][1]:  # Критерии добавления слов
            self.err = Error('Слово уже есть в базе данных')
            self.err.show()
        elif dct[speech][2] not in morph.parse(word)[0].tag.POS:
            self.err = Error('Неккоректно указана часть речи')
            self.err.show()
        elif trying(word, dct[speech][2]):
            self.err = Error('Слово не подходит по критериям')
            self.err.show()
        else:
            cur.execute("INSERT INTO Massive(word, part, standart) VALUES(?, ?, 1)",
                        (word.lower(), dct[speech][0])).fetchall()
            self.err = Error('Слово было успешно добавлено')
            self.err.show()

        con.commit()
        con.close()

        self.close()


class Error(QMainWindow):  # Третья форма, которая нужна для сообщений об ошибке/удаче
    def __init__(self, text):
        super().__init__()
        uic.loadUi(io.StringIO(designs.errored), self)
        self.label.setText(text)
        self.initUI()

    def initUI(self):
        self.buttons.accepted.connect(self.closing)

    def closing(self):
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Lolgen()
    ex.show()
    sys.exit(app.exec_())
