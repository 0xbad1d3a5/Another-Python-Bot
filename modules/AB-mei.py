import threading
import http
import json
import re

class module(threading.Thread):

    cmd = ".mei"

    def __init__(self, msg, queue):
        super(module, self).__init__()
        self.msg = msg
        self.queue = queue
        self.data = json.load(open("modules/data/AB-mei", "r"))

    def run(self):
        imgurl = self.msg["MSG"]
        self.msg["MSG"] = self.imgupload(imgurl)
        self.queue.put(self.msg)
        return

    def reqpage(self, conn, method, url, body, header):
        try:
            conn.request(method, url, body, header)
            resp = conn.getresponse()
            conn.close()
            return resp
        except:
            return None

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
        
        resp = self.reqpage(MEI, "POST", "/upload_ac.php", reqbody, meiheader)
        if resp != None:
            url = resp.getheader("Location")
            url = re.search("imageupload.php\?img=(.*)", url).group(1)
            url = meiurl + url
            if url != meiurl:
                return url
            return "ImageUpload Error"
        else:
            return "ImageUpload Error"
