import re
import copy
import sqlite3
import functools

from modules import _BaseModule
from xml.etree import ElementTree
from subprocess import Popen, PIPE

class Module(_BaseModule.BaseModule):

    cmd = ".relex"

    def __init__(self, msg, share):
        super(Module, self).__init__(msg, share)

    def splitRelation(self, string):
        
        m = re.match("(.*?)\((.*?)\[(\d+)\], (.*?)\[(\d+)\]\)", string)
        if m:
            return [m.group(1), (m.group(2), int(m.group(3))), (m.group(4), int(m.group(5)))]
        else:
            return None
        
    def getRelations(self, string):
        
        p = Popen(["sh", "/home/xyresic/relex/webformat.sh"], stdin=PIPE, stdout=PIPE)
        out = p.communicate(string.encode("utf-8"))[0].decode("utf-8")
        out = re.sub(" xmlns=\".*?\"", "", out, count=1)

        doc = ElementTree.fromstring(out)

        relations = doc.find("sentence").find("parse").find("relations").text.split("\n")
        relations = [self.splitRelation(r) for r in relations if self.splitRelation(r)]

        return relations

    # find us some Subject-Verb-Object relations
    def findSVO(self, relations):

        relation_list = []

        for r in relations:
            print(r)

        # Find SVO
        SV = [r for r in relations if "subj" in r[0]]
        for sv in SV:
            for r in relations:
                if sv[1][0] == r[1][0] and sv[1][1] < r[2][1] and sv != r:
                    relation_list.append([sv[2][0], sv[1][0], r[2][0]])

        # Find predicative adjectives
        for r in relations:
            if r[0] == "_predadj":
                relation_list.append([r[1][0], "be", r[2][0]])

        return relation_list

    def flattenRawRelation(self, r):
        return [r[0], r[1][0], r[2][0]]

    def handleQuestion(self, conn, c, raw_relations):
        
        relations = []
        for r1 in raw_relations:
            for r2 in raw_relations:
                if r1[1][0] == r2[1][0] and r1 != r2:
                    relations.append([r2[0], r1[2][0], r1[1][0], r2[2][0]])

        results = []
        for r in relations:
            temp = copy.deepcopy(r)
            if r[1] in ["_%atLocation", "_%atTime", "_%because", "_%copula", "_$qVar"]:
                temp[1] = '%'
            if r[2] in ["_%atLocation", "_%atTime", "_%because", "_%copula", "_$qVar"]:
                temp[2] = '%'
            if r[3] in ["_%atLocation", "_%atTime", "_%because", "_%copula", "_$qVar"]:
                temp[3] = '%'
            rows = c.execute("SELECT * FROM svo WHERE subject LIKE ? AND verb LIKE ? and object LIKE ?", (temp[1], temp[2], temp[3]))
            for row in rows:
                results.append([row, r])

        for r in results:
            if r[1][0] == "_%atLocation":
                self.sendmsg(r)
            elif r[1][0] == "_%atTime":
                self.sendmsg(r)
            else:
                self.sendmsg(r)

    def initDB(self):
        
        conn = sqlite3.connect("data/relex_db.sqlite")
        c = conn.cursor()

        c.execute("CREATE TABLE IF NOT EXISTS svo (subject TEXT, verb TEXT, object TEXT, count INT)")
        conn.commit()

        return conn, c
        
    def main(self):

        if self.args[0] == "-show":
            for r in self.getRelations(self.msg.MSG[7:]):
                self.sendmsg(r)
            return

        conn, c = self.initDB()

        print("CURRENT DB")
        for row in c.execute("SELECT * FROM svo"):
            print(row)
        print("END DB")

        raw_relations = self.getRelations(self.msg.MSG)
        relations = self.findSVO(raw_relations)

        #print(raw_relations)
        flat_relations = functools.reduce(lambda x,y: x+y, [self.flattenRawRelation(r) for r in raw_relations])
        
        if "_%atLocation" in flat_relations or \
                "_%atTime" in flat_relations or \
                "_%because" in flat_relations or \
                "_%copula" in flat_relations or \
                "_$qVar" in flat_relations:
            self.handleQuestion(conn, c, raw_relations)
        else:
            for r in relations:
                self.sendmsg(r)
                exist = c.execute("SELECT * FROM svo WHERE subject=? AND verb=? AND object=?",
                                  (r[0], r[1], r[2]))
                exist = exist.fetchone()
                if exist:
                    count = exist[3] + 1
                    c.execute("UPDATE svo SET count={} WHERE subject='{}' AND verb='{}' AND object='{}'".format(count, r[0], r[1], r[2]))
                else:
                    c.execute("INSERT INTO svo VALUES (?,?,?,?)", (r[0], r[1], r[2], 1))
        conn.commit()
