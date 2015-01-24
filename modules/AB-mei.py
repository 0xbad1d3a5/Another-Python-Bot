import os
import re
import http
import imghdr
import base64
import string
import random
import urllib
import subprocess
import requests

from urllib.request import urlopen

from modules import _BaseModule

class Module(_BaseModule.BaseModule):

    cmd = ".mei "

    def __init__(self, msg, share):
        super(Module, self).__init__(msg, share)

    def main(self):

        arg_list = list(self.args)

        # filter out some dangerous input
        arg_list = [a for a in arg_list if "../" not in a]
        arg_list = [a for a in arg_list if a != '*']
        arg_list = [a for a in arg_list if '/' not in a or re.search("http://|https://", a)]

        for i, arg in enumerate(arg_list):
            if re.search("http://|https://", arg):
                arg_list[i] = (arg, "IMG")
            else:
                arg_list[i] = (arg, "ARG")

        for i, arg in enumerate(arg_list):
            if arg[1] == "IMG":
                try:
                    image_http_resp = requests.get(arg[0])
                    if not imghdr.what(None, image_http_resp.content):
                        raise Exception
                    arg_list[i] = (image_http_resp.content, "IMG")
                except:
                    self.sendmsg("Error occured trying to get image(s)")
                    return

        file_names, size_before = self.processImage(arg_list)

        if len(file_names) > 10:
            self.sendmsg("ImageMagick resulted in more than 10 images, aborting")
            for f in file_names: os.remove(f)
            return

        optimized_images = []
        for f in file_names:
            optimized_images.append(self.optimizeImage(f))

        response = []
        size_after = 0
        for o in optimized_images:
            size_after += o[2]
            response.append(self.upload(o))

        if len(response) == 1:
            if size_after <= size_before:
                self.sendmsg("{} ({:.2f}% Reduction)".format(response[0], (1-size_after/size_before)*100))
            else:
                self.sendmsg("{} ({:.2f}% Increase)".format(response[0], (1-size_before/size_after)*100))
        else:
            for r in response:
                self.sendmsg(r)
            if size_after <= size_before:
                self.sendmsg("({:.2f}% Reduction)".format((1-size_after/size_before)*100))
            else:
                self.sendmsg("({:.2f}% Increase)".format((1-size_before/size_after)*100))

        for f in file_names: os.remove(f)

        return

    def randomName(self):
        return "data/images/_img_" + ''.join(random.choice(string.ascii_uppercase) for char in range(10))

    def processImage(self, arg_list):

        size = 0
        for i, arg in enumerate(arg_list):
            if arg[1] == "IMG":
                tempname = self.randomName()
                f = open(tempname, "wb")
                f.write(arg[0])
                f.close()
                size += os.path.getsize(tempname)
                arg_list[i] = (tempname, "IMG")

        if arg_list[-1][0] in ["png", "jpeg", "jpg", "gif"]:
            result_name = self.randomName() + '.' + arg_list[-1][0]
            arg_list.remove(arg_list[-1])
        else:
            result_name = self.randomName()
        arg_list.append((result_name, "ARG"))

        try:
            subprocess.check_call(["convert"] + [a[0] for a in arg_list])
        except:
            for arg in arg_list:
                if arg[1] == "IMG":
                    os.remove(arg[0])
            self.sendmsg("ImageMagick Error")
            return [], 0

        for arg in arg_list:
            if arg[1] == "IMG":
                os.remove(arg[0])

        file_names = os.listdir("data/images/")
        file_names = ["data/images/" + f for f in file_names if re.search("{0}.*".format(os.path.basename(result_name)), f)]

        return file_names, size

    def optimizeImage(self, file_name):

        image_type = imghdr.what(file_name)

        if image_type in ["jpeg", "png"]:
            if image_type == "jpeg":
                subprocess.check_call(["jpegoptim", "-s", file_name])
            if image_type == "png":
                subprocess.check_call(["optipng", "-fix", file_name])

        return (file_name, image_type, os.path.getsize(file_name))

    def upload(self, image_info):

        data = self.jsonread("AB-mei")
        meiurl = data["meiurl"]
        
        image = open(image_info[0], "rb")
        image_type = image_info[1]

        response = ""
        if image_type:
            data = { 'numFiles' : '1' }
            files = { ('ufile0', ('a.'+image_type, image, 'image/'+image_type)) }
            resp = requests.post("https://mei.animebytes.tv/upload_ac.php",
                                 files=files,
                                 data={ 'numFiles' : '1', 'Submit' : 'Upload' },
                                 allow_redirects=False)
            if resp != None:
                url = resp.headers["Location"]
                url = re.search("imageupload.php\?img=(.*)", url).group(1)
                url = meiurl + url
                if url != meiurl:
                    response = url
                else:
                    response = "ImageUpload Error: No image found"
            else:
                response = "ImageUpload Error: No response"
        
        return response
