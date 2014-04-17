import threading
import http
import json
import re

from modules import _BaseModule

class Module(_BaseModule.BaseModule):

    cmd = ".mei"

    def __init__(self, msg, queue):
        super(Module, self).__init__(msg, queue)
        self.data = json.load(open("modules/data/AB-mei", "r"))

    def run(self):
        self.sendmsg(self.imgupload(self.msg["MSG"]))
        return

    def imgupload(self, imgurl):

        MEI = http.client.HTTPSConnection(self.data["MEI"])
        meiurl = self.data["meiurl"]
        meiheader = self.data["meiheader"]
        
        reqbody = ""
        reqbody += "--stopboundaryhere\r\n"
        reqbody += "Content-Disposition: form-data; name=\"uurl\"\r\n\r\n"
        reqbody += imgurl + "\r\n"
        reqbody += "--stopboundaryhere\r\n"
        reqbody += "Content-Disposition: form-data; name=\"Submit\"\r\n\r\n"
        reqbody += "Upload\r\n"
        reqbody += "--stopboundaryhere"
        
        resp = self.reqPage(MEI, "POST", "/upload_ac.php", reqbody, meiheader)
        if resp != None:
            url = resp.getheader("Location")
            url = re.search("imageupload.php\?img=(.*)", url).group(1)
            url = meiurl + url
            if url != meiurl:
                return url
            else:
                return "ImageUpload Error"
        else:
            return "ImageUpload Error"
